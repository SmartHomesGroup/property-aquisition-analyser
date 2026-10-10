<script lang="ts">
	import { legendRows } from '#lib/colour.ts';
	import { PROPERTY_TYPES, WINDOWS } from '#lib/api.ts';
	import { mapState } from '#lib/state.svelte.ts';

	const rows = legendRows();
	const typeLabel = $derived(
		PROPERTY_TYPES.find((t) => t.code === mapState.ptype)?.label.toLowerCase() ?? ''
	);
	const windowLabel = $derived(WINDOWS.find((w) => w.months === mapState.window)?.label ?? '');
</script>

<div class="legend" aria-label="Map legend">
	<div class="title">£ per m², HPI-adjusted</div>
	<ul>
		{#each rows as row (row.label)}
			<li>
				<span class="swatch" style:background={row.colour}></span>
				<span class="mono">{row.label}</span>
			</li>
		{/each}
	</ul>
	<div class="note">
		Median of sales in each square · {typeLabel} · last {windowLabel} · squares with fewer than 5 sales
		are not shown
	</div>
</div>

<style>
	.legend {
		background: var(--panel);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: var(--space-2) var(--space-3);
		font-size: 11px;
		max-width: 220px;
	}
	.title {
		font-weight: 650;
		margin-bottom: var(--space-1);
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 2px;
	}
	li {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}
	.swatch {
		width: 14px;
		height: 10px;
		border: 1px solid rgba(0, 0, 0, 0.15);
		flex: none;
	}
	.note {
		color: var(--muted);
		margin-top: var(--space-2);
		line-height: 1.35;
	}
</style>
