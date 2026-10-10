# PostGIS serving and aggregation for a zoom-dependent £/m² heatmap (MapLibre GL JS, one Linux VM)

Research date: 2026-10-10. Target stack: PostgreSQL 16/17 + PostGIS 3.4/3.5 on Ubuntu 24.04, Python ETL, one VM, monthly Land Registry refresh. Anything dated before 2025 is flagged as such.

Scope note: three serving options are covered. (A) dynamic ST_AsMVT tiles via a tile server; (B) pre-generated PMTiles via tippecanoe served statically; (C) a bounding-box JSON API. Then aggregation geometry (H3 vs ST_HexagonGrid vs BNG squares), per-cell statistics SQL, HPI adjustment, comparables, local tooling, prior art.

---

## Key question 1: For a monthly-updated, read-only dataset, is pre-generated PMTiles or dynamic ST_AsMVT the better default?

### Takeaway
Practitioner guidance puts monthly updates squarely inside the "static tiles are fine" zone, and the FOSS4G 2026 framing is "hybrid: static for slow-changing layers, dynamic for fresh/filterable ones". For this project the heavy work (per-cell medians) must be precomputed into tables either way; after that, a Martin function source and a tippecanoe PMTiles build are both cheap. Choose PMTiles if the set of layer variants is small and fixed; choose Martin function sources (with its in-memory cache plus nginx) if users need interactive filters (property type, time window, metric) that would otherwise multiply the number of tilesets. One Martin instance can serve both, so the two are not mutually exclusive.

