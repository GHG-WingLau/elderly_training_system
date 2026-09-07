"""Phase 3 contract — RPE serialization, position computation, UPSERT idempotency.

Phase 6 Step 1 (strategy A): the private per-file SQLite fixture is
retired — tests run against the shared test Postgres (conftest truncates
before every test; autouse ordering precedes seeding). Raw reads in
test_upsert_idempotency ported to %s placeholders / dict rows. All pure
and override tests are unchanged (they passed pre-port)."""
import pytest

from db import queries
from db.database import get_connection
from utils.session_logic import format_rpe_scores, parse_rpe_scores, compute_current_position


# --- RPE serialization (pure) ---
def test_format_rpe_scores():
    assert format_rpe_scores({"C01": 2, "PC01": 3, "G02": 4}) == "C01:2,PC01:3,G02:4"


def test_format_rpe_empty():
    assert format_rpe_scores({}) == ""


def test_parse_rpe_scores():
    assert parse_rpe_scores("C01:2,PC01:3,G02:4") == {"C01": 2, "PC01": 3, "G02": 4}


def test_parse_rpe_empty():
    assert parse_rpe_scores("") == {}
    assert parse_rpe_scores(None) == {}


def test_rpe_roundtrip():
    m = {"C01": 1, "PC01": 5, "G02": 3}
    assert parse_rpe_scores(format_rpe_scores(m)) == m


# --- Position computation + idempotency (shared truncated test DB) ---
@pytest.fixture
def iso_db():
    """Seed the standard user on the shared truncated test DB."""
    queries.create_user("u@t.test", "tester", 65, "F")
    return get_connection()


def test_position_fresh(iso_db):
    pos = compute_current_position("u@t.test")
    assert pos == {"cycle": 1, "week": 0, "day": 1,
                   "is_rest_day": False, "is_program_complete": False}


def test_position_after_day1(iso_db):
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:2,PC01:3,G01:2")
    assert compute_current_position("u@t.test")["day"] == 2


def test_position_after_days1_6_routes_day7(iso_db):
    for d in range(1, 7):
        queries.upsert_training_progress("u@t.test", 1, 0, d, "C01", "C01:2")
    pos = compute_current_position("u@t.test")
    assert pos["week"] == 0 and pos["day"] == 7 and pos["is_rest_day"]
    assert not pos["is_program_complete"]


def test_position_after_day7_advances_week(iso_db):
    for d in range(1, 7):
        queries.upsert_training_progress("u@t.test", 1, 0, d, "C01", "C01:2")
    queries.upsert_rest_assessment("u@t.test", 1, 0, 3, "ok", 12, 20, 22)
    pos = compute_current_position("u@t.test")
    assert pos["week"] == 1 and pos["day"] == 1 and not pos["is_rest_day"]


def test_position_resumes_earliest_gap(iso_db):
    # did days 1 and 3 but skipped 2 -> resume at day 2 (OQ-07)
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01", "C01:2")
    queries.upsert_training_progress("u@t.test", 1, 0, 3, "C01", "C01:2")
    assert compute_current_position("u@t.test")["day"] == 2


def test_position_program_complete(iso_db):
    for w in range(5):
        for d in range(1, 7):
            queries.upsert_training_progress("u@t.test", 1, w, d, "C01", "C01:2")
        queries.upsert_rest_assessment("u@t.test", 1, w, 3, "ok", 12, 20, 22)
    assert compute_current_position("u@t.test")["is_program_complete"]


def test_upsert_idempotency(iso_db):
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:2,PC01:3,G01:4")
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:5,PC01:5,G01:5")
    n = iso_db.execute(
        "SELECT COUNT(*) AS n FROM training_progress "
        "WHERE user_email=%s AND cycle=1 AND week=0 AND day=1", ("u@t.test",)).fetchone()
    assert n["n"] == 1
    r = iso_db.execute(
        "SELECT rpe_scores FROM training_progress "
        "WHERE user_email=%s AND cycle=1 AND week=0 AND day=1", ("u@t.test",)).fetchone()
    assert r["rpe_scores"] == "C01:5,PC01:5,G01:5"

from utils.session_logic import normalize_rpe_score

@pytest.mark.parametrize("value,expected", [
    (1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
    ("3", 3),
    ("😃 1 — Very Easy", 1),
    ("😐 3 — Moderate", 3),
    ("😫 5 — Very Hard", 5),
])
def test_normalize_rpe_valid(value, expected):
    assert normalize_rpe_score(value) == expected


@pytest.mark.parametrize("value", [
    0, 6, -1, "no digit here", "6 reps", None, True, 3.5, ["3"],
])
def test_normalize_rpe_invalid_raises(value):
    with pytest.raises(ValueError):
        normalize_rpe_score(value)

def test_override_training_day():
    pos = compute_current_position("x@t.test",
                                   override={"cycle": 1, "week": 0, "day": 1})
    assert pos == {"cycle": 1, "week": 0, "day": 1,
                   "is_rest_day": False, "is_program_complete": False}

def test_override_day7_is_rest():
    pos = compute_current_position("x@t.test",
                                   override={"cycle": 2, "week": 3, "day": 7})
    assert pos["is_rest_day"] is True
    assert pos["is_program_complete"] is False


@pytest.mark.parametrize("ov", [
    {"cycle": 1, "week": 5, "day": 1},
    {"cycle": 1, "week": -1, "day": 1},
    {"cycle": 1, "week": 0, "day": 0},
    {"cycle": 1, "week": 0, "day": 8},
    {"cycle": 0, "week": 0, "day": 1},
])
def test_override_invalid_raises(ov):
    with pytest.raises(ValueError):
        compute_current_position("x@t.test", override=ov)