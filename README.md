# Property Acquisition Analyser

A buyer-side tool for UK property. Paste a listing link, see at a glance whether the price is
fair, and see the evidence.

## In brief

- **What it is:** a free, honest second opinion on the price of any UK home for sale.
- **Who it is for:** anyone buying a home. Underneath, a powerful tool for people who buy and
  improve property for a living.
- **Why it exists:** the data that proves whether a price is fair is public, but nobody can read
  it. We can.
- **What you get:** a verdict in one sentence, the three reasons behind it, and the evidence one
  click away.
- **How it feels:** peace of mind at a glance. Not a wall of statistics.
- **What makes it different:** every other house-price site shows you data. We answer your
  question.
- **Whose side we are on:** the buyer's. Always.
- **What we never do:** fake precision, a magic score, or a verdict without its doubts.
- **Where it goes:** from "is this house fair?" to "show me the undervalued houses for sale in
  this area" to "would a loft conversion here pay?"
- **Where we are now:** building the UK price-per-square-metre map that everything sits on.

## Mission

- Put the public record of UK house prices to work for the person buying, not the person selling.
- Turn opaque government data (Land Registry sales, EPC floor areas, the House Price Index) into a
  verdict a normal person can read in five seconds, with the workings one click away.
- Be honest about uncertainty: show sample sizes, dates and what could make us wrong. Never a
  fake-precise number or a green "GOOD DEAL 87/100" badge.
- Stay independent of whoever supplies the listing. Our value is the analysis, not the inventory.

## Purpose

- Rightmove exists to connect sellers with buyers. We exist to help buyers decide.
- Historic sale prices for every property in England and Wales are public, back to 1995. Floor
  areas are public via EPCs. Market movement is public via the UK HPI. Almost nobody can navigate
  that data fluently. We interpret and present it.
- Starting point: **price per square metre**, placed against comparable sales nearby, and **this
  property's own price history** compared with its neighbours'. Later: what a renovation or
  extension would plausibly add.
- Exploration mode: a scrollable UK heatmap of £/m² so you can see expensive and cheap pockets at a
  glance, then drop a listing onto it.

## USP

- **"Is this a good deal?" is the front page.** Every existing house-price map answers "what are
  homes worth round here?" and buries you in statistics. We answer the question the buyer actually
  has, in plain English, and show why.
- **Unashamedly buyer-side.** Portals and agents are paid by sellers. We are the second opinion
  that the buyer never had.
- **Evidence, not a score.** The comparables, the dates, the sample size and the caveats are all on
  the page. You can disagree with us, because you can see what we did.
- **One engine, two depths.** The free view gives peace of mind at a glance. The "double click
  down" gives professional developers the large-dataset view: the most undervalued listings in an
  area and budget, and the areas that are quietly rising.

## Typical users

- **Anyone buying a home.** Found a house, about to offer, wants to know whether £425k is sensible.
  Free. Peace of mind at a glance.
- **First-time buyers** who have no feel for the local market and nobody independent to ask.
- **Sellers and remortgagers** sanity-checking a valuation (a useful side effect of the same data).
- **Small property developers and renovators** (our customer zero). Want the handful of listings in
  an area whose condition puts off ordinary buyers but whose numbers work after a refurbishment.
  Paid tier, large datasets, exports, "up and coming" areas.

## Why people come, and why they come back

- **The problem it solves:** a house purchase is the largest decision most people make, and the
  only price signals they get come from the side that wants the price high. The data to check it
  is free but unusable. We make it usable.
- **The first visit:** either a link pasted in or an area and a budget typed in, and a clear answer
  out. Under-priced, fair, or looks expensive, with the three reasons that matter. The link entry
  point is how we start; the explore-by-area entry point over live listings is where we are going.
- **The return visits:**
  - Every new listing you are considering goes through the same check. Shortlists change weekly.
  - The heatmap is interesting in its own right; people explore their own street, their parents'
    town, the area they are thinking of moving to.
  - Watching an area or a property for price movement and new comparables.
  - For developers: the ranked list of what deserves a viewing this weekend, refreshed as new
    listings land.
- **Trust compounds.** Because we show our workings and our doubts, the tool becomes the thing you
  check before you believe anyone else's number.

## The key risk: live listings data

- Everything in the free product runs on open government data. Sold prices, floor areas and the
  price index are public. No listings feed is needed for "is this house fairly priced?".
- The exploration-by-area product ("show me the undervalued properties for sale in Enfield") needs
  **live listings**, and there is no open dataset of those. Rightmove's terms forbid scraping, and
  the other portals have no public API.
- The legitimate routes are estate-agent CRM feeds (authorised per agent, or by becoming a
  destination inside the CRM), auction catalogues, commercial data licences, and listings our own
  users contribute by analysing them.
- Our assessment: this is the biggest risk in the project, but not a late-stage killer, because the
  free product does not depend on it and because the question can be answered in the first three
  months, before we build on it. With two developers and a modest data budget, a regional live
  listings product is realistic in the first year; national coverage needs a partnership.
- The rule: no engineering on the full-listings product until the data route is confirmed in
  writing. Details, routes and the decision gate are in `AGENTS.md`.

## Status

Early. Two things exist:

- A live MVP (`index.html`) that sends a Rightmove URL to an n8n workflow using Claude to produce
  an investment summary. It is a demo, not the engine.
- A first draft of the real product: a UK £/m² heatmap built from Land Registry, EPC and House
  Price Index data on our own map (`backend/`, `web/`, `infra/`), with a pin-drop that shows the
  local price distribution and where an asking price sits in it. The same page takes a pasted
  listing link: the MVP's engine analyses it, the listing lands on the map, and its asking price
  is placed against the local evidence. Run it with `make up` and the steps in
  `backend/README.md`.

See `AGENTS.md` for scope, roadmap, data sources, architecture and decisions, and `docs/research/`
for the research behind them, including the mapping-tools report.
