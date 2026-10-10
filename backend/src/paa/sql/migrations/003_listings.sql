-- Every listing a user analyses is kept: the URL, what the engine returned, and the
-- identifying fields we could pull out of it. This is the "empty slot" for organic listings
-- data (see AGENTS.md, "Listings access"): user-contributed records accrue from the first user.

CREATE TABLE core.listing_analysis (
    id            bigserial PRIMARY KEY,
    url           text NOT NULL,
    url_key       text NOT NULL,                   -- normalised for de-duplication
    requested_at  timestamptz NOT NULL DEFAULT now(),
    duration_ms   integer,
    engine        text NOT NULL,                   -- which analysis produced `result`
    ok            boolean NOT NULL,
    error         text,
    result        jsonb,                           -- the engine's response, verbatim
    address       text,
    postcode      text,                            -- normalised (core.norm_postcode)
    asking_price  integer,
    property_type char(1),                         -- D/S/T/F when recognisable
    bedrooms      smallint
);

CREATE INDEX listing_analysis_url_key_idx ON core.listing_analysis (url_key, requested_at DESC);
CREATE INDEX listing_analysis_postcode_idx ON core.listing_analysis (postcode) WHERE postcode IS NOT NULL;

-- Street-level placement of a listing whose address has no full postcode: the centroid of the
-- postcodes of recorded sales on that street. Needs a lookup by street and town.
CREATE INDEX sale_street_town_idx ON core.sale (street, town) WHERE street IS NOT NULL;
-- Outward-code (district) fallback, e.g. "PR1".
CREATE INDEX postcode_outward_idx ON core.postcode (left(postcode, length(postcode) - 3))
    WHERE geom IS NOT NULL;