### Cited Findings
- Protomaps (the PMTiles authors) say PMTiles "requires re-uploading the whole file after each change", that this "is acceptable for hourly or daily updates" and that higher frequencies "use an uneconomical amount of data transfer"; best fit is "data that changes at most daily, or never". They recommend PostGIS + pg_tileserv/martin/ST_AsMVT for "sizeable, dynamic datasets with frequent user updates", and plain GeoJSON if total data is not "over a few megabytes". (Article dated 22 May 2024 — older than the 2025 cut-off but still the canonical statement.) — [Protomaps blog: You might not want PMTiles](https://protomaps.com/blog/you-might-not-want-pmtiles/)
- FOSS4G Europe 2026 talk "Vector Tiles: Static or Dynamic?" (James Milner, Addresscloud, 1 July 2026) compares the two on speed, cost, complexity, flexibility and data freshness; names Tippecanoe/PMTiles for static and PostGIS ST_AsMVT with Martin or Tegola for dynamic; and describes "a hybrid option, serving frequently updated data dynamically and less frequently updated data as static files". No single approach is prescribed. — [talks.osgeo.org FOSS4G-Europe 2026 8P3BMH](https://talks.osgeo.org/foss4g-europe-2026/talk/8P3BMH/)
- ST_AsMVT: `bytea ST_AsMVT(anyelement row, text name, integer extent, text geom_name, text feature_id_name)`; rows need a geometry already in tile space (use ST_AsMVTGeom); other columns become feature attributes; default extent 4096; available since PostGIS 2.4, parallel since 2.5, feature IDs since 3.0; multiple layers by concatenating with `||`. — [PostGIS docs: ST_AsMVT](https://postgis.net/docs/ST_AsMVT.html)
- ST_TileEnvelope: `ST_TileEnvelope(z, x, y, bounds = SRID 3857 world, margin = 0.0)`; `bounds` lets you tile any SRS; `margin=0.125` expands tile by 12.5%; since 3.0, margin since 3.1. — [PostGIS docs: ST_TileEnvelope](https://postgis.net/docs/ST_TileEnvelope.html)
- Paul Ramsey's canonical dynamic-tile pattern (2019, old but unchanged): bounds CTE → ST_AsMVTGeom(ST_Transform(geom,3857), bounds) filtered with ST_Intersects against the envelope → ST_AsMVT outer query; the server's only job is turning z/x/y into that SQL. — [Crunchy Data: Serving Dynamic Vector Tiles from PostGIS](https://www.crunchydata.com/blog/dynamic-vector-tiles-from-postgis)
- PMTiles hosting requirements: storage must support HTTP Range requests; CORS must allow GET/HEAD, allow headers `Range` and `If-Match`, expose `ETag`; OPTIONS preflight must be handled (nginx example exists); each Range tile request is billed as one GET on object storage; GitHub Pages caps a repo at 1 GB. — [Protomaps docs: cloud storage](https://docs.protomaps.com/pmtiles/cloud-storage)
- Self-hosting PMTiles: run `pmtiles serve` behind existing nginx/Apache, or use Caddy with the `pmtiles_proxy` plugin (serves from S3-compatible storage, Azure, GCS, public HTTP or local filesystem); `cache_size` (MB) caches only headers/directories, not tile data. — [Protomaps docs: deploy/server](https://docs.protomaps.com/deploy/server)
- PMTiles archives are read-only; the format is spec v3; the Python `pmtiles` package is beta; MapLibre GL JS is the recommended client via the JS `pmtiles` library. — [Protomaps docs: PMTiles](https://docs.protomaps.com/pmtiles/)
- Tippecanoe: BSD-2-Clause; write PMTiles directly with `-o file.pmtiles`; `-zg` guesses maxzoom from feature spacing; `-r/--drop-rate` (default 2.5), `-rg` keeps ≤~50,000 features in the densest tile; `--drop-densest-as-needed` when a tile exceeds 500 KB; `--coalesce` merges consecutive features with identical attributes; `--accumulate-attribute=POP_MAX:sum` (sum/mean/max/min/count) carries attributes from dropped features; `--cluster-distance`; `-P` parallel read for line-delimited GeoJSON (auto for FlatGeobuf); `tile-join` merges MBTiles/PMTiles/dirs and can join a CSV (`-c`); `TIPPECANOE_MAX_THREADS`, `-t` temp dir. — [felt/tippecanoe README](https://github.com/felt/tippecanoe)
- Tippecanoe latest release is 2.79.0 (24 Jul; release page omits the year; a MacPorts listing says the port was updated "1 year ago", so 2.79.0 is probably July 2025, unconfirmed). — [felt/tippecanoe releases](https://github.com/felt/tippecanoe/releases); [MacPorts tippecanoe](https://ports.macports.org/port/tippecanoe/details/)
- Timing anecdote (not a benchmark): WaterwayMap.org's maintainer reports ~20 GiB GeoJSON-Seq → ~1.4 GiB PMTiles in ~30 min with tippecanoe. — [OSM community: Efficient production of PMTiles or MVT](https://community.openstreetmap.org/t/efficient-production-of-pmtiles-or-mvt/109425)
- Wherobots (Spark-based, not tippecanoe) note that tile-generation time is driven by "the number of features multiplied by the number of tiles which that feature intersects", so points are cheap. — [Wherobots: Overture vector tile generation performance](https://wherobots.com/overture-vector-tile-generation-performance)
- A CARTO comparison (older, vendor-run) found ST_AsMVT faster than Mapnik's encoder but with differences in invalid-geometry handling, simplification and feature IDs. — [CARTO: An update on MVT encoders](https://carto.com/blog/an-update-on-mvt-encoders-c/)
- Martin's tile cache stores tiles after post-processing (compression) so cache hits skip regeneration; LRU with optional TTLs; default limit 512 MB; recommended production pattern is nginx/Apache reverse proxy in front for caching, TLS and load balancing; responses support ETag/304 and Content-Encoding; no built-in auth. — [Martin architecture](https://maplibre.org/martin/architecture/)

### Inferences
- With a monthly, read-only dataset the dynamic path has no cache-invalidation problem at all: set Martin's `cache.tile_expiry` to days (or restart Martin after the monthly ETL) and put nginx `proxy_cache` in front; after the first visitor per tile the database is never touched again until the next refresh. So "dynamic" here is effectively "lazily generated static tiles".
- The decisive factor is combinatorics, not freshness. If the UI needs N property types × M time windows × K metrics, static means N×M×K tilesets regenerated monthly, whereas a Martin function source accepts these as `?query` parameters against one `cell_stats` table (see Q4). If the UI is a single fixed layer (e.g. "all types, last 24 months HPI-adjusted, 4 resolutions"), tippecanoe + PMTiles on nginx is the simplest possible deployment (no tile server process, no DB connection pool in the request path).
- Tile payloads for an aggregated layer are tiny: a z14 Web Mercator tile at UK latitudes is roughly 1.5 km across (~2.3 km²), holding ~150 H3 res-10 cells (0.015 km² each); a z8 tile (~96 km across, ~9,200 km²) holds ~250 res-6 cells (36 km²). ST_AsMVT over a few hundred pre-built polygons with a GiST index is a millisecond-class query; no benchmark was found but the Crunchy pattern and Martin's reported cache-hit costs (72 µs CPU/request) support "cheap once cached".
- Recommended default for this project: (1) materialise `cell_stats` monthly; (2) serve it through Martin function sources with nginx caching during development and for any filterable views; (3) additionally run a tippecanoe job in the monthly ETL to emit a PMTiles file of the default view, so the public map can fall back to pure static files if the VM is under load. Martin serves PMTiles too, so no second server is needed.
- Option C (bbox JSON API) is the right tool for small result sets with rich attributes (e.g. the comparables list, or cells for the current viewport at high zoom), not for the heatmap at national zoom levels; see Q2 for the RE-Maps precedent.

### Gaps
- No published head-to-head benchmark of PMTiles vs ST_AsMVT for aggregated polygon layers was found; the only hard numbers are Martin's own cache-hit CPU figures and the tippecanoe anecdote above.
- Tippecanoe timing for ~30M points to a fixed zoom range is not reported anywhere found; must be measured locally.

---

## Key question 2: Martin vs pg_tileserv (and Tegola, FastAPI) in 2026 — maintenance, features, Docker

### Takeaway
Martin is the actively developed choice (stable 1.16.1 on 9 Sep 2026; 2.0.0-beta.3 on 9 Oct 2026) with function sources, a built-in tile cache, PMTiles/MBTiles/COG serving and official Docker images. pg_tileserv still works and is simpler, but has no GitHub releases, its last code change was January 2025 (only a README/dependency bump and a comment fix since) and it relies on an external cache. Tegola's last release was January 2025. A FastAPI endpoint is viable for Option C but reinvents what Martin does for tiles.

### Cited Findings
**Martin**
- crates.io: newest stable 1.16.1 (2026-09-09); 1.16.0 (2026-09-07), 1.15.0 (2026-08-31), 1.14.0 (2026-08-18), 1.13.0 (2026-07-25), 1.12.0 (2026-07-07), 1.11.0 (2026-06-16), 1.10.1 (2026-05-19); pre-releases 2.0.0-beta.0..3 from 2026-09-29 to 2026-10-09. (A lib.rs snippet claiming "1.3.1 Feb 2026" is consistent with this cadence, i.e. ~1 minor release a month through 2026.) — [crates.io API: martin](https://crates.io/api/v1/crates/martin)
- 2.0.0-beta notes: composite tiles cached in the client's encoding (CPU per request 2,504 µs → 72 µs on a Berlin extract); tile cache memory down ~17%; PMTiles no longer crashes (SIGBUS) when an archive is rewritten in place; remote PMTiles reload when leaf directories move; **prebuilt x86_64 binaries, Debian package and Docker images now require an x86-64-v3 CPU (AVX2/BMI2/FMA)**; a DoS fix in beta.2 affects binary installs only. — [maplibre/martin releases](https://github.com/maplibre/martin/releases)
- Architecture: Rust, Actix-Web; crates `martin`, `martin-core`, `mbtiles`, `martin-tile-utils`; sources: PostGIS tables and MVT-returning functions (deadpool-postgres pooling), PMTiles (local or remote via Range requests), MBTiles, COG, DuckDB/GeoParquet (experimental), GeoJSON (in-memory R-tree); Moka LRU cache with TTLs, default 512 MB; auto-discovery with a reload driver (filesystem events or polling) that keeps the previous catalog if discovery fails. — [Martin architecture](https://maplibre.org/martin/architecture/)
- Function sources: function must take `z` (or `zoom`), `x`, `y` as `integer`, optionally a fourth `json` argument of any name for query-string params; return `bytea`, or a record of `(bytea, text)` where the text is used as the ETag; the documented example is `IMMUTABLE STRICT PARALLEL SAFE`, uses `ST_TileEnvelope(z,x,y)`, filters with `&&` against the envelope reprojected to the data SRID so the index is used, then `ST_AsMVTGeom` + `ST_AsMVT`; URL params arrive as JSON (`query_params->>'answer'`), arrays/objects allowed when URL-encoded; TileJSON can be customised via a JSON `COMMENT ON FUNCTION` merged with RFC 7386 merge-patch. — [Martin docs: PostgreSQL function sources](https://maplibre.org/martin/sources-pg-functions/)
- Config keys: `cache.size_mb` (512), `cache.tile_size_mb` (default half of size_mb), `cache.expiry`/`idle_timeout` and `tile_expiry`/`tile_idle_timeout`, `cache.minzoom`/`maxzoom`, `cache_control` (default Cache-Control header), `postgres.pool_size` (20), `postgres.auto_publish.tables/functions` (`from_schemas`, `source_id_format`, table options `buffer`, `clip_geom`, `extent`, `id_columns`), `preferred_encoding: brotli` ("gzip is faster, but brotli is smaller, and may be faster with caching"). — [Martin docs: config file](https://maplibre.org/martin/config-file/)
- Docker Compose: `ghcr.io/maplibre/martin:2.0.0-beta.3` (docs example) with the connection string passed as the command (`postgres://postgres:password@db/db`), port 3000, alongside `postgis/postgis:17-3.5-alpine`; image has a HEALTHCHECK; Compose does not restart unhealthy containers (docs suggest Docker Autoheal). — [Martin docs: run with Docker Compose](https://maplibre.org/martin/run-with-docker-compose/)
- Martin DuckDB backend (GSoC 2026, 15 Aug 2026): serves MVT straight from GeoParquet using DuckDB's `ST_AsMVT`/`ST_AsMVTGeom`; gated behind `unstable-duckdb`; `.duckdb` table sources parsed but not served; no hot reload; parallelism ≈ `pool_size (4) × threads`. — [MapLibre news: GSoC Martin DuckDB](https://maplibre.org/news/2026-08-15-gsoc-martin-duckdb/)
- MapLibre roadmap page for Martin exists (martin-core library listed as released Sep 2025). — [maplibre.org roadmap: martin](https://maplibre.org/roadmap/martin-tile-server)

**pg_tileserv**
- Apache-2.0; 37 open issues; Releases section on GitHub is empty; README recommends "an HTTP proxy caching layer (eg Varnish)" and has a full Function Layers section. — [CrunchyData/pg_tileserv](https://github.com/CrunchyData/pg_tileserv)
- Commit history: 11 Dec 2025 "Correction function name in comment"; 17 Sep 2025 README update and dependency updates; 31 Jan 2025 last functional code changes (rtrim fix, Go version harmonisation, macOS uname switch). — [pg_tileserv commits](https://github.com/CrunchyData/pg_tileserv/commits/master)
- Docker Hub image `pramsey/pg_tileserv`, latest dated tag `20250131`. — [Docker Hub pramsey/pg_tileserv](https://hub.docker.com/r/pramsey/pg_tileserv)
- Function layers: first three params must be `z integer, x integer, y integer`; extra params should have defaults (exposed in layer JSON); return `bytea`; role needs EXECUTE; config `CacheTTL` (seconds for downstream caches; 0 = no header), `DbPoolMaxConns` (sample 4), `DefaultResolution` (4096), `DefaultBuffer` (256); env override prefix `TS_`; `Dockerfile.alpine` ≈ 18 MB. — [pg_tileserv README (raw)](https://raw.githubusercontent.com/CrunchyData/pg_tileserv/master/README.md)
- Paul Ramsey's "Tile serving with dynamic geometry" (24 Mar 2020, old) shows a pg_tileserv function `public.hexagons(z,x,y,step default 4)` generating hexagons whose edge = tile width / 2^step, so cells shrink with zoom. — [Crunchy Data: tile serving with dynamic geometry](https://crunchydata.com/blog/tile-serving-with-dynamic-geometry)

**Tegola**
- Latest release v0.21.2, published 7 Jan 2025 (pkg.go.dev). — [pkg.go.dev go-spatial/tegola](https://pkg.go.dev/github.com/go-spatial/tegola)
- v0.21.0 added S3 local-proxy option, Redis via URI (go-redis v9) and warned that an open issue (#999) causes "malformed geoprocessing with providers other than `mvt_postgis`" — advice is to stay on v0.19.0 or migrate to `mvt_postgis`; v0.20.0 switched PostGIS config to a single `uri` connection string (breaking). — [go-spatial/tegola releases](https://github.com/go-spatial/tegola/releases)
- AUR package `tegola-headless 0.21.0-1` first submitted 2026-06-12 (community packaging, not upstream activity). — [AUR tegola-headless](https://aur.archlinux.org/packages/tegola-headless/)

**FastAPI / JSON API precedent (Option C)**
- RE-Maps (MIT): FastAPI + PostgreSQL/PostGIS backend, Next.js + MapLibre GL frontend; maps zoom to 8 tiers (14.5+ individual properties; 13.2 street medians; 12.0 postcode unit; 10.5 postcode sector; 9.0 outcode; 7.0 local authority district; 4.5 county; 0 country); sector-and-coarser stats precomputed into an `area_stats` table, street/postcode medians computed live; EPC used only optionally for £/m²; a two-year sample (~1.9M sales) loads in "a few minutes". — [kianharia30/RE-Maps](https://github.com/kianharia30/RE-Maps)

### Inferences
- For one VM: Martin + nginx is the pragmatic 2026 default. It replaces pg_tileserv's need for Varnish with its own 512 MB in-process cache, serves the PMTiles fallback from the same process, and auto-discovers function sources. Check the VM's CPU flags before using 2.0 prebuilt binaries/images (x86-64-v3); stay on the 1.16.x image if the VM is older or build from source.
- pg_tileserv remains fine if already known to the team — same function-layer contract (z,x,y + defaults → bytea), so a function written for one works in the other (Martin additionally accepts a `json` params argument). But with no releases and near-zero 2025–26 code activity, treat it as maintenance-mode.
- Tegola's config/caching model (seed/purge to S3/Redis) targets multi-node deployments and adds little for a single VM; the #999 warning is a reason to avoid it here.
- A FastAPI tile endpoint is only worth writing if you also need per-request auth or business logic inside the tile path; otherwise use Martin for tiles and FastAPI for the JSON endpoints (comparables, cell detail).

### Gaps
- No official statement from Crunchy Data on pg_tileserv's maintenance status was found; the inference is from commit/release activity only.
- Tegola's commit activity after January 2025 was not verified (only release list and pkg.go.dev checked).
- The Martin stable-1.x Docker tag naming on ghcr.io was not verified (docs example only shows the 2.0 beta tag).

---

## Key question 3: H3 vs PostGIS ST_HexagonGrid vs British National Grid squares — simplest, best-looking, multi-resolution; does h3-pg build on PG17/PostGIS 3.5?

### Takeaway
h3-pg is alive and now a PostGIS-umbrella project (v4.5.0, 8 June 2026; CI covers PostgreSQL 14–18; apt package `postgresql-17-h3`); the old zachasme repo was archived on 30 Dec 2025. H3 is the cleanest for multi-resolution (one cell id per sale, `h3_cell_to_parent` for every coarser level, built-in zoom→resolution helper) and gives equal-area-ish hexagons that look good; its cells are not metric-sized or BNG-aligned. ST_HexagonGrid/ST_SquareGrid in EPSG:27700 are the simplest to get exactly right in metres (true 100 m / 250 m / 1 km / 5 km cells, OS-grid aligned squares) with zero extra extensions, but only the square grid nests cleanly. Because medians cannot be rolled up from child cells anyway, "nesting" matters less than it first appears: compute every resolution from the raw sales.

### Cited Findings
**h3-pg status and install**
- zachasme/h3-pg "was archived by the owner on Dec 30, 2025. It is now read-only." — [zachasme/h3-pg releases](https://github.com/zachasme/h3-pg/releases)
- postgis/h3-pg releases: v4.5.0 (8 Jun) bundles H3 core 4.5.0, adds `h3_grid_ring`, `h3_is_valid_index`, an experimental GiST operator class, a breaking btree comparator fix that auto-reindexes, and "fixes PostgreSQL 17+ maintenance failures"; v4.2.3 (24 Jun, previous year) added PostgreSQL 18 support, `h3_get_resolution_from_tile_zoom`, and renamed `lat_lng` functions to `latlng`; v4.2.0 bumped H3 to 4.2.0 and added `h3_polygon_to_cells_experimental` plus experimental SP-GiST opclass; v4.1.1 added `postgis_raster` integration. v4.5.0 states h3-pg "now lives under the PostGIS umbrella". — [postgis/h3-pg releases](https://github.com/postgis/h3-pg/releases)
- PostGIS Development Team announcement of h3-pg 4.5.0 ("first h3-pg release under the PostGIS umbrella"; bundled H3 core 4.5.0; GiST opclass work; PG17+ maintenance fixes; SP-GiST fixes; improved geometry/polygonisation in h3_postgis; on PGXN as `h3`). Mailing-list URL dated 2026-06-08. — [postgis-users announcement](https://lists.osgeo.org/pipermail/postgis-users/attachments/20260608/9316200e/attachment.htm)
- README: "CI currently tests PostgreSQL 14-18 on Linux and macOS"; Apache 2.0; install via `pgxn install h3`, `sudo apt install postgresql-16-h3` (Ubuntu 22.04+, substitute your PG major), `yum install h3-pg_16`, or CMake (`cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build && cmake --install build --component h3-pg`; needs CMake 3.20+). — [postgis/h3-pg README](https://github.com/postgis/h3-pg)
- Ubuntu archive carries `postgresql-17-h3` (h3-pg 4.2.3-4, depends on postgresql-17 and libh3 1.x). — [ubuntuupdates postgresql-17-h3](https://ubuntuupdates.org/package/core/questing/universe/base/postgresql-17-h3)
- PostGIS 3.5.0 requires PostgreSQL 12–17, GEOS 3.8+, Proj 6.1+ (released Sep/Oct 2024). — [PostGIS 3.5.0 release](https://postgis.net/2024/09/PostGIS-3.5.0)
- h3-pg API (postgis/h3-pg docs): `h3_latlng_to_cell(point, res)` (h3) and `h3_latlng_to_cell(geometry|geography, res)` (h3_postgis, since 4.2.3); `h3_cell_to_parent(cell, res)` and `h3_cell_to_parent(cell)`; `h3_cell_to_boundary_geometry(h3index)` and `h3_cell_to_geometry(h3index)` (centroid); `h3_get_resolution_from_tile_zoom(z, max_h3_resolution DEFAULT 15, min_h3_resolution, hex_edge_pixels DEFAULT 44, tile_size DEFAULT 512)` (h3_postgis, since 4.2.3); `h3_polygon_to_cells(geometry|geography, res)`; `h3_cell_area(cell, unit DEFAULT 'km^2')`; `h3_grid_disk(origin, k)`. h3_postgis functions treat coordinates as lon/lat degrees (SRID 4326) and do not reproject; `h3.strict = true` rejects out-of-range lon/lat (catches projected coordinates passed by mistake). — [postgis/h3-pg docs/api.md](https://github.com/postgis/h3-pg/blob/main/docs/api.md)

**H3 resolution table (H3 v4.x; areas on a sphere with the WGS84 authalic radius; edge lengths exact for res 0–6, extrapolated for finer)** — [h3geo.org resolution table](https://h3geo.org/docs/core-library/restable/)

| Res | Avg area (km²) | Avg edge (km) | Cells |
|---|---|---|---|
| 5 | 252.90 | 9.854 | 2,016,842 |
| 6 | 36.129 | 3.725 | 14,117,882 |
| 7 | 5.161 | 1.406 | 98,825,162 |
| 8 | 0.7373 | 0.5314 | 691,776,122 |
| 9 | 0.1053 | 0.2008 | 4,842,432,842 |
| 10 | 0.01505 | 0.07586 | 33,897,029,882 |
| 11 | 0.002150 | 0.02866 | 237,279,209,162 |

**PostGIS grid generators**
- `setof record ST_HexagonGrid(float8 size, geometry bounds)`: for a planar SRS and edge size there is one unique tiling starting at the SRS origin; returns hexagons (with i,j indices) overlapping the bounds; output SRS = bounds SRS; "Not a hexagon tiling of the globe, this is not the H3 tiling scheme"; doubling/tripling edge gives parent tilings aligned to the origin but "it is not possible to generate parent hexagon tilings that the child tiles perfectly fit inside"; since 3.1.0; documented point-summary example joins points with `ST_Intersects` and groups by `hexes.geom`. — [PostGIS docs: ST_HexagonGrid](https://postgis.net/docs/ST_HexagonGrid.html)
- `setof record ST_SquareGrid(float8 size, geometry bounds)`: tiling anchored at the SRS origin; "Doubling the edge size produces a parent tiling that aligns exactly with the original. Standard web map tilings in Mercator are power-of-two square grids on this principle"; result covers the full bounds (filter with ST_Intersects if needed); since 3.1.0; warns `ST_EstimatedExtent` may differ from the true extent so ANALYZE first. — [PostGIS docs: ST_SquareGrid](https://postgis.net/docs/ST_SquareGrid.html)
- Paul Ramsey (Nov 2020, old): grids are "fixed" (equal cell area/distance, stable cell coordinates for a given size) and point summaries can be computed on the fly without storing the grid; examples use ST_SquareGrid(400000, …3857) and ST_HexagonGrid(100000, …3857). — [Crunchy Data: Waiting for PostGIS 3.1 grid generators](https://www.crunchydata.com/blog/waiting-for-postgis-3.1-grid-generators)

**BNG vs Web Mercator on the client**
- MapLibre's roadmap lists non-Mercator support as an open goal in three parts (whole-map non-Mercator projection; loading vector tiles built in custom coordinate systems; specifying an EPSG code and tile matrix set) with no shipped status, linking to GitHub discussion #163 and an Open Collective funding page. — [MapLibre roadmap: non-Mercator projection](https://maplibre.org/roadmap/maplibre-gl-js/non-mercator-projection)
- The maplibre discussion #163 thread is still asking for progress; one commenter warns Proj4Js vs PROJ 9 can differ by up to ~400 m in rare cases. — [maplibre/maplibre discussion #163](https://github.com/maplibre/maplibre/discussions/163)
- Ordnance Survey's OS Maps API publishes EPSG:27700 and EPSG:3857 tile sets; Proj4Leaflet is the established non-Mercator route in Leaflet. — [OS docs: layers and styles](https://docs.os.uk/os-apis/accessing-os-apis/os-maps-api/layers-and-styles)
- ST_TileEnvelope's `bounds` argument can generate tiles in any coordinate system, which is how a 27700 tile matrix would be produced server-side if a client supported it. — [PostGIS docs: ST_TileEnvelope](https://postgis.net/docs/ST_TileEnvelope.html)

### Inferences
- **Mapping requested cell sizes to H3** (flat-to-flat width ≈ 1.73 × edge, from the table above): ~5 km → res 6 (edge 3.7 km, width ~6.4 km, 36 km²) or res 7 (edge 1.4 km, width ~2.4 km, 5.2 km²); ~1 km → res 8 (edge 531 m, width ~0.92 km, 0.74 km²); ~250 m → res 9 (edge 201 m, width ~350 m, 0.105 km²); ~100 m → res 10 (edge 76 m, width ~130 m, 0.015 km²). H3 cannot hit 100/250/1000/5000 m exactly; cell sizes also vary by location (the table gives averages). If exact OS-style sizes are a product requirement, use ST_SquareGrid or ST_HexagonGrid in EPSG:27700.
- **Metric correctness**: ST_HexagonGrid/ST_SquareGrid `size` is in SRS units. In EPSG:3857 at UK latitudes (51–58°N) Mercator scale distortion is roughly 1.6–1.9×, so a "1000 m" 3857 hexagon is ~530–630 m on the ground and varies north–south. In EPSG:27700 (metres, OS projection) `ST_SquareGrid(1000, bounds27700)` yields true 1 km OS grid squares aligned to National Grid lines because the grid is anchored at the SRS origin (the OS false origin). This is the simplest option to get exactly right.
- **Rendering BNG cells in MapLibre** is straightforward: MapLibre needs 3857 tiles, but the cell polygons are just geometry — `ST_AsMVTGeom(ST_Transform(cell_geom, 3857), ST_TileEnvelope(z,x,y))` works, and squares appear very slightly rotated relative to the Mercator graticule (the BNG convergence angle), which is normal and barely visible. Native EPSG:27700 tiling in MapLibre GL JS is still not available (roadmap open), so a BNG *tile matrix* is not an option; a BNG *cell grid* is.
- **Multi-resolution**: ST_SquareGrid parents nest exactly (power-of-two); ST_HexagonGrid parents do not nest; H3 gives a single parent per cell at every resolution (`h3_cell_to_parent`), which is why it is the usual choice for "one id per sale, many roll-ups". However, the £/m² statistics of interest (median, p25/p75) are not composable — a median of child medians is not the parent median — so every resolution must be aggregated from the sales table regardless of grid family. The practical difference is therefore: H3 lets you store one `h3index` per sale and group by `h3_cell_to_parent(cell, r)`; square/hex grids require a spatial join (or an i,j arithmetic) per resolution. Both are a few minutes of SQL at ~20M rows (no benchmark found; see Gaps).
- **Looks**: hexagons (H3 or ST_HexagonGrid) read better as a heatmap (no row/column striping, more isotropic neighbourhoods); OS squares look like the familiar OS grid and are easier to explain to UK property users ("the 1 km square"). Either is acceptable; this is a product decision.
- **Simplest to get right**: ST_SquareGrid in 27700 (no extra extension, exact metres, exact nesting). **Best for multi-resolution plumbing and zoom mapping**: H3 (use `h3_get_resolution_from_tile_zoom(z, max_h3_resolution => 10, min_h3_resolution => 6)` to pick the resolution per tile). **Build status**: h3-pg 4.5.0 explicitly fixes PostgreSQL 17+ and is CI-tested on PG 14–18; PostGIS 3.5 integration via `h3_postgis` is part of the same release; on Ubuntu 24.04 install `postgresql-17-h3` from PGDG/Ubuntu or build with CMake.

### Gaps
- No source states an explicit "h3-pg requires PostGIS ≥ x.y"; compatibility with PostGIS 3.5 is inferred from the h3_postgis improvements in the 4.5.0 release and the PG 14–18 CI matrix.
- Whether the PGDG apt repository (not just Ubuntu universe) ships `postgresql-17-h3` 4.5.0 for noble was not verified.
- No timing data was found for grouping ~20M points by H3 cell or joining them to ST_HexagonGrid cells in PostGIS.

---

## Key question 4: Concrete SQL — per-cell median/count/p25/p75, materialisation and refresh, minimum-count suppression, HPI adjustment, and the "top 10 comparables" query

### Takeaway
Use `percentile_cont(ARRAY[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY ppm2)` grouped by (resolution, cell) over the HPI-adjusted linked sales, write the result into a plain table or materialized view keyed by (res, cell) with a unique index (required for `REFRESH MATERIALIZED VIEW CONCURRENTLY`), suppress cells with fewer than 5 sales (the ONS HPSSA rule), and serve the pre-built polygons via a Martin function. Comparables: filter with `ST_DWithin` (metres in 27700 or geography) and order with the `<->` KNN operator; the HPI join is a two-row lookup on (area_code, property_type, month). All SQL below is author-composed from the cited function docs and has not been executed; test on the real schema.

### Cited Findings
- `percentile_cont(fraction) WITHIN GROUP (ORDER BY double precision)` and the array form `percentile_cont(fractions double precision[])` returning an array of the same shape; `percentile_disc` for discrete; `mode() WITHIN GROUP`; nulls ignored; fraction must be in [0,1]; **Partial Mode: No** for all of these (no parallel partial aggregation). — [PostgreSQL 17 docs: aggregate functions](https://www.postgresql.org/docs/17/functions-aggregate.html)
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` requires at least one UNIQUE index on column names only (no expressions, no WHERE) and a populated view; it does not lock out concurrent SELECTs and "may be faster when only a small number of rows are affected"; a non-concurrent refresh blocks readers but "tends to use fewer resources and finish faster" when many rows change; only one REFRESH per view at a time. — [PostgreSQL 17 docs: REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/17/sql-refreshmaterializedview.html)
- ONS HPSSA: statistics are withheld where an area has "fewer than five sales records in the Land Registry Price Paid Data" for that house type and year (median, mean, lower quartile and 10th percentile all withheld); for larger geographies, areas with fewer than five are combined if the combination totals at least five; HPSSAs use rolling 12-month windows (quarterly rolling years) "to reflect the actual mix of properties sold" and avoid seasonal effects; property-type statistics are published only from MSOA upward, all-type statistics down to LSOA. — [ONS: House price statistics for small areas QMI](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/methodologies/housepricestatisticsforsmallareasqmi)
- ONS also says "it is not possible to produce robust median house prices using the HPSSAs methodology for any smaller geography than MSOAs" (for property-type medians) and publishes sales counts alongside every median. — [ONS HPSSA bulletin](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/bulletins/housepricestatisticsforsmallareasinenglandandwales/2015-06-24)
- UK HPI full file: no header row; columns in order: Date, RegionName, AreaCode, Average Price, Index, IndexSA, 1m%change, 12m%change, AveragePricesSA, Sales Volume, then for each property type `[Type]Price, [Type]Index, [Type]1m%change, [Type]12m%change` (e.g. Detached…), then Cash/Mortgage, FTB/FOO and New/Old blocks; index base January 2015 = 100; previous 12 months revised every month; whole dataset may be revised ad hoc; coverage: national, regional, county/unitary, local authority and London borough; Isles of Scilly excluded for low volumes; "UK HPI estimates tend to be predominantly revised downwards" between first and final estimates. — [GOV.UK: About the UK House Price Index](https://www.gov.uk/government/publications/about-the-uk-house-price-index/about-the-uk-house-price-index)
- The HPI linked-data site states 441+ areas, four property types, index base Jan 2015 = 100, monthly GB updates, a SPARQL endpoint and CSV downloads; sales volumes are not available for the most recent two months. — [landregistry.data.gov.uk UKHPI doc](https://landregistry.data.gov.uk/app/ukhpi/doc)
- Note: one search snippet claimed the index was "re-referenced from January 2015 to January 2023"; the official About page fetched says January 2015 = 100. Treat the re-referencing claim as unconfirmed and check the current file. — [ckan.publishing.service.gov.uk UK HPI](https://ckan.publishing.service.gov.uk/dataset/uk-house-price-index2)
- Monthly HPI downloads exist as a full file plus split CSVs (average price by property type, index, index SA, sales, etc.); March 2026 release page. — [GOV.UK UK HPI data downloads March 2026](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-march-2026)
- PPD is updated "on the 20th working day of each month", under OGL v3; yearly files are 115–230 MB; address fields: Postcode, PAON, SAON, Street, Locality, Town/City, District, County. — [GOV.UK Price Paid Data downloads](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- PPD complete CSV: a third-party repo reports ~28M rows; the full CSV has no header; ClickHouse's loader lists the 16 columns (transaction id, price, date, postcode, property type, new-build flag, tenure, PAON, SAON, street, locality, town, district, county, PPD category, record status). — [vladignatyev/uk-land-registry-price-paid](https://github.com/vladignatyev/uk-land-registry-price-paid); [ClickHouse UK price paid sample](https://clickhouse.com/docs/zh/get-started/sample-datasets/uk-price-paid)
- `ST_DWithin(geometry, geometry, distance_in_srid_units)` and `ST_DWithin(geography, geography, distance_meters, use_spheroid = true)`; uses the spatial index via bounding-box comparison; `use_spheroid = false` for faster sphere evaluation. — [PostGIS docs: ST_DWithin](https://postgis.net/docs/ST_DWithin.html)
- `<->` returns 2D distance; "the spatial index is only used when the operator is in the ORDER BY clause"; "for geography KNN is based on sphere rather than spheroid"; true KNN since 2.2.0; documented example `ORDER BY geom <-> 'SRID=3005;POINT(…)'::geometry LIMIT 10`. — [PostGIS docs: geometry distance KNN](https://postgis.net/docs/geometry_distance_knn.html)
- A third-party guide repeats the practical caveat that the KNN index "only kicks in if one of the geometries is a constant (not in a subquery/cte)" — verify with EXPLAIN. — [skills.cat postgis-nearest](https://skills.cat/skills/mmbmf1/geospatial-skills/postgis-nearest)
- UCL's linkage of PPD to EPC gives match rates above 90% for 2011–2019 (93.15% overall; flats lowest at 88.62%) but only 56.2% in 2008; EPC data starts in 2008 so 1995–2008 matches are very sparse; the UCL code is CC BY-NC (not for commercial use). — [bin-chi.github.io Link-LR-PPD-and-Domestic-EPCs](https://bin-chi.github.io/Link-LR-PPD-and-Domestic-EPCs/)
- huwd/houseprices reports ~76.9% of ~29.3M PPD records matched to an EPC floor area in its March 2026 run (three-tier match via OS Open UPRN and the UBDC PPD→UPRN lookup), computes £/m² as total price / total floor area per postcode district and LSOA, and CPI-adjusts to real Jan-2026 £ using ONS series D7BT (CPI, not HPI). — [huwd/houseprices](https://github.com/huwd/houseprices)

### Inferences (author-composed SQL; untested)

**Schema sketch** (27700 geometry for metric queries; geography optional):

```sql
CREATE TABLE sale (
  transaction_id   uuid PRIMARY KEY,
  price            integer      NOT NULL,
  date_of_transfer date         NOT NULL,
  postcode         text,
  property_type    char(1)      NOT NULL,   -- PPD: D,S,T,F,O
  new_build        boolean,
  tenure           char(1),
  district         text,                    -- PPD District (name)
  la_code          text,                    -- GSS code mapped from district name (needs a lookup table)
  floor_area_m2    numeric,                 -- EPC TOTAL_FLOOR_AREA via UPRN/address match
  geom             geometry(Point, 27700)   -- from ONSPD/Code-Point/OS Open UPRN
);
CREATE INDEX sale_geom_gist ON sale USING gist (geom);
CREATE INDEX sale_type_date ON sale (property_type, date_of_transfer);

-- UK HPI, unpivoted from the full file's [Type]Index columns
CREATE TABLE ukhpi (
  area_code     text,
  month         date,          -- first of month
  property_type char(1),       -- D,S,T,F; plus 'A' for all-types Index
  idx           numeric,
  PRIMARY KEY (area_code, month, property_type)
);
```

**HPI adjustment** (price at sale month → reference month; fall back to the all-type index for PPD type 'O' or missing type rows):

```sql
CREATE MATERIALIZED VIEW sale_adj AS
SELECT s.*,
       s.price * (h_now.idx / h_then.idx)            AS price_adj,
       s.price * (h_now.idx / h_then.idx) / s.floor_area_m2 AS ppm2_adj
FROM sale s
JOIN LATERAL (
  SELECT idx FROM ukhpi h
  WHERE h.area_code = s.la_code
    AND h.month = date_trunc('month', s.date_of_transfer)::date
    AND h.property_type IN (s.property_type, 'A')
  ORDER BY (h.property_type = s.property_type) DESC LIMIT 1) h_then ON true
JOIN LATERAL (
  SELECT idx FROM ukhpi h
  WHERE h.area_code = s.la_code
    AND h.month = (SELECT max(month) FROM ukhpi)      -- reference month = latest HPI
    AND h.property_type IN (s.property_type, 'A')
  ORDER BY (h.property_type = s.property_type) DESC LIMIT 1) h_now ON true
WHERE s.floor_area_m2 BETWEEN 20 AND 500               -- crude outlier guard; tune
  AND s.price > 10000;
CREATE UNIQUE INDEX sale_adj_pk ON sale_adj (transaction_id);
CREATE INDEX sale_adj_geom ON sale_adj USING gist (geom);
CREATE INDEX sale_adj_type_date ON sale_adj (property_type, date_of_transfer);
```

Notes: (i) PPD gives a District *name*, HPI gives an *AreaCode*; a name→GSS code lookup is needed and must handle local-authority reorganisations (several since 2019) — treat as an ETL task. (ii) HPI revises the last 12 months every month, so `sale_adj` must be rebuilt, not appended. (iii) huwd/houseprices uses CPI instead; HPI by LA × type is closer to a "constant-quality" adjustment but noisier in small LAs.

**Per-cell statistics with H3** (index once at the finest resolution, roll up by parent; recompute percentiles per resolution — do not average child medians):

```sql
CREATE TABLE cell_stats (
  res          smallint NOT NULL,
  cell         h3index  NOT NULL,
  n            integer  NOT NULL,
  p25_ppm2     numeric, median_ppm2 numeric, p75_ppm2 numeric,
  geom         geometry(Polygon, 3857),
  PRIMARY KEY (res, cell)
);

WITH base AS (
  SELECT h3_latlng_to_cell(ST_Transform(geom, 4326), 10) AS cell10, ppm2_adj
  FROM sale_adj
  WHERE date_of_transfer >= current_date - interval '24 months'   -- or a longer rolling window at coarse res
), rolled AS (
  SELECT r.res, h3_cell_to_parent(b.cell10, r.res) AS cell, b.ppm2_adj
  FROM base b CROSS JOIN (VALUES (6),(7),(8),(9),(10)) AS r(res)
)
INSERT INTO cell_stats (res, cell, n, p25_ppm2, median_ppm2, p75_ppm2, geom)
SELECT res, cell, count(*) AS n,
       pct[1], pct[2], pct[3],
       ST_Transform(h3_cell_to_boundary_geometry(cell), 3857)
FROM (
  SELECT res, cell, count(*) AS n,
         percentile_cont(ARRAY[0.25, 0.5, 0.75]) WITHIN GROUP (ORDER BY ppm2_adj) AS pct
  FROM rolled
  GROUP BY res, cell
  HAVING count(*) >= 5                                   -- ONS HPSSA suppression floor
) s;
CREATE INDEX cell_stats_geom ON cell_stats USING gist (geom);
```

(`h3_latlng_to_cell(geometry, res)` requires lon/lat degrees; set `h3.strict = on` during development to catch 27700 coordinates passed by mistake.)

**Per-cell statistics with OS 1 km squares (ST_SquareGrid in 27700)** — equivalent pattern, one join per size:

```sql
WITH grid AS (
  SELECT 1000 AS size, i, j, geom
  FROM ST_SquareGrid(1000, ST_SetSRID(ST_EstimatedExtent('sale_adj','geom'), 27700))
)
SELECT g.size, g.i, g.j, count(*) AS n,
       percentile_cont(ARRAY[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY s.ppm2_adj) AS pct,
       ST_Transform(g.geom, 3857) AS geom
FROM grid g JOIN sale_adj s ON ST_Intersects(s.geom, g.geom)
WHERE s.date_of_transfer >= current_date - interval '24 months'
GROUP BY g.size, g.i, g.j, g.geom
HAVING count(*) >= 5;
```

Cheaper alternative avoiding the spatial join: compute `floor(ST_X(geom)/1000)`, `floor(ST_Y(geom)/1000)` as the cell key and build the square with `ST_MakeEnvelope` afterwards — valid because ST_SquareGrid is anchored at the SRS origin.

**Refresh strategy** (monthly, after PPD + HPI + EPC loads): rebuild `sale_adj` (full `REFRESH MATERIALIZED VIEW`, non-concurrent, since most rows change via HPI revisions), then rebuild `cell_stats` in a transaction (`TRUNCATE` + `INSERT`, or build `cell_stats_new` and swap by `ALTER TABLE … RENAME`). `CONCURRENTLY` is only worth it if `cell_stats` is itself a materialized view that must stay readable during the rebuild; the unique index on `(res, cell)` already satisfies its requirement. Because `percentile_cont` has no partial-aggregate mode it will not parallelise across workers; expect a single-process sort per group set — still minutes, not hours, for ~20M rows × 5 resolutions, but unmeasured (see Gaps).

**Minimum-count suppression**: follow ONS — never publish a cell with n < 5 (and hide p25/p75 below ~10, since quartiles of 5–9 values are noise); always ship `n` as a tile property so the client can fade low-count cells; at fine resolutions use a longer rolling window (ONS uses 12-month rolling years; 24–36 months at res 10 is reasonable) and fall back to the parent cell's statistic in the UI when a cell is suppressed.

**Martin function source for the heatmap** (zoom → H3 resolution via the h3_postgis helper; optional `?ptype=` filter would require a `cell_stats` keyed additionally by property type):

```sql
CREATE OR REPLACE FUNCTION public.ppm2_hex(z integer, x integer, y integer, query json DEFAULT '{}')
RETURNS bytea LANGUAGE plpgsql STABLE PARALLEL SAFE AS $$
DECLARE
  r   integer := h3_get_resolution_from_tile_zoom(z, max_h3_resolution => 10, min_h3_resolution => 6);
  env geometry := ST_TileEnvelope(z, x, y);
  mvt bytea;
BEGIN
  SELECT ST_AsMVT(t, 'ppm2', 4096, 'geom') INTO mvt
  FROM (
    SELECT ST_AsMVTGeom(c.geom, env, 4096, 64, true) AS geom,
           c.cell::text AS h3, c.n, c.median_ppm2, c.p25_ppm2, c.p75_ppm2
    FROM cell_stats c
    WHERE c.res = r AND c.geom && ST_TileEnvelope(z, x, y, margin => 0.02)
  ) t;
  RETURN mvt;
END $$;
COMMENT ON FUNCTION public.ppm2_hex IS '{"description":"HPI-adjusted £/m² by H3 cell","minzoom":5,"maxzoom":14}';
```

`h3_get_resolution_from_tile_zoom`'s defaults (`hex_edge_pixels 44`, `tile_size 512`) target roughly 44-pixel hexagon edges on 512-px tiles; override to taste. For the PMTiles route, instead export `cell_stats` per resolution to GeoJSONSeq/FlatGeobuf and run tippecanoe once per resolution with `-Z/-z` zoom bands, then `tile-join` them into one `.pmtiles`.

**Top-10 comparables: within 1 km, same type, floor area ±15%, last 24 months, HPI-adjusted**:

```sql
-- $1 easting, $2 northing (27700), $3 property_type, $4 subject floor area m²
SELECT s.transaction_id, s.date_of_transfer, s.price, round(s.price_adj) AS price_adj,
       s.floor_area_m2, round(s.ppm2_adj) AS ppm2_adj,
       round(ST_Distance(s.geom, ST_SetSRID(ST_Point($1, $2), 27700))) AS dist_m
FROM sale_adj s
WHERE s.property_type = $3
  AND s.floor_area_m2 BETWEEN $4 * 0.85 AND $4 * 1.15
  AND s.date_of_transfer >= current_date - interval '24 months'
  AND ST_DWithin(s.geom, ST_SetSRID(ST_Point($1, $2), 27700), 1000)   -- metres in 27700; GiST-assisted
ORDER BY s.geom <-> ST_SetSRID(ST_Point($1, $2), 27700)               -- KNN; keep the point a constant/parameter, not a CTE
LIMIT 10;
```

Using 27700 geometry avoids the geography sphere-vs-spheroid distinction entirely (planar metres are accurate at this scale in Great Britain). If the column is `geography`, the same query reads `ST_DWithin(s.geog, $pt::geography, 1000)` and `ORDER BY s.geog <-> $pt::geography`, with KNN distances on the sphere. With `ST_DWithin` already pruning to ≤1 km the KNN sort set is small, so the "constant" caveat matters less here, but check `EXPLAIN` for an Index Scan on `sale_adj_geom`. A hybrid index on `(property_type, date_of_transfer)` plus GiST is enough; a partial GiST index `WHERE date_of_transfer >= '2023-01-01'` can shrink the index if only recent sales are ever used for comparables.

### Gaps
- No published timing for `percentile_cont` grouped over ~20–30M rows at multiple resolutions; must be measured on the VM.
- No official PPD District-name → GSS-code crosswalk was located in this research; the mapping (and its handling of LA mergers) is an ETL task.
- Whether the UK HPI index base was re-referenced after Jan 2015 is unconfirmed (one snippet says Jan 2023, the fetched About page says Jan 2015 = 100).
- EPC coverage/match rates for the pre-2008 PPD are poor (UCL: 56% in 2008, far lower earlier), so £/m² history effectively starts ~2008–2011; the exact usable start year for a 24-month-window product is irrelevant but matters for any long-run trend view.

---

## Key question 5: Open-source projects already doing Land Registry + EPC → £/m² heatmap

### Takeaway
There is no ready-made PostGIS + MapLibre £/m² hex heatmap to lift wholesale. The closest reusable pieces are huwd/houseprices (DuckDB pipeline that already does the PPD↔EPC floor-area join via UPRN and emits £/m² by postcode district/LSOA; repo code licence not visible), kianharia30/RE-Maps (MIT; FastAPI + PostGIS + MapLibre with zoom-tiered aggregation, EPC optional), UCL's published £/m² dataset (22M+ linked transactions, non-commercial) and its CC BY-NC R linkage code. Anna Powell-Smith's houseprices.anna.ps is the methodological ancestor.

### Cited Findings
- **huwd/houseprices**: Python 3.12 + uv, DuckDB for joins and point-in-polygon, GDAL/ogr2ogr, Parquet checkpoints, Makefile, pytest; sources PPD, EPC bulk (needs a GOV.UK One Login bearer token), OS Open UPRN, UBDC PPD→UPRN lookup, ONS LSOA boundaries; three-tier match; ~76.9% of ~29.3M PPD rows matched (March 2026 run); outputs `price_per_sqm_postcode_district.csv` and `price_per_sqm_lsoa.csv`; headline figure CPI-adjusted (ONS D7BT) to Jan-2026 £; 333 commits, 0 stars; page says "All source data is Open Government Licence v3.0" but no code licence was visible; modelled on Anna Powell-Smith's analysis. — [huwd/houseprices](https://github.com/huwd/houseprices)
- **kianharia30/RE-Maps**: MIT; FastAPI + PostgreSQL/PostGIS; Next.js + MapLibre GL; 8 zoom tiers (property → street → postcode → sector → outcode → LAD → county → country); sector-and-coarser precomputed in `area_stats`, finer computed live; EPC optional for £/m²; full dataset 3.5 GB; ~6M rows, 18 SQL migrations, 365 tests; 17 commits, 0 stars; datasets not redistributed. — [kianharia30/RE-Maps](https://github.com/kianharia30/RE-Maps)
- **UCL "House Price per Square Metre in England and Wales"** (London Datastore, GLA): maintained by Bin Chi, Adam Dennett, Thomas Oléron-Evans, Robin Morphet; LR-PPD 1 Jan 1995–31 Oct 2024 linked to EPC floor areas by address matching; >22M transactions in the 2024 version (hpm_la_2024.zip, 1.24 GB); licence not stated on the page beyond "for non-commercial purposes"; linkage code and cleaning/validation code on UK Data Service ReShare (854942, 855033). — [London Datastore dataset](https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales-epo9w)
- **bin-chi/Link-LR-PPD-and-Domestic-EPCs**: R scripts (PPD_EPC_linkage.R, Evaluation.R, Data_cleaning.R) plus SQL loaders into PostGIS; four-stage, 251-rule address matching; geo-referenced via NSPL; **CC BY-NC — "not allowed to be used commercially"**; published in UCL Open: Environment (DOI 10.14324/111.444/ucloe.000019) after Scientific Data declined it. — [bin-chi.github.io](https://bin-chi.github.io/Link-LR-PPD-and-Domestic-EPCs/)
- An earlier UCL release (2011–2019) is catalogued with 19.96M transactions and 106 variables (1995–24 Jun 2022 version) and includes codes for Output Area → Local Authority. — [b2find: house price per square metre 1995-2022](https://b2find.eudat.eu/dataset/fdebca77-40d2-5346-85cd-061e8548768d)
- **Anna Powell-Smith, "House prices by square metre in England & Wales"**: average £/m² by postcode district (total price / total floor area). — [houseprices.anna.ps](http://houseprices.anna.ps/)
- **epimorphics/ukhpi**: the official UK HPI open-data web app (reference for HPI structure, no EPC). — [epimorphics/ukhpi](https://github.com/epimorphics/ukhpi)
- **ukhousing (R package)**: downloads PPD, EPC and planning data; UK HPI for 441+ regions; a data-loading layer, not a map. — [charlescoverdale ukhousing](https://charlescoverdale.github.io/ukhousing/)
- Commercial (not open source): an Apify "UK Property Intelligence" actor joins EPC and PPD and returns `price_per_sqm`. — [Apify UK Property Intelligence](https://apify.com/charles986/uk-property-intelligence)
- Since November 2021 domestic EPCs are published with UPRN, which the UCL notes say their later dataset carries — the cleanest join key. — [data.london.gov.uk UCL publisher page](https://data.london.gov.uk/publisher/ucl/?format=zip)

### Inferences
- Reuse strategy: borrow the UPRN-based three-tier match design from huwd/houseprices (DuckDB, OGL inputs) rather than the UCL address-rules code (CC BY-NC), unless the product is non-commercial. Confirm huwd's code licence by reading the repo's LICENSE file before copying code.
- RE-Maps validates the Option-C architecture (FastAPI + precomputed `area_stats` + MapLibre) at ~6M rows, and its zoom-tier table is a sensible starting point for zoom→resolution mapping even if H3 replaces postcode geographies.
- None of these projects implement hex/H3 cells, vector tiles, or HPI adjustment; those parts are new work (see Q3/Q4).

### Gaps
- GitHub search in this session did not surface any project combining PPD + EPC + H3/hex + vector tiles; absence of evidence, not proof of absence.
- huwd/houseprices code licence and last-commit date were not visible via fetch; check directly.

---

## Supplementary: local prototyping tooling (QGIS, DuckDB, Python) and realistic data sizes/timings

### Takeaway
DuckDB (spatial + postgres extensions) is a strong ETL stage: it reads the 5 GB PPD CSV and EPC bulk files directly, does the UPRN join and point-in-polygon (as huwd/houseprices does), and can write into Postgres — but geometry-column handling on the DuckDB→Postgres path is undocumented, so write WKB or GeoParquet and load with `ST_GeomFromWKB`/ogr2ogr. psycopg 3 `COPY` is the documented fast path from Python. Sizes: ~29M PPD rows / ~5 GB CSV; ~22M linkable to EPC floor areas; UCL's linked dataset is 1.24 GB zipped.

### Cited Findings
- PPD "is updated monthly and the average size of this file is 5GB" (complete CSV ≈ 5.3 GB); no header row. — [GOV.UK PPD downloads via search](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads); [ClickHouse UK price paid](https://clickhouse.com/docs/zh/get-started/sample-datasets/uk-price-paid)
- huwd/houseprices: ~29.3M PPD rows in March 2026; 76.9% matched to EPC. — [huwd/houseprices](https://github.com/huwd/houseprices)
- RE-Maps: ~1.9M sales (two years) load in "a few minutes"; full dataset 3.5 GB. — [kianharia30/RE-Maps](https://github.com/kianharia30/RE-Maps)
- A 2014 (old) blog notes the raw PPD file contains illegal characters that break naive Unix tools — expect encoding clean-up. — [Whatfettle: One CSV, thirty stories](https://blog.whatfettle.com/2014/10/13/one-csv-thirty-stories-bootstrapping)
- DuckDB postgres extension: `ATTACH 'conn' AS pg (TYPE postgres)`; supports CREATE TABLE, INSERT, UPDATE, DELETE, COPY in both directions using Postgres binary wire encoding, transactions; `pg_use_ctid_scan` parallel reads, `pg_connection_limit` 64; PostGIS geometry handling is not documented (hstore→VARCHAR, arrays via `pg_array_as_varchar`). — [DuckDB docs: postgres extension](https://duckdb.org/docs/current/core_extensions/postgres/overview.html)
- DuckDB spatial: `ST_Read()` reads dozens of formats via GDAL (`INSTALL spatial; LOAD spatial;`), GeoPackage in place; GeoParquet written via `COPY (…) TO 'file.parquet' (FORMAT PARQUET)`. — [DuckDB blog: spatial extension (Apr 2023, old)](https://duckdb.org/2023/04/28/spatial.html); [duckdb-book data import](https://duckdb-book.gishub.org/book/spatial/data-import)
- psycopg 3: `cursor.copy()` context manager with `write_row()` (adapted values) or `write()` (pre-formatted text/binary blocks); `FORMAT BINARY` needs binary dumpers and applies no cast rules (e.g. Python int may be sent as smallint — use `set_types()`); described as "one of the most efficient ways to load data into the database"; async variant available. — [psycopg 3 docs: COPY](https://www.psycopg.org/psycopg3/docs/basic/copy.html)
- Crunchy Bridge for Analytics (hosted, not OSS) maps DuckDB/GeoParquet columns to PostGIS geometry automatically — a sign of where the ecosystem is going, not something usable on one VM. — [Crunchy Data: PostGIS meets DuckDB](https://www.crunchydata.com/blog/postgis-meets-duckdb-crunchy-bridge-for-analytics-goes-spatial)
- Martin's experimental DuckDB backend can serve MVT directly from GeoParquet (`unstable-duckdb`), which would let a prototype skip PostGIS for the tile layer entirely. — [MapLibre news: GSoC Martin DuckDB](https://maplibre.org/news/2026-08-15-gsoc-martin-duckdb/)

### Inferences
- Pipeline for one VM: (1) DuckDB reads PPD CSV + EPC CSVs + OS Open UPRN + UPRN lookup, writes a Parquet `sale` table with easting/northing; (2) Python/psycopg `COPY` (or `ogr2ogr -f PostgreSQL` from GeoParquet) loads it into Postgres with `geom = ST_SetSRID(ST_Point(e,n),27700)`; (3) SQL from Q4 builds `sale_adj` and `cell_stats`; (4) Martin serves `ppm2_hex` and, optionally, a tippecanoe PMTiles build. Index creation after `COPY`, then `ANALYZE`.
- QGIS connects natively to PostGIS and can preview `cell_stats` and a Martin XYZ/MVT endpoint, which is the quickest way to eyeball resolution choices and colour ramps before touching the MapLibre front end. (Standard QGIS capability; not re-verified from a source in this session.)
- GeoPandas `read_postgis`/`to_postgis` and pyogrio are convenient for the ≤ few-million-row cell tables but are the wrong tool for the 29M-row load; use DuckDB/COPY for bulk and GeoPandas for analysis. (Not re-verified from a source in this session.)

### Gaps
- No measured Postgres `COPY` timing for the full PPD on commodity VM hardware was found; community guidance is "minutes" for ~30M rows but unverified.
- DuckDB → PostGIS geometry round-trip behaviour is undocumented; test with WKB first.
- No source fetched this session for QGIS PostGIS provider or GeoPandas/pyogrio specifics (treated as common knowledge; flagged).
