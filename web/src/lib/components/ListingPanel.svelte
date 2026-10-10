<script lang="ts">
	/**
	 * What the analysis engine said about a pasted listing. Sits above the pin panel so the
	 * engine's view (asking price, GDV, strategy, risks) and the Land Registry evidence (local
	 * £/m², comparables) read as one analysis of the same property.
	 *
	 * The figures here are the engine's own; the panel re-computes nothing and says where they
	 * came from. Every section the engine did not fill is left out rather than shown as "—".
	 */
	import { onMount } from 'svelte';
	import { mapState } from '#lib/state.svelte.ts';
	import { readEngine, strategyTone, elapsed } from '#lib/listing.ts';
	import { gbp, signedPct } from '#lib/format.ts';

	let { onRerun }: { onRerun?: (url: string) => void } = $props();

	const listing = $derived(mapState.listing);
	const engine = $derived(listing.result ? readEngine(listing.result.fields) : null);
	const property = $derived(listing.result?.property ?? null);
	const host = $derived.by(() => {
		try {
			return listing.url ? new URL(listing.url).hostname.replace(/^www\./, '') : '';
		} catch {
			return '';
		}
	});

	let now = $state(Date.now());
	onMount(() => {
		const t = setInterval(() => (now = Date.now()), 1000);
		return () => clearInterval(t);
	});

	function pct(v: number | null): string {
		return v == null ? '—' : `${v}%`;
	}
	const placement = {
		postcode: 'Pinned to the postcode centroid.',
		street:
			'Pinned to the street, using the postcodes of past sales there. Drag the pin if it is wrong.',
		district:
			'Only the postcode district was given, so the pin is at its centre. Drag it to the property.'
	};
</script>

