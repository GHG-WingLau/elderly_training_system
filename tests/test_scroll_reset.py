"""tests/test_scroll_reset.py — change #9 (transition-gated scroll reset).

AppTest cannot observe viewport position, so these tests pin the
observable contract of the gating logic:
  1. a completed render stores `prev_fingerprint` in session state;
  2. the stored fingerprint has the agreed shape;
  3. a plain rerun (no state change) leaves it untouched.

Actual scroll behaviour is covered by the manual QA checklist that
accompanies this change. No widget labels changed, so the rest of the
suite needs no edits — run the full suite after applying.
"""
from __future__ import annotations
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def _boot() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    return at


def test_completed_render_stores_fingerprint():
    at = _boot()
    assert "prev_fingerprint" in at.session_state


def test_fingerprint_shape_on_first_render():
    at = _boot()
    fp = tuple(at.session_state["prev_fingerprint"])
    assert fp == (False, "UNAUTHENTICATED", None)


def test_plain_rerun_leaves_fingerprint_unchanged():
    at = _boot()
    before = at.session_state["prev_fingerprint"]
    at.run()  # plain rerun — same (unauthenticated) page
    assert at.session_state["prev_fingerprint"] == before