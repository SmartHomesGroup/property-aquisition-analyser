<script lang="ts">
	/**
	 * The one box for both entry points: paste a listing link, or type a postcode.
	 * A link goes to the analysis engine and, when it answers, the listing lands on the map with
	 * its asking price filled in. A postcode drops the pin straight away (our own Code-Point
	 * table; no third-party geocoder).
	 */
	import type * as maplibregl from 'maplibre-gl';
	import { api, ApiError } from '#lib/api.ts';
	import { mapState } from '#lib/state.svelte.ts';
	import { looksLikeUrl } from '#lib/listing.ts';

	let { map, listingEnabled = true }: { map?: maplibregl.Map; listingEnabled?: boolean } = $props();

	let value = $state('');
	let busy = $state(false);
	let error = $state<string | null>(null);

	const analysing = $derived(mapState.listing.status === 'loading');

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		const q = value.trim();
		if (!q || busy || analysing) return;
		error = null;
		if (looksLikeUrl(q)) await analyse(q);
		else await postcode(q);
	}

	async function postcode(pc: string) {
		busy = true;
		try {
			const loc = await api.postcode(pc);
			mapState.dropPin(loc.lon, loc.lat, 'postcode', loc.postcode);
			map?.flyTo({ center: [loc.lon, loc.lat], zoom: Math.max(map.getZoom(), 15), speed: 1.4 });
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Could not reach the server';
		} finally {
			busy = false;
		}
	}

	export async function analyse(url: string, refresh = false) {
		if (!listingEnabled) {
			error = 'Listing analysis is not available on this server';
			return;
		}
		mapState.startListing(url);
		try {
			const result = await api.analyseListing(url, refresh);
			mapState.finishListing(result);
			const loc = result.property.location;
			if (loc) {
				const zoom = { postcode: 15, street: 15, district: 12 }[
					result.property.precision ?? 'district'
				];
				map?.flyTo({ center: [loc.lon, loc.lat], zoom, speed: 1.2 });
			}
			value = '';
		} catch (err) {
			mapState.failListing(err instanceof ApiError ? err.message : 'Could not reach the server');
		}
	}
</script>

<form class="search" onsubmit={submit} role="search">
	<label class="visually-hidden" for="q">Listing link or postcode</label>
	<input
		id="q"
		name="q"
		type="text"
		placeholder={listingEnabled
			? 'Paste a Rightmove link, or a postcode'
			: 'Postcode, e.g. N11 2AB'}
		autocomplete="off"
		spellcheck="false"
		bind:value
		aria-invalid={error ? 'true' : undefined}
		disabled={analysing}
	/>
	<button class="btn primary" type="submit" disabled={busy || analysing}>
		{analysing ? 'Analysing…' : busy ? '…' : 'Go'}
	</button>
	{#if error}<span class="error" role="alert">{error}</span>{/if}
</form>

<style>
	.search {
		display: flex;
		gap: var(--space-2);
		align-items: center;
		flex-wrap: wrap;
		flex: 1 1 320px;
	}
	input {
		border: 1px solid var(--border);
		border-radius: var(--radius);
		background: var(--panel);
		padding: 6px 10px;
		min-height: 32px;
		flex: 1 1 220px;
		min-width: 0;
	}
	input:disabled {
		color: var(--muted);
	}
	.error {
		color: var(--bad);
		font-size: 12px;
	}
	.visually-hidden {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
	}
</style>
