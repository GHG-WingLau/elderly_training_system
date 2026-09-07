"""CRUD + UPSERT helpers. All writes are idempotent via ON CONFLICT.
Convention: test fixtures call writers with keyword arguments so signature
drift fails loudly at the call site. (Positional use of create_user's
first four parameters is preserved for the logic-test fixtures.)

Step 2a (password auth + consent + sessions):
- create_user extended: password_hash, consent_version,
  consent_accepted_at (nullable — legacy seed fixtures omit them).
  NOTE: the ON CONFLICT update set deliberately does NOT touch
  password_hash/conssent columns; auth_view enforces a duplicate-email
  gate BEFORE create_user, because the upsert alone would overwrite an
  existing account's username/age/sex while keeping its old password.
- get_user_by_credentials REMOVED (username+email matching retired).
- Session-token functions (mechanism-independent — consumed by Step 2b
  "remember me" in either the localStorage or query-param design):
  create_session_token / get_session_user / delete_session_token /
  purge_expired_sessions; 32-byte urlsafe tokens, TIMESTAMPTZ expiry,
  opportunistic purge on creation.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from db.database import get_connection


def _row_to_dict(row: Optional[dict]) -> Optional[dict]:
    return dict(row) if row is not None else None


def create_user(email: str, username: str, age: int, sex: str,
                password_hash: Optional[str] = None,
                consent_version: Optional[str] = None,
                consent_accepted_at: Optional[datetime] = None) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (email, username, age, sex, password_hash,
        consent_version, consent_accepted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(email) DO UPDATE SET
        username=excluded.username, age=excluded.age,
        sex=excluded.sex""",
        (email, username, age, sex, password_hash, consent_version,
         consent_accepted_at),
    )
    conn.commit()


def get_user(email: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = %s", (email,)
    ).fetchone()
    return _row_to_dict(row)


def update_user_level(email: str, level: str, total_score: int,
                      sarc_f: int, calf: int, balance: int, chair_stand: int,
                      red_flags: str) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE users SET
        level = %s, total_score = %s, sarc_f_score = %s, calf_score = %s,
        balance_score = %s, chair_stand_score = %s, red_flags = %s
        WHERE email = %s""",
        (level, total_score, sarc_f, calf, balance, chair_stand,
         red_flags, email),
    )
    conn.commit()


def get_current_cycle(email: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT current_cycle FROM users WHERE email = %s", (email,)
    ).fetchone()
    return row["current_cycle"] if row else 1


def advance_cycle(email: str) -> int:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET current_cycle = current_cycle + 1 WHERE email = %s",
        (email,),
    )
    conn.commit()
    return get_current_cycle(email)


def set_user_level(email: str, level: str) -> None:
    """Light level update for mid-cycle regression (scores untouched)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET level = %s WHERE email = %s", (level, email)
    )
    conn.commit()


def upsert_training_progress(email: str, cycle: int, week: int, day: int,
                             exercise_ids: str, rpe_scores: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO training_progress
        (user_email, cycle, week, day, exercise_ids, rpe_scores)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT(user_email, cycle, week, day) DO UPDATE SET
        exercise_ids=excluded.exercise_ids,
        rpe_scores=excluded.rpe_scores""",
        (email, cycle, week, day, exercise_ids, rpe_scores),
    )
    conn.commit()


def upsert_weekly_plan(email: str, cycle: int, week: int, exercise_ids: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO weekly_plan (user_email, cycle, week, exercise_ids)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_email, cycle, week) DO UPDATE SET
        exercise_ids=excluded.exercise_ids""",
        (email, cycle, week, exercise_ids),
    )
    conn.commit()


def get_weekly_plan(email: str, cycle: int, week: int) -> Optional[str]:
    """Return persisted exercise_ids string for the week, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT exercise_ids FROM weekly_plan "
        "WHERE user_email = %s AND cycle = %s AND week = %s",
        (email, cycle, week),
    ).fetchone()
    return row["exercise_ids"] if row else None


def upsert_rest_assessment(email: str, cycle: int, week: int,
                            memory_recall_count: int, reflection: str,
                            sit_to_stand_15s: int, sls_left: int,
                            sls_right: int) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO rest_assessments
        (user_email, cycle, week, memory_recall_count, reflection,
         sit_to_stand_15s_cycles, sls_left_sec, sls_right_sec)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(user_email, cycle, week) DO UPDATE SET
        memory_recall_count=excluded.memory_recall_count,
        reflection=excluded.reflection,
        sit_to_stand_15s_cycles=excluded.sit_to_stand_15s_cycles,
        sls_left_sec=excluded.sls_left_sec,
        sls_right_sec=excluded.sls_right_sec""",
        (email, cycle, week, memory_recall_count, reflection,
         sit_to_stand_15s, sls_left, sls_right),
    )
    conn.commit()


def get_completed_days(email: str, cycle: int) -> set:
    conn = get_connection()
    rows = conn.execute(
        "SELECT week, day FROM training_progress WHERE user_email = %s AND "
        "cycle = %s",
        (email, cycle)).fetchall()
    return {(r["week"], r["day"]) for r in rows}


def get_completed_rests(email: str, cycle: int) -> set:
    conn = get_connection()
    rows = conn.execute(
        "SELECT week FROM rest_assessments WHERE user_email = %s AND cycle = %s",
        (email, cycle)).fetchall()
    return {r["week"] for r in rows}


def get_rpe_scores_for_week(email: str, cycle: int, week: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT rpe_scores FROM training_progress "
        "WHERE user_email = %s AND cycle = %s AND week = %s AND day BETWEEN 1 "
        "AND 6",
        (email, cycle, week)).fetchall()
    return [r["rpe_scores"] for r in rows]


def count_completed_workouts(email: str, cycle: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM training_progress "
        "WHERE user_email = %s AND cycle = %s", (email, cycle)).fetchone()
    return row["n"]


# --- session tokens (Step 2a; consumed by Step 2b "remember me") ----------

def create_session_token(email: str, days: int = 30) -> str:
    """Create a 30-day (default) session token for the user; returns it."""
    purge_expired_sessions()
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=days)
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, user_email, expires_at) "
        "VALUES (%s, %s, %s)",
        (token, email, expires),
    )
    conn.commit()
    return token


def get_session_user(token: str) -> Optional[dict]:
    """Return the user for a valid, unexpired token, else None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.email = s.user_email "
        "WHERE s.token = %s AND s.expires_at > now()",
        (token,),
    ).fetchone()
    return _row_to_dict(row)


def delete_session_token(token: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = %s", (token,))
    conn.commit()


def purge_expired_sessions() -> None:
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE expires_at < now()")
    conn.commit()