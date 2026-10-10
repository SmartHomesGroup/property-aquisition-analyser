/**
 * The £/m² colour scale. One scale for the whole country so colours mean the same thing
 * everywhere; breaks are quantile-ish on national £/m² (skewed, so not linear).
 *
 * Palette: ColorBrewer YlGnBu (sequential, colour-blind safe, reads on a light basemap).
 */
import type { ExpressionSpecification } from 'maplibre-gl';

/** Lower bound of each class in £/m². The first class is "below BREAKS[0]". */
export const BREAKS = [1500, 2000, 2500, 3000, 3500, 4000, 5000, 6500, 8000] as const;

export const COLOURS = [
	'#ffffd9',
	'#edf8b1',
	'#c7e9b4',
	'#7fcdbb',
	'#41b6c4',
	'#1d91c0',
	'#225ea8',
	'#253494',
	'#081d58',
	'#040b2b'
] as const;

/** Colour for a value, mirroring the MapLibre step expression (for legends and panels). */
export function colourFor(value: number): string {
	let i = 0;
	while (i < BREAKS.length && value >= BREAKS[i]) i++;
	return COLOURS[i];
}

/** MapLibre `step` expression over a numeric feature property. */
export function stepExpression(property: string): ExpressionSpecification {
	const expr: unknown[] = ['step', ['get', property], COLOURS[0]];
	BREAKS.forEach((b, i) => expr.push(b, COLOURS[i + 1]));
	return expr as ExpressionSpecification;
}

/** Legend rows, top (most expensive) first. */
export function legendRows(): { colour: string; label: string }[] {
	const rows: { colour: string; label: string }[] = [
		{ colour: COLOURS[0], label: `< £${BREAKS[0].toLocaleString('en-GB')}` }
	];
	for (let i = 0; i < BREAKS.length; i++) {
		const hi = BREAKS[i + 1];
		rows.push({
			colour: COLOURS[i + 1],
			label: hi
				? `£${BREAKS[i].toLocaleString('en-GB')} – ${hi.toLocaleString('en-GB')}`
				: `£${BREAKS[i].toLocaleString('en-GB')}+`
		});
	}
	return rows.reverse();
}

/** Black or white text that reads on the given class colour. */
export function textOn(colour: string): string {
	const i = COLOURS.indexOf(colour as (typeof COLOURS)[number]);
	return i >= 6 ? '#fff' : '#111';
}
