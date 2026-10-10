"""Load the UK House Price Index full file into ``core.hpi`` (unpivoted by property type)."""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path

import psycopg

from paa.config import get_settings
from paa.etl.util import timed, to_decimal_or_none

log = logging.getLogger(__name__)

# property_type code -> column in the HPI full file
INDEX_COLUMNS = {
    "A": "Index",
    "D": "DetachedIndex",
    "S": "SemiDetachedIndex",
    "T": "TerracedIndex",
    "F": "FlatIndex",
}


def load(path: Path) -> None:
    with timed(f"load UK HPI {path.name}"), psycopg.connect(get_settings().database_url) as conn:
        cur = conn.cursor()
        cur.execute("TRUNCATE core.hpi")
        n = 0
        with (
            path.open(newline="", encoding="utf-8-sig") as fh,
            cur.copy("COPY core.hpi (area_code, month, property_type, idx) FROM STDIN") as copy,
        ):
            for row in csv.DictReader(fh):
                month = datetime.strptime(row["Date"], "%d/%m/%Y").date().replace(day=1)
                for code, col in INDEX_COLUMNS.items():
                    idx = to_decimal_or_none(row.get(col))
                    if idx is not None:
                        copy.write_row([row["AreaCode"], month, code, idx])
                        n += 1
        log.info("  %d index points loaded", n)
        conn.commit()
