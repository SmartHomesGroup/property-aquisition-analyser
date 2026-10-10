/**
 * Environment variables (SvelteKit 3 style). Public + static: inlined at build time and safe
 * to ship to the browser. Set them in `.env` (see `.env.example`).
 */
import { defineEnvVars } from '@sveltejs/kit/env';

const withDefault = (fallback: string) => (value: string | undefined) =>
	(value && value.trim()) || fallback;

export const variables = defineEnvVars({
	API_URL: {
		public: true,
		static: true,
		schema: withDefault('http://localhost:8000'),
		description: 'Base URL of the FastAPI service, no trailing slash'
	},
	TILES_URL: {
		public: true,
		static: true,
		schema: withDefault('http://localhost:3000'),
		description: 'Base URL of the Martin tile server, no trailing slash'
	},
	BASEMAP_STYLE: {
		public: true,
		static: true,
		schema: withDefault('https://tiles.openfreemap.org/styles/positron'),
		description: 'MapLibre style JSON URL for the basemap'
	}
});
