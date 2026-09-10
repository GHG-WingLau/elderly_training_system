"""LOCKED COMPONENT — sign-off required to modify.
Orchestrates onboarding:
Step 0 red-flag screening (any flag -> Level 0 fast-path to step 4)
Step 1 SARC-F (sarc_f_assessment)
Step 2 baseline (baseline_timers)
Step 3 support preference
Step 4 confirmation -> update_user_level -> DAILY_HUB
compute_final_level() is a pure function (no Streamlit) and is the unit-tested
safety contract for this phase.

Phase 6 #14 / Phase 7 / Phase 9 history: guidance caption; tr-driven
chrome; preference selectbox index-mapped; red-flag labels data-driven;
baseline recorded at confirmation.

Phase 10 (signed off — FLOW-ONLY; safety contract, scoring, and clinical
semantics untouched): BACK NAVIGATION. _previous_step derives the
target (Step 0 for the red-flag fast path, Step 3 for the normal path);
entered values persist by widget key.

Phase 10 v2 (user feedback — usability; signed off via the thread):
(a) the Back button is COMPACT (auto width) and renders BELOW each
step's primary action — the full-width top placement read as out of
place; the 48px CSS floor still applies.
(b) CONFIRMATION-PAGE READABILITY: the red-flags line shows localized
LABELS, never the stored codes (the raw-code display was a genuine
defect); per-measure score lines carry plain-language descriptions; a
score legend; an intro line that also teaches Back; a level note that
states existing behavior (weekly autoregulation). The compact
wizard.metrics line goes DORMANT (localized; kept in ui_strings). The
new copy is PROVISIONAL EN — the next translation round migrates it
(7 strings).

v8 (translation round landed): the seven confirmation strings render
from ui_strings (tr-driven; constants retained as EN contract values).
The app remains 100% localized.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import streamlit as st
from db import queries
from utils.assessment_logic import calculate_total_score, assign_level_with_preference
from components.locked.sarc_f_assessment import get_rubrics, render_sarc_f_form
from components.locked.baseline_timers import render_baseline_form
from utils.strings import tr, level_display
from utils.locale import get_locale

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
# EN contract constants — equal the ui_strings EN values (rendered via
# tr since the Phase 10 v2 translation round; the tests import none of
# these — parity/no-leakage checks cover them).
CONFIRM_INTRO = ("Here is a summary of your answers. Press Back to "
                 "change anything, then Confirm to begin.")
MEASURE_SARCF = "SARC-F: {score} / 10 — how easy everyday movements feel"
MEASURE_CALF = "Calf: {score} / 2 — leg muscle size"
MEASURE_BALANCE = "Balance: {score} / 2 — standing on one leg"
MEASURE_CHAIR = "Chair-stand: {score} / 2 — getting up from a chair"
SCORE_LEGEND = "0 is the best score on every measure."
LEVEL_NOTE = ("The exercises will start at a level that matches how you "
              "feel today, and the program adjusts as you go.")

def _red_flag_pairs() -> list[tuple[str, str]]:
    """Red-flag (code, label) pairs for the ACTIVE locale.

    Labels from the locale rubrics' red_flag_labels when present (zh
    locale files); the EN constant pairs otherwise. Codes and order
    always come from RED_FLAGS (canonical)."""
    labels = get_rubrics().get("red_flag_labels")
    if labels:
        return [(code, labels[code]) for code, _ in RED_FLAGS]
    return RED_FLAGS


def _red_flag_labels_str(rf: str) -> str:
    """Localized DISPLAY labels for the stored red-flag codes ("" when
    none). The DB keeps codes (contract); the confirmation page shows
    labels — the v2 readability fix (raw codes were shown before)."""
    if not rf:
        return ""
    label_by_code = dict(_red_flag_pairs())
    return ", ".join(label_by_code.get(code.strip(), code.strip())
                     for code in rf.split(","))


def _previous_step(data: dict, step: int) -> int:
    """PURE (unit-tested): the Back target for the given step.

    Steps 1–3 -> the previous step. Step 4 -> DERIVED: Step 0 when the
    wizard arrived via the red-flag fast path (red flags set, no SARC-F
    data — the mistake-recovery path), Step 3 for the normal path."""
    if step in (1, 2, 3):
        return step - 1
    if data.get("red_flags") and "sarc_f" not in data:
        return 0          # fast path: back to the safety screen
    return 3              # normal path: back to the preference step


def _back_button(data: dict, step: int) -> None:
    """Compact Back affordance, rendered BELOW the step's primary
    action (v2: the full-width top placement read as out of place).
    No-op on Step 0. Auto width — the 48px target floor still applies
    via the button CSS."""
    if step == 0:
        return
    if st.button(tr("wizard.back"), key=f"wizard_back_{step}"):
        st.session_state["onboarding_step"] = _previous_step(data, step)
        st.rerun()


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
        _back_button(data, step)
        if result:
            data["sarc_f"] = result["sarc_f_score"]
            data["sarc_f_items"] = result["item_scores"]
            st.session_state["onboarding_step"] = 2
            st.rerun()
            return

    # Step 2 — baseline
    if step == 2:
        result = render_baseline_form(sex)
        _back_button(data, step)
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
                                      key=f"pref_label_{get_locale()}")
            submitted = st.form_submit_button(tr("wizard.continue"), width="stretch")
            if submitted:
                # Index-mapped: the stored value stays the EN level string.
                data["preference_level"] = f"Level {pref_labels.index(pref_label)}"
                st.session_state["onboarding_step"] = 4
                st.rerun()
                return
        _back_button(data, step)

    # Step 4 — confirmation (v2 readability layout)
    if step == 4:
        st.subheader(tr("wizard.review"))
        st.write(tr("wizard.confirm_intro"))
        rf = data.get("red_flags", "")
        st.write(tr("wizard.red_flags_label").format(
            red_flags=_red_flag_labels_str(rf)
            or tr("wizard.red_flags_none")))
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
            st.write(tr("wizard.measure_sarcf").format(score=sarc_f))
            st.write(tr("wizard.measure_calf").format(score=calf))
            st.write(tr("wizard.measure_balance").format(score=bal))
            st.write(tr("wizard.measure_chair").format(score=chair))
            st.write(tr("wizard.total").format(total=total))
            st.caption(tr("wizard.score_legend"))
            if pref:
                st.write(tr("wizard.preference_summary").format(
                    preference=level_display(pref)))
        st.write(tr("wizard.assigned_level").format(
            level=level_display(final_level)))
        st.caption(tr("wizard.level_note"))
        if st.button(tr("wizard.confirm"), width="stretch",
                     type="primary"):
            if "calf_cm" in data:
                # Phase 9 Step 2: record the raw baseline measures
                # (red-flag fast-path has none — guard by key presence).
                queries.record_baseline(
                    email=user["email"],
                    baseline={
                        "calf_cm": data["calf_cm"],
                        "sls_left_sec": data["sls_left_sec"],
                        "sls_right_sec": data["sls_right_sec"],
                        "chair_stand_reps": data["chair_stand_reps"],
                        "measured_at": datetime.now(timezone.utc).isoformat(),
                    })
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
        _back_button(data, step)