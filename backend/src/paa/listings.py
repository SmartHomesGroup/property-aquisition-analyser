"""The paste-a-listing flow: normalise the URL, read what the engine returned, find the postcode.

The analysis engine today is the stage-0 n8n workflow (``Settings.listing_webhook_url``), which
returns a flat dict of loosely named fields. Everything here that interprets those fields is
tolerant: a missing field is ``None``, never an error, because the engine's schema is not ours.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ALLOWED_SCHEMES = ("http", "https")

# Hosts the paste box accepts. Rightmove first; the others are the portals the stage-0 engine
# was built for. Subdomains (www., m.) are allowed.
ALLOWED_HOSTS = (
    "rightmove.co.uk",
    "zoopla.co.uk",
    "onthemarket.com",
    "auctionhouse.co.uk",
    "savills.co.uk",
    "allsop.co.uk",
)

# UK postcode anywhere in free text (outward + inward, with or without a space).
_POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}[0-9][A-Z0-9]?)\s*([0-9][ABD-HJLNP-UW-Z]{2})\b",
    re.IGNORECASE,
)

# Rightmove-style property descriptions -> Land Registry type codes.
_TYPE_WORDS: tuple[tuple[str, str], ...] = (
    ("semi", "S"),
    ("detached", "D"),
    ("terrace", "T"),
    ("end of terrace", "T"),
    ("town house", "T"),
    ("townhouse", "T"),
    ("flat", "F"),
    ("apartment", "F"),
    ("maisonette", "F"),
    ("bungalow", "D"),
    ("cottage", "D"),
)


class ListingUrlError(ValueError):
    """The pasted text is not a listing URL we accept."""


def normalise_url(raw: str) -> tuple[str, str]:
    """Validate a pasted URL. Returns ``(clean_url, key)``.

    ``clean_url`` is what we send to the engine (scheme + host + path + query, no fragment).
    ``key`` is the de-duplication key: lower-case host, path without a trailing slash, no
    query or fragment. Rightmove's ``#/`` suffix and tracking parameters thus collapse.
    """
    s = raw.strip()
    if not s:
        raise ListingUrlError("Paste a listing link")
    if "://" not in s:
        s = "https://" + s
    parts = urlsplit(s)
    if parts.scheme.lower() not in ALLOWED_SCHEMES or not parts.hostname:
        raise ListingUrlError("That doesn't look like a web link")
    host = parts.hostname.lower()
    if not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise ListingUrlError(
            "Only listing links from Rightmove, Zoopla, OnTheMarket and the main auction "
            "houses are accepted"
        )
    path = re.sub(r"/+$", "", parts.path) or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")])
    clean = urlunsplit(("https", host, path, query, ""))
    return clean, f"{host}{path}"


def unwrap_result(payload: Any) -> dict[str, Any]:
    """Reduce the engine's envelope to the flat field dict.

    n8n returns either ``[{"json": {...}}]``, ``{"json": {...}}``, ``{"fields": {...}}`` or
    the dict itself, depending on the last node. Mirrors the stage-0 page's ``render()``.
    """
    d = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(d, dict):
        return {}
    inner = d.get("json")
    if isinstance(inner, dict):
        d = inner
    fields = d.get("fields")
    if isinstance(fields, dict):
        d = fields
    return d


def pick(fields: dict[str, Any], *keys: str) -> Any:
    """First present, non-empty value among alternative field names."""
    for k in keys:
        v = fields.get(k)
        if v is not None and v != "":
            return v
    return None


def to_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, int | float):
        return round(v)
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(v))
    if not m:
        return None
    try:
        return round(float(m.group(0).replace(",", "")))
    except ValueError:
        return None


def find_postcode(*texts: Any) -> str | None:
    """Normalised postcode (no space, upper case) from the first text that contains one."""
    for t in texts:
        if not t:
            continue
        m = _POSTCODE_RE.search(str(t))
        if m:
            return (m.group(1) + m.group(2)).upper()
    return None


def property_type_code(description: Any) -> str | None:
    """Map a free-text type ("3 bed terraced house", "Semi-Detached") to D/S/T/F."""
    if not description:
        return None
    d = str(description).lower()
    for word, code in _TYPE_WORDS:
        if word in d:
            return code
    return None


def summarise(fields: dict[str, Any]) -> dict[str, Any]:
    """The identifying facts we store in columns and use to place the listing on the map."""
    address = pick(fields, "Address", "address", "Property Address", "property_address")
    return {
        "address": str(address) if address else None,
        "postcode": find_postcode(
            pick(fields, "Postcode", "postcode"), address, pick(fields, "Location", "location")
        ),
        "asking_price": to_int(pick(fields, "Asking Price", "asking_price", "Price", "price")),
        "property_type": property_type_code(
            pick(fields, "Property Type", "property_type", "Type", "type")
        ),
        "bedrooms": to_int(pick(fields, "Bedrooms", "bedrooms", "Beds", "beds")),
    }
