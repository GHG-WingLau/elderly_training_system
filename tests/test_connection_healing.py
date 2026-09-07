"""tests/test_connection_healing.py — deploy hotfix: reconnect-and-retry.

Unit-level: _HealingConnection is driven with FAKE connections
(_new_connection monkeypatched — no database, no Streamlit context).
The deployed failure mode (idle drop → OperationalError on first
execute) must heal transparently; genuine double-failure must surface
(no infinite retry). These tests never touch the database (conftest's
autouse reset still runs — harmless).

v2 harness fixes (4 v1 failures — the PROXY behaved exactly as designed:
caught, reconnected, retried; retries failed only because the scripted
fakes had nothing left to return): (a) the reconnect queue seeded WITH
the initial connection — every _reconnect re-served the dead conn →
IndexError; queue is now conns[1:]; (b) post-heal actions are scripted
explicitly.

v3 (1 v2 failure, my four-character miss): _RollbackRaisingConn moved
above _healing in the v2 rewrite and lost its no-arg constructor —
_FakeConn requires 'script'. Restored: __init__ defaults the script to
empty (rollback-raise needs none). RULE (extended): scripted fakes must
script every action AND define every constructor they're instantiated
with — move-and-rewrite of helper classes re-verifies call sites.
"""
from __future__ import annotations

import pytest
import psycopg

from db import database as db_database
from db.database import _HealingConnection


class _FakeConn:
    """Scripted connection: execute/commit pop the next scripted action —
    an Exception to raise, or a value to return. An unscripted action is
    an IndexError (the v1 lesson: script everything)."""

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


class _RollbackRaisingConn(_FakeConn):
    def __init__(self):
        super().__init__([])          # rollback-raise needs no script

    def rollback(self):
        raise _OPS()


def _healing(monkeypatch, conns):
    """Proxy over conns[0]; _new_connection serves conns[1:] in order —
    reconnects get the NEXT scripted connection, never the initial one
    (the v1 bug). An unscripted reconnect fails with a clear assertion."""
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