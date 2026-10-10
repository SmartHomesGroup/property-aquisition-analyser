"""DEVELOPMENT ONLY: fabricate EPC certificates so the pipeline can run without real EPC data.

Real EPC bulk data needs a GOV.UK One Login account and cannot be fetched automatically. This
generates one fake certificate per sale that has no real match, with a floor area drawn from a
plausible range for the property type. Floor areas are **made up**; every £/m² derived from them
is meaningless as a fact. The build records ``synthetic_epc=true`` and the UI shows a banner.

Remove the fakes with ``paa dev drop-synth`` once real certificates are loaded.
"""

from __future__ import annotations

import logging

import psycopg

from paa.config import get_settings
from paa.etl.util import timed

log = logging.getLogger(__name__)

PREFIX = "SYNTH-"


def generate() -> None:
    with timed("synthesise EPC (FAKE DATA)"), psycopg.connect(get_settings().database_url) as conn:
        cur = conn.cursor()
        # Deterministic per transaction so repeated runs agree: hash the id into [0, 1).
        cur.execute(
            f"""
            INSERT INTO core.epc (certificate_number, uprn, uprn_source, address1, address2,
                address3, postcode, property_type, built_form, total_floor_area, lodgement_date,
                current_energy_rating, construction_age_band, number_habitable_rooms,
                extension_count)
            SELECT '{PREFIX}' || s.transaction_id,
                   NULL, 'Synthetic',
                   concat_ws(' ', s.saon, s.paon, s.street), s.town, NULL,
                   s.postcode,
                   CASE s.property_type WHEN 'F' THEN 'Flat' ELSE 'House' END,
                   CASE s.property_type WHEN 'D' THEN 'Detached' WHEN 'S' THEN 'Semi-Detached'
                                        WHEN 'T' THEN 'Mid-Terrace' ELSE NULL END,
                   round((lo + (hi - lo) * r)::numeric, 1),
                   s.date_of_transfer,
                   (ARRAY['C','D','D','E'])[1 + (r * 4)::int % 4],
                   NULL, NULL, NULL
            FROM core.sale s
            CROSS JOIN LATERAL (
                SELECT (('x' || left(md5(s.transaction_id::text), 8))::bit(32)::int::bigint
                        & 2147483647)::numeric / 2147483647 AS r
            ) h
            CROSS JOIN LATERAL (
                SELECT CASE s.property_type
                           WHEN 'F' THEN 40 WHEN 'T' THEN 65 WHEN 'S' THEN 80 ELSE 100 END AS lo,
                       CASE s.property_type
                           WHEN 'F' THEN 95 WHEN 'T' THEN 120 WHEN 'S' THEN 145 ELSE 220 END AS hi
            ) b
            WHERE s.property_type IN ('D', 'S', 'T', 'F')
              AND s.postcode IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM core.epc e
                  WHERE e.postcode = s.postcode
                    AND e.certificate_number NOT LIKE '{PREFIX}%%'
              )
            ON CONFLICT (certificate_number) DO NOTHING
            """
        )
        log.warning(
            "  %d SYNTHETIC certificates inserted. These floor areas are fake.", cur.rowcount
        )
        cur.execute(
            "INSERT INTO meta.build_info (key, value) VALUES ('synthetic_epc', 'true') "
            "ON CONFLICT (key) DO UPDATE SET value = 'true', updated_at = now()"
        )
        conn.commit()


def drop() -> None:
    with timed("drop synthetic EPC"), psycopg.connect(get_settings().database_url) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM core.epc WHERE certificate_number LIKE '{PREFIX}%%'")
        log.info("  %d synthetic certificates removed", cur.rowcount)
        cur.execute("DELETE FROM meta.build_info WHERE key = 'synthetic_epc'")
        conn.commit()
