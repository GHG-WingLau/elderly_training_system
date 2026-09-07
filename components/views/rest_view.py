"""Phase 4 — DAY_7_REST view: recovery checks, reflection, auto-regulation."""
from __future__ import annotations
import streamlit as st

from db import queries
from utils.session_logic import get_session_position
from utils.autoregulation_logic import day7_plan
from utils.breathing_logic import get_safety_text
from utils.exercise_logic import format_prescription


def render_rest_view(user: dict) -> None:
    pos = get_session_position(user["email"])
    if not pos["is_rest_day"] or pos["is_program_complete"]:
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()
        return
    week, cycle = pos["week"], pos["cycle"]
    plan = day7_plan(user["email"], cycle, week, user["level"])
    safety = get_safety_text()

    st.title(f"Rest & Review — Week {week}")
    st.info(f"🪑 {safety['chair_standard']}")
    st.write("Light movement only. Complete the checks below to finish your week.")

    if plan["avg_rpe"] is not None:
        st.metric("Average effort this week (RPE)", f"{plan['avg_rpe']:.1f} / 5")
    if week == 0:
        st.caption("Induction week — checks are recorded as your baseline. "
                   "No adjustment is applied to Week 1.")
    elif plan["classification"] == "high":
        st.warning("This week felt hard — next week's volume will be reduced.")
    elif plan["classification"] == "low":
        st.success("This week felt easy — next week's volume will increase slightly.")
    else:
        st.info("This week felt just right — volume stays the same.")
    if plan["next_week_prescription"] is not None:
        st.write("**Next week's prescription:** "
                 f"{format_prescription(plan['next_week_prescription'])}")

    # Regression prompt (mandatory acknowledgment)
    ack_ok = True
    if plan["regression_to"] is not None:
        st.warning("⚠️ You've reported high effort for **two weeks in a row**. "
                   f"For your comfort and safety, your level will be adjusted "
                   f"from **{user['level']}** to **Level {plan['regression_to']}**.")
        ack_ok = st.checkbox(
            f"I understand my level will change to Level {plan['regression_to']}.",
            key="regression_ack")
    elif plan["hard_streak"]:
        st.warning("Two hard weeks in a row — you are already at the safest "
                   "level (Level 0). Your volume will be reduced instead.")

    with st.form("rest_form"):
        recall = st.number_input(
            "How many exercises can you remember learning this week?",
            0, 6, 0, key="rest_recall")
        reflection = st.text_area("How does your body feel? (optional)",
                                  key="rest_reflection")
        sts = st.number_input("Chair sit-to-stand — cycles in 15 seconds",
                              0, 30, 0, key="rest_sts")
        sls_l = st.number_input("Single-leg stance — left (sec)",
                                0.0, 120.0, 0.0, 0.5, key="rest_sls_l")
        sls_r = st.number_input("Single-leg stance — right (sec)",
                                0.0, 120.0, 0.0, 0.5, key="rest_sls_r")
        submitted = st.form_submit_button("Complete Weekly Review", width="stretch", type="primary")
    if not submitted:
        return
    if not ack_ok:
        st.error("Please confirm the level change above to continue.")
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