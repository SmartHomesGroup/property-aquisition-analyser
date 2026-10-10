"""Load OS Code-Point Open into ``core.postcode``.

The zip holds Data/CSV/<area>.csv files without headers. Columns:
  Postcode, Positional_quality_indicator, Eastings, Northings, Country_code,
  NHS_regional_HA_code, NHS_HA_code, Admin_county_code, Admin_district_code, Admin_ward_code
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from pathlib import Path

import psycopg

from paa.config import get_settings
from paa.etl.util import norm_postcode, timed

log = logging.getLogger(__name__)


def load(zip_path: Path) -> None:
    areas = get_settings().postcode_area_list
    with (
        timed("load Code-Point Open"),
        zipfile.ZipFile(zip_path) as zf,
        psycopg.connect(get_settings().database_url) as conn,
    ):
        cur = conn.cursor()
        cur.execute(
            "CREATE TEMP TABLE pc_stage (postcode text, pqi text, easting text, northing text,"
            " country_code text, district_code text) ON COMMIT DROP"
        )
        members = [
            m for m in zf.namelist() if m.lower().startswith("data/csv/") and m.endswith(".csv")
        ]
        if areas:
            members = [m for m in members if Path(m).stem.upper() in areas]
        n = 0
        with cur.copy("COPY pc_stage FROM STDIN") as copy:
            for member in members:
                with zf.open(member) as raw:
                    for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8")):
                        if len(row) < 9:
                            continue
                        copy.write_row(
                            [norm_postcode(row[0]), row[1], row[2], row[3], row[4], row[8]]
                        )
                        n += 1
        log.info("  %d postcodes staged from %d files", n, len(members))
        cur.execute("TRUNCATE core.postcode")
        cur.execute(
            """
            INSERT INTO core.postcode (postcode, pqi, easting, northing, country_code,
                                       district_code, geom)
            SELECT postcode, pqi::smallint,
                   nullif(easting, '')::integer, nullif(northing, '')::integer,
                   nullif(country_code, ''), nullif(district_code, ''),
                   CASE WHEN pqi::int < 90 AND easting <> '' AND northing <> ''
                        THEN ST_SetSRID(ST_MakePoint(easting::int, northing::int), 27700) END
            FROM pc_stage
            WHERE postcode IS NOT NULL
            ON CONFLICT (postcode) DO NOTHING
            """
        )
        log.info("  %d postcodes loaded", cur.rowcount)
        conn.commit()
