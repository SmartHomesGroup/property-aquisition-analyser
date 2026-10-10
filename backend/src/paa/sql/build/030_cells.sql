-- Step 3: aggregate HPI-adjusted £/m² into squares.
--
-- One row per (cell size, time window, property type, cell). Squares are laid out in Web
-- Mercator (EPSG:3857), the map's own projection, so they sit axis-aligned on screen. (British
-- National Grid squares were tried first: BNG is a Transverse Mercator centred on 2°W, so away
-- from that meridian its squares appear rotated by the grid convergence, up to ~3° at the edges
-- of Britain, which looks like a bug.) The nominal size (5000, 1000, 250, 100 m) is the ground
-- size at 53°N, the middle of Britain; Mercator stretches with latitude, so a "5 km" cell is
-- ~5.3 km on the south coast and ~4.4 km in the north of Scotland. Sizes nest exactly.
-- Medians are not composable, so every size is computed from the sales directly. Cells with
-- fewer than 5 sales are suppressed (not stored), following the ONS small-area statistics floor.

DROP TABLE IF EXISTS map.cell_stats;

CREATE TABLE map.cell_stats (
    size              integer  NOT NULL,     -- nominal metres on the ground at 53°N
    window_months     smallint NOT NULL,     -- 12 | 24 | 60
    ptype             char(1)  NOT NULL,     -- A | D | S | T | F
    i                 integer  NOT NULL,     -- floor(mercator_x / cell)
    j                 integer  NOT NULL,     -- floor(mercator_y / cell)
    n                 integer  NOT NULL,
    p25               integer,
    median            integer  NOT NULL,
    p75               integer,
    median_floor_area integer,
    median_date       date,
    geom              geometry(Polygon, 3857) NOT NULL,
    PRIMARY KEY (size, window_months, ptype, i, j)
);

INSERT INTO map.cell_stats
WITH params AS (
    -- `cell` is the edge in Mercator metres: nominal size scaled by 1/cos(53°).
    SELECT s.size, round(s.size / cos(radians(53)))::int AS cell, w.months, t.ptype
    FROM (VALUES (5000), (1000), (250), (100)) AS s(size)
    CROSS JOIN (VALUES (12), (24), (60)) AS w(months)
    CROSS JOIN (VALUES ('A'), ('D'), ('S'), ('T'), ('F')) AS t(ptype)
),
ref AS (SELECT meta.get_info('ref_date')::date AS d),
base AS (
    SELECT ST_X(g) AS x, ST_Y(g) AS y, property_type, date_of_transfer, ppm2_adj, floor_area_m2
    FROM (
        SELECT ST_Transform(geom, 3857) AS g, property_type, date_of_transfer, ppm2_adj,
               floor_area_m2
        FROM core.sale_enriched, ref
        WHERE ppm2_adj IS NOT NULL
          AND date_of_transfer > ref.d - interval '60 months'
    ) t
),
binned AS (
    SELECT p.size, p.cell, p.months, p.ptype,
           floor(b.x / p.cell)::int AS i,       -- floor(), not integer division: x < 0 west of Greenwich
           floor(b.y / p.cell)::int AS j,
           b.ppm2_adj, b.floor_area_m2, b.date_of_transfer
    FROM params p
    CROSS JOIN ref
    JOIN base b
      ON b.date_of_transfer > ref.d - make_interval(months => p.months)
     AND (p.ptype = 'A' OR b.property_type = p.ptype)
)
SELECT size, months, ptype, i, j,
       n::int,
       round(pct[1])::int, round(pct[2])::int, round(pct[3])::int,
       round(mfa)::int,
       mdate,
       ST_MakeEnvelope(i * cell, j * cell, (i + 1) * cell, (j + 1) * cell, 3857)
FROM (
    SELECT size, cell, months, ptype, i, j,
           percentile_cont(ARRAY[0.25, 0.5, 0.75]) WITHIN GROUP (ORDER BY ppm2_adj) AS pct,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY floor_area_m2)              AS mfa,
           percentile_disc(0.5) WITHIN GROUP (ORDER BY date_of_transfer)                 AS mdate,
           count(*) AS n
    FROM binned
    GROUP BY size, cell, months, ptype, i, j
    HAVING count(*) >= 5
) agg;

CREATE INDEX cell_stats_geom_gist ON map.cell_stats USING gist (geom);
CREATE INDEX cell_stats_lookup_idx ON map.cell_stats (size, window_months, ptype);
ANALYZE map.cell_stats;

INSERT INTO meta.build_info (key, value)
SELECT 'cells', count(*)::text FROM map.cell_stats
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();

INSERT INTO meta.build_info (key, value) VALUES ('built_at', now()::text)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
