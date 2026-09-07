"""Postgres connection handler (Phase 6 — Docker local / Neon production).

Deploy hotfix (SSL idle-drop): Neon suspends idle computes (free tier,
~5 min) and the pooled endpoint drops idle client connections — the
cached long-lived connection dies between user actions. Deployed
symptom: the first write after an idle gap raised OperationalError
("SSL connection has been closed unexpectedly"), and WITHOUT healing
the dead connection stays cached, failing every subsequent action until
process recycle. Fix: get_connection() returns a SELF-HEALING proxy —
OperationalError on execute triggers close + reconnect (schema
re-applied, idempotent) + one retry. Safe because every app write is a
single-statement UPSERT (idempotent by design) and every read is a
stateless SELECT. Commit-failure window (dead socket between execute
and commit) reconnects then re-raises — a user retry re-applies via
UPSERT. prepare_threshold=None disables psycopg's automatic prepared
statements (portable across poolers; negligible cost at beta scale).

Connection URL resolution: DATABASE_URL env var (tests, dev shells,
CI) — else st.secrets["database_url"] (Cloud; local secrets.toml —
st.secrets raises when no file exists, hence the wrap). Neon: use the
POOLED connection string (host contains "-pooler").
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg
import streamlit as st
from psycopg.rows import dict_row

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


def _new_connection():
    """Open a fresh schema-verified connection (never cached directly)."""
    conn = psycopg.connect(_database_url(), row_factory=dict_row,
                           autocommit=False, prepare_threshold=None)
    _apply_schema(conn)
    return conn


class _HealingConnection:
    """Duck-typed psycopg Connection proxy: reconnect-and-retry on
    OPERATIONAL (connection-level) failures.

    - execute: one reconnect+retry (idempotent-write safe).
    - commit: reconnect then re-raise (rare idle-suspend window between
      execute and commit; UPSERT makes the user's retry safe).
    - rollback: reconnect silently (cleanup path — dead connections
      must not break the next test's reset).
    Exposes cursor()/close() pass-throughs for schema init/cleanup.
    """

    def __init__(self, conn):
        self._conn = conn

    def _reconnect(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass  # the corpse may not even close cleanly
        self._conn = _new_connection()

    def execute(self, query, params=None):
        try:
            return self._conn.execute(query, params)
        except psycopg.OperationalError:
            self._reconnect()
            return self._conn.execute(query, params)

    def commit(self):
        try:
            self._conn.commit()
        except psycopg.OperationalError:
            self._reconnect()
            raise

    def rollback(self):
        try:
            self._conn.rollback()
        except psycopg.OperationalError:
            self._reconnect()

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


@st.cache_resource
def get_connection():
    """Cached self-healing connection (one per process)."""
    return _HealingConnection(_new_connection())


def init_db() -> None:
    """Ensure schema is applied. Cached underneath; safe to call every boot."""
    get_connection()