{#if listing.status !== 'idle'}
	<section class="panel listing" aria-live="polite">
		{#if listing.status === 'loading'}
			<h1>Analysing the listing</h1>
			<p class="muted small">
				{host || 'The listing'} is being read and the investment engine is running the numbers. This usually
				takes 30 to 60 seconds.
			</p>
			<p class="mono small muted">
				<span class="spinner" aria-hidden="true"></span>
				{elapsed(listing.startedAt ?? now, now)}
			</p>
		{:else if listing.status === 'error'}
			<header class="head">
				<h1>Could not analyse that listing</h1>
				<button class="btn" type="button" onclick={() => mapState.clearListing()}>Dismiss</button>
			</header>
			<p class="error" role="alert">{listing.error}</p>
			{#if listing.url}
				<p class="small">
					<button class="btn" type="button" onclick={() => onRerun?.(listing.url ?? '')}
						>Try again</button
					>
				</p>
			{/if}
		{:else if engine && property && listing.result}
			{@const r = listing.result}
			{@const tone = strategyTone(engine.strategy)}
			<header class="head">
				<div>
					<h1>{engine.address ?? property.address ?? 'The listing'}</h1>
					<p class="small muted">
						{[
							engine.propertyType,
							engine.bedrooms != null ? `${engine.bedrooms} bed` : null,
							engine.tenure,
							engine.agent
						]
							.filter(Boolean)
							.join(' · ')}
					</p>
				</div>
				<button class="btn" type="button" onclick={() => mapState.clearListing()}>Clear</button>
			</header>

			<p class="small">
				<!-- External link to the portal; the resolve() rule is for in-app routes. -->
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
				<a href={r.url} target="_blank" rel="noopener noreferrer">View the listing on {host} ↗</a>
			</p>

			<div class="headline">
				<span class="mono big">{gbp(engine.askingPrice)}</span>
				<span class="muted">asking</span>
				{#if engine.strategy}
					<span class="tone {tone}">{engine.strategy}</span>
				{/if}
			</div>
			{#if engine.category}
				<p class="small muted">{engine.category}</p>
			{/if}

			{#if property.precision}
				<p class="small muted">{placement[property.precision]}</p>
			{:else}
				<p class="small muted">
					We could not place this address on the map. Click the map or type its postcode to see the
					local evidence.
				</p>
			{/if}

			<h2>Engine estimates</h2>
			<dl class="grid">
				<div>
					<dt>Expected resale (GDV)</dt>
					<dd class="mono">{gbp(engine.gdv)}</dd>
				</div>
				<div>
					<dt>Refurbishment</dt>
					<dd class="mono">{gbp(engine.refurb)}</dd>
				</div>
				<div>
					<dt>Total project cost</dt>
					<dd class="mono">{gbp(engine.totalCost)}</dd>
				</div>
				<div>
					<dt>Engine score</dt>
					<dd class="mono">{engine.score ?? '—'}<span class="muted">/100</span></dd>
				</div>
			</dl>

			<div class="scenarios">
				<article>
					<h3>Buy, renovate, refinance</h3>
					<dl>
						<div>
							<dt>Maximum offer</dt>
							<dd class="mono strong">{gbp(engine.brrMao)}</dd>
						</div>
						<div>
							<dt>Equity created</dt>
							<dd class="mono">{gbp(engine.equity)}</dd>
						</div>
						{#if engine.cashLeft != null}
							<div>
								<dt>Cash left in</dt>
								<dd class="mono">{gbp(engine.cashLeft)}</dd>
							</div>
						{:else}
							<div>
								<dt>Cash released</dt>
								<dd class="mono">{gbp(engine.cashReleased)}</dd>
							</div>
						{/if}
					</dl>
					<details class="small">
						<summary>Workings</summary>
						<dl>
							<div>
								<dt>Purchase</dt>
								<dd class="mono">{gbp(engine.askingPrice)}</dd>
							</div>
							<div>
								<dt>Buying costs</dt>
								<dd class="mono">{gbp(engine.buyingCosts)}</dd>
							</div>
							<div>
								<dt>of which stamp duty</dt>
								<dd class="mono">{gbp(engine.stampDuty)}</dd>
							</div>
							<div>
								<dt>Refurbishment</dt>
								<dd class="mono">{gbp(engine.refurb)}</dd>
							</div>
							<div>
								<dt>Contingency</dt>
								<dd class="mono">{gbp(engine.contingency)}</dd>
							</div>
							<div>
								<dt>Bridge finance</dt>
								<dd class="mono">{gbp(engine.bridgeCost)}</dd>
							</div>
							<div>
								<dt>New mortgage</dt>
								<dd class="mono">{gbp(engine.brrMortgage)}</dd>
							</div>
							<div>
								<dt>Refinance costs</dt>
								<dd class="mono">{gbp(engine.refinanceCosts)}</dd>
							</div>
							<div>
								<dt>Bridge loan repaid</dt>
								<dd class="mono">{gbp(engine.bridgeLoan)}</dd>
							</div>
						</dl>
					</details>
				</article>
				<article>
					<h3>Buy, renovate, sell</h3>
					<dl>
						<div>
							<dt>Maximum offer</dt>
							<dd class="mono strong">{gbp(engine.flipMao)}</dd>
						</div>
						<div>
							<dt>Estimated profit</dt>
							<dd class="mono">{gbp(engine.profit)}</dd>
						</div>
						<div>
							<dt>Return on cost</dt>
							<dd class="mono">{pct(engine.roi)}</dd>
						</div>
					</dl>
					<details class="small">
						<summary>Workings</summary>
						<dl>
							<div>
								<dt>Total project cost</dt>
								<dd class="mono">{gbp(engine.totalCost)}</dd>
							</div>
							<div>
								<dt>Selling costs</dt>
								<dd class="mono">{gbp(engine.sellingCosts)}</dd>
							</div>
							<div>
								<dt>Expected resale</dt>
								<dd class="mono">{gbp(engine.gdv)}</dd>
							</div>
							{#if engine.valueGap != null && engine.askingPrice}
								<div>
									<dt>Resale vs asking</dt>
									<dd class="mono">{signedPct((engine.valueGap / engine.askingPrice) * 100)}</dd>
								</div>
							{/if}
						</dl>
					</details>
				</article>
			</div>

			{#if engine.summary}
				<h2>Engine summary</h2>
				<p class="prose">{engine.summary}</p>
			{/if}
			{#if engine.risks}
				<h2>Risks it noted</h2>
				<p class="prose">{engine.risks}</p>
			{/if}
			{#if engine.strategyNotes}
				<details class="small">
					<summary>Strategy notes</summary>
					<p class="prose">{engine.strategyNotes}</p>
				</details>
			{/if}
			{#if engine.refurbSummary}
				<details class="small">
					<summary>Refurbishment assessment</summary>
					<p class="prose">{engine.refurbSummary}</p>
				</details>
			{/if}

			<p class="small muted caveat">
				These figures are the stage-0 engine's estimates from reading the listing; the resale value
				and refurbishment cost are not yet checked against sold comparables. The Land Registry
				evidence for this location follows below.
				{#if r.cached}Analysed earlier; <button
						class="link"
						type="button"
						onclick={() => onRerun?.(r.url)}>run again</button
					>.{/if}
			</p>
		{/if}
	</section>
{/if}

<style>
	.panel {
		display: grid;
		gap: var(--space-3);
		align-content: start;
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--border);
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: start;
		gap: var(--space-2);
	}
	.headline {
		display: flex;
		align-items: baseline;
		gap: var(--space-2);
		flex-wrap: wrap;
	}
	.big {
		font-size: 24px;
		font-weight: 650;
	}
	.tone {
		font-weight: 600;
		padding: 0 8px;
		border-radius: 999px;
		border: 1px solid currentColor;
		font-size: 12px;
		line-height: 20px;
	}
	.tone.good {
		color: var(--good);
	}
	.tone.warn {
		color: var(--warn);
	}
	.tone.bad {
		color: var(--bad);
	}
	.error {
		color: var(--bad);
	}
	dl {
		margin: 0;
		display: grid;
		gap: 2px;
	}
	dl > div {
		display: flex;
		justify-content: space-between;
		gap: var(--space-2);
		align-items: baseline;
	}
	dt {
		color: var(--muted);
		font-size: 12px;
	}
	dd {
		margin: 0;
	}
	.grid {
		grid-template-columns: 1fr 1fr;
		gap: var(--space-2) var(--space-4);
	}
	.grid > div {
		flex-direction: column;
		align-items: start;
		gap: 0;
	}
	.scenarios {
		display: grid;
		gap: var(--space-3);
	}
	.scenarios article {
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: var(--space-2) var(--space-3);
		background: var(--panel-2);
		display: grid;
		gap: var(--space-2);
	}
	h3 {
		font-size: 13px;
	}
	.strong {
		font-weight: 650;
	}
	.prose {
		white-space: pre-wrap;
		font-size: 13px;
	}
	details summary {
		cursor: pointer;
		color: var(--muted);
	}
	details > :not(summary) {
		margin-top: var(--space-1);
	}
	.caveat {
		border-left: 3px solid var(--warn);
		padding-left: var(--space-2);
	}
	.link {
		border: 0;
		background: none;
		padding: 0;
		color: var(--accent);
		cursor: pointer;
		text-decoration: underline;
	}
	a {
		color: var(--accent);
	}
	.spinner {
		display: inline-block;
		width: 10px;
		height: 10px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		vertical-align: -1px;
		margin-right: 6px;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.spinner {
			animation: none;
		}
	}
</style>
