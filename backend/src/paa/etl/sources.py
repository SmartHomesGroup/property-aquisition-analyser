"""Where the open datasets come from, and a resumable downloader.

URLs verified 2026-10-10; see docs/research/reports/UK heatmap mapping tools.md.
All of these download anonymously. EPC bulk data does not (GOV.UK One Login), so it is
supplied by the user as files under ``<data_dir>/epc/``.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx

from paa.config import get_settings

log = logging.getLogger(__name__)

PPD_BASE = "https://price-paid-data.publicdata.landregistry.gov.uk"
HPI_BASE = "https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data"
CODEPOINT_URL = (
    "https://api.os.uk/downloads/v1/products/CodePointOpen/downloads?area=GB&format=CSV&redirect"
)


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    filename: str

    @property
    def path(self) -> Path:
        return get_settings().data_dir / self.filename


def ppd_complete() -> Source:
    """Every England & Wales transaction since 1995 (~5.5 GB)."""
    return Source("ppd-complete", f"{PPD_BASE}/pp-complete.csv", "ppd/pp-complete.csv")


def ppd_year(year: int) -> Source:
    """One calendar year of PPD (~100-200 MB). Handy for prototyping."""
    return Source(f"ppd-{year}", f"{PPD_BASE}/pp-{year}.csv", f"ppd/pp-{year}.csv")


def ppd_monthly() -> Source:
    """Latest monthly update (adds, changes and deletes)."""
    return Source(
        "ppd-monthly",
        f"{PPD_BASE}/pp-monthly-update-new-version.csv",
        "ppd/pp-monthly-update-new-version.csv",
    )


def ppd_uprn_lookup(year: int, month: int) -> Source:
    """Transaction id -> UPRN lookup, published monthly from August 2026."""
    mon = date(year, month, 1).strftime("%b").lower()
    name = f"pp-uprn-lookup-{mon}-{year}.csv"
    return Source("ppd-uprn", f"{PPD_BASE}/{name}", f"ppd/{name}")


def codepoint_open() -> Source:
    """OS Code-Point Open: GB postcode centroids (zip, ~14 MB)."""
    return Source("codepoint", CODEPOINT_URL, "codepoint/codepo_gb.zip")


def hpi_full(year: int, month: int) -> Source:
    """UK House Price Index full file for a release month (~35 MB)."""
    name = f"UK-HPI-full-file-{year}-{month:02d}.csv"
    return Source("hpi", f"{HPI_BASE}/{name}", f"hpi/{name}")


def latest_hpi() -> Source:
    """Find the newest HPI release by probing backwards from two months ago."""
    today = date.today()
    y, m = today.year, today.month
    with httpx.Client(timeout=get_settings().http_timeout_s, follow_redirects=True) as client:
        for _ in range(12):
            m -= 1
            if m == 0:
                y, m = y - 1, 12
            src = hpi_full(y, m)
            if client.head(src.url).status_code == 200:
                return src
    msg = "No UK HPI release found in the last 12 months"
    raise RuntimeError(msg)


def download(src: Source, *, force: bool = False) -> Path:
    """Stream a source to disk. Skips if present unless ``force``. Atomic via a .part file."""
    dest = src.path
    if dest.exists() and not force:
        log.info("%s already downloaded (%s)", src.name, dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    log.info("downloading %s -> %s", src.url, dest)
    with (
        httpx.Client(timeout=get_settings().http_timeout_s, follow_redirects=True) as client,
        client.stream("GET", src.url) as resp,
    ):
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0
        next_report = 0
        with part.open("wb") as fh:
            for chunk in resp.iter_bytes(1 << 20):
                fh.write(chunk)
                done += len(chunk)
                if done >= next_report:
                    pct = f" ({done * 100 // total}%)" if total else ""
                    log.info("  %d MB%s", done >> 20, pct)
                    next_report += 200 << 20
    shutil.move(part, dest)
    return dest
