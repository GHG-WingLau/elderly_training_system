"""Phase 4 contract — auto-regulation rules, regression, cycle restart.

Phase 6 Step 1 (strategy A): the private per-file SQLite fixture is
retired — tests run against the shared test Postgres (conftest sets
DATABASE_URL and truncates before every test; same-scope autouse
fixtures instantiate first, so truncation precedes this fixture's
seeding). iso_db seeds the standard user and returns the shared
connection for raw reads (dict rows; %s placeholders). Test bodies are
unchanged — the two raw reads here carry no placeholders and are
dialect-compatible as written."""
import pytest

from db import queries
from db.database import get_connection
from utils.autoregulation_logic import (
    classify, weekly_average_rpe, apply_rule, effective_prescription,
    hard_streak, regression_due, day7_plan,
)
from utils.session_logic import compute_current_position
from utils.exercise_logic import format_prescription


@pytest.fixture
def iso_db():
    """Seed the standard Level-2 user on the shared truncated test DB.
    Returns the shared connection (dict rows) for raw reads."""
    queries.create_user("u@t.test", "tester", 65, "F")
    queries.update_user_level(
        email="u@t.test", level="Level 2", total_score=5,
        sarc_f=2, calf=1, balance=1, chair_stand=1, red_flags="")
    return get_connection()


def _seed_week(email, cycle, week, rpe_value):
    for day in range(1, 7):
        ids = f"C{day:02d},PC{day:02d},G{day:02d}"
        rpes = ",".join(f"{i}:{rpe_value}" for i in ids.split(","))
        queries.upsert_training_progress(email, cycle, week, day, ids, rpes)


# --- classification boundaries (spec §3.11) ---
@pytest.mark.parametrize("avg,expected", [
    (2.49, "low"), (2.5, "maintain"), (2.6, "maintain"),
    (3.99, "maintain"), (4.0, "high"), (5.0, "high"),
])
def test_classify_boundaries(avg, expected):
    assert classify(avg) == expected


def test_weekly_average_rpe(iso_db):
    _seed_week("u@t.test", 1, 1, 4)          # 18 values of 4
    assert weekly_average_rpe("u@t.test", 1, 1) == pytest.approx(4.0)


def test_weekly_average_rpe_empty(iso_db):
    assert weekly_average_rpe("u@t.test", 1, 3) is None


# --- rule application ---
def test_apply_high_reduces_reps_20pct():
    rx = {"sets": 2, "reps_min": 8, "reps_max": 10, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "high")
    assert (out["reps_min"], out["reps_max"]) == (6, 8)
    assert out["sets"] == 2


def test_apply_high_sets_fallback_at_reps_floor():
    rx = {"sets": 2, "reps_min": 4, "reps_max": 6, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "high")
    assert out["sets"] == 1
    assert out["reps_min"] == 4


def test_apply_low_adds_2_reps():
    rx = {"sets": 2, "reps_min": 8, "reps_max": 10, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "low")
    assert (out["reps_min"], out["reps_max"]) == (10, 12)


def test_apply_low_increases_hold_only_when_defined():
    rx0 = {"sets": 2, "reps_min": 6, "reps_max": 8, "hold_s": 10,
           "rest_s_min": 60, "rest_s_max": 90}
    assert apply_rule(rx0, "low")["hold_s"] == 14
    assert apply_rule(dict(rx0, hold_s=None), "low")["hold_s"] is None


def test_apply_maintain_noop():
    rx = {"sets": 3, "reps_min": 12, "reps_max": 15, "hold_s": None,
          "rest_s_min": 30, "rest_s_max": 45}
    assert apply_rule(rx, "maintain") == rx


def test_reps_cap():
    rx = {"sets": 3, "reps_min": 20, "reps_max": 20, "hold_s": None,
          "rest_s_min": 30, "rest_s_max": 45}
    assert apply_rule(rx, "low")["reps_max"] == 20


# --- effective prescription fold ---
def test_effective_prescription_weeks_0_1_are_base(iso_db):
    base = effective_prescription("u@t.test", 1, 0, 2)
    assert (base["reps_min"], base["reps_max"], base["sets"]) == (10, 12, 2)
    assert effective_prescription("u@t.test", 1, 1, 2) == base


