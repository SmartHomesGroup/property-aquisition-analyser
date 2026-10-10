# Basemap tile providers for a UK-only MapLibre GL JS heatmap (as of 10 October 2026)

Scope: muted basemap under a £/m² heatmap overlay, Great Britain coverage, MapLibre GL JS, small commercial startup (may charge for a premium tier). All prices are as shown on vendor pages fetched on 10 Oct 2026 unless a different date is stated. Northern Ireland is noted separately where relevant.

## Key question 1: Does the OS NGD API – Tiles free (OpenData) plan genuinely cover a commercial startup's basemap needs down to building level, and what are the exact limits?

### Takeaway
No, not down to building level. On the free OS OpenData plan, OS NGD API – Tiles (Web Mercator) is open only at z6–z15; z16–z19 are "Premium data" and are charged per transaction (4 tiles = 1 transaction, £0.0331 each) once you have used the Premium plan's £1,000/month free allowance. Everything the OpenData plan serves is "free and unlimited" (subject to a 600 transactions/minute throttle), and OS's own Light and Black & White styles are available with no extra charge.

### Cited Findings

**Plans and pricing (OS Data Hub)**
- OS Data Hub has three plans. OS OpenData plan: "free and unlimited usage but with a data limit determined by the detail". Premium plan: access to premium datasets incl. OS MasterMap Topography Layer; "the requests and transactions contain a price"; includes "free premium data (API transactions) up to £1,000 per month"; projects run in "development mode or live mode"; Premium also gives all OpenData access. Public Sector plan: PSGA members only, "free unlimited access to OS OpenData and premium data". — [Ordnance Survey, What is the OS Data Hub?](https://www.ordnancesurvey.co.uk/developers/os-data-hub)
- The OS Data Hub plans page (JS-rendered; figures below come from a search-engine snippet of the page and should be verified in the live page) lists: OS NGD API – Tiles and OS Vector Tile API premium "map view" = 4 tiles = 1 transaction at £0.0331 (so the £1,000 allowance covers ~30,211 premium transactions/month); OS Maps API premium (MasterMap Topography) map view = 15 tiles at £0.0331; OS Maps API Leisure 1:25k/1:50k view = 15 tiles at £0.000525 (~1,904,762/month free); "Premium Plans get up to the first £1,000 of premium data free every month (excluding OS Places API)"; "All our API data (OS OpenData and Premium) are subject to a 600 transactions-per-minute throttle for your live projects." — [OS Data Hub plans](https://osdatahub.os.uk/plans) (snippet via search; page did not render for direct fetch)
- OS NGD API – Tiles product page lists it under "Public Sector Plan, Premium Plan, and OS OpenData Plan (FREE)"; scale "National scale to building scale (1:5 000 000 to 1:1 250)"; "This product is updated weekly"; OGC API – Tiles; works with OpenLayers, MapLibre GL JS, Leaflet. — [OS product page: OS NGD API – Tiles](https://ordnancesurvey.co.uk/products/os-ngd-api-tiles)

**Zoom levels: which are OpenData and which are Premium**
- EPSG:3857 tile matrix: min zoom 6, max zoom 19. Zoom 6–15 labelled "OpenData"; zoom 16, 17, 18, 19 labelled "Premium data". "The zoom levels start at 6 to fit in with the industry-standard initial zoom layer." — [OS NGD API – Tiles: Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels)
- EPSG:27700 tile matrix: zoom 0–15; zoom 0–11 "OpenData", zoom 12–15 "Premium data". "EPSG:27700 zoom level 0 is similar to EPSG:3857 zoom level 6." — [OS NGD API – Tiles: Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels)
- The 3857 scale at z15 is ~1:8,531 and at z16 ~1:4,265 (resolution 2.39 m/px at z15, 1.19 m/px at z16). — [OS NGD API – Tiles: Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels)
- For comparison, the older raster OS Maps API (EPSG:3857, Outdoor/Road/Light): z7–16 "Open data (Open Zoomstack)", z17 "Premium – MasterMap Topography blended with Open Zoomstack", z18–20 "Premium – MasterMap Topography". In EPSG:27700: z0–9 open, z10–13 premium. Premium layers "use detailed OS MasterMap content and require the appropriate product access and licensing." — [OS Maps API: Layers and styles](https://docs.os.uk/os-apis/accessing-os-apis/os-maps-api/layers-and-styles)

**What's in the free tiles (ngd-base)**
- The `ngd-base` collection "combines OS Open Zoomstack and OS NGD data" and includes: Buildings (Building Part); Geographical Names (Named Point); Land (Land, Land Point, Landform, Landform Line); Land Use (Site); Structures (Compound Structure, Field Boundary, Structure, Structure Line); Transport (Road, Road Line, Road Track Or Path, Path, Path Link, Rail, Cartographic Rail Detail); Water (Water, Water Point, Water Link, Inter Tidal Line, Tidal Boundary, etc.). Other collections: `asu-bdy` (boundaries, biannual), `wtr-ctch` (catchments), `trn-ntwk-railway` (monthly), `wtr-tidalboundary` (monthly). `ngd-base` is updated weekly. — [OS NGD API – Tiles: What data is available?](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/what-data-is-available)
- "The OS NGD API – Tiles basemap is updated weekly", "usually by Monday"; the basemap includes only a subset of OS NGD feature types/attributes to keep tiles lightweight; the Address Theme and RAMI collection are not available via Tiles. — [OS APIs FAQs](https://docs.os.uk/os-apis/core-concepts/faqs); [OS NGD API – Tiles overview](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-tiles)
- Coverage: "authoritative data for Great Britain" — Northern Ireland is not covered by OS NGD (OSNI is a separate agency). — [OS product page](https://ordnancesurvey.co.uk/products/os-ngd-api-tiles); [OS NGD API – Tiles overview](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-tiles)

**Styles (incl. Light and Black & White)**
- Style IDs served by the API: `3857`, `27700` (Outdoor), `road-3857`, `road-27700`, `light-3857`, `light-27700`, `blackwhite-3857`, `blackwhite-27700`. Base URL `https://api.os.uk/maps/vector/ngd/ota/v1`, style endpoint `/collections/{collectionId}/styles/{styleId}`. Style descriptions: Outdoor "Our traditional outdoor style focusing on spaces"; Road "Our road style focusing on the transport network"; Light "Our light style perfect for overlaying data"; Black & White "Our high contrast basemap perfect for overlaying data". — [OS NGD API – Tiles: Styles](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/technical-specification/styles); [OS NGD API – Tiles QGIS guide](https://docs.os.uk/osngd/accessing-os-ngd/access-the-os-ngd-api/os-ngd-api-tiles/getting-started/gis-software/qgis)
- OS blog (6 Oct 2025) announcing the new styles: Black & White is "designed to provide a clean, minimal backdrop that works especially well for overlaying your own data" and has no fill colours at large scales; Light "has been designed specifically for data visualisation" with a subtle palette; Road and Outdoor are higher-contrast. Editing can be done in "free to use applications such as" Maputnik, with an OS how-to guide. — [OS blog: New basemap styles added to OS NGD Tiles API](https://www.ordnancesurvey.co.uk/blog/new-basemap-styles-for-os-ngd)
- Light style: "subtle colour palette, providing just enough geographic context whilst allowing your own data overlays to shine"; Black & White: "no fill colours at the large scales (NGD building level), providing a clean and clear base over which to showcase your own data". Stylesheets for GIS are in the OS-NGD-Stylesheets GitHub repo. — [Styling OS NGD Data](https://docs.os.uk/osngd/getting-started/styling-os-ngd-data)

**API key setup and MapLibre wiring**
- "To access the OS NGD API – Tiles, you need an API Key", tied to an API project in your OS Data Hub account. — [OS NGD API – Tiles overview](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-tiles)
- OS's MapLibre template loads `https://api.os.uk/maps/vector/ngd/ota/v1/collections/ngd-base/styles/3857` (no key in the style URL) and uses a `fetch` interceptor to rewrite `sources['ngd-base'].tiles` to `${url}/{z}/{y}/{x}?key=${apiKey}`; map options `minZoom: 6, maxZoom: 19`, `attributionControl: false` plus OS branding CSS/JS. — [OS NGD API – Tiles: MapLibre GL JS](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/getting-started/libraries/maplibre-gl-js)
- Maputnik workflow: load the house style URL (`.../styles/blackwhite-3857`, `light-3857`, `road-3857`, or `3857` for Outdoor), delete the `ngd-base` source and re-add it as Vector (Tile URLs) with `.../tiles/3857/{z}/{y}/{x}?key=...`, scheme xyz, min 6, max 19; "the OS NGD API – Tiles only works in epsg: 3857 (Web Mercator) in Maputnik"; sprites/glyphs are referenced in the JSON and must be hosted if customised; save the JSON and host it yourself. — [OS: Creating a bespoke style for the OS NGD API – Tiles](https://docs.os.uk/more-than-maps/using-os-mapping-apis/creating-a-bespoke-style-for-the-os-ngd-api-tiles)
- OS also demonstrates a small server-side proxy so the API key stays off the client, warning that a production app would need protection so only legitimate users can reach the proxy. — [OrdnanceSurvey/OS-Data-Hub-API-Demos](https://github.com/OrdnanceSurvey/OS-Data-Hub-API-Demos)

**Licensing, attribution and caching**
- OS OpenData is licensed under the Open Government Licence; OS asks for the credit line "Contains OS data © Crown Copyright [and database right] (year)". — [OS OpenData](https://www.ordnancesurvey.co.uk/opendata)
- The APIs have their own terms (the OS Data Hub API Terms & Conditions at `osdatahub.os.uk/legal/apiTermsConditions`); that page is JS-rendered and did not return text to fetch, so its caching clauses are unverified here. — [Cartopy docs linking the OS API terms](https://cartopy.readthedocs.io/latest/reference/generated/cartopy.io.img_tiles.OrdnanceSurvey.html)
- The only text found on caching: a 2020 Cadcorp guest post on the OS blog says that "In order to comply with the OS Data Hub T&Cs, Premium Data products can only be cached locally for the duration of a SIS Desktop session"; OpenData can be imported for offline use. — [OS blog: Bringing the OS Data Hub to desktop GIS (8 Sep 2020)](https://www.ordnancesurvey.co.uk/blog/os-data-hub-to-desktop-gis)
- OS Vector Tile API docs describe vector tiles as "optimised for caching and scaling" but set no retention period. — [OS Vector Tile API](https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api)

**OS Maps API (raster), OS Vector Tile API and OS Open Zoomstack status**
- OS Vector Tile API: serves OS Open Zoomstack and OS MasterMap Topography Layer (premium), plus Boundary-Line, Greenspace, Sites; GB coverage; updates "15 working days from each product refresh date"; "anticipated to reach End of Life in Autumn 2028"; Water Network Layer removed 31 Mar 2026; Detailed Path Network removed 30 Sep 2026; Greenspace Layer removed 31 Mar 2027. Replacement is OS NGD API – Tiles "built on the latest OGC API – Tiles standard". — [OS Vector Tile API](https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api); [OS API change log](https://docs.os.uk/os-apis/service-and-data-status/change-log)
- OS Maps API (raster, WMTS/ZXY): roadmap entry says its end of life is "subject to future customer engagement and market readiness" and "planned to align to End of Life for OS MasterMap Topography Layer", which the roadmap dates "anticipated by Summer 2030". — [OS product roadmap](https://www.ordnancesurvey.co.uk/products/roadmap)
- OS Open Zoomstack (download product): roadmap lists "Date of notice: Spring 2027", "End of Life date: Spring 2028", "End of Life notice not yet issued". Successor: "New Open Zoomstack: national to local level basemap in an all-in-one zoomable product. Replacement for current OS Open Zoomstack product, designed for use alongside OS NGD themes or as a standalone product", "still in discovery and development, with release date TBC", "prototype data will be shared with a limited audience in Spring 2026"; the EOL migration timeline names the successor as "New product name TBD". OS commits to at least 12 months' notice before End of Life. — [OS product roadmap](https://www.ordnancesurvey.co.uk/products/roadmap); [Product EOL migration timeline (PDF)](https://www.ordnancesurvey.co.uk/documents/product-support/support/Product-EOL-migration-timeline.pdf)
- OS plans to "enhance the OS NGD API – Tiles following the release of the NGD-compatible Basemap product, which is in development". — [OS product roadmap overview (PDF)](https://www.ordnancesurvey.co.uk/documents/product-support/Product-roadmap-overview.pdf)
- A third-party blog (Spyro-Soft) names the successor "OS BaseMap Pro" with a 2027 launch; this is not confirmed by any OS source and conflicts with OS's "name TBD". — [Spyro-Soft blog](https://spyro-soft.com/blog/geospatial/what-os-ngd-means-for-enterprise-location-intelligence)
- OS Open Zoomstack download: GeoPackage (EPSG:27700) and vector tiles MBTiles (EPSG:3857, "Approximately 2.6GB", 18 layers, roads split national/regional/local), "updated every six months in June and December", scale "1:5 000 000 to 1:10 000", "supplied with four beautiful cartographic styles". — [OS Open Zoomstack technical specification](https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack/os-open-zoomstack-technical-specification); [OS Open Zoomstack documentation](https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack)
- Open Zoomstack converted to PMTiles was reported at 2.4 GB (from 2.6 GB MBTiles) in a community write-up, i.e. a self-hostable GB-only OS basemap under OGL. — [dev.to: Serve OS Open Zoomstack through PMTiles](https://dev.to/hfu/serve-os-open-zoomstack-2022-12-through-pmtiles-1di1)

### Inferences
- For a heatmap at street level (z≤15, ~2.4 m/px) the OpenData plan is sufficient and genuinely free for commercial use; the OpenData tiles include building parts (from Open Zoomstack/NGD) so building footprints do appear before z16, but at z16–z19 every 4 tiles cost £0.0331 (≈£8.28 per 1,000 tiles) after the £1,000 monthly allowance. At roughly 30k premium transactions (≈120k premium tiles) per month the allowance covers a small prototype; a popular consumer site zooming to z18 could exceed it quickly.
- Because the OpenData plan is "unlimited" but throttled at 600 transactions/minute per live project, burst traffic from a viral page could hit the throttle; put a CDN/edge cache in front only if the API terms allow (unverified, see Gaps).
- MapLibre GL JS renders Web Mercator only, so use the `*-3857` styles; the EPSG:27700 variants are for OpenLayers/QGIS/ArcGIS users. OS's own Maputnik guide confirms 3857-only.
- Attribution for OS tiles in MapLibre should use "Contains OS data © Crown copyright and database rights 2026" plus OS's API branding/logo snippet (OS's template disables the default attribution control and adds OS branding CSS/JS); the exact wording is governed by the API terms (unverified text).

### Gaps
- The OS Data Hub API Terms & Conditions page (osdatahub.os.uk/legal/apiTermsConditions) is JS-rendered and could not be fetched; the explicit caching clause (whether server-side/CDN caching of OpenData tiles is allowed, and for how long) and the exact attribution wording for API output are unverified. The 2020 Cadcorp note suggests Premium data may only be cached for a session.
- Per-transaction prices and the 600 tx/min throttle come from a search snippet of osdatahub.os.uk/plans; verify in the live page (the page did not render for direct fetch).
- OS docs do not state at which zoom buildings first appear in the `ngd-base` tiles or whether OpenData-zoom buildings are generalised Open Zoomstack footprints vs. NGD Building Parts.
- Development-mode vs live-mode transaction behaviour for Premium was not documented in fetched pages.

## Key question 2: Cheapest reliable zero-ops option for a prototype, and the best option for a commercial launch?

### Takeaway
For a zero-ops prototype, OS NGD API – Tiles on the free OpenData plan (Light or Black & White style, z6–15) or OpenFreeMap's public instance (no key, no limits, commercial use allowed) are both free; OS gives authoritative GB data with a proper SLA-backed service, OpenFreeMap is donation-run with no SLA. For a commercial launch, the two credible routes are OS NGD Tiles (OpenData for z≤15, Premium plan with £1,000/month free credit if you need z16–19) or self-hosted Protomaps PMTiles on Cloudflare R2 (~$5–12/month at 10M requests); MapTiler Flex ($30/month) and Stadia Starter ($20/month) are the cheapest hosted OSM options that permit commercial use.

### Cited Findings

**OS NGD API – Tiles**
- OpenData plan: "free and unlimited usage", OpenData zoom 6–15, 600 tx/min throttle; Premium plan: first £1,000/month of premium transactions free, then £0.0331 per 4 premium tiles. — [OS Data Hub](https://www.ordnancesurvey.co.uk/developers/os-data-hub); [OS Data Hub plans](https://osdatahub.os.uk/plans); [Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels)

**MapTiler Cloud** (pricing page, USD excl. VAT, fetched 10 Oct 2026)
- Free: $0, "for testing, prototyping, personal, or non-commercial use"; 5k sessions/month, 100k API requests/month, 5 GB storage (1 file), 5 custom styles; MapTiler logo shown; service pauses when quota exhausted. Flex: $30/month; 25k sessions, 500k API requests, 10 GB storage, 20 custom styles; overage $2.50/1k sessions, $0.15/1k requests; no logo required (except 3D). Custom: prepaid contract; "The only plan which allows reselling is the CUSTOM plan." — [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/)
- A third-party tracker dated 14 June 2026 listed Flex at $25/month with 25k sessions/500k requests; the official page now shows $30, so the price appears to have risen in 2026. — [frontdeskreview MapTiler pricing](https://frontdeskreview.com/software/maps-api/maptiler/) vs [MapTiler pricing](https://www.maptiler.com/cloud/pricing/)
- Terms: "Usage of the Free Plan is limited to non-commercial use and research & development for commercial products applications" (s1.2); "MapTiler attribution is required to be shown on screen while the map is displayed" (s5.4); "The Service must be always used with your own API key(s)" (s3.2). — [MapTiler Cloud Terms](https://www.maptiler.com/cloud/terms/)
- API keys can be restricted by "Allowed HTTP origins" (wildcards like `*.mydomain.com`); requests without an Origin/Referer header are rejected when origins are set; MapTiler advises a new key per application. — [MapTiler docs: How to protect your map key](https://docs.maptiler.com/guides/maps-apis/maps-platform/how-to-protect-your-map-key)
- Self-hosting (MapTiler Server, on-prem): Free tier $0 non-commercial/eval, 100 MAU, old 2020 OSM data; Standard $2,500/year, single internal app, 500 MAU, "Commercial B2B or B2C use is not allowed"; Custom (quote) for B2C/B2B and full MapTiler Planet. — [MapTiler Server pricing](https://www.maptiler.com/server/pricing/); [MapTiler Data subscriptions](https://docs.maptiler.com/guides/self-hosting/self-hosted-maps/maptiler-data-subscriptions)
- Coverage: global OpenStreetMap-based (OpenMapTiles schema) — UK coverage is the standard OSM planet; no UK-specific notes found.

**Stadia Maps** (pricing page, "$", fetched 10 Oct 2026)
- Free: $0, 200,000 credits/month, "Commercial use not allowed", "No additional usage" (hard cap). Starter: $20/month, 1,000,000 credits, +3¢/1,000 credits, commercial use allowed. Standard: $80, 7.5M credits. Professional: $250, 25M credits. Vector basemap tile = 1 credit; raster = 1 credit; satellite = 4. — [Stadia Maps pricing](https://stadiamaps.com/pricing/)
- Stadia's FAQ: commercial use "requires a paid subscription", defined broadly as a product or service that is sold or generates revenue (incl. advertising). — [Stadia Maps FAQs](https://stadiamaps.com/faqs/)
- Styles: Alidade Smooth "features a muted color scheme and fewer points of interest", Alidade Smooth Dark, Stamen Toner (B+W, with Toner Lite/Dark/Blacklite variants), OSM Bright, Outdoors. — [Stadia Maps themes](https://docs.stadiamaps.com/themes/)

**Thunderforest** (raster-first; GBP prices available)
- Hobby Project: 150,000 tile requests/month free ("Test out your ideas"); Solo Developer 1.5M requests £95/month ($125/€115); Small Business 15M £195/month; Large Business 150M £395/month; attribution cannot be removed; bulk download only on Small Business+; "Vector Tiles API requests count as 10 Map Tile API requests". — [Thunderforest pricing](https://thunderforest.com/pricing)

**Geoapify**
- Free: 3,000 credits/day, no card, "You can use the Free plan for commercial websites, apps, and business projects, including in production"; API 10 $59/month (10k credits/day) up to API 250 $609/month; map tiles: "the rate limit can be multiplied by 4"; attribution required ("Powered by" Geoapify + data sources). — [Geoapify pricing](https://www.geoapify.com/pricing/)

**Mapbox** (fetched 10 Oct 2026)
- Mapbox GL JS map loads: "Up to 50,000" monthly free; then $5.00/1k (50,001–100k), $4.00 (100k–200k), $3.00 (200k–1M), $2.50 (1M–5M). "A map load is counted every time Mapbox GL JS initializes". — [Mapbox pricing](https://www.mapbox.com/pricing)
- When Mapbox tiles are consumed from MapLibre, "tile requests are billed individually under the Maps API rather than being bundled into a map load"; "MapLibre does not natively resolve `mapbox://` scheme URIs". — [Mapbox: Use Mapbox APIs in MapLibre GL JS](https://docs.mapbox.com/help/dive-deeper/mapbox-in-maplibre/)

**OpenFreeMap**
- "Using our public instance is completely free: there are no limits on the number of map views or requests"; "no registration, no user database, no API keys, and no cookies"; commercial use allowed; "At the moment, I don't offer SLA guarantees or personalized support"; funded by donations. — [OpenFreeMap](https://openfreemap.org)
- Reliability evidence: August 2025, Wplace.live sent ~3 billion requests in 24 h (~215 TB, peak ~100,000 req/s); 99.4% Cloudflare cache rate, some empty tiles/206 responses; author added his first Cloudflare rule and offered Wplace a free self-hosted setup; plans per-referrer bandwidth caps "like 100 million requests per 24 hours", "everything will still stay free and without registration"; runs on ~$500/month donations with Cloudflare sponsoring bandwidth. — [Hyperknot: OpenFreeMap survived 100,000 requests per second (9 Aug 2025)](https://hyperknot.com/blog/openfreemap-survived-100000-requests/)

**Protomaps (self-host)**
- Cost calculator scenario (10M tile requests/month, 1,000 GB egress, 110 GB stored, 50% cache hit): Protomaps on Cloudflare $11.45/month (Workers paid plan $5 + $3 invocations + R2 storage $1.65 + R2 reads $1.80); on AWS $119.56; vs "Hosted Map API" $1,875 and Google Maps $3,640. — [Protomaps cost calculator](https://docs.protomaps.com/deploy/cost)

### Inferences
- Cheapest zero-ops commercial-safe prototype: OS NGD Tiles OpenData (free, authoritative GB, z≤15) with the `light-3857` or `blackwhite-3857` style. OpenFreeMap is the only free OSM option whose terms explicitly allow commercial use with no key; MapTiler Free and Stadia Free do not allow commercial use, so they are prototype-only.
- Best for commercial launch: if building-level zoom (z16+) matters, OS Premium plan's £1,000/month credit (≈30k premium map views) is the main lever; otherwise Protomaps on R2 is the cheapest at scale and has no per-view vendor risk, at the cost of owning updates. Stadia Starter ($20) or MapTiler Flex ($30) are the lowest-friction paid hosted options with muted styles.

### Gaps
- No independent uptime/SLA figures were found for OpenFreeMap, Protomaps builds, or OS APIs; OS publishes a service status page but no SLA numbers were fetched.
- Stadia attribution page and Stadia caching terms for tiles were not fetched (pricing page only mentions cacheable static maps).

## Key question 3: Self-hosting cost and effort for a GB-only PMTiles file versus a hosted provider

### Takeaway
A GB extract of the Protomaps OSM basemap, measured on 10 Oct 2026 from the daily planet build, is 61 MB at z0–10, 348 MB at z0–12, 1.42 GB (1,418 MB) at z0–14 and 2.86 GB (2,863 MB) at the full z0–15 (bbox −8.7,49.8 → 1.9,61.0, which also captures Northern Ireland and a strip of Ireland); extraction takes seconds to minutes via HTTP range requests, and hosting on Cloudflare R2 + Workers costs roughly $5–12/month at 10M requests, with a weekly or monthly re-extract as the update workflow.

### Cited Findings
- Protomaps planet builds: "roughly 120 GB" covering zoom 0–15 (z15 max); daily builds at maps.protomaps.com/builds with BLAKE3 hashes; builds kept for the past week plus latest per patch version; mirror on Source Cooperative; the page discourages hotlinking and recommends copying to your own storage; licence: "ODbL Produced Work", OpenStreetMap attribution required. — [Protomaps basemap downloads](https://docs.protomaps.com/basemaps/downloads)
- Measured on 10 Oct 2026: `https://build.protomaps.com/20261010.pmtiles` is 138,768,930,345 bytes (~139 GB / 129 GiB) per HTTP HEAD; daily files for 2026-10-06..10 all present, older 2025 dates return 404 (consistent with the one-week retention). — measured with `curl -I` against [build.protomaps.com](https://build.protomaps.com/)
- Measured with `go-pmtiles v1.31.2` (`pmtiles extract https://build.protomaps.com/20261010.pmtiles gb.pmtiles --bbox=-8.7,49.8,1.9,61.0 --maxzoom=Z --download-threads=8`): z0–10 → 61 MB archive (64 MB transferred, 7 s); z0–12 → 348 MB archive (365 MB transferred, 12 s); z0–14 → 1,418 MB on disk (1.6 GB transferred, 27 s); z0–15 → 2,863 MB on disk (3.1 GB transferred, 113 s on a home connection) — measured locally; CLI per [pmtiles CLI docs](https://docs.protomaps.com/pmtiles/cli)
- `pmtiles extract` syntax supports `--bbox=MIN_LON,MIN_LAT,MAX_LON,MAX_LAT`, `--region=REGION.geojson` (Polygon/MultiPolygon/Feature/FeatureCollection), `--maxzoom`, `--download-threads`, `--overfetch` (default 0.05); extracting 0..maxzoom "is always an efficient operation that makes minimal I/O or network requests to the source archive"; "The source archive must be clustered". — [pmtiles CLI](https://docs.protomaps.com/pmtiles/cli)
- "Each additional zoom level roughly doubles the size of the file"; a planet extract limited to z0–6 is ~60 MB. — [Protomaps basemap downloads](https://docs.protomaps.com/basemaps/downloads); [Protomaps getting started](https://docs.protomaps.com/guide/getting-started)
- Cloudflare deployment: upload to R2 (web UI ≤300 MB, else rclone), deploy the Worker with `ALLOWED_ORIGINS` (comma-separated CORS origins, default none) and an R2 binding `BUCKET`; "the worker must be assigned a zone on your own domain, not workers.dev" for caching; `CACHE_CONTROL` default `public, max-age=86400`; R2 "lower storage and no egress costs" but "higher latency (500ms or higher)" on cache misses; Workers "$5 USD per month" with 10M requests included, $0.30 per extra million; R2 charges for storage/reads only on cache misses. — [Protomaps: Cloudflare deployment](https://docs.protomaps.com/deploy/cloudflare)
- Cost calculator (110 GB stored, 10M requests, 1,000 GB egress): Cloudflare total $11.45/month; AWS S3+CloudFront+Lambda $119.56/month; "Does not include any free tiers or monthly credit". — [Protomaps cost calculator](https://docs.protomaps.com/deploy/cost)
- Styles: `@protomaps/basemaps` npm package exposes `layers(source, flavor, options)` returning a full MapLibre layer stack; built-in flavors `light`, `dark`, `white`, `grayscale`, `black` (white/grayscale/black are "intended for data visualization"); a flavor is "a plain object of color definitions"; override via `{...namedFlavor("light"), buildings: "red"}`; each flavor has a matching spritesheet; the old `protomaps-themes-base` package is deprecated. — [Protomaps basemap flavors](https://docs.protomaps.com/basemaps/flavors); [@protomaps/basemaps on yarn](https://classic.yarnpkg.com/en/package/@protomaps/basemaps)
- Protomaps map design is CC0 ("You can use the visual design without attribution"), tiles are ODbL so OSM attribution is still required. — [Protomaps basemap layers/attribution](https://docs.protomaps.com/basemaps/layers)
- A static host alternative: PMTiles can be served from any HTTP server supporting range requests, e.g. GitHub Pages, as shown in a community guide. — [dev.to: Host and test PMTiles on GitHub Pages](https://dev.to/ronitjadhav/how-to-host-and-test-pmtiles-on-github-pages-the-easiest-way-to-serve-maps-without-a-server-2ei8)
- OpenFreeMap self-host alternative: Ubuntu 24.04, planet Btrfs image ~170 GB (200 GB disk, 400 GB with auto-update), SSD recommended, regional `areas` supported, recommended Contabo Storage VPS "€4.5 / month"; tile generation needs 1 TB SSD + 64 GB RAM but pre-built planet images are downloadable. — [OpenFreeMap self-hosting docs](https://github.com/hyperknot/openfreemap/blob/main/docs/self_hosting.md)
- VersaTiles: OSM via Planetiler + Shortbread schema; "fully self-hostable, requires no API keys, charges no usage fees"; styles "Colorful, Natural, Muted, Gray, Toner, Satellite"; public demo server tiles.versatiles.org; Docker/Linux/macOS server builds. — [VersaTiles](https://versatiles.org/); [VersaTiles docs](https://docs.versatiles.org/)

### Inferences
- Effort: a one-line `pmtiles extract` plus an `rclone copy` to R2 and the stock Worker is an afternoon's work; the recurring effort is re-running the extract (cron, weekly) and purging the Cloudflare cache. GB-only at z15 fits comfortably in R2 (sub-10 GB), so storage is cents per month; at low traffic the Workers $5/month plan is the floor (or $0 if you accept no edge caching and serve range requests straight from a public R2 bucket/static host).
- Versus hosted: at prototype traffic (<100k tiles/month) OS OpenData or OpenFreeMap are $0 and zero-ops, so self-hosting only pays off when you want (a) no third-party dependency/SLA risk, (b) building-level OSM zooms without per-tile charges, or (c) full control over style/sprites/glyphs.
- Protomaps builds stop at z15; MapLibre overzooms vector tiles, so z16–z20 render from z15 data (building footprints in OSM are included where mapped, but UK OSM building completeness varies by area), with no extra tile fetches.

### Gaps
- No published figure for a GB-only Protomaps extract existed; the sizes above are my own measurement on 10 Oct 2026 and will drift with OSM growth (the planet file grew ~135 MB between the 6 Oct and 10 Oct builds).
- Cloudflare R2 free-tier allowances (10 GB storage, 10M Class B reads/month) were not cited from a Cloudflare page in this research; Protomaps' calculator explicitly excludes free tiers.

## Key question 4: Which providers have maintained Maputnik-compatible styles we can mute easily?

### Takeaway
All vector options are MapLibre style JSON and therefore Maputnik-editable: OS ships `light-3857`/`blackwhite-3857` with an official Maputnik how-to; Protomaps' `white`/`grayscale`/`black` flavors are generated programmatically (export static JSON then edit, or just override the flavor colours in code); OpenFreeMap's Positron and Stadia's Alidade Smooth/Toner Lite are ready-made muted styles; MapTiler has an in-house style editor plus Dataviz/Toner styles (not fetched here).

### Cited Findings
- OS NGD Tiles: four house styles; OS Maputnik guide loads `.../styles/blackwhite-3857`, `light-3857`, `road-3857`, `3857`; Black & White has "no fill colours at the large scales"; Light is "designed specifically for data visualisation"; style editing "in free to use applications such as" Maputnik. — [OS Maputnik guide](https://docs.os.uk/more-than-maps/using-os-mapping-apis/creating-a-bespoke-style-for-the-os-ngd-api-tiles); [OS blog Oct 2025](https://www.ordnancesurvey.co.uk/blog/new-basemap-styles-for-os-ngd)
- OpenFreeMap: styles Positron, Bright, Liberty, Dark, Fiord, 3D; "You can customize the styles using the Maputnik editor. For example, you can remove labels, POIs, or change colors"; "When you use a customized style, you need to host the style JSON yourself"; quick start links open `https://tiles.openfreemap.org/styles/positron` and `/styles/bright` in Maputnik; schema is "unmodified OpenMapTiles". — [OpenFreeMap quick start](https://openfreemap.org/quick_start/); [OpenFreeMap](https://openfreemap.org)
- Protomaps: flavors `white`, `grayscale`, `black` for data visualisation; customise by spreading `namedFlavor()`; static style JSON can be generated from maps.protomaps.com ("Get style JSON") for a theme/package version and then edited; sprites are version-specific (e.g. `sprites/v4/light`). — [Protomaps flavors](https://docs.protomaps.com/basemaps/flavors); [Protomaps MapLibre docs](https://docs.protomaps.com/basemaps/maplibre)
- Stadia: Alidade Smooth ("muted color scheme and fewer points of interest"), Alidade Smooth Dark, Stamen Toner / Toner Lite (B+W), custom styling page. — [Stadia themes](https://docs.stadiamaps.com/themes/)
- VersaTiles ships "Muted", "Gray" and "Toner" styles in its style toolkit. — [VersaTiles](https://versatiles.org/)
- MapTiler Free/Flex include 5/20 custom map styles respectively (its own editor). — [MapTiler pricing](https://www.maptiler.com/cloud/pricing/)
- The older OS Vector Tile API stylesheets repo notes the API "only works in epsg: 3857 (Web Mercator) in Maputnik". — [OS-Vector-Tile-API-Stylesheets via search](https://docs.os.uk/more-than-maps/using-os-mapping-apis/creating-a-bespoke-style-for-the-os-vector-tile-api)

### Inferences
- Easiest muting path with OS: start from `blackwhite-3857` (already colourless at large scales) and lower contrast of roads/labels in Maputnik; host the resulting JSON yourself with the key injected server-side or via a key-restricted proxy.
- Easiest muting path with OSM data: Protomaps `grayscale`/`white` flavor needs no editor at all; OpenFreeMap Positron is the closest "muted" hosted style and is OpenMapTiles-schema so any OpenMapTiles-compatible Maputnik style (e.g. Positron, Toner) works unchanged.

### Gaps
- MapTiler's style catalogue (Dataviz, Toner, Basic) and MapTiler Customize editor were not fetched; whether MapTiler styles can be exported for Maputnik under the Free plan is unverified.
- Stadia's MapLibre style JSON URLs were not confirmed from the fetched page.

## Key question 5: Known gotchas (projection, key restrictions, abuse policies, building-level zoom behaviour, caching, attribution)

### Takeaway
Main gotchas: OS NGD tiles are served in both EPSG:27700 and 3857 but MapLibre/Maputnik only work with the `*-3857` styles, OpenData stops at z15 in 3857 (z11 in 27700) and the API key must be appended to the tile URL (exposed unless proxied); MapTiler's free plan forbids commercial use and its terms prohibit server-side caching; OpenFreeMap has no SLA and is introducing per-referrer bandwidth caps after the Wplace incident; Protomaps/OpenFreeMap OSM tiles stop at z15/z14 and overzoom thereafter, while OS Premium serves true z16–19 data at a per-tile cost.

### Cited Findings

**Projection**
- OS NGD API – Tiles: "available in two projections: British National Grid for Great Britain (GB) data and Web Mercator"; 3857 zoom 6–19; 27700 zoom 0–15; "the OS NGD API – Tiles only works in epsg: 3857 (Web Mercator) in Maputnik"; for 27700 contact geodataviz@os.uk. — [OS NGD API – Tiles overview](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-tiles); [Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels); [OS Maputnik guide](https://docs.os.uk/more-than-maps/using-os-mapping-apis/creating-a-bespoke-style-for-the-os-ngd-api-tiles)
- OS NGD tile URL order is `{z}/{y}/{x}` (y before x) in OS's own MapLibre template, unlike the common `{z}/{x}/{y}`. — [OS MapLibre template](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/getting-started/libraries/maplibre-gl-js)

**Building-level zoom (z17–z20)**
- OS NGD Tiles 3857: z16–19 are Premium (£0.0331 per 4 tiles after the £1,000 allowance); the API's max zoom is 19, so z20 is MapLibre overzoom of z19 tiles; scale at z19 ≈ 1:533. — [Zoom levels](https://docs.os.uk/os-apis/accessing-os-apis/os-ngd-api-tiles/zoom-levels); [OS Data Hub plans](https://osdatahub.os.uk/plans)
- OS Maps API raster: z17 premium blended, z18–20 premium MasterMap Topography; max z20. — [OS Maps API layers and styles](https://docs.os.uk/os-apis/accessing-os-apis/os-maps-api/layers-and-styles)
- Protomaps builds cover zoom 0–15; higher zooms are client-side overzoom. — [Protomaps downloads](https://docs.protomaps.com/basemaps/downloads)
- OpenFreeMap serves the OpenMapTiles schema; the fetched pages did not state a max zoom (OpenMapTiles planets are conventionally z14, so expect overzoom above z14). — [OpenFreeMap](https://openfreemap.org) (max zoom not stated)
- MapTiler: Free plan counts "sessions" (5k) and API requests (100k); Flex overage $2.50/1k sessions; a session, not per tile, is the billing unit. — [MapTiler pricing](https://www.maptiler.com/cloud/pricing/)

**Key restrictions and abuse policies**
- MapTiler: "Allowed HTTP origins" restriction per key; requests lacking Origin/Referer are rejected when origins are set; "You must only use your own API keys"; Free plan is non-commercial; service pauses on quota exhaustion. — [MapTiler key protection](https://docs.maptiler.com/guides/maps-apis/maps-platform/how-to-protect-your-map-key); [MapTiler terms](https://www.maptiler.com/cloud/terms/)
- OpenFreeMap: no keys, no limits, no SLA; after Wplace (Aug 2025) the author plans per-referrer caps ("100 million requests per 24 hours or something similar") and wants native apps to send an identifying header; a third-party note describes the service as "provided as-is and subject to change or discontinuation" and suits prototypes, with critical production maps better on a contractual provider or self-host. — [Hyperknot blog](https://hyperknot.com/blog/openfreemap-survived-100000-requests/); [Nuxt scripts MapLibre guide](https://scripts.nuxt.com/scripts/maplibre/guides/styles-and-providers.md)
- OS: 600 transactions/minute throttle on live projects; API key must be in the request (OS demo shows a proxy pattern to hide it). — [OS Data Hub plans](https://osdatahub.os.uk/plans); [OS-Data-Hub-API-Demos](https://github.com/OrdnanceSurvey/OS-Data-Hub-API-Demos)
- Stadia: free plan hard-capped (errors, not charges) and non-commercial. — [Stadia pricing](https://stadiamaps.com/pricing/)

**Caching on your own server**
- MapTiler: "It is prohibited to store, save, and/or redistribute any map content from a server-side cache or temporary storage" (s7.2); device cache allowed "for use by a single end-user only" (s5.7); bulk download prohibited (s6.3). — [MapTiler Cloud Terms](https://www.maptiler.com/cloud/terms/)
- Thunderforest: bulk downloading only on Small Business or higher. — [Thunderforest pricing](https://thunderforest.com/pricing)
- Protomaps/OpenFreeMap self-host/VersaTiles: you own the tiles (ODbL), so caching is unrestricted; OpenFreeMap public instance asks only for attribution. — [Protomaps downloads](https://docs.protomaps.com/basemaps/downloads); [OpenFreeMap](https://openfreemap.org)
- OS: API terms not retrievable (JS page); only secondary evidence that Premium data may be cached for a session only. — [OS blog 2020](https://www.ordnancesurvey.co.uk/blog/os-data-hub-to-desktop-gis)

**Attribution strings**
- OS: "Contains OS data © Crown Copyright [and database right] (year)". — [OS OpenData](https://www.ordnancesurvey.co.uk/opendata)
- OpenFreeMap: "OpenFreeMap © OpenMapTiles. Data from OpenStreetMap" with links (the OpenFreeMap part is optional); MapLibre adds it automatically from the style. — [OpenFreeMap](https://openfreemap.org)
- Protomaps: OSM attribution required (ODbL); design CC0. — [Protomaps downloads](https://docs.protomaps.com/basemaps/downloads)
- MapTiler: "MapTiler attribution is required to be shown on screen while the map is displayed"; logo on Free plan. — [MapTiler terms](https://www.maptiler.com/cloud/terms/); [MapTiler pricing](https://www.maptiler.com/cloud/pricing/)
- Mapbox raster-in-MapLibre example uses "© Mapbox © OpenStreetMap". — [Mapbox in MapLibre](https://docs.mapbox.com/help/dive-deeper/mapbox-in-maplibre/)
- Thunderforest: "it's not permitted to remove the attribution"; Geoapify: Geoapify + data-source attribution, "Powered by" link recommended. — [Thunderforest pricing](https://thunderforest.com/pricing); [Geoapify pricing](https://www.geoapify.com/pricing/)

**Northern Ireland**
- OS NGD/OS Open Zoomstack cover Great Britain only; the OSM-based options (Protomaps, OpenFreeMap, MapTiler, Stadia, VersaTiles) cover NI as part of the global OSM planet. — [OS NGD API – Tiles overview](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-tiles); [Protomaps downloads](https://docs.protomaps.com/basemaps/downloads)

### Inferences
- If you need genuine building outlines at z17–z20 across GB with authoritative OS geometry, only OS NGD Tiles (Premium zooms) delivers it; budget ≈£8.28 per 1,000 premium tiles beyond the free £1,000. A pragmatic hybrid is OS OpenData/OSM for z≤15 and switching sources at z16+ only for logged-in/paid users.
- Because the OS key sits in the tile URL, a commercial deployment should proxy or at least monitor usage; OS does not document origin/referrer key restrictions in the fetched pages (gap).
- MapTiler's no-server-cache clause rules out a CDN/proxy cache in front of MapTiler; Protomaps/self-host is the clean answer if caching on your own infrastructure is a requirement.

### Gaps
- Whether OS Data Hub supports origin/referrer restrictions on API keys was not found in fetched docs.
- OpenFreeMap's max zoom and the current status of the planned per-referrer limits (as of Oct 2026) were not confirmed from primary pages.
- Mapbox Product Terms regarding use of Mapbox vector tiles in third-party renderers were not fetched; Mapbox's own help page documents MapLibre use with per-tile billing, so it appears permitted, but the legal text is unverified.
