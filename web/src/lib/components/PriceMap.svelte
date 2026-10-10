<script lang="ts">
	/**
	 * The map: basemap, £/m² cells from Martin, per-postcode points at street zoom,
	 * a hover readout, and the draggable pin. Click anywhere to drop the pin.
	 *
	 * Cells come in zoom bands (see bands.ts). Each band is its own source, fetched at a single
	 * zoom and overzoomed, so the map only downloads new tiles when the cell size changes.
	 */
	import {
		MapLibre,
		VectorTileSource,
		FillLayer,
		LineLayer,
		CircleLayer,
		Marker,
		Popup,
		NavigationControl,
		ScaleControl,
		AttributionControl
	} from 'svelte-maplibre-gl';
	import type * as maplibregl from 'maplibre-gl';
	import { config, GB_BOUNDS, INITIAL_VIEW, MAX_BOUNDS } from '#lib/config.ts';
	import { mapState } from '#lib/state.svelte.ts';
	import { stepExpression } from '#lib/colour.ts';
	import { CELL_BANDS, POSTCODE_BAND } from '#lib/bands.ts';
	import { installWheelZoom } from '#lib/wheelZoom.ts';
	import { ppm2, count, monthOf, m2, dateOf } from '#lib/format.ts';

	interface CellProps {
		size: number;
		n: number;
		median: number;
		p25: number | null;
		p75: number | null;
		median_floor_area: number | null;
		median_date: string | null;
	}
	interface PostcodeProps {
		postcode: string;
		n: number;
		median: number;
		latest_sale: string;
	}
	type Hover =
		| { kind: 'cell'; lnglat: maplibregl.LngLat; p: CellProps }
		| { kind: 'postcode'; lnglat: maplibregl.LngLat; p: PostcodeProps };

	let { map = $bindable<maplibregl.Map | undefined>(undefined) }: { map?: maplibregl.Map } =
		$props();

	let hover = $state<Hover | null>(null);

	const cellsUrl = $derived(`${config.tilesUrl}/${mapState.cellsTiles}`);
	const postcodesUrl = $derived(`${config.tilesUrl}/${mapState.postcodeTiles}`);
	const fill = stepExpression('median');
	const gbBbox: [number, number, number, number] = [
		GB_BOUNDS[0][0],
		GB_BOUNDS[0][1],
		GB_BOUNDS[1][0],
		GB_BOUNDS[1][1]
	];

	// Momentum wheel zoom replaces MapLibre's stepped default (wheelZoom.ts).
	$effect(() => {
		if (!map) return;
		return installWheelZoom(map);
	});

	// MapLibre opens the compact attribution on first render and leaves it covering the map
	// until clicked. The full credits are also in the page footer, so start it collapsed.
	$effect(() => {
		if (!map) return;
		const m = map;
		const collapse = () =>
			m
				.getContainer()
				.querySelector('.maplibregl-compact-show')
				?.classList.remove('maplibregl-compact-show');
		m.once('idle', collapse);
	});

	function onMapClick(e: maplibregl.MapMouseEvent) {
		mapState.dropPin(e.lngLat.lng, e.lngLat.lat, 'click');
	}

	function onCellMove(e: maplibregl.MapLayerMouseEvent) {
		const f = e.features?.[0];
		if (!f) return;
		hover = { kind: 'cell', lnglat: e.lngLat, p: f.properties as unknown as CellProps };
	}
	function onPostcodeMove(e: maplibregl.MapLayerMouseEvent) {
		const f = e.features?.[0];
		if (!f) return;
		hover = { kind: 'postcode', lnglat: e.lngLat, p: f.properties as unknown as PostcodeProps };
	}
	function onLeave() {
		hover = null;
	}

	// The marker's position is two-way bound; a drag end commits it to shared state.
	let pinLngLat = $state<[number, number]>([0, 0]);
	$effect(() => {
		if (mapState.pin) pinLngLat = [mapState.pin.lng, mapState.pin.lat];
	});
	function onPinDragEnd() {
		const [lng, lat] = pinLngLat;
		mapState.dropPin(lng, lat, 'drag');
	}

	const attribution =
		'Contains HM Land Registry data © Crown copyright and database right 2026 (OGL v3). ' +
		'Contains OS data © Crown copyright and database right 2026. ' +
		'Basemap © <a href="https://openfreemap.org">OpenFreeMap</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
