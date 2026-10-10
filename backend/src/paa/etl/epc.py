"""Load domestic EPC certificates from CSV files the user has downloaded.

The EPC open data service needs a GOV.UK One Login account, so files are not fetched here.
Place the ``certificates.csv`` from each local-authority zip (or the all-England file)
anywhere under ``<data_dir>/epc/``. Files are read by column name, so both the
pre-March-2026 (``LMK_KEY``) and current (``CERTIFICATE_NUMBER``) layouts load.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from pathlib import Path

import psycopg

from paa.config import get_settings
from paa.etl.util import norm_postcode, timed, to_decimal_or_none

log = logging.getLogger(__name__)

# target column -> acceptable source headers, first match wins
FIELD_MAP: dict[str, tuple[str, ...]] = {
    "certificate_number": ("CERTIFICATE_NUMBER", "LMK_KEY"),
    "uprn": ("UPRN",),
    "uprn_source": ("UPRN_SOURCE",),
    "address1": ("ADDRESS1",),
    "address2": ("ADDRESS2",),
    "address3": ("ADDRESS3",),
    "postcode": ("POSTCODE",),
    "property_type": ("PROPERTY_TYPE",),
    "built_form": ("BUILT_FORM",),
    "total_floor_area": ("TOTAL_FLOOR_AREA",),
    "lodgement_date": ("LODGEMENT_DATE",),
    "current_energy_rating": ("CURRENT_ENERGY_RATING",),
    "construction_age_band": ("CONSTRUCTION_AGE_BAND",),
    "number_habitable_rooms": ("NUMBER_HABITABLE_ROOMS",),
    "extension_count": ("EXTENSION_COUNT",),
}
NUMERIC = {"uprn", "total_floor_area", "number_habitable_rooms", "extension_count"}


def find_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.csv") if p.name.lower().startswith("certificates"))


def _rows(path: Path, areas: list[str]) -> Iterator[list[str | None]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = {h.upper(): h for h in reader.fieldnames or []}
        picks: dict[str, str | None] = {}
        for target, candidates in FIELD_MAP.items():
            picks[target] = next((headers[c] for c in candidates if c in headers), None)
        if picks["certificate_number"] is None or picks["total_floor_area"] is None:
            log.warning("skipping %s: no certificate id / floor area column", path)
            return
        for row in reader:
            pc = norm_postcode(row.get(picks["postcode"] or "", ""))
            if areas and not (pc and any(pc.startswith(a) for a in areas)):
                continue
            out: list[str | None] = []
            for target in FIELD_MAP:
                col = picks[target]
                val = row.get(col) if col else None
                val = val.strip() if isinstance(val, str) else None
                if target == "postcode":
                    val = pc
                elif target in NUMERIC:
                    val = to_decimal_or_none(val)
                elif target == "lodgement_date" and val:
                    val = val[:10]
                elif target == "current_energy_rating" and val:
                    val = val[:1].upper()
                out.append(val or None)
            yield out


def load(root: Path) -> None:
    files = find_files(root)
    if not files:
        log.warning("no EPC certificates*.csv files under %s", root)
        return
    areas = get_settings().postcode_area_list
    cols = list(FIELD_MAP)
    with (
        timed(f"load EPC ({len(files)} files)"),
        psycopg.connect(get_settings().database_url) as conn,
    ):
        cur = conn.cursor()
        cur.execute(
            "CREATE TEMP TABLE epc_stage ("
            + ", ".join(f"{c} text" for c in cols)
            + ") ON COMMIT DROP"
        )
        n = 0
        with cur.copy("COPY epc_stage FROM STDIN") as copy:
            for path in files:
                log.info("  reading %s", path)
                for row in _rows(path, areas):
                    copy.write_row(row)
                    n += 1
        log.info("  %d certificates staged; merging", n)
        cur.execute(
            """
            INSERT INTO core.epc (certificate_number, uprn, uprn_source, address1, address2,
                address3, postcode, property_type, built_form, total_floor_area, lodgement_date,
                current_energy_rating, construction_age_band, number_habitable_rooms,
                extension_count)
            SELECT DISTINCT ON (certificate_number)
                   certificate_number, uprn::numeric::bigint, uprn_source, address1, address2,
                   address3, postcode, property_type, built_form, total_floor_area::numeric,
                   lodgement_date::date, current_energy_rating, construction_age_band,
                   number_habitable_rooms::numeric::smallint, extension_count::numeric::smallint
            FROM epc_stage
            WHERE certificate_number IS NOT NULL
            ORDER BY certificate_number, lodgement_date DESC NULLS LAST
            ON CONFLICT (certificate_number) DO UPDATE SET
                uprn = EXCLUDED.uprn, uprn_source = EXCLUDED.uprn_source,
                address1 = EXCLUDED.address1, address2 = EXCLUDED.address2,
                address3 = EXCLUDED.address3, postcode = EXCLUDED.postcode,
                property_type = EXCLUDED.property_type, built_form = EXCLUDED.built_form,
                total_floor_area = EXCLUDED.total_floor_area,
                lodgement_date = EXCLUDED.lodgement_date,
                current_energy_rating = EXCLUDED.current_energy_rating,
                construction_age_band = EXCLUDED.construction_age_band,
                number_habitable_rooms = EXCLUDED.number_habitable_rooms,
                extension_count = EXCLUDED.extension_count
            """
        )
        log.info("  %d certificates merged into core.epc", cur.rowcount)
        conn.commit()
