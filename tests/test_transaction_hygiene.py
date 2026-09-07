"""tests/test_transaction_hygiene.py — deploy hotfix round 2 regression.

The 2026-09-07 drill: the cached connection idled IN an open read
transaction (autocommit=False + read-without-rollback) and Neon's
idle_in_transaction_session_timeout terminated it. Pinned directly via
pg_stat_activity: after every read/write, the shared connection's state
must be 'idle' — never 'idle in transaction'. This is the local-Docker
guard for a platform behavior local Postgres doesn't enforce (timeout
disabled by default) — the exact gap that let the incident reach
production."""
from db import queries
from db.database import get_connection
from tests.helpers_e2e import db


def _our_pid() -> int:
    conn = get_connection()
    pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
    conn.rollback()  # release this read's own implicit transaction
    return pid


def _backend_state(pid: int) -> str:
    row = db().execute(
        "SELECT state FROM pg_stat_activity WHERE pid = %s",
        (pid,)).fetchone()
    assert row is not None, "backend vanished — connection reconnected?"
    return row["state"]


def test_read_leaves_connection_idle_not_in_transaction():
    queries.create_user(email="hyg-r@t.test", username="t", age=60, sex="F")
    pid = _our_pid()
    queries.get_user("hyg-r@t.test")          # the fixed read path
    assert _backend_state(pid) == "idle"      # NOT 'idle in transaction'


def test_write_leaves_connection_idle_after_commit():
    pid = _our_pid()
    queries.create_user(email="hyg-w@t.test", username="t", age=60, sex="F")
    assert _backend_state(pid) == "idle"      # commit ended the transaction