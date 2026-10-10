-- Step 4: vector-tile functions served by Martin (auto-published from schema `map`).
--
-- Martin calls f(z, x, y, query) where `query` holds the URL query string as JSON, so the
-- frontend selects the time window and property type with ?window=24&ptype=T.

-- £/m² cells. The cell size follows the zoom (see map.cell_size_for_zoom).
CREATE OR REPLACE FUNCTION map.cells(z integer, x integer, y integer, query json DEFAULT '{}')
RETURNS bytea
LANGUAGE plpgsql STABLE PARALLEL SAFE AS $$
DECLARE
    v_size   integer  := map.cell_size_for_zoom(z);
    v_months smallint := coalesce(nullif(query->>'window', '')::smallint, 24);
    v_ptype  char(1)  := coalesce(nullif(query->>'ptype', ''), 'A');
    v_env    geometry := ST_TileEnvelope(z, x, y);
    v_mvt    bytea;
BEGIN
    IF v_months NOT IN (12, 24, 60) OR v_ptype NOT IN ('A', 'D', 'S', 'T', 'F') THEN
        RETURN NULL;
    END IF;

    SELECT ST_AsMVT(t, 'cells', 4096, 'geom') INTO v_mvt
    FROM (
        SELECT ST_AsMVTGeom(c.geom, v_env, 4096, 64, true) AS geom,
               c.size, c.n, c.median, c.p25, c.p75, c.median_floor_area,
               c.median_date::text AS median_date,
               c.i, c.j
        FROM map.cell_stats c
        WHERE c.size = v_size
          AND c.window_months = v_months
          AND c.ptype = v_ptype
          AND c.geom && ST_TileEnvelope(z, x, y, margin => 0.02)
    ) t;

    RETURN v_mvt;
END
$$;

COMMENT ON FUNCTION map.cells IS
'{"description":"HPI-adjusted £/m² by British National Grid square","minzoom":5,"maxzoom":16}';

-- Per-postcode points for street-level zoom. Sales geocode to postcode centroids, so showing
-- one point per postcode (with its count and median) is honest; individual sales stack otherwise.
CREATE OR REPLACE FUNCTION map.postcodes(z integer, x integer, y integer, query json DEFAULT '{}')
RETURNS bytea
LANGUAGE plpgsql STABLE PARALLEL SAFE AS $$
DECLARE
    v_months smallint := coalesce(nullif(query->>'window', '')::smallint, 24);
    v_ptype  char(1)  := coalesce(nullif(query->>'ptype', ''), 'A');
    v_env    geometry := ST_TileEnvelope(z, x, y);
    v_ref    date     := meta.get_info('ref_date')::date;
    v_mvt    bytea;
BEGIN
    IF z < 14 OR v_months NOT IN (12, 24, 60) OR v_ptype NOT IN ('A', 'D', 'S', 'T', 'F') THEN
        RETURN NULL;
    END IF;

    SELECT ST_AsMVT(t, 'postcodes', 4096, 'geom') INTO v_mvt
    FROM (
        SELECT ST_AsMVTGeom(ST_Transform(s.geom, 3857), v_env, 4096, 64, true) AS geom,
               core.fmt_postcode(s.postcode) AS postcode,
               count(*)::int AS n,
               round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.ppm2_adj))::int AS median,
               max(s.date_of_transfer)::text AS latest_sale
        FROM core.sale_enriched s
        WHERE s.ppm2_adj IS NOT NULL
          AND s.date_of_transfer > v_ref - make_interval(months => v_months)
          AND (v_ptype = 'A' OR s.property_type = v_ptype)
          -- Transform the envelope into BNG, not every row into Web Mercator: the former uses
          -- the GiST index on s.geom, the latter scans every sale (0.5 s per tile).
          AND s.geom && ST_Transform(ST_TileEnvelope(z, x, y, margin => 0.05), 27700)
        GROUP BY s.postcode, s.geom
    ) t;

    RETURN v_mvt;
END
$$;

COMMENT ON FUNCTION map.postcodes IS
'{"description":"Sales per postcode centroid, HPI-adjusted £/m² median","minzoom":14,"maxzoom":18}';
