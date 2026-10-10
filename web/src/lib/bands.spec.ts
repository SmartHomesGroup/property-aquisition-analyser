import { describe, expect, it } from 'vitest';
import { CELL_BANDS, POSTCODE_BAND, bandForZoom, cellSizeForZoom } from './bands.ts';

describe('cell bands', () => {
	it('are contiguous from z5 upwards with sizes getting finer', () => {
		expect(CELL_BANDS[0].minzoom).toBe(5);
		for (let i = 1; i < CELL_BANDS.length; i++) {
			expect(CELL_BANDS[i].minzoom).toBe(CELL_BANDS[i - 1].maxzoom);
			expect(CELL_BANDS[i].size).toBeLessThan(CELL_BANDS[i - 1].size);
		}
		expect(CELL_BANDS.at(-1)?.maxzoom).toBeGreaterThanOrEqual(19);
	});

	it('fetch each band at a zoom the SQL serves with that cell size', () => {
		for (const b of CELL_BANDS) {
			expect(b.fetchZoom).toBeGreaterThanOrEqual(b.minzoom);
			expect(b.fetchZoom).toBeLessThan(b.maxzoom);
			expect(cellSizeForZoom(b.fetchZoom)).toBe(b.size);
			// Every zoom in the band would be served the same size, so overzooming is faithful.
			for (let z = b.minzoom; z < Math.min(b.maxzoom, 17); z++) {
				expect(cellSizeForZoom(z)).toBe(b.size);
			}
		}
	});

	it('resolves a zoom to its band', () => {
		expect(bandForZoom(5.6).size).toBe(5000);
		expect(bandForZoom(8.99).size).toBe(5000);
		expect(bandForZoom(9).size).toBe(1000);
		expect(bandForZoom(13.5).size).toBe(250);
		expect(bandForZoom(18).size).toBe(100);
	});

	it('serves postcode points only where the SQL function does (z ≥ 14)', () => {
		expect(POSTCODE_BAND.fetchZoom).toBe(14);
		expect(POSTCODE_BAND.minzoom).toBe(14);
	});
});