</script>

<MapLibre
	bind:map
	class="map"
	style={config.basemapStyle}
	center={INITIAL_VIEW.center}
	zoom={INITIAL_VIEW.zoom}
	maxBounds={MAX_BOUNDS}
	minZoom={5}
	maxZoom={18}
	attributionControl={false}
	autoloadGlobalCss={false}
	cursor="crosshair"
	onclick={onMapClick}
>
	{#key cellsUrl}
		{#each CELL_BANDS as band (band.size)}
			<VectorTileSource
				id="cells-{band.size}"
				tiles={[cellsUrl]}
				minzoom={band.fetchZoom}
				maxzoom={band.fetchZoom}
				bounds={gbBbox}
			>
				<FillLayer
					id="cells-{band.size}-fill"
					sourceLayer="cells"
					minzoom={band.minzoom}
					maxzoom={band.maxzoom}
					paint={{
						'fill-color': fill,
						'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 13, 0.6, 15, 0.35]
					}}
					onmousemove={onCellMove}
					onmouseleave={onLeave}
				/>
				<LineLayer
					id="cells-{band.size}-line"
					sourceLayer="cells"
					minzoom={band.minzoom}
					maxzoom={band.maxzoom}
					paint={{ 'line-color': 'rgba(20, 24, 29, 0.18)', 'line-width': 0.5 }}
				/>
			</VectorTileSource>
		{/each}
	{/key}

	{#key postcodesUrl}
		<VectorTileSource
			id="postcodes"
			tiles={[postcodesUrl]}
			minzoom={POSTCODE_BAND.fetchZoom}
			maxzoom={POSTCODE_BAND.fetchZoom}
			bounds={gbBbox}
		>
			<CircleLayer
				id="postcodes-circle"
				sourceLayer="postcodes"
				minzoom={POSTCODE_BAND.minzoom}
				paint={{
					'circle-color': fill,
					'circle-radius': ['interpolate', ['linear'], ['get', 'n'], 1, 5, 10, 9, 40, 14],
					'circle-stroke-color': '#ffffff',
					'circle-stroke-width': 1.5,
					'circle-opacity': 0.95
				}}
				onmousemove={onPostcodeMove}
				onmouseleave={onLeave}
			/>
		</VectorTileSource>
	{/key}

	{#if hover}
		<Popup
			lnglat={hover.lnglat}
			closeButton={false}
			closeOnClick={false}
			offset={14}
			maxWidth="260px"
		>
			{#if hover.kind === 'cell'}
				<div class="readout">
					<div class="value">{ppm2(hover.p.median)}</div>
					<div class="line">
						median of {count(hover.p.n)} sales · ~{hover.p.size >= 1000
							? `${hover.p.size / 1000} km`
							: `${hover.p.size} m`} square
					</div>
					{#if hover.p.p25 != null && hover.p.p75 != null}
						<div class="line">middle half {ppm2(hover.p.p25)} – {ppm2(hover.p.p75)}</div>
					{/if}
					<div class="line">
						typical size {m2(hover.p.median_floor_area)} · typical sale {monthOf(
							hover.p.median_date
						)}
					</div>
				</div>
			{:else}
				<div class="readout">
					<div class="value">{hover.p.postcode}</div>
					<div class="line">{ppm2(hover.p.median)} median · {count(hover.p.n)} sales</div>
					<div class="line">latest {dateOf(hover.p.latest_sale)}</div>
				</div>
			{/if}
		</Popup>
	{/if}

	{#if mapState.pin}
		<Marker bind:lnglat={pinLngLat} draggable ondragend={onPinDragEnd} />
	{/if}

	<NavigationControl position="top-right" showCompass={false} />
	<ScaleControl position="bottom-right" />
	<AttributionControl position="bottom-right" compact customAttribution={attribution} />
</MapLibre>

<style>
	:global(.map) {
		position: absolute;
		inset: 0;
	}
	.readout {
		font-size: 12px;
		line-height: 1.4;
	}
	.value {
		font-family: var(--font-mono);
		font-size: 15px;
		font-weight: 650;
		margin-bottom: 2px;
	}
	.line {
		color: #4b5563;
	}
</style>
