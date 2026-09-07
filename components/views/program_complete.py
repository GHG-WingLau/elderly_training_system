"""Phase 4 — PROGRAM_COMPLETE view: summary + cycle restart actions."""
from __future__ import annotations
import streamlit as st

from db import queries


def _restart(user: dict, reassess: bool) -> None:
    email = user["email"]
    queries.advance_cycle(email)
    st.session_state["user"] = queries.get_user(email)   # refresh cached user
    for k in ("onboarding_step", "onboarding_data", "regression_ack"):
        st.session_state.pop(k, None)
    st.session_state["current_state"] = (
        "ONBOARDING_SARC_F" if reassess else "DAILY_HUB")
    st.rerun()


def render_program_complete(user: dict) -> None:
    st.title("🎉 Program Complete!")
    st.balloons()
    n = queries.count_completed_workouts(user["email"], user["current_cycle"])
    st.write(f"You completed **{n} workouts** across 5 weeks, "
             f"{user['username']} — outstanding work!")
    st.write("Choose how you'd like to continue:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Retake Assessment & Restart", key="btn_retake", width="stretch"):
            _restart(user, reassess=True)
    with c2:
        if st.button("Restart with Current Level", key="btn_restart", width="stretch"):
            _restart(user, reassess=False)