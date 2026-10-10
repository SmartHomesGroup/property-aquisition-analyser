-- Step 1: match each sale to an EPC certificate so we know its floor area.
--
-- Two routes, in priority order:
--   uprn     : HMLR transaction->UPRN lookup joined to the EPC UPRN (new transactions only).
--   address  : same postcode, and the PPD PAON (house number/name) and SAON (flat) appear as
--              whole words in the EPC address lines. First-draft matcher; see AGENTS.md for the
--              better routes (uk_address_matcher / Splink) when match rate needs improving.
-- Where several certificates match, keep the one lodged closest to the sale date.

DROP TABLE IF EXISTS core.sale_epc;

CREATE TABLE core.sale_epc AS
WITH candidates AS (
    -- UPRN route
    SELECT s.transaction_id, e.certificate_number, e.lodgement_date, s.date_of_transfer,
           'uprn'::text AS method, 1 AS priority
    FROM core.sale s
    JOIN core.sale_uprn su ON su.transaction_id = s.transaction_id
    JOIN core.epc e ON e.uprn = su.uprn
    WHERE e.total_floor_area IS NOT NULL

    UNION ALL

    -- Address route
    SELECT s.transaction_id, e.certificate_number, e.lodgement_date, s.date_of_transfer,
           'address', 2
    FROM core.sale s
    JOIN core.epc e ON e.postcode = s.postcode
    CROSS JOIN LATERAL (
        SELECT core.norm_addr(concat_ws(' ', e.address1, e.address2, e.address3)) AS epc_addr,
               core.norm_addr(s.paon) AS paon,
               core.norm_addr(s.saon) AS saon
    ) n
    WHERE s.postcode IS NOT NULL
      AND e.total_floor_area IS NOT NULL
      AND n.paon IS NOT NULL
      AND core.addr_contains(n.epc_addr, n.paon)
      AND (n.saon IS NULL OR core.addr_contains(n.epc_addr, n.saon))
)
SELECT DISTINCT ON (transaction_id)
       transaction_id, certificate_number, method
FROM candidates
ORDER BY transaction_id,
         priority,
         abs(coalesce(lodgement_date, date_of_transfer) - date_of_transfer);

ALTER TABLE core.sale_epc ADD PRIMARY KEY (transaction_id);
CREATE INDEX sale_epc_cert_idx ON core.sale_epc (certificate_number);

INSERT INTO meta.build_info (key, value)
SELECT 'sales_matched', count(*)::text FROM core.sale_epc
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();

INSERT INTO meta.build_info (key, value)
SELECT 'sales_total', count(*)::text FROM core.sale WHERE record_status <> 'D'
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
