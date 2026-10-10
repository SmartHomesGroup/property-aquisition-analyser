"""Small shared helpers for ETL jobs."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

log = logging.getLogger(__name__)


@contextmanager
def timed(label: str) -> Iterator[None]:
    """Log how long a block took."""
    t0 = time.perf_counter()
    log.info("%s: start", label)
    try:
        yield
    finally:
        log.info("%s: done in %.1fs", label, time.perf_counter() - t0)


def norm_postcode(p: str | None) -> str | None:
    """Upper case, no whitespace; None when empty. Mirrors ``core.norm_postcode`` in SQL."""
    if p is None:
        return None
    s = "".join(p.split()).upper()
    return s or None


def to_decimal_or_none(s: str | None) -> str | None:
    """Pass numeric strings through; blank or non-numeric become None (SQL NULL)."""
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        float(s)
    except ValueError:
        return None
    return s
