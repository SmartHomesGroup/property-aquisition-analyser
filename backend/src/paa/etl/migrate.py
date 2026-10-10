"""Apply SQL files in order. Migrations are tracked; build steps always run."""

from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path

import psycopg

from paa.config import get_settings
from paa.etl.util import timed

log = logging.getLogger(__name__)


def sql_dir(sub: str) -> Path:
    base = resources.files("paa") / "sql" / sub
    return Path(str(base))


def _files(sub: str) -> list[Path]:
    return sorted(sql_dir(sub).glob("*.sql"))


def migrate() -> None:
    """Apply any migrations in ``sql/migrations`` not yet recorded."""
    with psycopg.connect(get_settings().database_url) as conn:
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS meta")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS meta.schema_migrations ("
            "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        cur.execute("SELECT name FROM meta.schema_migrations")
        done = {r[0] for r in cur.fetchall()}
        conn.commit()
        for path in _files("migrations"):
            if path.name in done:
                continue
            with timed(f"migrate {path.name}"):
                cur.execute(path.read_text(encoding="utf-8"))
                cur.execute("INSERT INTO meta.schema_migrations (name) VALUES (%s)", (path.name,))
                conn.commit()


def build(only: list[str] | None = None) -> None:
    """Run the derived-data build steps (``sql/build``), each in its own transaction."""
    with psycopg.connect(get_settings().database_url) as conn:
        for path in _files("build"):
            if only and not any(path.name.startswith(o) for o in only):
                continue
            with timed(f"build {path.name}"):
                conn.execute(path.read_text(encoding="utf-8"))
                conn.commit()
