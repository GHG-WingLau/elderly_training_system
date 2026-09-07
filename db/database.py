"""Postgres connection handler (Phase 6 deployment port — Docker/Neon).

Strategy A (single dialect): app + test suite both run Postgres —
locally via docker-compose.yml, in production via Neon. SQLite is
retired from the runtime (schema_sqlite.sql retained for git history;
instance/local_test.db is obsolete).

Connection URL resolution:
  1. DATABASE_URL environment variable (dev shells, tests, CI)
  2. st.secrets["database_url"] (Streamlit Cloud; local secrets.toml —
     st.secrets raises when no file exists, hence the wrap)

Neon guidance: use the POOLED connection string (host contains
"-pooler") — serverless autosuspend makes direct connections leak.

@st.cache_resource keeps one connection per process (the Streamlit DB
pattern). The historical cosmetic 'coroutine expire_cache was never
awaited' note was SQLite-era; the suppression in app.py is retained and
harmless.

Postgres vs SQLite:
- FK enforcement is native (no PRAGMA).
- psycopg executes one statement per call — the schema is applied
  statement-by-statement after stripping full-line '--' comments (the
  schema file must not contain ';' inside string literals; it doesn't).
- dict_row row factory keeps row["col"] access — queries.py is
  unchanged in substance (placeholders and IDENTITY only).
- The doc's Phase 6 note ("Neon router — connection pattern changes")
  is hereby discharged.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

SCHEMA_PATH = Path(__file__).resolve().parent / "schema_postgres.sql"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        return st.secrets["database_url"]
    except Exception:
        raise RuntimeError(
            "No database URL configured: set DATABASE_URL (env) or "
            "st.secrets['database_url'] — see .streamlit/secrets.toml.example"
        )


@st.cache_resource
def get_connection():
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_database_url(), row_factory=dict_row,
                           autocommit=False)
    _apply_schema(conn)
    return conn


def _apply_schema(conn) -> None:
    """Apply the schema idempotently (CREATE ... IF NOT EXISTS)."""
    sql = SCHEMA_PATH.read_text()
    lines = [ln for ln in sql.splitlines()
             if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)
    conn.commit()


def init_db() -> None:
    """Ensure schema is applied. Cached underneath; safe to call every boot."""
    get_connection()