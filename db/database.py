"""Postgres connection handler (Phase 6 — Docker local / Neon production).

Deploy hotfix round 2 (idle-in-transaction, drill 2026-09-07): Neon
enforces idle_in_transaction_session_timeout (~5 min) — a connection
left in an OPEN transaction is terminated server-side (SQLSTATE 25P03,
IdleInTransactionSessionTimeout). ROOT CAUSE: with autocommit=False every
SELECT opens an implicit transaction and the READ functions in
queries.py never committed/rolled back — the cached connection sat in an
open read transaction between user actions. Two-layer fix:
  1. QUERIES (prevention): every read ends with conn.rollback() — the
     connection idles OUT of transaction, so 25P03 cannot fire in normal
     operation (see db/queries.py). Local Docker Postgres has the timeout
     disabled — which is why the suite never caught it; remote-branch
     validation (DEPLOYMENT.md §1.3) exists for exactly this class.
  2. PROXY (detection/healing): the catch set is the DEAD_CONNECTION_ERRORS
     tuple — psycopg 3.3.5 does NOT map 25P03 under OperationalError
     (empirical: the drill's exception escaped `except
     psycopg.OperationalError` in the round-1 release). Both layers are
     retained as defense in depth: a future read that forgets rollback
     still heals.

Round 1 (SSL idle-drop, still active): Neon suspends idle computes and
the pooled endpoint drops idle clients — the cached connection dies
between user actions. get_connection() returns a SELF-HEALING proxy:
connection-class failure on execute → close + reconnect (schema
re-applied, idempotent) + one retry. Safe because every app write is a
single-statement UPSERT (Phase-1 idempotency) and every read is a
stateless SELECT. Commit failure reconnects then re-raises (rare
execute→commit window; user retry re-applies via UPSERT). Rollback heals
silently (protects reset_database). prepare_threshold=None (pooler
portability, defensive).

Connection URL resolution: DATABASE_URL env var (tests, dev, CI) — else
st.secrets["database_url"] (Cloud; local secrets.toml). Neon: use the
POOLED connection string (host contains "-pooler").
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg
import streamlit as st
from psycopg import errors as pg_errors
from psycopg.rows import dict_row

SCHEMA_PATH = Path(__file__).resolve().parent / "schema_postgres.sql"

# Connection-death exceptions that trigger reconnect-and-retry.
# psycopg 3.3.5 mapping note (empirical, drill 2026-09-07): SQLSTATE 25P03
# (IdleInTransactionSessionTimeout) is NOT an OperationalError subclass —
# it escaped the round-1 `except psycopg.OperationalError` handler.
# OperationalError covers the 08/57/58-class deaths (incl. the SSL-closed
# error); InterfaceError covers locally-closed connections. Extend this
# tuple when a new connection-death class is observed — never narrow it.
DEAD_CONNECTION_ERRORS = (
    psycopg.OperationalError,
    psycopg.InterfaceError,
    pg_errors.IdleInTransactionSessionTimeout,
)


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
    connection-death exceptions (DEAD_CONNECTION_ERRORS).

    - execute: one reconnect+retry (idempotent-write safe).
    - commit: reconnect then re-raise (rare idle-suspend window between
      execute and commit; UPSERT makes the user's retry safe).
    - rollback: reconnect silently (cleanup path — dead connections
      must not break the next test's reset).
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
        except DEAD_CONNECTION_ERRORS:
            self._reconnect()
            return self._conn.execute(query, params)

    def commit(self):
        try:
            self._conn.commit()
        except DEAD_CONNECTION_ERRORS:
            self._reconnect()
            raise

    def rollback(self):
        try:
            self._conn.rollback()
        except DEAD_CONNECTION_ERRORS:
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