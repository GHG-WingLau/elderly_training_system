"""Phase 3 — WORKOUT_SUMMARY."""
from __future__ import annotations
import streamlit as st
from utils.session_logic import parse_rpe_scores


def render_summary(user: dict) -> None:
    flags = st.session_state.get("session_flags", {})
    rpe_str = flags.get("last_rpe", "")
    daily = flags.get("last_daily", [])
    rpe_map = parse_rpe_scores(rpe_str)
    avg = (sum(rpe_map.values()) / len(rpe_map)) if rpe_map else 0
    st.title("Workout Complete! 🎉")
    st.balloons()
    st.write(f"**Exercises completed:** {len(daily)}")
    if rpe_map:
        st.write(f"**Average RPE:** {avg:.1f} / 5")
        for cid, score in rpe_map.items():
            st.write(f"- {cid}: {score}/5")
    if st.button("Return to Daily Hub", key="btn_return_hub", width="stretch", type="primary"):
        st.session_state["session_flags"] = {}
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()