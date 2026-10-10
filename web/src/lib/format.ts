/** Number and date formatting. UK locale, GBP, no spurious precision. */

const gbp0 = new Intl.NumberFormat('en-GB', {
	style: 'currency',
	currency: 'GBP',
	maximumFractionDigits: 0
});
const int = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });

export function gbp(v: number | null | undefined): string {
	return v == null ? '—' : gbp0.format(v);
}

/** £/m², e.g. "£4,350/m²". */
export function ppm2(v: number | null | undefined): string {
	return v == null ? '—' : `${gbp0.format(v)}/m²`;
}

/** Short form for legends and tooltips, e.g. "£4.4k". */
export function gbpShort(v: number): string {
	// Round in integer space first: 4350 / 1000 is 4.3499999 in binary and toFixed would say 4.3.
	if (v >= 1_000_000) return `£${(Math.round(v / 100_000) / 10).toFixed(1)}m`;
	if (v >= 10_000) return `£${Math.round(v / 1000)}k`;
	if (v >= 1_000) return `£${(Math.round(v / 100) / 10).toFixed(1)}k`;
	return `£${Math.round(v)}`;
}

export function count(v: number | null | undefined): string {
	return v == null ? '—' : int.format(v);
}

export function m2(v: number | null | undefined): string {
	return v == null ? '—' : `${int.format(Math.round(v))} m²`;
}

/** Signed percentage with one decimal, e.g. "−12.3%" or "+4.0%". */
export function signedPct(v: number | null | undefined): string {
	if (v == null) return '—';
	const sign = v < 0 ? '−' : '+';
	return `${sign}${Math.abs(v).toFixed(1)}%`;
}

const monthYear = new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric' });
const dayMonthYear = new Intl.DateTimeFormat('en-GB', {
	day: 'numeric',
	month: 'short',
	year: 'numeric'
});

export function monthOf(iso: string | null | undefined): string {
	return iso ? monthYear.format(new Date(iso)) : '—';
}

export function dateOf(iso: string | null | undefined): string {
	return iso ? dayMonthYear.format(new Date(iso)) : '—';
}

export function metres(v: number): string {
	return v >= 1000 ? `${(v / 1000).toFixed(1)} km` : `${Math.round(v)} m`;
}

/** Ordinal percentile label: 12 -> "12th". */
export function ordinal(n: number): string {
	const r = Math.round(n);
	const s = ['th', 'st', 'nd', 'rd'];
	const v = r % 100;
	return `${r}${s[(v - 20) % 10] ?? s[v] ?? s[0]}`;
}
