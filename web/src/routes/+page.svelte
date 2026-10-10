<script lang="ts">
	import type * as maplibregl from 'maplibre-gl';
	import { onMount } from 'svelte';
	import { api, type BuildInfo } from '#lib/api.ts';
	import { count, dateOf, monthOf } from '#lib/format.ts';
	import PriceMap from '#lib/components/PriceMap.svelte';
	import Legend from '#lib/components/Legend.svelte';
	import FilterBar from '#lib/components/FilterBar.svelte';
	import SearchBox from '#lib/components/SearchBox.svelte';
	import ListingPanel from '#lib/components/ListingPanel.svelte';
	import PinPanel from '#lib/components/PinPanel.svelte';

	let map = $state<maplibregl.Map | undefined>(undefined);
	let meta = $state<BuildInfo | null>(null);
	let apiDown = $state(false);
	let search = $state<SearchBox | undefined>(undefined);

	onMount(async () => {
		try {
			meta = await api.meta();
		} catch {
			apiDown = true;
		}
	});

	// Development hook so tools/ scripts can drive the map (zoom tests, screenshots).
	$effect(() => {
		if (import.meta.env.DEV && map) (window as unknown as { __paaMap?: unknown }).__paaMap = map;
	});
</script>

<div class="app">
	<header class="topbar">
		<div class="brand">
			<span class="mark" aria-hidden="true"></span>
			<span>Property Acquisition Analyser</span>
		</div>
		<SearchBox bind:this={search} {map} listingEnabled={meta?.listing_analysis ?? true} />
		<FilterBar />
	</header>

	<main class="stage">
		<PriceMap bind:map />
		<div class="overlay legend-slot"><Legend /></div>
		{#if apiDown}
			<div class="overlay banner" role="alert">
				The analysis API is not reachable. The map still works; pin analysis will not.
			</div>
		{:else if meta && !meta.ref_date}
			<div class="overlay banner" role="status">
				No data has been built yet. Run the pipeline (see backend/README.md).
			</div>
		{:else if meta?.synthetic}
			<div class="overlay banner danger" role="alert">
				Development build: floor areas are synthetic, so every £/m² shown here is fake.
			</div>
		{/if}
	</main>

	<aside class="side">
		<ListingPanel onRerun={(url) => search?.analyse(url, true)} />
		<PinPanel />
		{#if meta?.ref_date}
			<footer class="small muted">
				<p>
					{count(meta.sales_enriched)} sales with floor area, latest {dateOf(meta.ref_date)}; prices
					indexed to {monthOf(meta.hpi_ref_month)}.
				</p>
				{#each meta.attribution as line (line)}
					<p>{line}</p>
				{/each}
				<p>
					Basemap © <a href="https://openfreemap.org">OpenFreeMap</a> ©
					<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.
				</p>
				<p>Not financial advice. Sold prices only; current condition is unknown.</p>
			</footer>
		{/if}
	</aside>
</div>

<style>
	.app {
		height: 100dvh;
		display: grid;
		grid-template-columns: 1fr var(--panel-width);
		grid-template-rows: auto 1fr;
		grid-template-areas:
			'top top'
			'stage side';
	}
	.topbar {
		grid-area: top;
		display: flex;
		align-items: center;
		gap: var(--space-4);
		flex-wrap: wrap;
		padding: var(--space-2) var(--space-4);
		border-bottom: 1px solid var(--border);
		background: var(--panel);
	}
	.brand {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-weight: 700;
		margin-right: auto;
	}
	.mark {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		background: var(--accent);
	}
	.stage {
		grid-area: stage;
		position: relative;
		min-height: 0;
	}
	.overlay {
		position: absolute;
		z-index: 2;
	}
	.legend-slot {
		left: var(--space-3);
		bottom: var(--space-5);
	}
	.banner.danger {
		border-left-color: var(--bad);
		font-weight: 600;
	}
	.banner {
		top: var(--space-3);
		left: 50%;
		transform: translateX(-50%);
		background: var(--panel);
		border: 1px solid var(--border);
		border-left: 3px solid var(--warn);
		border-radius: var(--radius);
		padding: var(--space-2) var(--space-3);
		box-shadow: var(--shadow);
		max-width: min(92%, 520px);
	}
	.side {
		grid-area: side;
		overflow-y: auto;
		padding: var(--space-4);
		border-left: 1px solid var(--border);
		background: var(--panel);
		display: grid;
		gap: var(--space-5);
		align-content: start;
	}
	footer p + p {
		margin-top: var(--space-1);
	}

	@media (max-width: 820px) {
		.app {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr minmax(200px, 42dvh);
			grid-template-areas:
				'top'
				'stage'
				'side';
		}
		.side {
			border-left: 0;
			border-top: 1px solid var(--border);
		}
		.legend-slot {
			display: none;
		}
	}
</style>
