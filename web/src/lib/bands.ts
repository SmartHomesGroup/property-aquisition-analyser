/**
 * Zoom bands for the £/m² cells.
 *
 * Each band's tiles are fetched at ONE zoom level (`fetchZoom`) and overzoomed through the rest
 * of the band, so zooming within a band is a pure transform in the GPU: no new tile requests,
 * no re-parsing of identical geometry at every integer zoom. The map only loads new data when
 * it crosses into the next band, which is also where the cell size changes.
 *
 * Must agree with `map.cell_size_for_zoom()` in backend/src/paa/sql/migrations/002_functions.sql
 * (z ≤ 8 → 5000 m, ≤ 11 → 1000 m, ≤ 13 → 250 m, else 100 m): a tile requested at `fetchZoom`
 * must come back containing cells of `size`.
 */
export interface Band {
	/** Nominal cell edge in metres (Web Mercator squares; exact at 53°N). */
	size: number;
	/** The only zoom at which tiles for this band are requested. */
	fetchZoom: number;
	/** Layer visible from this zoom (inclusive)... */
	minzoom: number;
	/** ...up to this zoom (exclusive), MapLibre's convention. */
	maxzoom: number;
}

export const CELL_BANDS: readonly Band[] = [
	{ size: 5000, fetchZoom: 5, minzoom: 5, maxzoom: 9 },
	{ size: 1000, fetchZoom: 9, minzoom: 9, maxzoom: 12 },
	{ size: 250, fetchZoom: 12, minzoom: 12, maxzoom: 14 },
	{ size: 100, fetchZoom: 14, minzoom: 14, maxzoom: 24 }
];

/** Per-postcode points: fetched once at z14, overzoomed to street level. */
export const POSTCODE_BAND: Band = { size: 0, fetchZoom: 14, minzoom: 14, maxzoom: 24 };

/** Mirror of the SQL function, so the bands can be checked against it in tests. */
export function cellSizeForZoom(z: number): number {
	if (z <= 8) return 5000;
	if (z <= 11) return 1000;
	if (z <= 13) return 250;
	return 100;
}

export function bandForZoom(z: number): Band {
	return CELL_BANDS.find((b) => z >= b.minzoom && z < b.maxzoom) ?? CELL_BANDS[0];
}
