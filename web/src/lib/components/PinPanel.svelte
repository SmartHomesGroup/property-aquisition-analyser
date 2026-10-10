<script lang="ts">
	/**
	 * The pin-drop analysis: local £/m² distribution around the pin, the subject's position in it
	 * when the user supplies a price and floor area, recent sales, and comparables.
	 * Every figure is shown with its bracket (radius, window, type, n, reference dates).
	 */
	import { api, ApiError, PROPERTY_TYPES, type AreaStats, type Comparables } from '#lib/api.ts';
	import { mapState } from '#lib/state.svelte.ts';
	import { gbp, ppm2, count, monthOf, dateOf, signedPct, ordinal, m2 } from '#lib/format.ts';
	import DistributionBar from './DistributionBar.svelte';
	import SalesList from './SalesList.svelte';

	const RADII = [250, 500, 1000] as const;

	let stats = $state<AreaStats | null>(null);
	let comps = $state<Comparables | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let seq = 0;

	// Refetch whenever the pin, filters or subject inputs change.
	$effect(() => {
		const pin = mapState.pin;
		const { window, ptype, radiusM } = mapState;
		const { askingPrice, floorAreaM2, propertyType } = mapState.subject;
		if (!pin) {
			stats = null;
			comps = null;
			return;
		}
		const mine = ++seq;
		loading = true;
		error = null;
		const haveSubject = askingPrice != null && floorAreaM2 != null && floorAreaM2 > 0;
		Promise.all([
			api.area({
				lat: pin.lat,
				lon: pin.lng,
				radius_m: radiusM,
				window,
				ptype,
				asking_price: haveSubject ? askingPrice : undefined,
				floor_area_m2: haveSubject ? floorAreaM2 : undefined
			}),
			propertyType && floorAreaM2
				? api.comparables({
						lat: pin.lat,
						lon: pin.lng,
						ptype: propertyType,
						floor_area_m2: floorAreaM2,
						radius_m: Math.max(radiusM, 1000),
						window
					})
				: Promise.resolve(null)
		])
			.then(([a, c]) => {
				if (mine !== seq) return;
				stats = a;
				comps = c;
			})
			.catch((err) => {
				if (mine !== seq) return;
				error = err instanceof ApiError ? err.message : 'Could not reach the server';
			})
			.finally(() => {
				if (mine === seq) loading = false;
			});
	});

	const verdict = $derived.by(() => {
		const s = stats?.subject;
		if (!s || s.vs_median_pct == null) return null;
		const v = s.vs_median_pct;
		if (v <= -15) return { text: 'Well below the local £/m²', tone: 'good' };
		if (v <= -5) return { text: 'Below the local £/m²', tone: 'good' };
		if (v < 5) return { text: 'In line with the local £/m²', tone: 'neutral' };
		if (v < 15) return { text: 'Above the local £/m²', tone: 'warn' };
		return { text: 'Well above the local £/m²', tone: 'bad' };
	});

	function numberOrNull(v: string): number | null {
		const n = Number(v.replace(/[£,\s]/g, ''));
		return Number.isFinite(n) && n > 0 ? n : null;
	}
</script>

