"""Phase 2 contract — curriculum engine.

Phase 6 Step 1 (strategy A): the private per-file SQLite fixture
(in-memory-style temp DB + queries.get_connection monkeypatch) is
retired — tests run against the shared test Postgres (conftest sets
DATABASE_URL and truncates before every test; autouse fixtures
instantiate first, so seeding lands on a clean DB). iso_db seeds the
two standard users; no raw reads in this file, so the return value is
the shared connection by convention."""
from collections import Counter

import pytest

from db import queries
from db.database import get_connection
from utils import exercise_logic as el


@pytest.fixture
def iso_db():
    """Seed the two standard users on the shared truncated test DB."""
    queries.create_user("u@t.test", "tester", 65, "F")
    queries.create_user("v@t.test", "tester2", 70, "M")
    return get_connection()


def test_apply_position_cue():
    cards = {c["card_id"]: c for c in el._load_cards()}
    out = el.apply_position_cue(cards["C01"], "Level 3")
    assert out["position_cue"] == cards["C01"]["position_cues"]["3"]
    assert out["card_id"] == "C01"
    assert "position_cue" not in cards["C01"]  # original untouched


def test_get_prescription_all_levels():
    for lvl in range(5):
        p = el.get_prescription(lvl)
        assert {"sets", "reps_min", "reps_max", "hold_s",
                "rest_s_min", "rest_s_max"} <= set(p)


def test_weekly_pool_shape_all_weeks(iso_db):
    for week in range(5):
        pool = el.get_weekly_pool("u@t.test", 1, week)
        assert len(pool) == 6, f"week {week}: {pool}"
        counts = Counter(el._card_category(c) for c in pool)
        assert len(counts) == 3, f"week {week}: {list(counts)}"
        assert all(v == 2 for v in counts.values()), f"week {week}: {dict(counts)}"


def test_week0_week1_are_complement(iso_db):
    w0 = set(el.get_weekly_pool("u@t.test", 1, 0))
    w1 = set(el.get_weekly_pool("u@t.test", 1, 1))
    assert w0.isdisjoint(w1)
    union = w0 | w1
    assert len(union) == 12
    assert all(el._card_category(c) in {"C", "PC", "G"} for c in union)


def test_new_category_introduced(iso_db):
    assert "HF" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 2)}
    assert "SP" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 3)}
    assert "CM" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 4)}


def test_daily_set_constraints(iso_db):
    for week in range(5):
        prev = None
        for day in range(1, 7):
            ds = el.select_daily_set("u@t.test", 1, week, day)
            assert len(ds) == 3
            assert len(set(ds)) == 3                          # unique
            cats = [el._card_category(c) for c in ds]
            assert len(set(cats)) == 3                       # distinct categories
            if prev is not None:
                assert set(ds).isdisjoint(prev), f"w{week} d{day}: {ds} ∩ {prev}"
            prev = set(ds)


def test_determinism_same_inputs(iso_db):
    pool1 = el.get_weekly_pool("u@t.test", 1, 2)
    pool2 = el.get_weekly_pool("u@t.test", 1, 2)             # second call reads DB
    assert pool1 == pool2
    for day in range(1, 7):
        a = el.select_daily_set("u@t.test", 1, 2, day)
        b = el.select_daily_set("u@t.test", 1, 2, day)
        assert a == b


def test_pool_persistence(iso_db):
    el.get_weekly_pool("u@t.test", 1, 3)
    row = queries.get_weekly_plan("u@t.test", 1, 3)
    assert row is not None
    assert el.get_weekly_pool("u@t.test", 1, 3) == row.split(",")


def test_two_users_both_valid(iso_db):
    a = el.get_weekly_pool("u@t.test", 1, 2)
    b = el.get_weekly_pool("v@t.test", 1, 2)
    assert len(a) == 6 and len(b) == 6
    assert len({el._card_category(c) for c in a}) == 3
    assert len({el._card_category(c) for c in b}) == 3