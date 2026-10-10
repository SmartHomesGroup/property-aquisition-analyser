import { describe, expect, it } from 'vitest';
import { BREAKS, COLOURS, colourFor, legendRows, stepExpression } from './colour';

describe('colour scale', () => {
	it('has one more colour than breaks', () => {
		expect(COLOURS.length).toBe(BREAKS.length + 1);
	});
	it('classifies values consistently with the step expression', () => {
		expect(colourFor(0)).toBe(COLOURS[0]);
		expect(colourFor(BREAKS[0])).toBe(COLOURS[1]);
		expect(colourFor(BREAKS[0] - 1)).toBe(COLOURS[0]);
		expect(colourFor(1e9)).toBe(COLOURS[COLOURS.length - 1]);
		const expr = stepExpression('median') as unknown[];
		expect(expr[0]).toBe('step');
		expect(expr.length).toBe(3 + BREAKS.length * 2);
	});
	it('builds a legend row per class, most expensive first', () => {
		const rows = legendRows();
		expect(rows.length).toBe(COLOURS.length);
		expect(rows[0].colour).toBe(COLOURS[COLOURS.length - 1]);
		expect(rows[rows.length - 1].label.startsWith('<')).toBe(true);
	});
});
