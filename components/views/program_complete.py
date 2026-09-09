"""Phase 4 — PROGRAM_COMPLETE view: summary + cycle restart actions.

Phase 7 (view conversion): chrome via utils.strings; button keys
unchanged.
"""
from __future__ import annotations
import streamlit as st

from db import queries
from utils.strings import tr


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
    st.title(tr("program_complete.title"))
    st.balloons()
    n = queries.count_completed_workouts(user["email"], user["current_cycle"])
    st.write(tr("program_complete.congrats").format(
        n=n, username=user["username"]))
    st.write(tr("program_complete.choose"))
    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("program_complete.retake"), key="btn_retake",
                     width="stretch"):
            _restart(user, reassess=True)
    with c2:
        if st.button(tr("program_complete.restart"), key="btn_restart",
                     width="stretch"):
            _restart(user, reassess=False)