"""Build information and data attribution."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from paa.api.deps import Conn
from paa.api.schemas import BuildInfo
from paa.config import get_settings

router = APIRouter(tags=["meta"])

# Required by the data licences. Years are the dataset editions, not the current year.
ATTRIBUTION = [
    "Contains HM Land Registry data © Crown copyright and database right 2026. "
    "This data is licensed under the Open Government Licence v3.0.",
    "Contains OS data © Crown copyright and database right 2026.",
    "Contains Royal Mail data © Royal Mail copyright and database right 2026.",
    "Contains National Statistics data © Crown copyright and database right 2026.",
    "Energy Performance Certificate data © Crown copyright; "
    "licensed under the Open Government Licence v3.0 except address fields.",
]


@router.get("/health")
def health(conn: Conn) -> dict[str, str]:
    conn.execute("SELECT 1")
    return {"status": "ok"}


@router.get("/meta", response_model=BuildInfo)
def build_info(conn: Conn) -> BuildInfo:
    rows = conn.execute("SELECT key, value FROM meta.build_info").fetchall()
    info = {r["key"]: r["value"] for r in rows}

    def as_int(k: str) -> int | None:
        return int(info[k]) if k in info else None

    def as_date(k: str) -> date | None:
        return date.fromisoformat(info[k][:10]) if k in info else None

    return BuildInfo(
        built_at=info.get("built_at"),
        ref_date=as_date("ref_date"),
        hpi_ref_month=as_date("hpi_ref_month"),
        sales_total=as_int("sales_total"),
        sales_matched=as_int("sales_matched"),
        sales_enriched=as_int("sales_enriched"),
        cells=as_int("cells"),
        synthetic=info.get("synthetic_epc") == "true",
        listing_analysis=bool(get_settings().listing_webhook_url),
        attribution=ATTRIBUTION,
    )
