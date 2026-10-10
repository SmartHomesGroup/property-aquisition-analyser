<script lang="ts">
	import { PROPERTY_TYPES, WINDOWS } from '#lib/api.ts';
	import { mapState } from '#lib/state.svelte.ts';
</script>

<div class="filters">
	<div class="segmented" role="group" aria-label="Time window">
		{#each WINDOWS as w (w.months)}
			<button
				type="button"
				aria-pressed={mapState.window === w.months}
				onclick={() => (mapState.window = w.months)}>{w.label}</button
			>
		{/each}
	</div>
	<div class="segmented" role="group" aria-label="Property type">
		{#each PROPERTY_TYPES as t (t.code)}
			<button
				type="button"
				aria-pressed={mapState.ptype === t.code}
				onclick={() => (mapState.ptype = t.code)}>{t.label}</button
			>
		{/each}
	</div>
</div>

<style>
	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}
	.segmented button {
		font-size: 12px;
	}
</style>
