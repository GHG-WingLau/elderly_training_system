"""Phase 4 — DAY_7_REST view: recovery checks, reflection, auto-regulation.

Phase 7 (view conversion): chrome via utils.strings; level-bearing lines
(regression warning, acknowledgment, hard-streak) compose level_display
names — the accepted descriptor gains materialize for EN here. Widget
keys unchanged.
"""
from __future__ import annotations
import streamlit as st

from db import queries
from utils.session_logic import get_session_position
from utils.autoregulation_logic import day7_plan
from utils.breathing_logic import get_safety_text
from utils.exercise_logic import format_prescription
from utils.strings import tr, level_display


def render_rest_view(user: dict) -> None:
    pos = get_session_position(user["email"])
    if not pos["is_rest_day"] or pos["is_program_complete"]:
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()
        return
    week, cycle = pos["week"], pos["cycle"]
    plan = day7_plan(user["email"], cycle, week, user["level"])
    safety = get_safety_text()

    st.title(tr("rest.title").format(week=week))
    st.info(f"🪑 {safety['chair_standard']}")
    st.write(tr("rest.light_movement"))

    if plan["avg_rpe"] is not None:
        st.metric(tr("rest.metric_label"), f"{plan['avg_rpe']:.1f} / 5")
    if week == 0:
        st.caption(tr("rest.induction"))
    elif plan["classification"] == "high":
        st.warning(tr("rest.hard"))
    elif plan["classification"] == "low":
        st.success(tr("rest.easy"))
    else:
        st.info(tr("rest.moderate"))
    if plan["next_week_prescription"] is not None:
        st.write(tr("rest.next_prescription").format(
            prescription=format_prescription(plan["next_week_prescription"])))

    # Regression prompt (mandatory acknowledgment)
    ack_ok = True
    if plan["regression_to"] is not None:
        new_level_value = f"Level {plan['regression_to']}"
        st.warning(tr("rest.regression_warning").format(
            current_level=level_display(user["level"]),
            new_level=level_display(new_level_value)))
        ack_ok = st.checkbox(
            tr("rest.regression_ack").format(n=level_display(new_level_value)),
            key="regression_ack")
    elif plan["hard_streak"]:
        st.warning(tr("rest.hard_streak").format(n=level_display("Level 0")))

    with st.form("rest_form"):
        recall = st.number_input(tr("rest.recall"), 0, 6, 0, key="rest_recall")
        reflection = st.text_area(tr("rest.reflection"), key="rest_reflection")
        sts = st.number_input(tr("rest.sts"), 0, 30, 0, key="rest_sts")
        sls_l = st.number_input(tr("rest.sls_left"), 0.0, 120.0, 0.0, 0.5,
                                key="rest_sls_l")
        sls_r = st.number_input(tr("rest.sls_right"), 0.0, 120.0, 0.0, 0.5,
                                key="rest_sls_r")
        submitted = st.form_submit_button(tr("rest.submit"), width="stretch",
                                          type="primary")
    if not submitted:
        return
    if not ack_ok:
        st.error(tr("rest.ack_error"))
        return

    queries.upsert_rest_assessment(user["email"], cycle, week, int(recall),
                                   reflection, int(sts), int(sls_l), int(sls_r))
    if plan["regression_to"] is not None:
        new_level = f"Level {plan['regression_to']}"
        queries.set_user_level(user["email"], new_level)
        user["level"] = new_level
        st.session_state["user"] = user
    st.session_state.pop("regression_ack", None)
    st.session_state["current_state"] = (
        "PROGRAM_COMPLETE" if week == 4 else "DAILY_HUB")
    st.rerun()