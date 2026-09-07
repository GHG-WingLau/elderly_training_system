"""E2E — one full workout day for a seeded user: login → hub → breathing →
exercises → RPE → summary; verified against the DB. Deliberately stops at
WORKOUT_SUMMARY (no click back to hub): each rerun crossing multiplies
AppTest replay risk, and the day-advance is proven by the DB row +
test_session_logic's position tests.

Phase 6 Step 1: raw verification reads via psycopg against the shared
test Postgres (%s placeholders, dict rows)."""
from tests.helpers_e2e import (make_app, login, seed_user, db,
                               rendered_text, _click)

RPE_HARD = "😣 4 — Hard"


def test_workout_loop_records_session(tmp_path, monkeypatch):
    email = "e2e4@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2", age=70, sex="F")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    # DAILY_HUB -> BREATHING_SESSION
    _click(at, "Start Today's Workout"); at.run()
    assert "Stage 1 — Breathing" in rendered_text(at)
    # BREATHING_SESSION -> EXERCISE_SESSION
    _click(at, "Start Exercises"); at.run()
    assert "Stage 2 — Exercises" in rendered_text(at)
    # 3 per-exercise RPE selectboxes -> all Hard
    rpe_boxes = [sb for sb in at.selectbox
                 if (getattr(sb, "label", "") or "").startswith(
                     "How hard did that feel?")]
    assert len(rpe_boxes) == 3
    for sb in rpe_boxes:
        sb.select(RPE_HARD)
    # EXERCISE_SESSION -> WORKOUT_SUMMARY
    _click(at, "Submit Workout"); at.run()
    assert "Workout Complete" in rendered_text(at)
    # DB verification (raw reads)
    rows = db().execute(
        "SELECT week, day, exercise_ids, rpe_scores FROM training_progress "
        "WHERE user_email=%s", (email,)).fetchall()
    assert len(rows) == 1  # UPSERT idempotency
    row = rows[0]
    assert (row["week"], row["day"]) == (0, 1)
    ids = row["exercise_ids"].split(",")
    assert len(ids) == 3 and len(set(ids)) == 3
    assert row["rpe_scores"] == ",".join(f"{i}:4" for i in ids)


def test_hub_advances_with_seeded_progress(tmp_path, monkeypatch):
    """Position rendering without live crossings: seed two completed days,
    login, hub must show Day 3."""
    email = "e2e5@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    from db import queries
    for day in (1, 2):
        queries.upsert_training_progress(
            email=email, cycle=1, week=0, day=day,
            exercise_ids="C01,PC01,G01", rpe_scores="C01:3,PC01:3,G01:3")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert "Day** 3" in rendered_text(at)