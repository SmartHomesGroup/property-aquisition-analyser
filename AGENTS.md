# AGENTS.md

Guidance for AI coding agents (and humans) working in this repo. `CLAUDE.md` is a symlink to this
file — edit this one. `README.md` holds the mission, purpose, USP and user profiles; this file holds
the working context: what we are building, in what order, on what data, and what we have already
decided.

Read in this order at the start of a session:

1. `README.md` — why the product exists.
2. This file — product scope, roadmap, data, architecture, decisions.
3. `docs/research/chatgpt-uk-house-price-apis.md` — the full exploratory research transcript
   (long; skim the headings, read the sections you need).

## Working with the author

- Tom is an experienced **firmware/embedded engineer, not a web developer**. Explain web, GIS and
  cloud concepts as they come up; firmware analogies land well. Don't assume familiarity with
  JS tooling, mapping libraries or cloud billing.
- Prefers discussion before big moves and wants **a recommendation, not a survey**.
- The product is being built with and for Tom's brother, who is getting into small-scale property
  development with tradespeople friends and modest backing. **He is customer zero**: when a metric
  or feature is in doubt, the test is "would he act on this?"
- The sibling repo `../home` (Liminal Instruments site: Astro + Svelte, interactive "tiles") has a
  graphing/interaction kit we intend to reuse for sliders and animated infographics. See
  "Interactive figures" below.
- Commit and push only when asked. This repo's remote is the `SmartHomesGroup` GitHub org; the
  local git identity is set per-repo. Don't touch global git/SSH config.
- UK English throughout (analyser, metres, colour). Currency is GBP.

## What we are building

**Property Acquisition Analyser** (brand on the current page: "Smart Homes"). UK only.

Rightmove connects sellers with buyers. **We are on the buyer's side.** The user pastes a listing
link (Rightmove first; others later) and gets a clear, honest, at-a-glance read on whether that
property looks under- or over-priced relative to the evidence, and why. Historic sale data is all
public but opaque; we interpret and present it.

Two tiers, one engine:

| Tier | Who | What they get |
|---|---|---|
| **Free, "peace of mind at a glance"** | Anyone buying a home | Paste a link → price vs local £/m², this property's history vs its neighbours, plain-English "why", and the caveats. |
| **"Double click down"** (likely paid) | Professional small developers | Large-dataset views: the most undervalued listings in an area/budget, "up and coming" areas, renovation-uplift projections, exports. |

### Two entry points, equal standing

1. **"I have a listing. Is £425k reasonable?"** Paste a link → verdict in five seconds, evidence
   one click away.
2. **"I have an area and a budget. What is undervalued?"** Explore the map → ranked list of
   listings currently for sale that sit furthest below their comparables.

The paste-a-link flow is how we **bootstrap** before we hold organic listings data. It is not the
product's identity. The destination is an **exploration-focused interface over organic data**:
every active listing on our own map, searchable by area and budget.

### The balance between the two audiences

- The surface reads as a helpful, convenient tool for anyone buying a home. Nothing on the front
  page says "for investors"; it must not be obvious that developers are a target.
- The depth reveals itself. Anyone who clicks down finds a very capable engine for identifying
  undervalued properties currently for sale.
- That depth grows into builder-grade granularity over time: "a loft conversion here adds roughly
  £X, a rear extension £Y", so a tradesperson or small developer can see in a minute whether their
  time and money would pay. That audience is the long-term commercial core.

### How we differ from Housometer (the yardstick)

Housometer (and HouseMetric, anna.ps) is a **map that shows data**. We are a **tool that answers a
question**. Every feature should be judged against this list:

1. **Question in, verdict out.** Listing or area+budget in; one sentence and three reasons out.
   The map is the evidence, not the product.
2. **Exploration answers "where should I look?"**, not "what is here?". Budget slider that
   recolours the map by "how many m² does my £350k buy here"; type filter; a *deal density* layer
   (where listings sit furthest below local comparables). The map is a search tool, not an atlas.
