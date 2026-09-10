"""Phase 9/10 — progress presentation contracts (v3: the verdict-G chart).

- _stance_data: the FULL journey — Day 1 (stance only, when a baseline
  exists) + ALL five weeks as placeholders (None for unmeasured) — the
  formative horizon the team approved.
- _y_domain: [0, 1.5 × max(values, norm)] — zero floor, norm included,
  degenerate cases fall back to a visible scale.
- _progress_metrics: latest values + deltas (stance vs Day 1,
  sit-to-stand vs the previous review).
- Decision (a) PINNED: an entered 0 is data; a DB NULL is a gap.
- Render smoke: the rest page renders with progress data present —
  AppTest is blind to chart/metric visuals; the visual is a permanent
  manual-QA line.
"""
from tests.helpers_e2e import (_click, login, make_app, rendered_text,
                               seed_user)

_BASELINE = {"calf_cm": 34.0, "sls_left_sec": 12.5, "sls_right_sec": 10.0,
             "chair_stand_reps": 12,
             "measured_at": "2026-09-12T00:00:00+00:00"}


def _seed_rest_week(email):
    from db import queries
    for day in range(1, 7):
        queries.upsert_training_progress(
            email=email, cycle=1, week=0, day=day,
            exercise_ids="C01,PC01,G01",
            rpe_scores="C01:3,PC01:3,G01:3")


def test_progress_data_and_metrics(tmp_path, monkeypatch):
    from db import queries
    from components.views.rest_view import (_progress_metrics,
                                            _stance_data, _y_domain)
    email = "chart-data@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    queries.record_baseline(email=email, baseline=_BASELINE)
    queries.upsert_rest_assessment(email=email, cycle=1, week=0,
                                   memory_recall_count=3, reflection="",
                                   sit_to_stand_15s=5, sls_left=13.0,
                                   sls_right=11.0)
    queries.upsert_rest_assessment(email=email, cycle=1, week=1,
                                   memory_recall_count=4, reflection="",
                                   sit_to_stand_15s=6, sls_left=14.5,
                                   sls_right=12.0)
    baseline = queries.get_user(email)["baseline"]
    rows = queries.get_rest_assessment_history(email, 1)
    x_order, left, right = _stance_data(baseline, rows)
    assert x_order == ["Day 1", "Week 0", "Week 1", "Week 2",
                       "Week 3", "Week 4"]      # the FULL journey
    assert left == [12.5, 13.0, 14.5, None, None, None]
    assert right == [10.0, 11.0, 12.0, None, None, None]
    metrics = {k: (v, d) for k, v, d in
               _progress_metrics(baseline, rows)}
    assert metrics["rest.sls_left"] == (14.5, 2.0)   # latest, vs Day 1
    assert metrics["rest.sls_right"] == (12.0, 2.0)
    assert metrics["rest.sts"] == (6, 1)             # latest, vs prev week
    # Domain: zero floor, 1.5x, the norm must fit.
    assert _y_domain(left + right, norm=20.0) == [0, 30.0]
    assert _y_domain([4, 6]) == [0, 9.0]
    assert _y_domain([0]) == [0, 1.0]                # degenerate fallback
    assert _y_domain([]) == [0, 1.0]


def test_progress_plots_as_entered(tmp_path, monkeypatch):
    """Team decision (a) pinned: entered 0 is data; NULL is a gap; the
    placeholder horizon shows all five weeks."""
    from db import queries
    from components.views.rest_view import _progress_metrics, _stance_data
    email = "chart-zero@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    queries.upsert_rest_assessment(email=email, cycle=1, week=0,
                                   memory_recall_count=0, reflection="",
                                   sit_to_stand_15s=0, sls_left=0,
                                   sls_right=None)
    rows = queries.get_rest_assessment_history(email, 1)
    x_order, left, right = _stance_data(None, rows)
    assert x_order == ["Week 0", "Week 1", "Week 2", "Week 3", "Week 4"]
    assert left == [0, None, None, None, None]      # entered zero is data
    assert right == [None, None, None, None, None]  # NULL = a gap
    metrics = {k: (v, d) for k, v, d in _progress_metrics(None, rows)}
    assert metrics["rest.sls_left"] == (0, None)    # no baseline -> no delta
    assert metrics["rest.sls_right"] == (None, None)


def test_rest_page_renders_with_chart_data(tmp_path, monkeypatch):
    """AppTest cannot see chart/metric elements — this smoke proves the
    progress path does not crash the rest render when data exists."""
    from db import queries
    email = "chart-e2e@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    _seed_rest_week(email)
    queries.record_baseline(email=email, baseline=_BASELINE)
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    _click(at, "Start Weekly Review")
    at.run()
    text = rendered_text(at)
    assert "Rest & Review" in text              # the page rendered
    assert "Why we measure again each week" in text