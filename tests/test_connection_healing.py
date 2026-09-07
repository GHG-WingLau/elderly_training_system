"""tests/test_connection_healing.py — deploy hotfix: reconnect-and-retry.

Unit-level: _HealingConnection is driven with FAKE connections
(_new_connection monkeypatched — no database, no Streamlit context).
These tests never touch the database (conftest's autouse reset still
runs — harmless).

v2 fixed the harness (reconnect queue seeded with the initial connection;
post-heal actions now scripted). v3 restored a no-arg constructor.
v4 (round-2 drill incident): SQLSTATE 25P03 IdleInTransactionSessionTimeout
is NOT an OperationalError in psycopg 3.3.5 — it escaped the round-1
handler; the catch set is now the DEAD_CONNECTION_ERRORS tuple, pinned
here by construction (a 25P03-heals test) and by a tuple guard test.
"""
from __future__ import annotations

import pytest
import psycopg
from psycopg import errors as pg_errors

from db import database as db_database
from db.database import DEAD_CONNECTION_ERRORS, _HealingConnection


class _FakeConn:
    """Scripted connection: execute/commit pop the next scripted action —
    an Exception to raise, or a value to return. An unscripted action is
    an IndexError (script everything, including post-heal actions)."""

    def __init__(self, script, name="fake"):
        self.script = list(script)
        self.name = name
        self.closed = False

    def execute(self, query, params=None):
        action = self.script.pop(0)
        if isinstance(action, Exception):
            raise action
        return action

    def commit(self):
        action = self.script.pop(0)
        if isinstance(action, Exception):
            raise action

    def rollback(self):
        pass

    def close(self):
        self.closed = True


_OPS = lambda: psycopg.OperationalError("SSL connection has been closed")
_25P03 = lambda: pg_errors.IdleInTransactionSessionTimeout(
    "terminating connection due to idle-in-transaction timeout")


class _RollbackRaisingConn(_FakeConn):
    def __init__(self):
        super().__init__([])          # rollback-raise needs no script

    def rollback(self):
        raise _OPS()


def _healing(monkeypatch, conns):
    """Proxy over conns[0]; _new_connection serves conns[1:] in order.
    An unscripted reconnect fails with a clear assertion."""
    queue = list(conns[1:])

    def _factory():
        assert queue, "unexpected reconnect: no more scripted connections"
        return queue.pop(0)

    monkeypatch.setattr(db_database, "_new_connection", _factory)
    return _HealingConnection(conns[0])


def test_execute_heals_after_idle_drop(monkeypatch):
    dead = _FakeConn([_OPS()], name="dead")
    fresh = _FakeConn(["row"], name="fresh")
    proxy = _healing(monkeypatch, [dead, fresh])
    assert proxy.execute("SELECT 1") == "row"   # retried on the fresh conn
    assert dead.closed                            # corpse closed


def test_idle_in_transaction_timeout_heals(monkeypatch):
    """THE round-2 drill incident: SQLSTATE 25P03 is NOT an
    OperationalError in psycopg 3.3.5 — it escaped the round-1 handler
    and must be in the reconnect-and-retry catch set."""
    dead = _FakeConn([_25P03()], name="dead")
    fresh = _FakeConn(["row"], name="fresh")
    proxy = _healing(monkeypatch, [dead, fresh])
    assert proxy.execute("SELECT 1") == "row"
    assert dead.closed


def test_double_failure_surfaces(monkeypatch):
    """Genuine outage (reconnect also fails): the error propagates — no
    infinite retry, no silent swallowing."""
    dead = _FakeConn([_OPS()], name="dead")
    also_dead = _FakeConn([_OPS()], name="also-dead")
    proxy = _healing(monkeypatch, [dead, also_dead])
    with pytest.raises(psycopg.OperationalError):
        proxy.execute("SELECT 1")


def test_commit_failure_reconnects_then_raises(monkeypatch):
    dead = _FakeConn(["ok", _OPS()], name="dead")   # execute ok, commit dies
    fresh = _FakeConn([None], name="fresh")          # scripted post-heal read
    proxy = _healing(monkeypatch, [dead, fresh])
    assert proxy.execute("INSERT ...") == "ok"
    with pytest.raises(psycopg.OperationalError):
        proxy.commit()
    assert dead.closed
    assert proxy.execute("SELECT 1") is None        # healed: runs on fresh


def test_rollback_swallows_connection_death(monkeypatch):
    """reset_database's rollback must never break the next test's setup
    when the shared connection died idle."""
    dead = _RollbackRaisingConn()
    fresh = _FakeConn(["truncated"])
    proxy = _healing(monkeypatch, [dead, fresh])
    proxy.rollback()                               # heals silently
    assert proxy.execute("TRUNCATE ...") == "truncated"


def test_dead_connection_error_tuple_covers_known_kills():
    """The catch set is a contract: both observed connection-death classes
    (SSL/suspend OperationalError; Neon 25P03) must stay in the tuple —
    extend it when new classes are observed, never narrow it silently."""
    assert psycopg.OperationalError in DEAD_CONNECTION_ERRORS
    assert pg_errors.IdleInTransactionSessionTimeout in DEAD_CONNECTION_ERRORS