<section class="panel" aria-live="polite">
	{#if !mapState.pin}
		<h1>Drop a pin</h1>
		<p class="muted">
			Click the map or enter a postcode to see what nearby homes sold for per square metre, and how
			an asking price compares.
		</p>
	{:else}
		<header class="head">
			<div>
				<h1>
					{mapState.pin.source === 'listing'
						? 'Around the listing'
						: (mapState.pin.label ?? 'Pinned location')}
				</h1>
				<p class="small muted mono">
					{mapState.pin.lat.toFixed(5)}, {mapState.pin.lng.toFixed(5)}
				</p>
			</div>
			<button class="btn" type="button" onclick={() => mapState.clearPin()}>Clear</button>
		</header>

		<div class="controls">
			<div class="segmented" role="group" aria-label="Radius">
				{#each RADII as r (r)}
					<button
						type="button"
						aria-pressed={mapState.radiusM === r}
						onclick={() => (mapState.radiusM = r)}
					>
						{r >= 1000 ? `${r / 1000} km` : `${r} m`}
					</button>
				{/each}
			</div>
		</div>

		<h2>The property (optional)</h2>
		<div class="subject">
			<div class="field">
				<label for="asking">Asking price</label>
				<input
					id="asking"
					inputmode="numeric"
					placeholder="£425,000"
					value={mapState.subject.askingPrice ?? ''}
					onchange={(e) => (mapState.subject.askingPrice = numberOrNull(e.currentTarget.value))}
				/>
			</div>
			<div class="field">
				<label for="area">Floor area (m²)</label>
				<input
					id="area"
					inputmode="decimal"
					placeholder="e.g. 96"
					value={mapState.subject.floorAreaM2 ?? ''}
					onchange={(e) => (mapState.subject.floorAreaM2 = numberOrNull(e.currentTarget.value))}
				/>
			</div>
			<div class="field type">
				<label for="ptype">Type</label>
				<div
					class="segmented"
					id="ptype"
					role="group"
					aria-label="Property type of the pinned home"
				>
					{#each PROPERTY_TYPES.filter((t) => t.code !== 'A') as t (t.code)}
						<button
							type="button"
							aria-pressed={mapState.subject.propertyType === t.code}
							onclick={() =>
								(mapState.subject.propertyType =
									mapState.subject.propertyType === t.code
										? null
										: (t.code as 'D' | 'S' | 'T' | 'F'))}
						>
							{t.label}
						</button>
					{/each}
				</div>
			</div>
		</div>

		{#if error}
			<p class="error" role="alert">{error}</p>
		{:else if stats}
			{@const b = stats.bracket}
			<h2>Local £/m² {loading ? '· updating…' : ''}</h2>
			{#if b.n === 0}
				<p class="muted">
					No matching sales within {b.radius_m} m in the last {b.window_months} months ({b.property_type_label}).
					Widen the radius or window.
				</p>
			{:else}
				<div class="headline">
					<span class="mono big">{ppm2(stats.ppm2_adj.median)}</span>
					<span class="muted">median</span>
				</div>
				<DistributionBar dist={stats.ppm2_adj} subject={stats.subject?.ppm2 ?? null} />
				<p class="bracket small muted">
					Based on <strong>{count(b.n)}</strong> sales of {b.property_type_label} within
					<strong>{b.radius_m} m</strong>, {dateOf(b.since)} to {dateOf(b.until)}, with prices
					adjusted to {monthOf(b.hpi_ref_month)} using the UK House Price Index. Middle half
					{ppm2(stats.ppm2_adj.p25)} – {ppm2(stats.ppm2_adj.p75)}; typical home
					{m2(stats.ppm2_adj.median_floor_area_m2)}.
				</p>
			{/if}

			{#if stats.subject}
				{@const s = stats.subject}
				<h2>This asking price</h2>
				<div class="headline">
					<span class="mono big">{ppm2(s.ppm2)}</span>
					{#if verdict}<span class="tone {verdict.tone}">{verdict.text}</span>{/if}
				</div>
				{#if s.vs_median_pct != null && s.percentile != null}
					<p class="small">
						{gbp(s.asking_price)} over {m2(s.floor_area_m2)} is
						<strong>{signedPct(s.vs_median_pct)}</strong> against the local median. About
						<strong>{Math.round(s.percentile)}%</strong> of nearby sales were cheaper per m² ({ordinal(
							s.percentile
						)} percentile).
					</p>
				{/if}
				<details class="small">
					<summary>What could make this wrong</summary>
					<ul>
						<li>Condition, extensions and outside space are not in the data.</li>
						<li>Floor areas come from EPC certificates and may be out of date.</li>
						<li>Sales geocode to postcode centroids, not individual buildings.</li>
						<li>
							{count(b.n)} sales is {b.n < 15 ? 'a small sample' : 'a reasonable sample'}; the
							middle-half range shows the spread.
						</li>
						<li>Land Registry data lags completions by weeks to months.</li>
					</ul>
				</details>
			{/if}

			{#if comps}
				<h2>Closest comparables</h2>
				<p class="small muted">
					{comps.bracket.property_type_label}, {Math.round(comps.floor_area_m2)} m² ± {comps.tolerance_pct}%,
					within {comps.bracket.radius_m} m, last {comps.bracket.window_months} months.
				</p>
				<SalesList sales={comps.sales} empty="No close comparables with these criteria." />
			{/if}

			{#if b.n > 0}
				<h2>Recent sales nearby</h2>
				<SalesList sales={stats.recent_sales} />
			{/if}
		{:else if loading}
			<p class="muted">Loading…</p>
		{/if}
	{/if}
</section>

<style>
	.panel {
		display: grid;
		gap: var(--space-3);
		align-content: start;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: start;
		gap: var(--space-2);
	}
	.controls {
		display: flex;
		gap: var(--space-2);
		flex-wrap: wrap;
	}
	.subject {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-2);
	}
	.subject .type {
		grid-column: 1 / -1;
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
	.bracket strong {
		color: var(--text);
	}
	.tone {
		font-weight: 600;
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
	details summary {
		cursor: pointer;
		color: var(--muted);
	}
	details ul {
		margin: var(--space-1) 0 0;
		padding-left: 18px;
		color: var(--muted);
	}
</style>