def test_effective_prescription_fold_after_hard_week(iso_db):
    _seed_week("u@t.test", 1, 1, 5)          # week 1 high
    rx = effective_prescription("u@t.test", 1, 2, 2)
    assert (rx["reps_min"], rx["reps_max"]) == (8, 9)   # floor(10*.8), floor(12*.8)


def test_effective_prescription_caps(iso_db):
    for w in (1, 2, 3):
        _seed_week("u@t.test", 1, w, 5)
    rx = effective_prescription("u@t.test", 1, 4, 2)    # folds weeks 1-3
    assert (rx["reps_min"], rx["reps_max"], rx["sets"]) == (4, 5, 2)


def test_week0_average_does_not_adjust_week1(iso_db):
    _seed_week("u@t.test", 1, 0, 5)          # week 0 high
    base = effective_prescription("u@t.test", 1, 0, 2)
    assert effective_prescription("u@t.test", 1, 1, 2)["reps_min"] == base["reps_min"]

# --- regression (spec: 2 consecutive weeks >= 4.0; floor Level 0) ---
def test_regression_due_two_high_weeks(iso_db):
    _seed_week("u@t.test", 1, 0, 5)
    _seed_week("u@t.test", 1, 1, 4)
    assert regression_due("u@t.test", 1, 1, 2) == 1


def test_regression_not_due_single_high(iso_db):
    _seed_week("u@t.test", 1, 0, 2)
    _seed_week("u@t.test", 1, 1, 5)
    assert regression_due("u@t.test", 1, 1, 2) is None


def test_regression_boundary_exactly_4(iso_db):
    _seed_week("u@t.test", 1, 0, 4)
    _seed_week("u@t.test", 1, 1, 4)
    assert regression_due("u@t.test", 1, 1, 3) == 2


def test_regression_floor_level0(iso_db):
    _seed_week("u@t.test", 1, 0, 5)
    _seed_week("u@t.test", 1, 1, 5)
    assert regression_due("u@t.test", 1, 1, 0) is None
    assert hard_streak("u@t.test", 1, 1) is True   # streak detected anyway


def test_day7_plan_uses_regressed_level_for_next_rx(iso_db):
    _seed_week("u@t.test", 1, 1, 5)
    _seed_week("u@t.test", 1, 2, 5)
    plan = day7_plan("u@t.test", 1, 2, "Level 2")
    assert plan["regression_to"] == 1
    # next rx from Level 1 base (8,10), folded twice high -> (4,6)
    assert plan["next_week_prescription"]["reps_min"] == 4


# --- cycle restart ---
def test_cycle_restart_preserves_history(iso_db):
    for w in range(5):
        _seed_week("u@t.test", 1, w, 3)
        queries.upsert_rest_assessment("u@t.test", 1, w, 3, "ok", 12, 20, 22)
    assert compute_current_position("u@t.test")["is_program_complete"]
    queries.advance_cycle("u@t.test")
    assert compute_current_position("u@t.test") == {
        "cycle": 2, "week": 0, "day": 1,
        "is_rest_day": False, "is_program_complete": False}
    assert iso_db.execute(
        "SELECT COUNT(*) AS n FROM training_progress").fetchone()["n"] == 30
    assert iso_db.execute(
        "SELECT COUNT(*) AS n FROM rest_assessments").fetchone()["n"] == 5


def test_new_cycle_resets_adjustments(iso_db):
    _seed_week("u@t.test", 1, 1, 5)
    assert effective_prescription("u@t.test", 1, 2, 2)["reps_min"] == 8
    queries.advance_cycle("u@t.test")
    assert effective_prescription("u@t.test", 2, 2, 2)["reps_min"] == 10


def test_set_user_level(iso_db):
    queries.set_user_level("u@t.test", "Level 1")
    assert queries.get_user("u@t.test")["level"] == "Level 1"


def test_count_completed_workouts(iso_db):
    _seed_week("u@t.test", 1, 0, 3)
    assert queries.count_completed_workouts("u@t.test", 1) == 6


# --- display formatting ---
def test_format_prescription():
    rx = {"sets": 2, "reps_min": 6, "reps_max": 8, "hold_s": 10,
          "rest_s_min": 60, "rest_s_max": 90}
    s = format_prescription(rx)
    assert "2 sets" in s and "6–8 reps" in s and "10s hold" in s and "60–90s" in s
    s2 = format_prescription(dict(rx, hold_s=None, rest_s_min=60, rest_s_max=60))
    assert "hold" not in s2 and "60s" in s2