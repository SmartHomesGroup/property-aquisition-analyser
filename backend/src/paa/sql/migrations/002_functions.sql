-- Helper functions used by the build and the API.

-- Normalise a UK postcode for joins: upper case, no whitespace. NULL for empty input.
CREATE OR REPLACE FUNCTION core.norm_postcode(p text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT nullif(regexp_replace(upper(coalesce(p, '')), '\s+', '', 'g'), '')
$$;

-- Format a normalised postcode for display: "N112AB" -> "N11 2AB".
CREATE OR REPLACE FUNCTION core.fmt_postcode(p text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT CASE WHEN p IS NULL OR length(p) < 5 THEN p
                ELSE left(p, length(p) - 3) || ' ' || right(p, 3) END
$$;

-- Normalise free-text address parts for matching: upper, alphanumerics only, single spaces.
CREATE OR REPLACE FUNCTION core.norm_addr(t text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT nullif(btrim(regexp_replace(
               regexp_replace(upper(coalesce(t, '')), '[^A-Z0-9]+', ' ', 'g'),
               '\s+', ' ', 'g')), '')
$$;

-- Does normalised token sequence `needle` appear as whole words inside `hay`?
CREATE OR REPLACE FUNCTION core.addr_contains(hay text, needle text) RETURNS boolean
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT hay IS NOT NULL AND needle IS NOT NULL
       AND (' ' || hay || ' ') LIKE ('% ' || needle || ' %')
$$;

-- UK HPI index for an area/type/month with fallbacks: LA+type -> LA+all -> country+type -> country+all.
CREATE OR REPLACE FUNCTION core.hpi_index(la text, country text, ptype char, m date) RETURNS numeric
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT h.idx
    FROM core.hpi h
    WHERE h.month = m
      AND ((h.area_code = la AND h.property_type IN (ptype, 'A'))
        OR (h.area_code = country AND h.property_type IN (ptype, 'A')))
    ORDER BY (h.area_code = la) DESC, (h.property_type = ptype) DESC
    LIMIT 1
$$;

-- Build-info accessors.
CREATE OR REPLACE FUNCTION meta.get_info(k text) RETURNS text
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT value FROM meta.build_info WHERE key = k
$$;

-- Zoom level -> BNG cell size in metres. Shared by the tile function and the API.
CREATE OR REPLACE FUNCTION map.cell_size_for_zoom(z integer) RETURNS integer
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT CASE WHEN z <= 8 THEN 5000
                WHEN z <= 11 THEN 1000
                WHEN z <= 13 THEN 250
                ELSE 100 END
$$;
