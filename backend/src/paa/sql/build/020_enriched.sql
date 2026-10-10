-- Step 2: the analysis table. One row per usable sale with location, floor area and
-- HPI-adjusted price. Everything downstream (cells, comparables, pin-drop stats) reads this.
--
-- Filters (deliberate, documented so the UI can say so):
--   * standard price paid transactions only (category A), not deleted
--   * property types D/S/T/F (O = other: commercial, land, etc.)
--   * floor area 20..500 m² and price >= £10,000 as crude outlier guards
--   * must geocode via a current postcode (terminated postcodes are a known gap)

DROP TABLE IF EXISTS core.sale_enriched;

-- Reference month for HPI adjustment: the latest month present for England.
INSERT INTO meta.build_info (key, value)
SELECT 'hpi_ref_month', max(month)::text FROM core.hpi WHERE area_code = 'E92000001'
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();

CREATE TABLE core.sale_enriched AS
WITH ref AS (SELECT meta.get_info('hpi_ref_month')::date AS month)
SELECT s.transaction_id,
       s.price,
       s.date_of_transfer,
       s.property_type,
       s.new_build,
       s.tenure,
       s.postcode,
       s.paon, s.saon, s.street, s.town,
       e.certificate_number,
       se.method AS match_method,
       e.total_floor_area                    AS floor_area_m2,
       e.current_energy_rating,
       e.construction_age_band,
       p.easting, p.northing,
       p.district_code                       AS la_code,
       p.country_code,
       p.geom,
       hpi_then.idx                          AS hpi_then,
       hpi_now.idx                           AS hpi_now,
       (s.price::numeric / e.total_floor_area)                         AS ppm2,
       (s.price::numeric * hpi_now.idx / hpi_then.idx)                 AS price_adj,
       (s.price::numeric * hpi_now.idx / hpi_then.idx / e.total_floor_area) AS ppm2_adj
FROM core.sale s
JOIN core.sale_epc se   ON se.transaction_id = s.transaction_id
JOIN core.epc e         ON e.certificate_number = se.certificate_number
JOIN core.postcode p    ON p.postcode = s.postcode
CROSS JOIN ref
LEFT JOIN LATERAL (
    SELECT core.hpi_index(p.district_code, p.country_code, s.property_type,
                          date_trunc('month', s.date_of_transfer)::date) AS idx
) hpi_then ON true
LEFT JOIN LATERAL (
    SELECT core.hpi_index(p.district_code, p.country_code, s.property_type, ref.month) AS idx
) hpi_now ON true
WHERE s.ppd_category = 'A'
  AND s.record_status <> 'D'
  AND s.property_type IN ('D', 'S', 'T', 'F')
  AND e.total_floor_area BETWEEN 20 AND 500
  AND s.price >= 10000
  AND p.geom IS NOT NULL;

ALTER TABLE core.sale_enriched ADD PRIMARY KEY (transaction_id);
CREATE INDEX sale_enriched_geom_gist ON core.sale_enriched USING gist (geom);
CREATE INDEX sale_enriched_type_date_idx ON core.sale_enriched (property_type, date_of_transfer);
CREATE INDEX sale_enriched_postcode_idx ON core.sale_enriched (postcode);

ANALYZE core.sale_enriched;

INSERT INTO meta.build_info (key, value)
SELECT 'sales_enriched', count(*)::text FROM core.sale_enriched
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();

-- The "today" that time windows count back from: the latest sale we hold, not the wall clock,
-- because registration lags by weeks and the UI must state the real bracket.
INSERT INTO meta.build_info (key, value)
SELECT 'ref_date', max(date_of_transfer)::text FROM core.sale_enriched
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