3. **Relative, not absolute.** With a property selected, every cell and pin is coloured relative
   to it.
4. **Every number states its bracket.** Period, geography, property type, nominal vs HPI-adjusted,
   n. Sparse cells say "insufficient data", not a colour. (Tom's "+2% of what?" complaint.)
5. **The property's own history vs its neighbours**, per property, indexed to today.
6. **Zoom continuity down to the comparable model.** Heatmap → cells → buildings → transactions →
   the ranked comparables that drove the verdict. The bottom level is where we live.
7. **A doubt panel** on every analysis: what could make us wrong.
8. **Interactive explanations** (sliders, animated figures from the `home` kit), not static stats.
9. **The developer depth**: ranked opportunities within budget and radius, planning precedent on
   the street, renovation uplift estimates, and over time the brother's real cost and outcome data
   as calibration.

Do not compete on breadth of layers, data volume or cartography. Muted basemap; our data dominates.

### What it is not

- Not another portal. We never host the transaction; we link back to the listing.
- Not a scraper business. Rightmove is a *discovery/input* tool for the user, not our data
  source. See "Listings access" below.
- Not a yes/no oracle. We say "unusually interesting" or "looks expensive", show *why*, and show
  *what could make us wrong*. No fake precision ("renovation will cost £63,420").
- Not "estate agents are lying to you". Buyer-side, not anti-agent.

## Core metrics (v1)

Work in **£/m²** internally (EPC floor area is in m²); display £/ft² as an option.

1. **Price per square metre vs the local distribution.** Asking price ÷ floor area, placed against
   the £/m² of comparable sold properties nearby (same type, similar size, recent, time-adjusted).
   Output: a position in the local distribution (e.g. "12% below the median for terraces within
   500 m, n=38"), never a bare number.
2. **This property's history vs its neighbours.** Land Registry Price Paid gives every sale of this
   address since 1995. Index each sale to today with UK HPI (local-authority level, by type) and
   compare the implied appreciation against the surrounding street/postcode/500 m/1 km. "Has this
   house appreciated less than its neighbours?" is a strong, cheap signal of condition or a
   past problem.
3. **Projected value and where investment adds value** (later). Loft conversions, rear
   extensions, EPC improvements. Needs planning-application data (neighbours' approvals),
   renovated comparables and the brother's real cost data. Deliberately deferred; see roadmap.

Plus the **exploration mode**: a scrollable UK heatmap of £/m² (and later price movement and
"deal density"), with the selected listing dropped on it as a star.

Each metric must carry its **sample size, date range and geography** on the face of the UI.
The research notes (and Tom's own reaction to Housometer) are explicit: "+2%" with no bracket,
period or n is worse than nothing.

## Roadmap (staged)

| Stage | Goal | Status |
|---|---|---|
| 0 | Current MVP: paste URL → n8n webhook → Claude-generated investment analysis (`index.html`). | Live. **Keep for now** while the rest is built; not the long-term engine. |
| 1 | **Heatmap.** Build the UK £/m² dataset (PPD + EPC + postcodes → PostGIS → aggregated cells) and an interactive map. A Rightmove property pops up on *our* map. | **Now.** |
| 2 | Single-listing overlay (bootstrapping entry point): paste link → identify address + asking price → place on the map, compute metric 1 and 2, show comparables and the "why / what could make us wrong" panel. | Next |
| 3 | Our own analysis protocol replaces the generic AI call (may still be agentic, but streamlined, deterministic where possible, with fixed inputs/outputs). | After 2 |
| 4 | Organic data: full listings overlay and the area+budget entry point ("most undervalued in area/budget", "up and coming areas"). Requires a legitimate listings feed. This is the destination, not an add-on. | Later |
| 5 | Builder-grade granularity: renovation/extension uplift projections (metric 3), "loft adds £X, rear extension £Y", ROI on time and money. | Future |

Prototype order for stage 1, per the research: local PostgreSQL + PostGIS → import one area →
join EPC → `ST_DWithin` comparables query → look at it in **QGIS** before writing any map UI.
Get the *information design* right (cell size, colour scale, sparse-data handling, type split,
time window) before touching MapLibre.

## Current state of the repo

- `index.html` — a single static page. Pastes a Rightmove/auction URL, POSTs it to an n8n
  webhook, and renders whatever JSON comes back: investment score, BRR and Flip scenarios,
  GDV, refurb cost, buying/bridge/selling costs, summary, risks. The UI recreates no numbers;
  all figures come from the "Investment Engine" (an n8n workflow calling Claude). The field
  names it reads (`Asking Price`, `Estimated GDV`, `BRR Maximum Allowable Offer (MAO)`,
  `Flip ROI` …) are the de-facto contract with that workflow.
- Note the hard-coded Lancashire refurbishment assumption and fixed targets (£25k min profit,
  20% min ROI, 12% contingency, 75% LTV) buried in the modal text. Those belong in config once
  the engine is ours.
- No build, no tests, no backend in this repo yet. The n8n workflow lives outside the repo.

### Assessment of the current AI approach

Agreed with Tom: generic LLM-per-request analysis is **not scalable** and not the product.

- Every answer is a fresh, unverifiable estimate; two runs on the same house can disagree.
- Cost and latency per lookup are high; the dataset features (stage 4) are impossible this way.
- The model has no access to the actual local comparables, so "GDV" is a guess dressed as a number.
- It is, however, a useful **front for the investor-side UX** (BRR/Flip framing, cost breakdown
  modals), and a fine way to keep a demo alive. Keep it, but route the stage-1/2 outputs around it.

Target shape for stage 3: deterministic pipeline (identify property → fetch comparables → compute
metrics → render), with an LLM used only where language is the job (reading a listing
description for condition phrases, writing the plain-English "why" from computed facts). Fixed
schema in, fixed schema out, every number traceable to rows in our database.

## Data sources

All free/open unless noted. England & Wales first; Scotland (Registers of Scotland) and Northern
Ireland (LPS) have separate, less open datasets. Verify licences before launch.

| Need | Source | Notes |
|---|---|---|
| Sold prices, 1995→ | **HM Land Registry Price Paid Data (PPD)** | Monthly CSV (~5 GB complete, or per-year files). Address, price, date, type (D/S/T/F/O), new-build, tenure. Registration lag 2 weeks–2 months. OGL v3; needs attribution. There is also a PPD→UPRN lookup. |
| Floor area + fabric | **EPC register open data** (MHCLG) | Bulk CSV by local authority; needs registration. Gives total floor area (m²), rating, heating, walls, roof, glazing, and construction-age band. Join to PPD by address. Prior art reports ~79% match rate; **address matching is a real engineering problem**. |
| Market movement | **UK House Price Index** | Monthly, by local authority and property type. Use it to time-adjust historic sales to "today". |
| Postcode → coordinates | ONS Postcode Directory / Code-Point Open | Postcode centroids; good enough for cells, not for individual buildings. |
| Property identifiers | **OS Open UPRN**, OS Linked Identifiers API | Join key across government datasets; linked identifiers map UPRN ↔ street ↔ building. |
| Basemap | **OS NGD API – Tiles** (free OpenData plan) or MapTiler/OpenStreetMap | Vector tiles for MapLibre. Decision pending; see "Mapping stack". OS Open Zoomstack retires spring 2028. |
| Planning applications | Local authority planning portals / PlanIt / planning.data.gov.uk | For "neighbours got a loft conversion approved". Patchy; stage 5. |
| Current listings | User-pasted Rightmove URL (stage 2); agent CRM feeds later (Street, Reapit, Jupix) | See "Listings access". |

Attribution strings to carry on the site (verify exact wording at launch):
"Contains HM Land Registry data © Crown copyright and database right 2026. This data is licensed
under the Open Government Licence v3.0." and "Contains OS data © Crown copyright and database
right 2026." EPC data has its own copyright notice from the register terms.

## Architecture direction

Decided in principle (from research; revisit if evidence says otherwise):

- **PostgreSQL + PostGIS** is the core. Raw tables (`raw_ppd`, `raw_epc`, `raw_postcodes`,
  `raw_hpi`) → ETL → `properties`, `transactions`, `epc_certificates` → analysis →
  `property_sales_enriched`, `price_grid_250m`, `price_grid_1km`, `price_grid_5km`. Keep the raw
  layer so matching improvements regenerate derived tables without re-downloading (ADC samples
  vs DSP outputs).
- **Derived cells, not raw dots**, at each zoom: UK ≈ 5 km, region ≈ 1 km, town ≈ 250 m,
  neighbourhood ≈ 100 m/street, then individual transactions, then the comparable-sale model for
  one property. Each cell stores median £/m², count, p25/p75, median floor area, median sale
  date. Enforce a minimum count before colouring a cell (Housometer does this; so should we).
- **Time is a first-class dimension**: store nominal £/m² and the HPI-adjusted £/m²; UI offers
  1 / 2 / 5-year windows and a property-type filter from day one.
- **Thin API over the DB** (FastAPI or similar), bounding-box + zoom → JSON cells. Postgres never
  faces the internet. Frontend and API are separable.
- **Hosting**: one Linux VM (Hetzner favoured; DigitalOcean/Lightsail as alternatives) behind
  Cloudflare, Caddy/nginx → API → Postgres on localhost, admin over Tailscale, SSH keys only,
  unattended upgrades, backups. This workload is read-heavy and small (tens of millions of rows);
  1k–10k visitors/day is trivial on 4 vCPU/8 GB. Scale vertically, then split API/DB, then
  cache, then replicas, only when measurements say so. Managed Postgres is worth paying for once
  it's commercial. Tailscale's free plan is personal/non-commercial; budget for it later.
- **Mapping stack**: **MapLibre GL JS** is the renderer (decided). The basemap provider is
  **not** decided: OS NGD Tiles (British, building-level, free OpenData plan, custom Black & White
  / Light styles made for overlays) vs MapTiler/OSM (Housometer's proven choice). The overlay
  code is identical either way; A/B both once we have an OS Data Hub key. Google Maps was
  rejected: metered billing, inherits Google's visual language, and Google's HeatmapLayer was
  removed in 2026 (they point to deck.gl).
- The heatmap and comparables engine are **infrastructure, not the moat**. Don't spend three
  months polishing the heatmap; get the pipeline right and move to "why is this house £3,800/m²
  when its neighbours are £5,000/m²?".

## Listings access (the biggest risk in the project)

### Risk assessment (2026-10-10)

**Live listings data is the single biggest risk. It is not a late-stage project killer provided
the decision gate below is honoured.** Reasoning:

- Stages 1–3 (heatmap, paste-a-link, our own analysis engine) run entirely on open data. They are
  safe whatever happens with listings. The free product never needs bulk listings.
- What is at risk is the **national "every undervalued property for sale" view** (stage 4). That
  needs either an ongoing commercial data licence or a portal-style relationship with CRM vendors.
- Several partial routes exist and they stack (see "Routes"). Precedent: new portals do get
  CRM feeds (Boomin had them within months of its 2021 launch; it died in 2022 on traffic and
  economics, not data).
- The scalable route is **business development, not engineering**. Two developers cannot code
  their way through it.
- Our buyer-side framing may make some agents reluctant to feed us. Lead with "we send you
  qualified buyers, listing is free"; keep "potentially overpriced" language calm.

**Budget planning assumption (2 FTE developers, £20k data budget, 12 months):**

| Outcome | Assessment |
|---|---|
| Free product, national | Achievable; no listings data required. |
| Developer tier, 1–2 regions with live listings | Achievable: a handful of agent feeds + auctions + a regional licence or aggregator feed. |
| Developer tier, national | Not on this budget alone. Needs a CRM-vendor partnership or a larger ongoing licence. |

Rough odds (judgement, not data): near-zero that the free product dies on this; roughly one in
three that the national developer tier has to change commercial shape (regional first,
partner-led, or sold to agents as well as buyers); near-zero chance of a late *surprise* if the
gate is kept. No reliable prices for commercial listings data are known at time of writing;
£20k is assumed to buy regional coverage or a limited national feed, not both. **Get quotes.**

### Decision gate

- **Month 1:** written answers from Street, Reapit and at least one commercial aggregator on
  terms, coverage and price. One developer spends a day a week on this. Not optional.
- **Month 3:** decide go / go-regional / reshape. **Stage 4 engineering does not start before
  this decision.**
- **From day one:** stage 1 builds the listings layer as an empty slot; the paste flow stores
  every listing a user analyses (user-contributed organic data accrues from the first user).

### Routes to live listings (they stack)

1. **Agent CRM feeds, per agent** — Street, Reapit, Jupix (details below). Free, authorised by
   the agent, scales by relationship count.
2. **Portal destination inside CRMs** — being added as a "portal" option so any agent can tick a
   box. The scalable route; a vendor negotiation.
3. **Auction catalogues** — openly published, and the most developer-relevant stock ("needs
   modernisation", probate, "cash buyers only"). Aggregated commercially by EIG. Good first
   inventory for the developer tier.
4. **Commercial aggregators** licensing portal-derived listings data to the industry: TwentyCi,
   PropertyMarketIntel are known names; PropertyData has an API. Pricing unknown; quote in month 1.
5. **Agents' own websites** — structured data (schema.org) on thousands of sites; each site has
   its own terms; messy but not Rightmove's terms.
6. **User-contributed listings** — every URL pasted into the free tool becomes a record.
7. **EPC lodgements as a leading indicator** — an EPC is required to market a property, and the
   register is open, so "about to be listed" is partly visible with no portal data at all. No
   asking price, but a strong candidate list.

### Constraints

- Rightmove's terms prohibit automated scraping/data collection and commercial property-market
  research without written consent. Linking back does not change how the data was obtained.
  Do **not** build the business on a Rightmove crawler. Zoopla closed its public API years ago;
  OnTheMarket (CoStar) has none.
- Rightmove's supply side is estate agents' CRMs pushing a data feed (Rightmove ADF). Agents want
  wide distribution; CRM vendors are built for syndication:
  - **Street.co.uk** — free, documented Property Feed API (search sales/lettings, 600 GET/min),
    sandbox; the agent generates a token to authorise us. Best first prototype target.
  - **Reapit** — mature REST API, OAuth, webhooks, AppMarket (agent installs our app → access).
  - **Jupix** — per-agent XML feed URL, rich fields (tenure, EPC, planning, flood risk…).
- Pitch to agents/CRMs: "specialist buyer-side discovery portal; listing with us is free;
  enquiries go straight to you." Expect tension between buyer advocacy ("potentially overpriced by
  £25–45k, listed by X") and listing supply. Hence: **keep the intelligence independent of
  whoever supplies the listing.**
- MVP path that needs no feed: the user supplies the URL; we extract only *which* property and
  the asking price. If extraction is fragile, fall back to the user typing postcode + price.
  Browser-extension extraction (the user's own browser reads the page) is a grey area that
  existing tools have survived on for years; acceptable for the single-listing flow, never for
  bulk collection.

## Prior art and comparable sites

Found in research (verify current state before citing publicly):

- **Housometer** — https://www.housometer.com/house-prices-map — the closest existing thing to
  our stage-1 map. ~1.27M sales over two years, three layers (sold price, £/m², rising/falling),
  £/m² built from Land Registry + EPC, hexagonal cells (4 km national, 500 m town, 250 m local),
  minimum transaction counts, MapTiler + OpenStreetMap basemap, OS for address geography.
  Weakness Tom noted: too much data, headline figures without bracket/period/n.
- **HouseMetric** — https://housemetric.co.uk/ — same dataset join; validates feasibility.
- **houseprices.anna.ps** — https://houseprices.anna.ps/ — Anna Powell-Smith's £/m² map;
  documented methodology (normalise addresses, join PPD to latest EPC, 79% match, 6.2M sales).
- **PlumPlot** — https://www.plumplot.co.uk/ — per-town £/m² pages and insights.
- Street.co.uk, Reapit, Jupix — see "Listings access".
- OS NGD examples — https://www.ordnancesurvey.co.uk/products/os-ngd-api-tiles — the "live"
  demos need an API key before they render; expect that.

Other sites to study (from general knowledge; confirm they still exist and what they charge):

- **Zoopla** and **Rightmove** sold-price pages and value estimates: the incumbent "what's it
  worth" answer, seller-leaning, no £/m² or evidence trail.
- **PropertyData** (propertydata.co.uk): paid investor analytics (yields, £/ft², sold comps);
  closest to our "double click down" tier in spirit, spreadsheet-like in feel.
- **LandInsight / Searchland / Nimbus Maps**: developer site-finding tools (ownership, planning,
  constraints) at professional price points; relevant to stage 5, not to the free tier.
- **Mouseprice**, **Home.co.uk**, **StreetCheck**: older sold-price and area-stats sites; useful
  for seeing how not to overwhelm a user.
- **PropCast**: "how hot is this market" indices; an example of compressing data into one signal.

None of these present an opinionated, buyer-side "is this listing interesting, and why" view. That
gap is the product.

## Research summary (from the ChatGPT exploration, 2026-10)

Full transcript: `docs/research/chatgpt-uk-house-price-apis.md`. Conclusions we are carrying
forward, in the order they were reached:

1. **Data access.** PPD is the backbone (bulk CSV into our own DB; linked-data/SPARQL for ad hoc).
   UK HPI for trends. Land Registry's REST API is about ownership/polygons, not a price lookup.
   First estimate of value: last sale × HPI(now)/HPI(sale). Comparables + £/m² make it an AVM.
2. **Hosting.** Don't design for scale; design so each scaling step is incremental. One VM,
   Postgres + PostGIS, index postcode/date/type, GiST on location, API in front, Cloudflare at the
   edge. Hetzner over AWS for predictability. Security is ours inside the VM (shared
   responsibility): keys only, Tailscale admin, 5432 never public, Cloudflare-only origin later.
3. **Product framing.** The unit of ranking is *opportunity*, not desirability. First algorithm:
   `expected = median of suitable comparables; discount = (expected − asking)/expected; rank`.
   Then improve comparable selection (distance, type, area ±10%, beds, tenure, recency, street,
   HPI, condition). Show evidence, not a magic score. Position the developer tier as "properties
   whose condition puts off ordinary buyers but have development potential", not "exploit
   underpriced sellers".
4. **Listings.** Scraping is out; agent CRM feeds (Street, Reapit, Jupix) are the legitimate,
   scalable route; the paste-a-URL MVP needs none of it. Brother's cost/outcome data over time
   becomes proprietary calibration data that nobody else has.
5. **Heatmap first.** Build the UK £/m² dataset as infrastructure; prototype locally in
   PostGIS + QGIS; derived cells by zoom; time-adjusted £/m²; keep raw tables.
6. **Prior art exists** (Housometer, HouseMetric, anna.ps). That validates the data join and tells
   us the map is not the moat. The USP is the buyer-side decision interface.
7. **UI principle.** Opinionated and compressed: "27 for sale → 5 worth investigating", each with a
   one-line reason; the detail (heatmap, comps, n, dates, HPI, planning) one click deeper;
   always a "what could make us wrong" list. Not YES/NO; "is this unusually interesting?".
8. **Mapping.** MapLibre renderer; OS NGD Tiles vs MapTiler/OSM basemap undecided; Google
   rejected. OS pricing: NGD Tiles on the free OpenData plan; premium NGD API usage has a £1,000/
   month royalty-free allowance; a free six-month Data Exploration Licence exists for startups
   evaluating premium data. Open question: which NGD layers the free plan actually exposes.

## Interactive figures: reuse the `home` kit

`../home/src/tiles/kit/` is a self-contained Svelte 5 toolkit built for interactive, animated
figures with no Astro dependency: `Tile` frame (label/readout/controls/caption), `Slider`
(`format`, `step="any"` for log scales), `RunButton`, `PlayButton`, `Segmented` presets, `Label`
(HTML over SVG at viewBox coords), `frame.ts` (animation loop that pauses off-screen), `svg.ts`
helpers, and `figure.css` (`fig-axis`, `fig-trace`, `fig-guide`, `fig-grab`… the only "pens").
Draggable handles always have a slider equivalent; no text inside SVGs (it shrinks on phones);
`vector-effect: non-scaling-stroke`; respects `prefers-reduced-motion`.

Plan: when this project gets to graphs (price history vs neighbours, £/m² distributions, budget
sliders, "what if we extend" infographics), lift the kit rather than reinventing it. Options, in
preference order: (a) extract the kit into a small shared package both repos consume, (b) copy
the kit with a note of the source commit. The audio pieces (`audio.ts`, `tone.ts`, `dsp.ts`,
`noise.ts`, `TimeFreq`) are not needed here.

Design-language note: `home` is datasheet/test-equipment (light + dark, hairlines, 2 px radius,
one orange accent, Inter + JetBrains Mono, all colours as tokens in `theme.css`). The current
`index.html` is dark-only neon-blue with gradients and glows. Decide the Property Analyser's own
language before the heatmap UI lands; whichever we choose, **tokens in one CSS file, light and
dark both working, mobile first** carry over from `home`.

## UI and content principles

- Lead with the verdict in plain English, then the evidence, then the caveats. Five-second read.
- Every number shows its basis: n, window, radius/geography, nominal vs HPI-adjusted.
- Ranges and percentiles over point estimates. Never invent precision.
- Comparables are listed and clickable; the user can see *which* sales drove the figure.
- Always link back to the original listing.
- Caveat block on every analysis: condition unknown, floor area from EPC (may be stale), small
  sample, registration lag, not financial advice.
- Mobile-friendly is a requirement. Check at ~390 px and desktop.
- Colour scales for the heatmap must be colour-blind safe and carry a legend with real £/m²
  values; sparse cells render as "insufficient data", not as a value.

## Open questions

- Basemap: OS NGD Tiles vs MapTiler/OSM (needs an OS Data Hub key to compare).
- Address matching strategy PPD ↔ EPC (UPRN-based vs normalised-string; target match rate).
- Cell geometry: hexagons vs squares; sizes per zoom; minimum n per cell.
- How much of "identify the property from a Rightmove URL" can be done without violating terms
  (user-supplied fields vs extraction); fall-back is manual postcode + price.
- Pricing/packaging of the developer tier; what the first dataset export looks like.
- Scotland and Northern Ireland coverage.
- Name/brand ("Smart Homes" vs "Property Acquisition Analyser"), and the design language.

## Conventions

- Spelling: the repo name is `aquisition`; the product name is spelled **Acquisition**. Keep the
  repo name as is; spell it correctly in prose and UI.
- Units: m² internally, £/m² as the canonical metric; £/ft² as a display toggle.
- Keep data-pipeline scripts, API and frontend in separate top-level directories when they
  arrive (`data/`, `api/`, `web/`); keep `docs/research/` for saved explorations.
- Record decisions here under the relevant heading with a one-line "why", so the next session
  doesn't relitigate them.
