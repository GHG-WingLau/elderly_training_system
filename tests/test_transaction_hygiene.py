"""tests/test_transaction_hygiene.py — deploy hotfix round 2 regression.

The 2026-09-07 drill: the cached connection idled IN an open read
transaction and Neon terminated it (25P03). The invariant: after every
read/write, NO transaction remains open on the shared connection.

v2 — observation-channel redesign (v1 failed deterministically with
state='active' in both tests — an observer-contamination defect, the
same class as the healing-harness v1 bug):
  - pg_stat_activity.state is a TRANSIENT tri-state ('idle',
    'idle in transaction', 'active'); asserting a single snapshot
    against it races the probe's own snapshot timing.
  - The oracle is therefore the FORBIDDEN state, not the desired one:
    assert 'idle in transaction' NEVER appears during a polling window
    after the operation. A genuinely stuck transaction (the incident)
    holds the forbidden state for the whole window — impossible to
    miss; a healthy connection shows transient 'idle'/'active' only.
  - The probe runs on its own autocommit connection (db()) — it never
    holds a transaction while observing.
"""
from __future__ import annotations

import time

from db import queries
from db.database import get_connection
from tests.helpers_e2e import db

_POLL_SECONDS = 2.0
_POLL_INTERVAL = 0.25


def _our_pid() -> int:
    conn = get_connection()
    pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
    conn.rollback()  # release this read's own implicit transaction
    return pid


def _states_seen(pid: int) -> set:
    """All pg_stat_activity states observed for pid during the window,
    sampled on the probe's own autocommit connection (holds no
    transaction while observing)."""
    seen: set = set()
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        row = db().execute(
            "SELECT state FROM pg_stat_activity WHERE pid = %s",
            (pid,)).fetchone()
        if row is not None:
            seen.add(row["state"])
        time.sleep(_POLL_INTERVAL)
    return seen


def test_read_leaves_no_open_transaction():
    queries.create_user(email="hyg-r@t.test", username="t", age=60, sex="F")
    pid = _our_pid()
    queries.get_user("hyg-r@t.test")          # the fixed read path
    states = _states_seen(pid)
    assert "idle in transaction" not in states, (
        f"read left an open transaction (incident 2026-09-07): states "
        f"observed = {sorted(states)}")


def test_write_leaves_no_open_transaction():
    pid = _our_pid()
    queries.create_user(email="hyg-w@t.test", username="t", age=60, sex="F")
    states = _states_seen(pid)
    assert "idle in transaction" not in states, (
        f"write left an open transaction after commit: states "
        f"observed = {sorted(states)}")


def test_incident_reproducer_is_detected():
    """Harness validity: a deliberately-unreleased read transaction MUST
    be caught by the same oracle (forbidden state observed). If this
    fails, the observation channel has gone soft — not the app code."""
    conn = get_connection()
    conn.execute("SELECT 1").fetchone()       # implicit transaction, NOT released
    pid = (conn.execute("SELECT pg_backend_pid() AS pid")
           .fetchone()["pid"])
    states = _states_seen(pid)                # probe observes the stuck state
    conn.rollback()                           # clean up
    assert "idle in transaction" in states, (
        "oracle failed to detect a deliberately stuck transaction — "
        f"states observed = {sorted(states)}")