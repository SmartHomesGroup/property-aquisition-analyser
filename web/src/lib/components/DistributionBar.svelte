<script lang="ts">
	/**
	 * Where a value sits in a local distribution: p10..p90 track, p25..p75 band, median tick,
	 * optional subject marker. Pure presentation; the numbers are labelled next to it.
	 */
	import type { Distribution } from '#lib/api.ts';
	import { gbpShort } from '#lib/format.ts';

	let { dist, subject = null }: { dist: Distribution; subject?: number | null } = $props();

	const domain = $derived.by(() => {
		const vals = [dist.p10, dist.p90, subject].filter((v): v is number => v != null);
		if (vals.length === 0) return null;
		const lo = Math.min(...vals) * 0.9;
		const hi = Math.max(...vals) * 1.1;
		return { lo, hi };
	});

	function pct(v: number | null | undefined): string {
		if (v == null || !domain) return '0%';
		return `${((v - domain.lo) / (domain.hi - domain.lo)) * 100}%`;
	}
</script>

{#if domain && dist.median != null}
	<div class="bar" aria-hidden="true">
		<div class="track" style:left={pct(dist.p10)} style:right="calc(100% - {pct(dist.p90)})"></div>
		<div class="band" style:left={pct(dist.p25)} style:right="calc(100% - {pct(dist.p75)})"></div>
		<div class="tick median" style:left={pct(dist.median)}></div>
		{#if subject != null}
			<div class="tick subject" style:left={pct(subject)}></div>
		{/if}
	</div>
	<div class="labels mono" aria-hidden="true">
		<span style:left={pct(dist.p10)}>{gbpShort(dist.p10 ?? 0)}</span>
		<span style:left={pct(dist.median)} class="median">{gbpShort(dist.median)}</span>
		<span style:left={pct(dist.p90)}>{gbpShort(dist.p90 ?? 0)}</span>
	</div>
{/if}

<style>
	.bar {
		position: relative;
		height: 14px;
		margin: var(--space-3) 0 var(--space-1);
	}
	.track {
		position: absolute;
		top: 5px;
		height: 4px;
		background: var(--border);
		border-radius: 2px;
	}
	.band {
		position: absolute;
		top: 3px;
		height: 8px;
		background: var(--accent);
		opacity: 0.45;
		border-radius: 2px;
	}
	.tick {
		position: absolute;
		top: 0;
		width: 2px;
		height: 14px;
		transform: translateX(-1px);
	}
	.tick.median {
		background: var(--text);
	}
	.tick.subject {
		background: var(--bad);
		width: 3px;
		height: 18px;
		top: -2px;
		border-radius: 1px;
	}
	.labels {
		position: relative;
		height: 14px;
		font-size: 10px;
		color: var(--muted);
	}
	.labels span {
		position: absolute;
		transform: translateX(-50%);
		white-space: nowrap;
	}
	.labels .median {
		color: var(--text);
		font-weight: 650;
	}
</style>
