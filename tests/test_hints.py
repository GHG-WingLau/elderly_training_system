"""Phase 8 (option B) — in-flow hint + feedback-fix contracts.

v3/v4 history: click-then-run fix (v3); translation round landed —
constants equal the EN ui_strings values (drift pins), the bookmark tip
dismiss-once un-parked (v4), zh feedback-fix pins (v4).
"""
import json
from pathlib import Path

from tests.helpers_e2e import (_click, db, login, make_app,
                               rendered_text, seed_user)
from utils.hints import (GOT_IT_LABEL, HINT_BREATHING, HINT_BREATHING_TITLE,
                         HINT_HUB, HINT_HUB_TITLE, is_dismissed)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_dismiss_ui_hint_roundtrip(tmp_path, monkeypatch):
    from db import queries
    email = "hint-db@test"
    make_app(tmp_path, monkeypatch)
    user = seed_user(email, "Level 2")
    assert not is_dismissed(user, HINT_HUB)          # NULL = all active
    queries.dismiss_ui_hint(email=email, key=HINT_HUB)
    user = queries.get_user(email)
    assert is_dismissed(user, HINT_HUB)
    queries.dismiss_ui_hint(email=email, key=HINT_HUB)  # idempotent merge
    assert is_dismissed(queries.get_user(email), HINT_HUB)


def test_hub_hint_shown_then_dismissed(tmp_path, monkeypatch):
    email = "hint-e2e@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert HINT_HUB_TITLE in rendered_text(at)       # first visit: visible
    _click(at, GOT_IT_LABEL)
    at.run()
    assert HINT_HUB_TITLE not in rendered_text(at)   # dismissed this session
    conn = db()
    row = conn.execute("SELECT ui_hints FROM users WHERE email = %s",
                       (email,)).fetchone()
    assert HINT_HUB in (row["ui_hints"] or {})       # and persisted


def test_pre_dismissed_hint_not_reshown(tmp_path, monkeypatch):
    from db import queries
    email = "hint-pre@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    queries.dismiss_ui_hint(email=email, key=HINT_HUB)
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert HINT_HUB_TITLE not in rendered_text(at)


def test_orientation_block_on_auth(tmp_path, monkeypatch):
    """Beta-feedback fix: the landing page orients every visitor —
    5-week duration, 60+ audience, free / nothing to cancel."""
    at = make_app(tmp_path, monkeypatch)
    text = rendered_text(at)
    assert "A gentle 5-week exercise program" in text
    assert "nothing to cancel" in text
    assert "5-week" in text          # the REAL duration, up front


def test_breathing_hint_shown_then_dismissed(tmp_path, monkeypatch):
    email = "hint-breath@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    _click(at, "Start Today's Workout")   # hub -> breathing (EN label)
    at.run()
    assert HINT_BREATHING_TITLE in rendered_text(at)
    _click(at, GOT_IT_LABEL)
    at.run()
    assert HINT_BREATHING_TITLE not in rendered_text(at)
    conn = db()
    row = conn.execute("SELECT ui_hints FROM users WHERE email = %s",
                       (email,)).fetchone()
    assert HINT_BREATHING in (row["ui_hints"] or {})


def test_remember_label_reword_pinned():
    """Beta-feedback fix pinned: the remember-me label carries no
    duration figure (was misread as the program's duration)."""
    doc = json.loads((_DATA_DIR / "ui_strings.json").read_text(
        encoding="utf-8"))
    label = doc["auth"]["remember_label"]
    assert label == "Keep me logged in on this device"
    assert "30" not in label


def test_bookmark_tip_dismiss_once(tmp_path, monkeypatch):
    """The un-parked refinement: the bookmark tip (token-conditional)
    dismisses once via the same ui_hints store. Two tips show on a
    fresh hub (hub hint + bookmark tip) — dismiss the hub hint first
    so the bookmark tip's Got it becomes the unique match."""
    email = "hint-bookmark@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)                    # remember ON -> ?t= -> tip
    assert "bookmark this page" in rendered_text(at)
    _click(at, GOT_IT_LABEL)            # first match = the hub hint's
    at.run()
    assert "bookmark this page" in rendered_text(at)   # still there
    _click(at, GOT_IT_LABEL)            # now unique = the bookmark's
    at.run()
    assert "bookmark this page" not in rendered_text(at)
    conn = db()
    row = conn.execute("SELECT ui_hints FROM users WHERE email = %s",
                       (email,)).fetchone()
    assert "bookmark_tip" in (row["ui_hints"] or {})


def test_feedback_fix_zh_pinned():
    """The beta-feedback fix, verified in both zh locales: no duration
    figure in the remember label; the orientation states the real
    5-week duration, free, and nothing to cancel."""
    for loc in ("zh-HK", "zh-TW"):
        doc = json.loads((_DATA_DIR / f"ui_strings.{loc}.json").read_text(
            encoding="utf-8"))
        assert "30" not in doc["auth"]["remember_label"]
        assert "5" in doc["auth"]["orientation_lead"]
        assert "費用全免" in doc["auth"]["orientation_lead"]
        assert "取消" in doc["auth"]["orientation_account"]