"""Phase 3 — WORKOUT_SUMMARY.

Phase 7 (view conversion): chrome via utils.strings; the per-card ID
line stays code-composed (card IDs never localize).
"""
from __future__ import annotations
import streamlit as st
from utils.session_logic import parse_rpe_scores
from utils.strings import tr


def render_summary(user: dict) -> None:
    flags = st.session_state.get("session_flags", {})
    rpe_str = flags.get("last_rpe", "")
    daily = flags.get("last_daily", [])
    rpe_map = parse_rpe_scores(rpe_str)
    avg = (sum(rpe_map.values()) / len(rpe_map)) if rpe_map else 0
    st.title(tr("summary.title"))
    st.balloons()
    st.write(tr("summary.completed").format(n=len(daily)))
    if rpe_map:
        st.write(tr("summary.avg_rpe").format(avg=f"{avg:.1f}"))
        for cid, score in rpe_map.items():
            st.write(f"- {cid}: {score}/5")
    if st.button(tr("summary.return_hub"), key="btn_return_hub",
                 width="stretch", type="primary"):
        st.session_state["session_flags"] = {}
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()