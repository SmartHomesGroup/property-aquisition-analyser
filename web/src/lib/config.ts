/**
 * Public runtime configuration. Values are declared in `src/env.ts`, set in `.env`, and inlined
 * at build time; the defaults match the local docker-compose stack.
 */
import { API_URL, TILES_URL, BASEMAP_STYLE } from '$app/env/public';

export const config = {
	/** Base URL of the FastAPI service (no trailing slash). */
	apiUrl: API_URL.replace(/\/$/, ''),
	/** Base URL of the Martin tile server (no trailing slash). */
	tilesUrl: TILES_URL.replace(/\/$/, ''),
	/** MapLibre style JSON for the basemap. OpenFreeMap Positron is free and keyless. */
	basemapStyle: BASEMAP_STYLE
} as const;

/** Great Britain, with a little slack: the extent our tiles cover. */
export const GB_BOUNDS: [[number, number], [number, number]] = [
	[-11, 49],
	[4, 61.5]
];

/**
 * How far the map may be panned. Deliberately much wider than GB_BOUNDS: MapLibre forces the
 * zoom up until the bounds fill the viewport, so tight bounds made zooming out "stick" and
 * snap the centre. These keep the map on this side of the Atlantic without that.
 */
export const MAX_BOUNDS: [[number, number], [number, number]] = [
	[-40, 38],
	[35, 66]
];

export const INITIAL_VIEW = { center: [-1.8, 53.0] as [number, number], zoom: 5.6 };
