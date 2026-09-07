"""LOCKED COMPONENT — sign-off required to modify.
Renders baseline measures: calf circumference, single-leg stance (L/R),
30-second chair stand. Sub-scores computed via utils.assessment_logic
(sex-aware rubric scoring). Widget labels below are mandated for AppTest
stability — do not rename without sign-off.
Phase 5 note (NON-CLINICAL, key-only change): explicit keys added to all form
INPUT widgets to avoid auto-generated $$WIDGET_ID session-state keys,
which break AppTest replay. Submit buttons take no key (unsupported on
minimum-validated Streamlit); located by label in tests.

Changes #7/#8 (NON-CLINICAL: entry granularity + presentation; signed off):
- #7: number_input step 0.1 -> 0.5 for calf (cm) and both single-leg
  stance (sec); chair stand unchanged (integer reps). Scoring untouched
  (continuous band comparisons; 0.5-grid reachability verified).
- #8: procedure illustrations above each input via utils.assets.render_image
  (placeholder fallback; width="stretch"); paths as module constants.

Change #13 (approved baseline copy; signed off): descriptions + patient
instructions render from data/baseline_instructions.json (data, not code);
loader mirrors the sarc_f_assessment cache precedent; placement follows
the #5 house pattern; shared SLS description rendered once, above the
LEFT block only (the approved right-side instruction itself states the
repeat — no copy invented or duplicated); reads are direct (fail-loud),
enforced by tests/test_copy_contract.py. The page-level DRAFT caption is
RETAINED pending the #8 illustration clinical review.

Change #14 (label readability; signed off per user direction —
presentation only): the four input labels are now verb-first
("Enter your ..."), naming what is measured (time/count) and
disambiguating legs; constant NAMES (LABEL_*) are unchanged so any
imports survive; values are pinned by tests/test_copy_contract.py.
Per constraint 3, any test locating these widgets by label updates in
the same change — expected zero (the wizard is not AppTest-driven per
the Phase-5 E2E strategy decision).
"""
from __future__ import annotations
from typing import Optional
import json
from pathlib import Path
import streamlit as st
from utils.assessment_logic import score_calf, score_sls, score_chair_stand
from utils.assets import render_image

LABEL_CALF = "Enter your calf circumference (cm)"
LABEL_SLS_L = "Enter your single-leg stance time — left leg (sec)"
LABEL_SLS_R = "Enter your single-leg stance time — right leg (sec)"
LABEL_CHAIR = "Enter your 30-second chair stand count (reps)"

# Procedure illustrations (change #8) — presentation assets; module constants
# per the RED_FLAGS precedent in onboarding_wizard.
ASSESS_CALF = "assets/exercises/ASSESS_Calf_Measurement.jpeg"
ASSESS_SLS_L = "assets/exercises/ASSESS_SLS_Left_Foot_Stand.jpeg"
ASSESS_SLS_R = "assets/exercises/ASSESS_SLS_Right_Foot_Stand.jpeg"
ASSESS_CHAIR = "assets/exercises/ASSESS_Sit_To_Stand.jpeg"

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_bi_cache: Optional[dict] = None


def _load_instructions() -> dict:
    """Approved baseline copy (data, not code). Cached per process —
    restart the dev server after editing the JSON."""
    global _bi_cache
    if _bi_cache is None:
        with open(DATA_DIR / "baseline_instructions.json") as f:
            _bi_cache = json.load(f)
    return _bi_cache


def render_baseline_form(sex: str) -> Optional[dict]:
    """Return sub-scores + raw measures on submit, else None."""
    data = _load_instructions()
    m = data["measures"]
    st.subheader("Baseline Measures")
    st.caption("DRAFT — clinical review required. Use a sturdy, non-wheeled "
               "chair on a non-slip surface.")
    st.write(data["intro"])
    with st.form("baseline_form"):
        st.write(m["calf"]["description"])
        render_image(ASSESS_CALF, label="Calf circumference measurement",
                     caption="Calf circumference measurement")
        st.write(m["calf"]["instruction"])
        calf_cm = st.number_input(LABEL_CALF, min_value=20.0,
                                  max_value=60.0,
                                  value=34.0, step=0.5, format="%.1f",
                                  key="base_calf")
        st.write(m["single_leg_stance"]["description"])
        render_image(ASSESS_SLS_L, label="Single-leg stance — left",
                     caption="Single-leg stance — left")
        st.write(m["single_leg_stance"]["instruction_left"])
        sls_l = st.number_input(LABEL_SLS_L, min_value=0.0, max_value=120.0,
                                value=10.0, step=0.5, format="%.1f",
                                key="base_sls_l")
        # Shared SLS description is NOT repeated here: the approved
        # right-side instruction itself states the repeat — no copy is
        # invented or duplicated (verbatim-only discipline).
        render_image(ASSESS_SLS_R, label="Single-leg stance — right",
                     caption="Single-leg stance — right")
        st.write(m["single_leg_stance"]["instruction_right"])
        sls_r = st.number_input(LABEL_SLS_R, min_value=0.0, max_value=120.0,
                                value=10.0, step=0.5, format="%.1f",
                                key="base_sls_r")
        st.write(m["chair_stand"]["description"])
        render_image(ASSESS_CHAIR, label="30-second chair stand",
                     caption="30-second chair stand")
        st.write(m["chair_stand"]["instruction"])
        chair = st.number_input(LABEL_CHAIR, min_value=0, max_value=60,
                                value=12, step=1, key="base_chair")
        submitted = st.form_submit_button("Continue", width="stretch")
        if not submitted:
            return None
        return {
            "calf_cm": calf_cm,
            "sls_left_sec": sls_l,
            "sls_right_sec": sls_r,
            "chair_stand_reps": chair,
            "calf_score": score_calf(calf_cm, sex),
            "balance_score": score_sls(max(sls_l, sls_r)),  # UPST: best of L/R
            "chair_stand_score": score_chair_stand(chair, sex),
        }