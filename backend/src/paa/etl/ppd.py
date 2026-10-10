"""Load HM Land Registry Price Paid Data into ``core.sale``.

PPD files have no header. Fields, in order:
  transaction id, price, date of transfer, postcode, property type, old/new, duration,
  PAON, SAON, street, locality, town/city, district, county, PPD category, record status.
Older "complete" extracts may omit the final record status column.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

import psycopg

from paa.config import get_settings
from paa.etl.util import timed

log = logging.getLogger(__name__)

COLUMNS = (
    "transaction_id",
    "price",
    "date_of_transfer",
    "postcode",
    "property_type",
    "new_build",
    "tenure",
    "paon",
    "saon",
    "street",
    "locality",
    "town",
    "district",
    "county",
    "ppd_category",
    "record_status",
)


def _rows(path: Path, areas: list[str]) -> Iterator[list[str]]:
    """Yield PPD rows, filtered to postcode areas when configured, padded to 16 fields."""
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            if areas:
                pc = row[3].replace(" ", "").upper()
                if not any(
                    pc.startswith(a) and not pc[len(a) : len(a) + 1].isalpha() for a in areas
                ):
                    continue
            if len(row) == 15:
                row.append("A")
            yield row


def _copy_rows(cur: psycopg.Cursor, rows: Iterable[list[str]]) -> int:
    n = 0
    with cur.copy("COPY ppd_stage FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)
            n += 1
            if n % 1_000_000 == 0:
                log.info("  %d rows staged", n)
    return n


def load(path: Path, *, replace: bool) -> None:
    """Load a PPD CSV. ``replace`` truncates first (complete file); otherwise upsert (monthly)."""
    areas = get_settings().postcode_area_list
    with timed(f"load PPD {path.name}"), psycopg.connect(get_settings().database_url) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TEMP TABLE ppd_stage ("
            + ", ".join(f"{c} text" for c in COLUMNS)
            + ") ON COMMIT DROP"
        )
        n = _copy_rows(cur, _rows(path, areas))
        log.info("  %d rows staged; merging", n)
        if replace:
            cur.execute("TRUNCATE core.sale")
        cur.execute(
            """
            INSERT INTO core.sale AS s (
                transaction_id, price, date_of_transfer, postcode, property_type, new_build,
                tenure, paon, saon, street, locality, town, district, county,
                ppd_category, record_status)
            SELECT transaction_id::uuid,
                   price::integer,
                   left(date_of_transfer, 10)::date,
                   core.norm_postcode(postcode),
                   property_type,
                   new_build = 'Y',
                   nullif(tenure, ''),
                   nullif(paon, ''), nullif(saon, ''), nullif(street, ''),
                   nullif(locality, ''), nullif(town, ''), nullif(district, ''),
                   nullif(county, ''),
                   ppd_category,
                   coalesce(nullif(record_status, ''), 'A')
            FROM ppd_stage
            ON CONFLICT (transaction_id) DO UPDATE SET
                price = EXCLUDED.price,
                date_of_transfer = EXCLUDED.date_of_transfer,
                postcode = EXCLUDED.postcode,
                property_type = EXCLUDED.property_type,
                new_build = EXCLUDED.new_build,
                tenure = EXCLUDED.tenure,
                paon = EXCLUDED.paon, saon = EXCLUDED.saon, street = EXCLUDED.street,
                locality = EXCLUDED.locality, town = EXCLUDED.town,
                district = EXCLUDED.district, county = EXCLUDED.county,
                ppd_category = EXCLUDED.ppd_category,
                record_status = EXCLUDED.record_status
            """
        )
        log.info("  %d rows merged into core.sale", cur.rowcount)
        conn.commit()


def load_uprn_lookup(path: Path) -> None:
    """Load a transaction->UPRN lookup file (two quoted columns, no header)."""
    with (
        timed(f"load UPRN lookup {path.name}"),
        psycopg.connect(get_settings().database_url) as conn,
    ):
        cur = conn.cursor()
        cur.execute("CREATE TEMP TABLE uprn_stage (transaction_id text, uprn text) ON COMMIT DROP")
        with (
            path.open(newline="", encoding="utf-8") as fh,
            cur.copy("COPY uprn_stage FROM STDIN") as copy,
        ):
            for row in csv.reader(fh):
                if len(row) >= 2 and row[1].strip():
                    copy.write_row(row[:2])
        cur.execute(
            """
            INSERT INTO core.sale_uprn (transaction_id, uprn)
            SELECT transaction_id::uuid, uprn::bigint FROM uprn_stage
            ON CONFLICT (transaction_id) DO UPDATE SET uprn = EXCLUDED.uprn
            """
        )
        log.info("  %d lookups merged", cur.rowcount)
        conn.commit()
