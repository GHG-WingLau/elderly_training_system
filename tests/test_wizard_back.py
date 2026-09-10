"""Phase 10 — wizard back-navigation + confirmation-display contracts.

_previous_step: pure derivation (the wizard itself remains deliberately
un-driven by AppTest — the Phase-5 st.form replay limitation; flow
verified by the manual-QA line).
_red_flag_labels_str: the confirmation page shows localized LABELS,
never the stored codes (the raw-code display was the v2 readability
defect)."""
from components.locked.onboarding_wizard import (
    _previous_step, _red_flag_labels_str)


def test_previous_step_derivation():
    normal = {"red_flags": "", "sarc_f": 4, "calf_score": 1}
    fast = {"red_flags": "chest_pain"}          # no SARC-F -> fast path
    assert _previous_step(normal, 1) == 0
    assert _previous_step(normal, 2) == 1
    assert _previous_step(normal, 3) == 2
    assert _previous_step(normal, 4) == 3        # normal path
    assert _previous_step(fast, 4) == 0          # red-flag fast path


def test_red_flag_labels_display():
    assert _red_flag_labels_str("") == ""
    assert _red_flag_labels_str("chest_pain") == "Chest pain"
    assert _red_flag_labels_str(
        "chest_pain,joint_replacement_under_6mo") == (
        "Chest pain, Joint replacement (< 6 months)")