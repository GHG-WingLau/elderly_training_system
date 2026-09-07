"""LOCKED COMPONENT — sign-off required to modify.
Orchestrates onboarding:
Step 0 red-flag screening (any flag -> Level 0 fast-path to step 4)
Step 1 SARC-F (sarc_f_assessment)
Step 2 baseline (baseline_timers)
Step 3 support preference
Step 4 confirmation -> update_user_level -> DAILY_HUB
compute_final_level() is a pure function (no Streamlit) and is the unit-tested
safety contract for this phase.

Phase 6 label-readability change (#14, signed off per user direction —
presentation only, no logic): Step 0 gains a guidance line under its
subheader ("Check all boxes that apply to you. If none apply, leave them
unchecked and press Continue."). This states EXISTING behavior (empty
submission is valid and advances to SARC-F) — no flow change. Buttons use
width="stretch" per the pinned 1.62 unified sizing API.
"""
from __future__ import annotations
from typing import Optional
import streamlit as st
from db import queries
from utils.assessment_logic import calculate_total_score, assign_level_with_preference
from components.locked.sarc_f_assessment import render_sarc_f_form
from components.locked.baseline_timers import render_baseline_form

RED_FLAGS = [
    ("chest_pain", "Chest pain"),
    ("joint_replacement_under_6mo", "Joint replacement (< 6 months)"),
    ("uncontrolled_bp_over_160_100", "Uncontrolled BP (> 160/100)"),
    ("two_or_more_recent_falls", "2+ falls in past 12 months"),
]
PREFERENCE_OPTIONS = [
    ("Level 0", "Chair-Assisted"),
    ("Level 1", "Seated"),
    ("Level 2", "Supported Standing"),
    ("Level 3", "Independent Standing"),
    ("Level 4", "Dynamic Standing"),
]


def compute_final_level(red_flags: Optional[str], sarc_f: Optional[int],
                        calf_score: Optional[int], balance_score: Optional[int],
                        chair_stand_score: Optional[int], age: int,
                        preference_level: Optional[str] = None
                        ) -> tuple[str, Optional[int]]:
    """Pure safety contract. Returns (final_level, total_score).
    Red-flag fast-path (scores None) -> ('Level 0', None)."""
    if red_flags and None in (sarc_f, calf_score, balance_score, chair_stand_score):
        return "Level 0", None
    total = calculate_total_score(sarc_f, calf_score, balance_score,
                                  chair_stand_score)
    level = assign_level_with_preference(total, sarc_f, age, red_flags,
                                         preference_level)
    return level, total


def _flags_to_str(flags: dict) -> str:
    return ",".join(code for code, _ in RED_FLAGS if flags.get(code))


def render_onboarding_wizard(user: dict) -> None:
    st.title("Welcome! Let's complete your assessment.")
    st.session_state.setdefault("onboarding_step", 0)
    st.session_state.setdefault("onboarding_data", {})
    data = st.session_state["onboarding_data"]
    step = st.session_state["onboarding_step"]
    age, sex = user["age"], user.get("sex", "U")

    # Step 0 — red flags
    if step == 0:
        st.subheader("Step 1 of 4 — Safety screening")
        st.caption("Check all boxes that apply to you. If none apply, "
                   "leave them unchecked and press Continue.")
        with st.form("red_flags_form"):
            flags = {code: st.checkbox(label, key=f"rf_{code}")
                     for code, label in RED_FLAGS}
            submitted = st.form_submit_button("Continue", width="stretch")
            if submitted:
                data["red_flags"] = _flags_to_str(flags)
                st.session_state["onboarding_step"] = 4 if data["red_flags"] else 1
                st.rerun()
            return

    # Step 1 — SARC-F
    if step == 1:
        result = render_sarc_f_form()
        if result:
            data["sarc_f"] = result["sarc_f_score"]
            data["sarc_f_items"] = result["item_scores"]
            st.session_state["onboarding_step"] = 2
            st.rerun()
            return

    # Step 2 — baseline
    if step == 2:
        result = render_baseline_form(sex)
        if result:
            data.update(result)
            st.session_state["onboarding_step"] = 3
            st.rerun()
            return

    # Step 3 — preference
    if step == 3:
        st.subheader("Step 4 of 4 — Your comfort preference")
        with st.form("preference_form"):
            pref_label = st.selectbox("Your comfort preference",
                                      [lbl for _, lbl in PREFERENCE_OPTIONS],
                                      key="pref_label")
            submitted = st.form_submit_button("Continue", width="stretch")
            if submitted:
                data["preference_level"] = next(
                    lvl for lvl, lbl in PREFERENCE_OPTIONS if lbl == pref_label)
                st.session_state["onboarding_step"] = 4
                st.rerun()
                return

    # Step 4 — confirmation
    if step == 4:
        st.subheader("Review and confirm")
        rf = data.get("red_flags", "")
        st.write(f"**Red flags:** {rf if rf else 'None'}")
        if rf:
            st.warning("A safety red flag was reported. Your level is set to "
                       "**Level 0 (Chair-Assisted)** for your safety.")
            final_level, total = "Level 0", None
        else:
            sarc_f = data["sarc_f"]
            calf, bal, chair = (data["calf_score"], data["balance_score"],
                                data["chair_stand_score"])
            pref = data.get("preference_level")
            total = calculate_total_score(sarc_f, calf, bal, chair)
            final_level = assign_level_with_preference(total, sarc_f, age, rf, pref)
            st.write(f"**SARC-F:** {sarc_f}/10 · **Calf:** {calf} · "
                     f"**Balance:** {bal} · **Chair-stand:** {chair}")
            st.write(f"**Total:** {total}/16 (lower = higher function)")
            if pref:
                st.write(f"**Your preference:** {pref}")
        st.write(f"### Assigned level: {final_level}")
        if st.button("Confirm and start training", width="stretch",
                     type="primary"):
            queries.update_user_level(
                email=user["email"], level=final_level, total_score=total,
                sarc_f=data.get("sarc_f"), calf=data.get("calf_score"),
                balance=data.get("balance_score"),
                chair_stand=data.get("chair_stand_score"),
                red_flags=data.get("red_flags", ""),
            )
            user["level"] = final_level
            user["total_score"] = total
            st.session_state["user"] = user
            st.session_state["current_state"] = "DAILY_HUB"
            for k in ("onboarding_step", "onboarding_data"):
                st.session_state.pop(k, None)
            st.rerun()