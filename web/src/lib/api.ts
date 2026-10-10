/** Typed client for the backend API. Mirrors backend/src/paa/api/schemas.py. */
import { config } from '#lib/config.ts';

export type PropertyType = 'A' | 'D' | 'S' | 'T' | 'F';
export type WindowMonths = 12 | 24 | 60;

export const PROPERTY_TYPES: { code: PropertyType; label: string }[] = [
	{ code: 'A', label: 'All' },
	{ code: 'D', label: 'Detached' },
	{ code: 'S', label: 'Semi' },
	{ code: 'T', label: 'Terraced' },
	{ code: 'F', label: 'Flats' }
];
export const WINDOWS: { months: WindowMonths; label: string }[] = [
	{ months: 12, label: '1 yr' },
	{ months: 24, label: '2 yrs' },
	{ months: 60, label: '5 yrs' }
];

export interface BuildInfo {
	built_at: string | null;
	ref_date: string | null;
	hpi_ref_month: string | null;
	sales_total: number | null;
	sales_matched: number | null;
	sales_enriched: number | null;
	cells: number | null;
	/** True when floor areas include development-only fakes; the UI must say so. */
	synthetic: boolean;
	/** Whether the paste-a-listing flow is available (the engine webhook is configured). */
	listing_analysis: boolean;
	attribution: string[];
}

export interface PostcodeLocation {
	postcode: string;
	lat: number;
	lon: number;
	easting: number;
	northing: number;
	district_code: string | null;
	positional_quality: number;
}

export interface Sale {
	transaction_id: string;
	address: string;
	postcode: string;
	date_of_transfer: string;
	price: number;
	price_adj: number | null;
	floor_area_m2: number;
	ppm2: number;
	ppm2_adj: number | null;
	property_type: string;
	new_build: boolean;
	energy_rating: string | null;
	distance_m: number;
}

export interface Bracket {
	radius_m: number;
	window_months: number;
	property_type: PropertyType;
	property_type_label: string;
	since: string;
	until: string;
	hpi_ref_month: string | null;
	n: number;
}

export interface Distribution {
	p10: number | null;
	p25: number | null;
	median: number | null;
	p75: number | null;
	p90: number | null;
	median_floor_area_m2: number | null;
}

export interface Subject {
	asking_price: number;
	floor_area_m2: number;
	ppm2: number;
	vs_median_pct: number | null;
	percentile: number | null;
}

export interface AreaStats {
	bracket: Bracket;
	ppm2_adj: Distribution;
	subject: Subject | null;
	recent_sales: Sale[];
}

export interface Comparables {
	bracket: Bracket;
	floor_area_m2: number;
	tolerance_pct: number;
	sales: Sale[];
}

export type Precision = 'postcode' | 'street' | 'district';

export interface ListingProperty {
	address: string | null;
	postcode: string | null;
	asking_price: number | null;
	property_type: Exclude<PropertyType, 'A'> | null;
	bedrooms: number | null;
	location: PostcodeLocation | null;
	precision: Precision | null;
}

export interface ListingAnalysis {
	id: number;
	url: string;
	requested_at: string;
	cached: boolean;
	duration_ms: number | null;
	engine: string;
	property: ListingProperty;
	/** The engine's response, verbatim. Read it with the helpers in `listing.ts`. */
	fields: Record<string, unknown>;
}

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

async function get<T>(
	path: string,
	params: Record<string, string | number | undefined>
): Promise<T> {
	const url = new URL(config.apiUrl + path);
	for (const [k, v] of Object.entries(params)) {
		if (v !== undefined && v !== '') url.searchParams.set(k, String(v));
	}
	return request<T>(fetch(url, { headers: { accept: 'application/json' } }));
}

async function post<T>(path: string, body: unknown): Promise<T> {
	return request<T>(
		fetch(config.apiUrl + path, {
			method: 'POST',
			headers: { accept: 'application/json', 'content-type': 'application/json' },
			body: JSON.stringify(body)
		})
	);
}

async function request<T>(pending: Promise<Response>): Promise<T> {
	const res = await pending;
	if (!res.ok) {
		let detail = res.statusText;
		try {
			detail = (await res.json()).detail ?? detail;
		} catch {
			/* not JSON */
		}
		throw new ApiError(res.status, detail);
	}
	return res.json() as Promise<T>;
}

export const api = {
	meta: () => get<BuildInfo>('/api/meta', {}),
	postcode: (pc: string) => get<PostcodeLocation>(`/api/postcodes/${encodeURIComponent(pc)}`, {}),
	area: (q: {
		lat: number;
		lon: number;
		radius_m: number;
		window: WindowMonths;
		ptype: PropertyType;
		asking_price?: number;
		floor_area_m2?: number;
	}) => get<AreaStats>('/api/area', q),
	comparables: (q: {
		lat: number;
		lon: number;
		ptype: Exclude<PropertyType, 'A'>;
		floor_area_m2: number;
		radius_m?: number;
		window?: WindowMonths;
	}) => get<Comparables>('/api/comparables', q),
	/** Slow: the engine reads the listing and runs an LLM; allow a minute or more. */
	analyseListing: (url: string, refresh = false) =>
		post<ListingAnalysis>('/api/listings/analyse', { url, refresh })
};
