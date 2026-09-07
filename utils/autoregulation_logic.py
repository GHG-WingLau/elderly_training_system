"""Phase 4 — auto-regulation engine (spec §3.11).
Thresholds and caps are spec/decision constants — do not tune without
clinical sign-off. Deterministic: a pure function of stored RPE history +
current level; no extra state, so it is rerun-safe by construction."""
from __future__ import annotations
import math
from typing import Optional

from db import queries
from utils.session_logic import parse_rpe_scores
from utils.exercise_logic import get_prescription

HIGH_THRESHOLD = 4.0
LOW_THRESHOLD = 2.5
REPS_FLOOR, REPS_CAP = 4, 20
HOLD_FLOOR, HOLD_CAP = 5, 20
SETS_FLOOR = 1


def classify(avg: float) -> str:
    if avg >= HIGH_THRESHOLD:
        return "high"
    if avg >= LOW_THRESHOLD:
        return "maintain"
    return "low"


def weekly_average_rpe(email: str, cycle: int, week: int) -> Optional[float]:
    """Mean of all per-exercise RPE values across days 1-6; None if no data."""
    values: list[int] = []
    for s in queries.get_rpe_scores_for_week(email, cycle, week):
        values.extend(parse_rpe_scores(s).values())
    return sum(values) / len(values) if values else None


def apply_rule(rx: dict, classification: str) -> dict:
    """One adjustment step on a numeric prescription dict (returns a copy)."""
    rx = dict(rx)
    if classification == "maintain":
        return rx
    if classification == "high":
        if rx["reps_min"] <= REPS_FLOOR:
            rx["sets"] = max(SETS_FLOOR, rx["sets"] - 1)      # spec's 'or': sets fallback
        else:
            rx["reps_min"] = max(REPS_FLOOR, math.floor(rx["reps_min"] * 0.8))
            rx["reps_max"] = max(rx["reps_min"], math.floor(rx["reps_max"] * 0.8))
        if rx.get("hold_s"):
            rx["hold_s"] = max(HOLD_FLOOR, math.floor(rx["hold_s"] * 0.8))
    elif classification == "low":
        rx["reps_min"] = min(REPS_CAP, rx["reps_min"] + 2)
        rx["reps_max"] = min(REPS_CAP, rx["reps_max"] + 2)
        if rx.get("hold_s"):
            rx["hold_s"] = min(HOLD_CAP, rx["hold_s"] + 4)
    return rx


def effective_prescription(email: str, cycle: int, week: int, level) -> dict:
    """Prescription for `week` = base for current level, folded with the
    adjustment rule over completed weeks 1..week-1 (week 0 excluded per spec)."""
    rx = get_prescription(level)
    for w in range(1, week):
        avg = weekly_average_rpe(email, cycle, w)
        if avg is not None:
            rx = apply_rule(rx, classify(avg))
    return rx


def hard_streak(email: str, cycle: int, week: int) -> bool:
    """True if weeks week-1 and week both averaged >= 4.0 (week-1 may be 0)."""
    if week < 1:
        return False
    a = weekly_average_rpe(email, cycle, week)
    b = weekly_average_rpe(email, cycle, week - 1)
    return (a is not None and b is not None
            and a >= HIGH_THRESHOLD and b >= HIGH_THRESHOLD)


def regression_due(email: str, cycle: int, week: int,
                   current_level_int: int) -> Optional[int]:
    """New level int if a one-step regression should apply at Day 7 of `week`;
    None otherwise (including the Level 0 floor)."""
    if hard_streak(email, cycle, week) and current_level_int > 0:
        return current_level_int - 1
    return None


def day7_plan(email: str, cycle: int, week: int, level_str: str) -> dict:
    """Everything the Day 7 view needs. Read-only; no writes."""
    lvl = int(str(level_str).split()[-1])
    avg = weekly_average_rpe(email, cycle, week)
    new_level_int = regression_due(email, cycle, week, lvl)
    level_for_next = (f"Level {new_level_int}"
                      if new_level_int is not None else level_str)
    next_rx = (effective_prescription(email, cycle, week + 1, level_for_next)
               if week < 4 else None)
    return {
        "week": week,
        "avg_rpe": avg,
        "classification": classify(avg) if avg is not None else None,
        "hard_streak": hard_streak(email, cycle, week),
        "regression_to": new_level_int,
        "next_week_prescription": next_rx,
    }