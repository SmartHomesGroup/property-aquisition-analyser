# Backend: pipeline and API

Python package `paa`. Two jobs:

- **ETL** (`paa fetch`, `paa load-*`, `paa build`): open data in, analysis tables out.
- **API** (`paa serve`): read-only JSON for the web app. Map tiles are served by Martin, not here.

```bash
make up                      # from the repo root: PostGIS + Martin in Docker
cd backend
uv sync                      # install (creates .venv)
cp .env.example .env         # then edit PAA_* values
uv run paa db migrate        # schema
uv run paa fetch --ppd-year 2025
uv run paa load-postcodes
uv run paa load-hpi
uv run paa load-ppd ../data/ppd/pp-2025.csv --replace
uv run paa load-epc          # needs EPC CSVs under ../data/epc (see below) ...
uv run paa dev synth-epc     # ... or FAKE floor areas for development (UI shows a red banner)
uv run paa build             # match, enrich, aggregate, tile functions
docker compose -f ../infra/docker-compose.yml restart tiles   # Martin discovers functions at start
uv run paa serve --reload    # http://127.0.0.1:8000/api/docs
```

The paste-a-listing flow needs `PAA_LISTING_WEBHOOK_URL` (the stage-0 n8n engine) in `.env`;
leave it empty to disable `POST /api/listings/analyse` (the web app then only takes postcodes).

Quality gates: `uv run ruff check .`, `uv run ruff format .`, `uv run mypy`, `uv run pytest`.
Run `uv` commands one at a time; two in parallel race on the venv and one fails to spawn.

Loading one PPD year, 1.75M postcodes and the HPI takes about 25 s; the build with ~1M sales
takes about a minute. The complete PPD history (`paa fetch --ppd-complete`, 5.5 GB) is needed for
the 2- and 5-year windows and for property price history.

## Data layout

```
data/                    git-ignored
  ppd/                   pp-complete.csv | pp-<year>.csv | pp-monthly-update-new-version.csv
  codepoint/codepo_gb.zip
  hpi/UK-HPI-full-file-<yyyy>-<mm>.csv
  epc/**/certificates.csv    <- you download these (GOV.UK One Login needed)
```

EPC bulk files: https://get-energy-performance-data.communities.gov.uk/ → sign in → download by
local authority (or all). Unzip anywhere under `data/epc/`; only `certificates.csv` is read.

## Prototyping on a small area

Set `PAA_POSTCODE_AREAS=EN,N` to load only those postcode areas from every source. Builds then
take seconds rather than hours. Clear it and reload for national coverage.

## Schema

- `core.*` loaded sources: `postcode`, `hpi`, `sale`, `sale_uprn`, `epc`
- `core.sale_epc` sale → certificate match, with the method used
- `core.sale_enriched` the analysis table: location, floor area, HPI-adjusted £/m²
- `map.cell_stats` Web Mercator squares (nominal 5 km / 1 km / 250 m / 100 m) × window × type → n, quartiles
- `map.cells(z,x,y,query)` and `map.postcodes(...)` vector-tile functions for Martin
- `meta.build_info` reference dates and counts; `/api/meta` exposes them
- `core.listing_analysis` every pasted listing: URL, the engine's response, what we identified

SQL lives in `src/paa/sql/`: `migrations/` are applied once and tracked; `build/` steps are
re-run in full by `paa build` (they drop and recreate derived tables).
