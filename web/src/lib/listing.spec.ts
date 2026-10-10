import { describe, expect, it } from 'vitest';
import { elapsed, looksLikeUrl, num, pick, readEngine, strategyTone } from './listing.ts';

describe('looksLikeUrl', () => {
	it('tells links from postcodes', () => {
		expect(looksLikeUrl('https://www.rightmove.co.uk/properties/91660647#/')).toBe(true);
		expect(looksLikeUrl('rightmove.co.uk/properties/91660647')).toBe(true);
		expect(looksLikeUrl('N11 2AB')).toBe(false);
		expect(looksLikeUrl('pr1 2ab')).toBe(false);
		expect(looksLikeUrl('')).toBe(false);
	});
});

describe('field readers', () => {
	it('pick skips empty values and tries alternatives', () => {
		expect(pick({ a: '', b: null, c: 0 }, 'a', 'b', 'c')).toBe(0);
		expect(pick({}, 'a')).toBeNull();
	});

	it('num parses money strings', () => {
		expect(num(165000)).toBe(165000);
		expect(num('£165,000')).toBe(165000);
		expect(num('Offers over £120,000')).toBe(120000);
		expect(num('n/a')).toBeNull();
		expect(num(undefined)).toBeNull();
	});

	it('readEngine maps the stage-0 field names', () => {
		const e = readEngine({
			'Asking Price': 165000,
			'Expected GDV': 175000,
			'BRR Maximum Allowable Offer (MAO)': 212887,
			'Recommended Strategy': 'Reject',
			'Bridge Interest': 5198
		});
		expect(e.askingPrice).toBe(165000);
		expect(e.gdv).toBe(175000);
		expect(e.brrMao).toBe(212887);
		expect(e.strategy).toBe('Reject');
		expect(e.bridgeCost).toBe(5198);
		expect(e.summary).toBeNull();
	});
});

describe('presentation helpers', () => {
	it('strategyTone', () => {
		expect(strategyTone('Reject')).toBe('bad');
		expect(strategyTone('Watch')).toBe('warn');
		expect(strategyTone('BRR')).toBe('good');
		expect(strategyTone(null)).toBe('neutral');
	});

	it('elapsed', () => {
		expect(elapsed(0, 42_000)).toBe('42 s');
		expect(elapsed(0, 125_000)).toBe('2 min 5 s');
	});
});
