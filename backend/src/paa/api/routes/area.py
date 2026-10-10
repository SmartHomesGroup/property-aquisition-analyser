"""Pin-drop statistics: the £/m² distribution around a point, and where a subject sits in it."""

from __future__ import annotations

from typing import Annotated

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
from paa.api.schemas import WINDOWS, AreaStats, Distribution, PropertyType, Subject

router = APIRouter(tags=["analysis"])


@router.get("/area", response_model=AreaStats)
def area_stats(
    conn: Conn,
    lat: Annotated[float, Query(ge=49.5, le=61.0)],
    lon: Annotated[float, Query(ge=-8.5, le=2.0)],
    radius_m: Annotated[int, Query(ge=100, le=5000)] = 500,
    window: Annotated[
        int, Query(description="Months back from the latest sale: 12, 24 or 60")
    ] = 24,
    ptype: PropertyType = "A",
    asking_price: Annotated[int | None, Query(ge=1000)] = None,
    floor_area_m2: Annotated[float | None, Query(gt=5, lt=2000)] = None,
    recent: Annotated[int, Query(ge=0, le=100)] = 20,
) -> AreaStats:
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
        "recent": recent,
    }
    where = f"""
        ST_DWithin(s.geom, {POINT_27700}, %(radius)s)
        AND s.date_of_transfer >= %(since)s
        AND (%(ptype)s = 'A' OR s.property_type = %(ptype)s)
        AND s.ppm2_adj IS NOT NULL
    """
    dist = conn.execute(
        f"""
        SELECT count(*) AS n,
               percentile_cont(ARRAY[0.1, 0.25, 0.5, 0.75, 0.9])
                   WITHIN GROUP (ORDER BY s.ppm2_adj) AS pct,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY s.floor_area_m2) AS mfa
        FROM core.sale_enriched s
        WHERE {where}
        """,
        params,
    ).fetchone()
    assert dist is not None  # aggregate query always returns one row
    n = int(dist["n"])
    pct = dist["pct"] or [None] * 5

    subject = None
    if asking_price is not None and floor_area_m2 is not None:
        ppm2 = asking_price / floor_area_m2
        pos = conn.execute(
            f"""
            SELECT count(*) FILTER (WHERE s.ppm2_adj < %(ppm2)s) AS below
            FROM core.sale_enriched s
            WHERE {where}
            """,
            {**params, "ppm2": ppm2},
        ).fetchone()
        assert pos is not None
        median = pct[2]
        subject = Subject(
            asking_price=asking_price,
            floor_area_m2=floor_area_m2,
            ppm2=round(ppm2),
            vs_median_pct=round((ppm2 - float(median)) / float(median) * 100, 1)
            if median
            else None,
            percentile=round(int(pos["below"]) / n * 100, 1) if n else None,
        )

    sales = conn.execute(
        f"""
        SELECT {SALE_COLUMNS}
        FROM core.sale_enriched s
        WHERE {where}
        ORDER BY s.date_of_transfer DESC
        LIMIT %(recent)s
        """,
        params,
    ).fetchall()

    return AreaStats(
        bracket=bracket(
            radius_m=radius_m, months=window, ptype=ptype, since=since, until=until, hpi=hpi, n=n
        ),
        ppm2_adj=Distribution(
            p10=_r(pct[0]),
            p25=_r(pct[1]),
            median=_r(pct[2]),
            p75=_r(pct[3]),
            p90=_r(pct[4]),
            median_floor_area_m2=float(dist["mfa"]) if dist["mfa"] is not None else None,
        ),
        subject=subject,
        recent_sales=[to_sale(r) for r in sales],
    )


def _r(v: object) -> int | None:
    return round(float(v)) if v is not None else None  # type: ignore[arg-type]
