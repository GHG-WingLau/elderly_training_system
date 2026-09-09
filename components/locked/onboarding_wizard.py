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

Phase 7 (localization; signed off via the localization thread): Step 0
red-flag LABELS are data-driven from the active-locale rubrics
(red_flag_labels; the consent-checkbox precedent). RED_FLAGS stays as
the canonical CODE list (order + rf_{code} widget keys are
locale-independent) and the EN label fallback — EN rubrics carries codes
only.

Phase 7 ACTIVATION (team sign-off, localization thread): all wizard
chrome renders via utils.strings. PREFERENCE_OPTIONS is retained as the
EN contract constant — the selectbox renders the locale's preference
labels, INDEX-MAPPED to Level {i} (codes/indices never localize; the
stored value is unchanged). The confirmation step composes
level_display names ({n} tokens per the level-composition decision);
the preference summary renders the level display name of the stored
value. Logic, flow, widget keys, and compute_final_level are untouched.
"""
from __future__ import annotations
from typing import Optional
import streamlit as st
from db import queries
from utils.assessment_logic import calculate_total_score, assign_level_with_preference
from components.locked.sarc_f_assessment import get_rubrics, render_sarc_f_form
from components.locked.baseline_timers import render_baseline_form
from utils.strings import tr, level_display

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


def _red_flag_pairs() -> list[tuple[str, str]]:
    """Red-flag (code, label) pairs for the ACTIVE locale.

    Labels from the locale rubrics' red_flag_labels when present (zh
    locale files); the EN constant pairs otherwise. Codes and order
    always come from RED_FLAGS (canonical)."""
    labels = get_rubrics().get("red_flag_labels")
    if labels:
        return [(code, labels[code]) for code, _ in RED_FLAGS]
    return RED_FLAGS


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
    st.title(tr("wizard.title"))
    st.session_state.setdefault("onboarding_step", 0)
    st.session_state.setdefault("onboarding_data", {})
    data = st.session_state["onboarding_data"]
    step = st.session_state["onboarding_step"]
    age, sex = user["age"], user.get("sex", "U")

    # Step 0 — red flags
    if step == 0:
        st.subheader(tr("wizard.step1"))
        st.caption(tr("wizard.step0_caption"))
        with st.form("red_flags_form"):
            flags = {code: st.checkbox(label, key=f"rf_{code}")
                     for code, label in _red_flag_pairs()}
            submitted = st.form_submit_button(tr("wizard.continue"), width="stretch")
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
        st.subheader(tr("wizard.step4"))
        with st.form("preference_form"):
            pref_labels = [tr(f"wizard.preference_{i}") for i in range(5)]
            pref_label = st.selectbox(tr("wizard.preference_label"),
                                      pref_labels,
                                      key="pref_label")
            submitted = st.form_submit_button(tr("wizard.continue"), width="stretch")
            if submitted:
                # Index-mapped: the stored value stays the EN level string.
                data["preference_level"] = f"Level {pref_labels.index(pref_label)}"
                st.session_state["onboarding_step"] = 4
                st.rerun()
                return

    # Step 4 — confirmation
    if step == 4:
        st.subheader(tr("wizard.review"))
        rf = data.get("red_flags", "")
        st.write(tr("wizard.red_flags_label").format(
            red_flags=rf if rf else tr("wizard.red_flags_none")))
        if rf:
            st.warning(tr("wizard.red_flag_warning").format(
                n=level_display("Level 0")))
            final_level, total = "Level 0", None
        else:
            sarc_f = data["sarc_f"]
            calf, bal, chair = (data["calf_score"], data["balance_score"],
                                data["chair_stand_score"])
            pref = data.get("preference_level")
            total = calculate_total_score(sarc_f, calf, bal, chair)
            final_level = assign_level_with_preference(total, sarc_f, age, rf, pref)
            st.write(tr("wizard.metrics").format(
                sarc_f=sarc_f, calf=calf, balance=bal, chair_stand=chair))
            st.write(tr("wizard.total").format(total=total))
            if pref:
                st.write(tr("wizard.preference_summary").format(
                    preference=level_display(pref)))
        st.write(tr("wizard.assigned_level").format(
            level=level_display(final_level)))
        if st.button(tr("wizard.confirm"), width="stretch",
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