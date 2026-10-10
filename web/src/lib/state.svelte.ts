/**
 * Shared UI state for the map page (Svelte 5 runes). One instance, imported where needed.
 */
import type { ListingAnalysis, Precision, PropertyType, WindowMonths } from '#lib/api.ts';

export interface Pin {
	lng: number;
	lat: number;
	/** Where the pin came from, for the panel's wording. */
	source: 'click' | 'postcode' | 'drag' | 'listing';
	label?: string;
	/** For a listing: how precisely we could place it. */
	precision?: Precision;
}

/** The paste-a-listing flow. One listing at a time. */
export interface ListingState {
	status: 'idle' | 'loading' | 'done' | 'error';
	url: string | null;
	startedAt: number | null;
	result: ListingAnalysis | null;
	error: string | null;
}

/** What the user knows about the property under the pin. All optional. */
export interface SubjectInput {
	askingPrice: number | null;
	floorAreaM2: number | null;
	propertyType: Exclude<PropertyType, 'A'> | null;
}

class MapState {
	window = $state<WindowMonths>(24);
	ptype = $state<PropertyType>('A');
	radiusM = $state<number>(500);
	pin = $state<Pin | null>(null);
	subject = $state<SubjectInput>({ askingPrice: null, floorAreaM2: null, propertyType: null });
	listing = $state<ListingState>({
		status: 'idle',
		url: null,
		startedAt: null,
		result: null,
		error: null
	});

	/** Tile URL template for the cells layer, reflecting the current filters. */
	cellsTiles = $derived(`cells/{z}/{x}/{y}?window=${this.window}&ptype=${this.ptype}`);
	postcodeTiles = $derived(`postcodes/{z}/{x}/{y}?window=${this.window}&ptype=${this.ptype}`);

	dropPin(lng: number, lat: number, source: Pin['source'], label?: string, precision?: Precision) {
		this.pin = { lng, lat, source, label, precision };
	}

	clearPin() {
		this.pin = null;
	}

	startListing(url: string) {
		this.listing = { status: 'loading', url, startedAt: Date.now(), result: null, error: null };
	}

	/** Store the engine's answer and carry what it knows about the property into the pin flow. */
	finishListing(result: ListingAnalysis) {
		this.listing = { ...this.listing, status: 'done', result, error: null };
		const p = result.property;
		this.subject = {
			askingPrice: p.asking_price,
			floorAreaM2: this.subject.floorAreaM2,
			propertyType: p.property_type
		};
		if (p.location) {
			this.dropPin(
				p.location.lon,
				p.location.lat,
				'listing',
				p.address ?? p.location.postcode,
				p.precision ?? undefined
			);
		}
	}

	failListing(message: string) {
		this.listing = { ...this.listing, status: 'error', result: null, error: message };
	}

	clearListing() {
		this.listing = { status: 'idle', url: null, startedAt: null, result: null, error: null };
		if (this.pin?.source === 'listing') this.clearPin();
	}
}

export const mapState = new MapState();
