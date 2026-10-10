"""Postcode -> location, from our own Code-Point Open table (no third-party call)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from paa.api.deps import Conn
from paa.api.schemas import PostcodeLocation
from paa.etl.util import norm_postcode

router = APIRouter(tags=["postcodes"])


@router.get("/postcodes/{postcode}", response_model=PostcodeLocation)
def lookup(postcode: str, conn: Conn) -> PostcodeLocation:
    pc = norm_postcode(postcode)
    if not pc or len(pc) < 5 or len(pc) > 7:
        raise HTTPException(status_code=400, detail="That doesn't look like a UK postcode")
    row = conn.execute(
        """
        SELECT core.fmt_postcode(postcode) AS postcode,
               ST_Y(ST_Transform(geom, 4326)) AS lat,
               ST_X(ST_Transform(geom, 4326)) AS lon,
               easting, northing, district_code, pqi
        FROM core.postcode
        WHERE postcode = %s AND geom IS NOT NULL
        """,
        (pc,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Postcode not found")
    return PostcodeLocation(
        postcode=row["postcode"],
        lat=row["lat"],
        lon=row["lon"],
        easting=row["easting"],
        northing=row["northing"],
        district_code=row["district_code"],
        positional_quality=row["pqi"],
    )
