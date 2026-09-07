"""Phase 3/4/5 — EXERCISE_SESSION. Effective (autoregulated) prescription,
distinct per-exercise RPE labels (a11y + AppTest-selectable), shared image
helper with placeholder fallback.

Change #5: approved clinical copy — "purpose" renders before the visual;
"instructions" is the team-approved text.

Change #12: narration — a native st.audio player renders directly under
each instruction (utils.assets.render_audio; B1: always visible, no
autoplay, no session flags; missing audio renders nothing — text is
authoritative).

Prescription reminder placement (user-approved): the Level · sets/reps/
rest line renders PER CARD, directly below the audio player — the last
element read before performing — instead of a single banner at page top.
The line's string and element type are byte-identical to the former
banner (test-contract safety); Level travels with it, and the daily hub
still orients (Level/Cycle/Week/Day) on entry.

Card order: title -> purpose -> image -> position cue -> instruction ->
audio -> Level/prescription reminder -> RPE. No widget labels or keys
changed — the E2E selector contract is untouched.
"""
from __future__ import annotations

import streamlit as st

from utils.session_logic import (
    get_session_position,
    format_rpe_scores,
    normalize_rpe_score,
)
from utils.exercise_logic import (
    select_daily_set,
    get_card,
    apply_position_cue,
    format_prescription,
)
from utils.autoregulation_logic import effective_prescription
from utils.assets import render_image, render_audio
from db import queries

RPE_OPTIONS = [
    "😃 1 — Very Easy",
    "🙂 2 — Easy",
    "😐 3 — Moderate",
    "😣 4 — Hard",
    "😫 5 — Very Hard",
]


def _level_int(level: str) -> int:
    return int(level.split()[-1])


def render_training_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    daily = select_daily_set(user["email"], pos["cycle"],
                             pos["week"], pos["day"])
    lvl = _level_int(user["level"])
    rx = effective_prescription(user["email"], pos["cycle"],
                                pos["week"], lvl)

    st.title("Stage 2 — Exercises")

    # position-tagged keys prevent stale RPE leaking across days
    key_tag = f"{pos['cycle']}_{pos['week']}_{pos['day']}"

    for cid in daily:
        card = apply_position_cue(get_card(cid), lvl)
        with st.container(border=True):
            st.subheader(card["title"])
            st.write(card["purpose"])       # brief description before the visual
            render_image(card["image"], label=card["title"])
            st.write(f"**Position:** {card['position_cue']}")
            st.write(card["instructions"])  # approved copy; plain, not italic
            render_audio(card.get("audio"))  # change #12 — narration alongside
            # Prescription reminder — execution info where the action is
            # (string identical to the former page-top banner).
            st.info(f"**Level** {user['level']} · {format_prescription(rx)}")
            st.selectbox(
                f"How hard did that feel? — {card['title']}",  # distinct label per exercise
                options=RPE_OPTIONS,  # raw == displayed
                index=2,  # default Moderate
                key=f"rpe_{key_tag}_{cid}",
            )

    if st.button("Submit Workout", key="btn_submit_workout",
                 width="stretch", type="primary"):
        rpe_map = {cid: normalize_rpe_score(
                       st.session_state[f"rpe_{key_tag}_{cid}"])
                   for cid in daily}
        rpe_str = format_rpe_scores(rpe_map)
        queries.upsert_training_progress(
            user["email"], pos["cycle"], pos["week"], pos["day"],
            ",".join(daily), rpe_str)
        st.session_state["session_flags"] = {"last_rpe": rpe_str,
                                             "last_daily": daily}
        st.session_state["current_state"] = "WORKOUT_SUMMARY"
        st.rerun()