"""Query fragments and row mappers shared by the area and comparables routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from paa.api.deps import DictConnection
from paa.api.schemas import PROPERTY_TYPE_LABEL, Bracket, Sale

# A point in BNG from lon/lat parameters; used as the centre of every spatial query.
POINT_27700 = "ST_Transform(ST_SetSRID(ST_Point(%(lon)s, %(lat)s), 4326), 27700)"

SALE_COLUMNS = f"""
    s.transaction_id::text AS transaction_id,
    concat_ws(', ', s.saon, s.paon, initcap(lower(s.street)), initcap(lower(s.town))) AS address,
    core.fmt_postcode(s.postcode) AS postcode,
    s.date_of_transfer, s.price,
    round(s.price_adj)::int AS price_adj,
    s.floor_area_m2,
    round(s.ppm2)::int AS ppm2,
    round(s.ppm2_adj)::int AS ppm2_adj,
    s.property_type, s.new_build,
    s.current_energy_rating AS energy_rating,
    round(ST_Distance(s.geom, {POINT_27700}))::int AS distance_m
"""


def ref_dates(conn: DictConnection) -> tuple[date, date | None]:
    """(reference 'today' for windows, HPI reference month). Raises if the build hasn't run."""
    rows = conn.execute(
        "SELECT key, value FROM meta.build_info WHERE key IN ('ref_date', 'hpi_ref_month')"
    ).fetchall()
    info = {r["key"]: r["value"] for r in rows}
    if "ref_date" not in info:
        msg = "No built data: run `paa build`"
        raise RuntimeError(msg)
    hpi = date.fromisoformat(info["hpi_ref_month"]) if "hpi_ref_month" in info else None
    return date.fromisoformat(info["ref_date"]), hpi


def since_date(until: date, months: int) -> date:
    y, m = until.year, until.month - months
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, min(until.day, 28))


def bracket(
    *, radius_m: int, months: int, ptype: str, since: date, until: date, hpi: date | None, n: int
) -> Bracket:
    return Bracket(
        radius_m=radius_m,
        window_months=months,
        property_type=ptype,  # type: ignore[arg-type]
        property_type_label=PROPERTY_TYPE_LABEL[ptype],
        since=since,
        until=until,
        hpi_ref_month=hpi,
        n=n,
    )


def to_sale(row: dict[str, Any]) -> Sale:
    return Sale(**row)
