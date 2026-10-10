"""Paste-a-listing: run the analysis engine on a listing URL, keep the result, place it on the map.

The engine is the stage-0 n8n workflow (see AGENTS.md). This route is the seam that lets the
web app use it today and lets stage 3 swap in our own pipeline without the frontend noticing:
the response always has a ``property`` block we derived and a ``fields`` block the engine owns.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from paa.api.deps import Conn, DictConnection
from paa.api.schemas import ListingAnalysis, ListingProperty, PostcodeLocation, Precision
from paa.config import Settings, get_settings
from paa.listings import ListingUrlError, normalise_url, summarise, unwrap_result

log = logging.getLogger(__name__)
router = APIRouter(tags=["listings"])

ENGINE = "n8n-stage0"


class ListingRequest(BaseModel):
    url: str = Field(max_length=2000)
    refresh: bool = Field(default=False, description="Ignore a stored recent analysis")


class EngineError(RuntimeError):
    pass


def call_engine(
    url: str, *, settings: Settings, client: httpx.Client | None = None
) -> tuple[Any, int]:
    """POST the listing URL to the engine. Returns (parsed JSON, elapsed ms)."""
    t0 = time.perf_counter()
    try:
        if client is None:
            with httpx.Client(timeout=settings.listing_timeout_s) as c:
                r = c.post(settings.listing_webhook_url, json={"url": url})
        else:
            r = client.post(settings.listing_webhook_url, json={"url": url})
        r.raise_for_status()
        payload = r.json()
    except httpx.TimeoutException as e:
        raise EngineError("The analysis engine took too long to answer") from e
    except httpx.HTTPStatusError as e:
        raise EngineError(f"The analysis engine returned HTTP {e.response.status_code}") from e
    except (httpx.HTTPError, ValueError) as e:
        raise EngineError("The analysis engine did not answer") from e
    return payload, int((time.perf_counter() - t0) * 1000)


@router.post("/listings/analyse", response_model=ListingAnalysis)
def analyse(body: ListingRequest, conn: Conn) -> ListingAnalysis:
    settings = get_settings()
    if not settings.listing_webhook_url:
        raise HTTPException(status_code=503, detail="Listing analysis is not configured")
    try:
        url, key = normalise_url(body.url)
    except ListingUrlError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not body.refresh and settings.listing_cache_hours > 0:
        row = conn.execute(
            """
            SELECT id, url, requested_at, duration_ms, result
            FROM core.listing_analysis
            WHERE url_key = %(key)s AND ok
              AND requested_at > now() - make_interval(secs => %(secs)s)
            ORDER BY requested_at DESC LIMIT 1
            """,
            {"key": key, "secs": settings.listing_cache_hours * 3600},
        ).fetchone()
        if row is not None:
            fields = unwrap_result(row["result"])
            return _response(conn, row, fields, cached=True)

    try:
        payload, ms = call_engine(url, settings=settings)
    except EngineError as e:
        conn.execute(
            """
            INSERT INTO core.listing_analysis (url, url_key, engine, ok, error)
            VALUES (%s, %s, %s, false, %s)
            """,
            (url, key, ENGINE, str(e)),
        )
        conn.commit()
        log.warning("engine failed for %s: %s", url, e)
        raise HTTPException(status_code=502, detail=str(e)) from e

    fields = unwrap_result(payload)
    summary = summarise(fields)
    row = conn.execute(
        """
        INSERT INTO core.listing_analysis
            (url, url_key, duration_ms, engine, ok, result,
             address, postcode, asking_price, property_type, bedrooms)
        VALUES (%(url)s, %(key)s, %(ms)s, %(engine)s, true, %(result)s,
                %(address)s, %(postcode)s, %(asking_price)s, %(property_type)s, %(bedrooms)s)
        RETURNING id, url, requested_at, duration_ms, result
        """,
        {
            "url": url,
            "key": key,
            "ms": ms,
            "engine": ENGINE,
            "result": json.dumps(payload),
            **summary,
        },
    ).fetchone()
    conn.commit()
    assert row is not None
    return _response(conn, row, fields, cached=False)


def _response(
    conn: DictConnection, row: dict[str, Any], fields: dict[str, Any], *, cached: bool
) -> ListingAnalysis:
    summary = summarise(fields)
    location, precision = locate(conn, summary["postcode"], summary["address"])
    requested = row["requested_at"]
    return ListingAnalysis(
        id=row["id"],
        url=row["url"],
        requested_at=requested.isoformat() if isinstance(requested, datetime) else str(requested),
        cached=cached,
        duration_ms=row["duration_ms"],
        engine=ENGINE,
        property=ListingProperty(
            address=summary["address"],
            postcode=_fmt_postcode(summary["postcode"]),
            asking_price=summary["asking_price"],
            property_type=summary["property_type"],
            bedrooms=summary["bedrooms"],
            location=location,
            precision=precision,
        ),
        fields=fields,
    )


# --- placing the listing on the map -------------------------------------------------------------

_OUTWARD_RE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?$")
_LEADING_NUMBER_RE = re.compile(r"^\s*(flat\s+\S+\s*,?\s*)?\d+[a-z]?\s+", re.IGNORECASE)

_LOCATION_SELECT = """
    SELECT %(label)s::text AS postcode,
           ST_Y(ST_Transform(g, 4326)) AS lat,
           ST_X(ST_Transform(g, 4326)) AS lon,
           round(ST_X(g))::int AS easting, round(ST_Y(g))::int AS northing,
           NULL::text AS district_code, %(pqi)s::int AS pqi
    FROM (SELECT ST_Centroid(ST_Collect(geom)) AS g FROM ({inner}) q) c
    WHERE g IS NOT NULL
