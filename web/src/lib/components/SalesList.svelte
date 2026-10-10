<script lang="ts">
	import type { Sale } from '#lib/api.ts';
	import { gbp, ppm2, m2, dateOf, metres } from '#lib/format.ts';
	import { colourFor, textOn } from '#lib/colour.ts';

	let { sales, empty = 'No sales to show.' }: { sales: Sale[]; empty?: string } = $props();
</script>

{#if sales.length === 0}
	<p class="muted small">{empty}</p>
{:else}
	<ul class="sales">
		{#each sales as s (s.transaction_id)}
			<li>
				<div class="top">
					<span class="addr">{s.address}</span>
					<span class="mono price">{gbp(s.price)}</span>
				</div>
				<div class="bottom small muted">
					<span>{dateOf(s.date_of_transfer)} · {s.postcode} · {metres(s.distance_m)}</span>
					<span
						class="mono chip"
						style:background={colourFor(s.ppm2_adj ?? s.ppm2)}
						style:color={textOn(colourFor(s.ppm2_adj ?? s.ppm2))}
					>
						{ppm2(s.ppm2_adj ?? s.ppm2)}
					</span>
					<span>{m2(s.floor_area_m2)}{s.energy_rating ? ` · EPC ${s.energy_rating}` : ''}</span>
				</div>
			</li>
		{/each}
	</ul>
{/if}

<style>
	.sales {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: var(--space-2);
	}
	li {
		padding: var(--space-2) 0;
		border-top: 1px solid var(--border);
	}
	.top,
	.bottom {
		display: flex;
		justify-content: space-between;
		gap: var(--space-2);
		align-items: baseline;
	}
	.bottom {
		flex-wrap: wrap;
		margin-top: 2px;
	}
	.addr {
		font-weight: 550;
	}
	.price {
		font-weight: 650;
		white-space: nowrap;
	}
	.chip {
		padding: 0 6px;
		border-radius: 999px;
		font-size: 11px;
		line-height: 18px;
	}
</style>
