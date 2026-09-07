"""Phase 3/5 — session position computation and RPE (de)serialization."""
from __future__ import annotations
import re

import streamlit as st

from db import queries


def format_rpe_scores(rpe_map: dict) -> str:
    """{'C01':2,'PC01':3} -> 'C01:2,PC01:3' (insertion order preserved)."""
    return ",".join(f"{cid}:{score}" for cid, score in rpe_map.items())


def parse_rpe_scores(s: str) -> dict:
    s = (s or "").strip()
    if not s:
        return {}
    out: dict[str, int] = {}
    for pair in s.split(","):
        cid, _, score = pair.partition(":")
        out[cid.strip()] = int(score.strip())
    return out


def normalize_rpe_score(value) -> int:
    """Defensive RPE normalizer: int 1-5, numeric string, or full emoji label.
    Raises ValueError otherwise. Phase 4 auto-regulation consumes these values."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"unparseable RPE value: {value!r}")
    if isinstance(value, int):
        score = value
    elif isinstance(value, str):
        m = re.search(r"\b([1-5])\b", value)
        if not m:
            raise ValueError(f"unparseable RPE value: {value!r}")
        score = int(m.group(1))
    else:
        raise ValueError(f"unparseable RPE value: {value!r}")
    if not 1 <= score <= 5:
        raise ValueError(f"RPE out of range: {score}")
    return score


def compute_current_position(email: str, override: dict | None = None) -> dict:
    """Earliest incomplete day (OQ-07: resume, no auto-skip).
    If a debug override dict is supplied (QA only), validate it and return it
    directly; is_program_complete is always False under override so QA can
    reach the Day 7 views."""
    if override is not None:
        week, day, cycle = (int(override["week"]), int(override["day"]),
                            int(override["cycle"]))
        if not (0 <= week <= 4):
            raise ValueError(f"override week out of range: {week}")
        if not (1 <= day <= 7):
            raise ValueError(f"override day out of range: {day}")
        if cycle < 1:
            raise ValueError(f"override cycle out of range: {cycle}")
        return {"cycle": cycle, "week": week, "day": day,
                "is_rest_day": day == 7, "is_program_complete": False}
    user = queries.get_user(email)
    cycle = user["current_cycle"]
    done_days = queries.get_completed_days(email, cycle)
    done_rests = queries.get_completed_rests(email, cycle)
    for week in range(5):
        for day in range(1, 7):
            if (week, day) not in done_days:
                return {"cycle": cycle, "week": week, "day": day,
                        "is_rest_day": False, "is_program_complete": False}
        if week not in done_rests:
            return {"cycle": cycle, "week": week, "day": 7,
                    "is_rest_day": True, "is_program_complete": False}
    return {"cycle": cycle, "week": 4, "day": 7,
            "is_rest_day": True, "is_program_complete": True}


def get_session_position(email: str) -> dict:
    """View-facing wrapper: applies the debug override only when ?debug=true
    is active. Production behaviour is identical to compute_current_position."""
    override = None
    if st.session_state.get("debug") and st.session_state.get("debug_override"):
        override = st.session_state["debug_override"]
    return compute_current_position(email, override)