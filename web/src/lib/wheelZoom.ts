/**
 * Wheel zoom with momentum.
 *
 * MapLibre's built-in scroll zoom moves a fixed ~0.15 zoom per mouse notch with a short 200 ms
 * ease, which feels stepped. This replaces it with a velocity model, like a flywheel: each wheel
 * event adds an impulse, the zoom integrates the velocity every animation frame, and the velocity
 * decays exponentially so the map coasts to a stop after the last notch. Trackpads, which send
 * many small deltas, get the same treatment and feel like inertial scrolling.
 *
 * Zooming is always about the cursor. Touch pinch is untouched (MapLibre's handler stays on).
 * Honours `prefers-reduced-motion`: then the built-in handler is left as is.
 */
import type * as maplibregl from 'maplibre-gl';

export interface WheelZoomOptions {
	/** Zoom levels travelled per 100 px of wheel delta, once the momentum has run out. */
	levelsPerNotch?: number;
	/** Time constant of the velocity decay, in ms. Larger coasts longer. */
	decayMs?: number;
	/** Cap on pending travel, in zoom levels, so a fast spin cannot run away. */
	maxPendingLevels?: number;
}

const DEFAULTS: Required<WheelZoomOptions> = {
	levelsPerNotch: 0.45,
	decayMs: 160,
	maxPendingLevels: 3
};

/** Install on a map. Returns a function that removes it and restores the default handler. */
export function installWheelZoom(map: maplibregl.Map, opts: WheelZoomOptions = {}): () => void {
	if (typeof window === 'undefined') return () => {};
	if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return () => {};

	const o = { ...DEFAULTS, ...opts };
	const el = map.getCanvasContainer();
	let velocity = 0; // zoom levels per second
	let zoom = map.getZoom();
	let around: maplibregl.LngLat | null = null;
	let frame: number | null = null;
	let last = 0;

	map.scrollZoom.disable();

	function step(now: number) {
		const dt = Math.min((now - last) / 1000, 0.05); // clamp: tab switches must not teleport
		last = now;
		zoom += velocity * dt;
		const min = map.getMinZoom();
		const max = map.getMaxZoom();
		if (zoom <= min || zoom >= max) {
			zoom = Math.max(min, Math.min(max, zoom));
			velocity = 0;
		}
		velocity *= Math.exp((-dt * 1000) / o.decayMs);
		map.easeTo({ zoom, around: around ?? undefined, duration: 0, animate: false });
		if (Math.abs(velocity) > 0.02) {
			frame = requestAnimationFrame(step);
		} else {
			frame = null;
			velocity = 0;
		}
	}

	function onWheel(e: WheelEvent) {
		e.preventDefault();
		if (map.isMoving() && frame === null) zoom = map.getZoom();
		// Lines (Firefox mouse wheels) -> pixels, as MapLibre does; pinch-zoom (ctrlKey) is
		// also delivered as wheel events, with small deltas, so give it more weight.
		let delta = e.deltaMode === WheelEvent.DOM_DELTA_LINE ? e.deltaY * 40 : e.deltaY;
		if (e.ctrlKey) delta *= 3;
		// Impulse such that the total coasting distance for one notch is `levelsPerNotch`.
		const impulse = (-(delta / 100) * o.levelsPerNotch) / (o.decayMs / 1000);
		const maxV = o.maxPendingLevels / (o.decayMs / 1000);
		velocity = Math.max(-maxV, Math.min(maxV, velocity + impulse));
		const rect = el.getBoundingClientRect();
		around = map.unproject([e.clientX - rect.left, e.clientY - rect.top]);
		if (frame === null) {
			zoom = map.getZoom();
			last = performance.now();
			frame = requestAnimationFrame(step);
		}
	}

	el.addEventListener('wheel', onWheel, { passive: false });
	return () => {
		el.removeEventListener('wheel', onWheel);
		if (frame !== null) cancelAnimationFrame(frame);
		map.scrollZoom.enable();
	};
}
