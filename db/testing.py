"""Test-support helpers (strategy A) — NOT imported by the app runtime.

reset_database() truncates all tables between tests so each test starts
hermetic. conftest.py calls it (autouse fixture); the table list is a
module constant — no dynamic SQL surface.

Phase 6 hardening: rollback before truncate — a failing test can leave
the shared connection in an aborted transaction (psycopg
InFailedSqlTransaction), which would make even the next test's TRUNCATE
fail. Rollback is a no-op on a clean connection.
"""
from __future__ import annotations

from db.database import get_connection

_TABLES = ("training_progress", "weekly_plan", "rest_assessments",
           "sessions", "users")


def reset_database() -> None:
    """Truncate every table, restart identity columns. TEST DB ONLY."""
    conn = get_connection()
    conn.rollback()  # no-op when clean; clears aborted transactions
    conn.execute(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE")
    conn.commit()