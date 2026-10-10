"""Request-scoped dependencies."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, Request
from psycopg.rows import DictRow

DictConnection = psycopg.Connection[DictRow]


def get_conn(request: Request) -> Iterator[DictConnection]:
    with request.app.state.pool.connection() as conn:
        yield conn


Conn = Annotated[DictConnection, Depends(get_conn)]
