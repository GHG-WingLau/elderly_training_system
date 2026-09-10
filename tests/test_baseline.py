"""Phase 9, Step 2 — baseline storage + review-page display contracts.

- DB roundtrip: record_baseline stores the raw measures (get_user
  surfaces the dict); overwrite semantics (re-assessment latest-wins).
- E2E: the rest page shows the explainer (always) and the baseline
  block + per-input captions for users WITH a baseline; skips the
  block for users without one (red-flag fast-path).
"""
from components.views.rest_view import (BASELINE_TITLE, WHY_TITLE)
from tests.helpers_e2e import (_click, login, make_app, rendered_text,
                               seed_user)


def _seed_rest_week(email):
    """Six completed training days -> the hub offers the weekly review."""
    from db import queries
    for day in range(1, 7):
        queries.upsert_training_progress(
            email=email, cycle=1, week=0, day=day,
            exercise_ids="C01,PC01,G01",
            rpe_scores="C01:3,PC01:3,G01:3")


_BASELINE = {"calf_cm": 34.0, "sls_left_sec": 12.5, "sls_right_sec": 10.0,
             "chair_stand_reps": 12,
             "measured_at": "2026-09-12T00:00:00+00:00"}


def test_record_baseline_roundtrip(tmp_path, monkeypatch):
    from db import queries
    email = "base-db@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    queries.record_baseline(email=email, baseline=_BASELINE)
    user = queries.get_user(email)
    assert user["baseline"]["sls_left_sec"] == 12.5
    assert user["baseline"]["chair_stand_reps"] == 12
    # Overwrite semantics: a re-assessment latest-wins.
    queries.record_baseline(email=email, baseline={
        "calf_cm": 35.0, "sls_left_sec": 14.0, "sls_right_sec": 13.0,
        "chair_stand_reps": 14, "measured_at": "2026-10-01T00:00:00+00:00"})
    assert queries.get_user(email)["baseline"]["sls_left_sec"] == 14.0


def test_rest_shows_explainer_and_baseline(tmp_path, monkeypatch):
    from db import queries
    email = "base-show@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    _seed_rest_week(email)
    queries.record_baseline(email=email, baseline=_BASELINE)
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    _click(at, "Start Weekly Review")
    at.run()
    text = rendered_text(at)
    assert WHY_TITLE in text                          # explainer (always)
    assert "Many people see their numbers improve" in text
    assert BASELINE_TITLE in text                     # baseline block
    assert "left: 12.5 sec" in text and "right: 10.0 sec" in text
    assert "Your Day 1 result: 12.5 sec" in text      # per-input caption


def test_rest_without_baseline_skips_block(tmp_path, monkeypatch):
    email = "base-none@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    _seed_rest_week(email)
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    _click(at, "Start Weekly Review")
    at.run()
    text = rendered_text(at)
    assert WHY_TITLE in text                # explainer still shows
    assert BASELINE_TITLE not in text       # no baseline -> no block