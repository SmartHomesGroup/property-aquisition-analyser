"""Database access helpers.

The ETL uses plain connections; the API uses a pool created at startup.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from paa.config import get_settings


@contextmanager
def connect(*, autocommit: bool = False) -> Iterator[psycopg.Connection]:
    """A single connection for ETL jobs. Commits on clean exit, rolls back on error."""
    conn = psycopg.connect(get_settings().database_url, autocommit=autocommit)
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except BaseException:
        if not autocommit:
            conn.rollback()
        raise
    finally:
        conn.close()


def make_pool() -> ConnectionPool:
    """Connection pool for the API. Rows come back as dicts."""
    return ConnectionPool(
        get_settings().database_url,
        min_size=1,
        max_size=8,
        kwargs={"row_factory": dict_row},
        open=False,
    )
