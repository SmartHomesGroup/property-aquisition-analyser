/**
 * Reading the analysis engine's output. The stage-0 engine returns a flat object of loosely
 * named fields ("Asking Price", "BRR Maximum Allowable Offer (MAO)", ...). Nothing here trusts
 * a field to exist: every reader returns null when it doesn't, and the panel shows "—".
 */

export type Fields = Record<string, unknown>;

/** Does the search box's text look like a web link rather than a postcode? */
export function looksLikeUrl(text: string): boolean {
	const s = text.trim();
	return /^https?:\/\//i.test(s) || /^(www\.)?[a-z0-9-]+(\.[a-z0-9-]+)+\//i.test(s);
}

/** First present, non-empty value among alternative field names. */
export function pick(fields: Fields, ...keys: string[]): unknown {
	for (const k of keys) {
		const v = fields[k];
		if (v !== undefined && v !== null && v !== '') return v;
	}
	return null;
}

/** A number from a numeric field or a "£165,000" / "Offers over £120,000" string. */
export function num(v: unknown): number | null {
	if (typeof v === 'number') return Number.isFinite(v) ? v : null;
	if (typeof v !== 'string') return null;
	const m = v.match(/-?\d[\d,]*(?:\.\d+)?/);
	if (!m) return null;
	const n = Number(m[0].replace(/,/g, ''));
	return Number.isFinite(n) ? n : null;
}

export function text(v: unknown): string | null {
	if (v === null || v === undefined) return null;
	const s = String(v).trim();
	return s ? s : null;
}

/** The figures the panel shows, each read from the engine's field names (old and new spellings). */
export function readEngine(f: Fields) {
	return {
		address: text(pick(f, 'Address', 'address')),
		propertyType: text(pick(f, 'Property Type', 'property_type')),
		bedrooms: num(pick(f, 'Bedrooms', 'bedrooms')),
		bathrooms: num(pick(f, 'Bathrooms', 'bathrooms')),
		tenure: text(pick(f, 'Tenure', 'tenure')),
		purchaseType: text(pick(f, 'Purchase Type', 'purchase_type')),
		agent: text(pick(f, 'Estate Agent', 'estate_agent')),
		source: text(pick(f, 'Source Website', 'source_website')),
		askingPrice: num(pick(f, 'Asking Price', 'asking_price')),
		gdv: num(pick(f, 'Expected GDV', 'Estimated GDV', 'estimated_gdv', 'expected_gdv')),
		valueGap: num(pick(f, 'Value Gap', 'value_gap')),
		score: num(pick(f, 'Investment Score', 'investment_score')),
		strategy: text(pick(f, 'Recommended Strategy', 'recommended_strategy')),
		category: text(pick(f, 'Opportunity Category', 'opportunity_category')),
		refurb: num(pick(f, 'Estimated Refurb Cost', 'estimated_refurb_cost')),
		contingency: num(pick(f, 'Contingency', 'contingency')),
		buyingCosts: num(pick(f, 'Buying Costs', 'buying_costs')),
		stampDuty: num(pick(f, 'Stamp Duty', 'stamp_duty')),
		bridgeCost: num(pick(f, 'Bridge Finance Cost', 'Bridge Interest', 'bridge_finance_cost')),
		bridgeLoan: num(pick(f, 'Bridge Loan', 'bridge_loan')),
		totalCost: num(pick(f, 'Total Project Cost', 'total_project_cost')),
		sellingCosts: num(pick(f, 'Selling Costs', 'selling_costs')),
		profit: num(pick(f, 'Estimated Profit', 'estimated_profit')),
		roi: num(pick(f, 'Flip ROI', 'flip_roi')),
		flipMao: num(
			pick(f, 'Flip Maximum Allowable Offer', 'Flip MAO', 'flip_maximum_allowable_offer')
		),
		brrMortgage: num(pick(f, 'BRR Mortgage', 'brr_mortgage')),
		refinanceCosts: num(pick(f, 'Refinance Costs', 'refinance_costs')),
		cashLeft: num(pick(f, 'BRR Cash Left', 'brr_cash_left')),
		cashReleased: num(pick(f, 'BRR Cash Released', 'brr_cash_released')),
		equity: num(pick(f, 'Equity Created', 'equity_created')),
		brrMao: num(
			pick(f, 'BRR Maximum Allowable Offer (MAO)', 'BRR MAO', 'brr_maximum_allowable_offer')
		),
		summary: text(pick(f, 'Investment Summary', 'investment_summary')),
		strategyNotes: text(pick(f, 'Strategy Notes', 'strategy_notes')),
		refurbSummary: text(pick(f, 'Refurbishment Summary', 'refurbishment_summary')),
		risks: text(pick(f, 'Major Risks', 'major_risks'))
	};
}

export type Engine = ReturnType<typeof readEngine>;

/** Colour the engine's recommendation without inventing one. */
export function strategyTone(strategy: string | null): 'good' | 'warn' | 'bad' | 'neutral' {
	const s = (strategy ?? '').toLowerCase();
	if (!s) return 'neutral';
	if (s.includes('reject') || s.includes('avoid')) return 'bad';
	if (s.includes('watch') || s.includes('monitor') || s.includes('caution')) return 'warn';
	return 'good';
}

/** "Just now", "42 s", "2 min" for the elapsed-time readout while the engine runs. */
export function elapsed(startedAt: number, now: number): string {
	const s = Math.max(0, Math.round((now - startedAt) / 1000));
	if (s < 60) return `${s} s`;
	return `${Math.floor(s / 60)} min ${s % 60} s`;
}
