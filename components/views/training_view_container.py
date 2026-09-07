"""Phase 3/4/5 — EXERCISE_SESSION. Effective (autoregulated) prescription,
distinct per-exercise RPE labels (a11y + AppTest-selectable), placeholder
fallback with absolute paths."""
from __future__ import annotations
from pathlib import Path
import streamlit as st
from utils.session_logic import (get_session_position, format_rpe_scores,
                                 normalize_rpe_score)
from utils.exercise_logic import (select_daily_set, get_card,
                                  apply_position_cue, format_prescription)
from utils.autoregulation_logic import effective_prescription
from db import queries

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLACEHOLDER = PROJECT_ROOT / "assets" / "card_placeholder.jpeg"

RPE_OPTIONS = [
    "😃 1 — Very Easy",
    "🙂 2 — Easy",
    "😐 3 — Moderate",
    "😣 4 — Hard",
    "😫 5 — Very Hard",
]


def _level_int(level: str) -> int:
    return int(level.split()[-1])


def _safe_image(path: str, label: str) -> None:
    p = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path
    if p.exists():
        st.image(str(p), width="stretch")
    elif PLACEHOLDER.exists():
        st.image(str(PLACEHOLDER), width="stretch")
    else:
        st.info(f"[image: {label}]")


def render_training_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    daily = select_daily_set(user["email"], pos["cycle"], pos["week"], pos["day"])
    lvl = _level_int(user["level"])
    rx = effective_prescription(user["email"], pos["cycle"], pos["week"], lvl)
    st.title("Stage 2 — Exercises")
    st.info(f"**Level** {user['level']}  ·  {format_prescription(rx)}")
    key_tag = f"{pos['cycle']}_{pos['week']}_{pos['day']}"
    for cid in daily:
        card = apply_position_cue(get_card(cid), lvl)
        with st.container(border=True):
            _safe_image(card["image"], card["title"])
            st.subheader(card["title"])
            st.write(f"**Position:** {card['position_cue']}")
            st.write(f"_{card['instructions']}_")
            st.selectbox(
                f"How hard did that feel? — {card['title']}",   # distinct label per exercise
                options=RPE_OPTIONS,                            # raw == displayed
                index=2,
                key=f"rpe_{key_tag}_{cid}",
            )
    if st.button("Submit Workout", key="btn_submit_workout", width="stretch", type="primary"):
        rpe_map = {cid: normalize_rpe_score(st.session_state[f"rpe_{key_tag}_{cid}"])
                   for cid in daily}
        rpe_str = format_rpe_scores(rpe_map)
        queries.upsert_training_progress(
            user["email"], pos["cycle"], pos["week"], pos["day"],
            ",".join(daily), rpe_str)
        st.session_state["session_flags"] = {"last_rpe": rpe_str, "last_daily": daily}
        st.session_state["current_state"] = "WORKOUT_SUMMARY"
        st.rerun()