"""


def parse_address(address: str | None) -> tuple[str | None, str | None, str | None]:
    """ "12 Christ Church Street, Preston, Lancashire, PR1" -> (street, town, outward)."""
    if not address:
        return None, None, None
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if not parts:
        return None, None, None
    outward = None
    if _OUTWARD_RE.match(parts[-1].upper()):
        outward = parts.pop().upper()
    if not parts:
        return None, None, outward
    street = _LEADING_NUMBER_RE.sub("", parts[0]).strip().upper() or None
    town = parts[1].upper() if len(parts) > 1 else None
    return street, town, outward


def locate(
    conn: DictConnection, postcode: str | None, address: str | None
) -> tuple[PostcodeLocation | None, Precision | None]:
    """Best available point for the listing, and how precise it is.

    1. Full postcode -> its Code-Point centroid ("postcode").
    2. Street + town from the address -> centroid of the postcodes of sales on that street
       ("street"; a few hundred metres at worst).
    3. Outward code (e.g. PR1) -> centroid of the district's postcodes ("district"; kilometres).
    """
    if postcode:
        row = conn.execute(
            """
            SELECT core.fmt_postcode(postcode) AS postcode,
                   ST_Y(ST_Transform(geom, 4326)) AS lat, ST_X(ST_Transform(geom, 4326)) AS lon,
                   easting, northing, district_code, pqi
            FROM core.postcode WHERE postcode = %s AND geom IS NOT NULL
            """,
            (postcode,),
        ).fetchone()
        if row:
            return _loc(row), "postcode"

    street, town, outward = parse_address(address)
    if street and town:
        inner = """
            SELECT p.geom FROM core.sale s JOIN core.postcode p ON p.postcode = s.postcode
            WHERE s.street = %(street)s AND s.town = %(town)s AND p.geom IS NOT NULL
              AND (%(outward)s::text IS NULL
                   OR left(s.postcode, length(s.postcode) - 3) = %(outward)s::text)
        """
        row = conn.execute(
            _LOCATION_SELECT.format(inner=inner),
            {
                "street": street,
                "town": town,
                "outward": outward,
                "label": street.title(),
                "pqi": 50,
            },
        ).fetchone()
        if row:
            return _loc(row), "street"

    if outward:
        inner = """
            SELECT geom FROM core.postcode
            WHERE left(postcode, length(postcode) - 3) = %(outward)s::text AND geom IS NOT NULL
        """
        row = conn.execute(
            _LOCATION_SELECT.format(inner=inner),
            {"outward": outward, "label": outward, "pqi": 90},
        ).fetchone()
        if row:
            return _loc(row), "district"

    return None, None


def _loc(row: dict[str, Any]) -> PostcodeLocation:
    return PostcodeLocation(
        postcode=row["postcode"],
        lat=row["lat"],
        lon=row["lon"],
        easting=row["easting"],
        northing=row["northing"],
        district_code=row["district_code"],
        positional_quality=row["pqi"],
    )


def _fmt_postcode(pc: str | None) -> str | None:
    return f"{pc[:-3]} {pc[-3:]}" if pc and len(pc) > 3 else pc
