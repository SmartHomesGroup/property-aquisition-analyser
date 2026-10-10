"""Nearest comparable sales: same type, similar floor area, recent, close by."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from paa.api.deps import Conn
from paa.api.routes._shared import (
    POINT_27700,
    SALE_COLUMNS,
    bracket,
    ref_dates,
    since_date,
    to_sale,
)
from paa.api.schemas import WINDOWS, Comparables

router = APIRouter(tags=["analysis"])


@router.get("/comparables", response_model=Comparables)
def comparables(
    conn: Conn,
    lat: Annotated[float, Query(ge=49.5, le=61.0)],
    lon: Annotated[float, Query(ge=-8.5, le=2.0)],
    ptype: Literal["D", "S", "T", "F"],
    floor_area_m2: Annotated[float, Query(gt=5, lt=2000)],
    radius_m: Annotated[int, Query(ge=100, le=5000)] = 1000,
    window: Annotated[
        int, Query(description="Months back from the latest sale: 12, 24 or 60")
    ] = 24,
    tolerance_pct: Annotated[int, Query(ge=5, le=50)] = 15,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Comparables:
    if window not in WINDOWS:
        raise HTTPException(status_code=422, detail=f"window must be one of {WINDOWS}")
    until, hpi = ref_dates(conn)
    since = since_date(until, window)
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius_m,
        "since": since,
        "ptype": ptype,
        "lo": floor_area_m2 * (1 - tolerance_pct / 100),
        "hi": floor_area_m2 * (1 + tolerance_pct / 100),
        "limit": limit,
    }
    rows = conn.execute(
        f"""
        SELECT {SALE_COLUMNS}
        FROM core.sale_enriched s
        WHERE ST_DWithin(s.geom, {POINT_27700}, %(radius)s)
          AND s.date_of_transfer >= %(since)s
          AND s.property_type = %(ptype)s
          AND s.floor_area_m2 BETWEEN %(lo)s AND %(hi)s
          AND s.ppm2_adj IS NOT NULL
        ORDER BY s.geom <-> {POINT_27700}, s.date_of_transfer DESC
        LIMIT %(limit)s
        """,
        params,
    ).fetchall()
    return Comparables(
        bracket=bracket(
            radius_m=radius_m,
            months=window,
            ptype=ptype,
            since=since,
            until=until,
            hpi=hpi,
            n=len(rows),
        ),
        floor_area_m2=floor_area_m2,
        tolerance_pct=tolerance_pct,
        sales=[to_sale(r) for r in rows],
    )
