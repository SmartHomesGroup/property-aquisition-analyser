import { describe, expect, it } from 'vitest';
import { gbp, gbpShort, ordinal, ppm2, signedPct } from './format';

describe('format', () => {
	it('formats GBP without pennies', () => {
		expect(gbp(425000)).toBe('£425,000');
		expect(gbp(null)).toBe('—');
	});
	it('formats £/m²', () => {
		expect(ppm2(4350)).toBe('£4,350/m²');
	});
	it('shortens large values', () => {
		expect(gbpShort(4350)).toBe('£4.4k');
		expect(gbpShort(12500)).toBe('£13k');
		expect(gbpShort(1250000)).toBe('£1.3m');
	});
	it('signs percentages with a true minus', () => {
		expect(signedPct(-12.34)).toBe('−12.3%');
		expect(signedPct(4)).toBe('+4.0%');
	});
	it('ordinals', () => {
		expect(ordinal(1)).toBe('1st');
		expect(ordinal(12)).toBe('12th');
		expect(ordinal(23)).toBe('23rd');
		expect(ordinal(111)).toBe('111th');
	});
});
