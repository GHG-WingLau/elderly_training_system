"""Phase 1 safety contract — pure-function tests for onboarding level
computation. Hermetic (no Streamlit runtime, no DB). This IS the change
contract for the locked wizard; modifying the ladder requires updating these
rows AND clinical sign-off."""
import pytest
from components.locked.onboarding_wizard import compute_final_level


@pytest.mark.parametrize(
    "red_flags,sarc_f,calf,bal,chair,age,pref,exp_level,exp_total",
    [
        # SARC-F clinical override (>= 4) -> Level 0
        ("", 6, 0, 0, 0, 70, None, "Level 0", 6),
        ("", 4, 0, 0, 0, 62, None, "Level 0", 4),
        # Total >= 8 -> Level 0
        ("", 3, 2, 2, 1, 70, None, "Level 0", 8),
        # Age >= 80 -> Level 0
        ("", 0, 0, 0, 0, 80, None, "Level 0", 0),
        # total 3, age 70 -> Level 3 ; age 76 -> Level 2
        ("", 2, 1, 0, 0, 70, None, "Level 3", 3),
        ("", 2, 1, 0, 0, 76, None, "Level 2", 3),
        # total 5, age 70 -> Level 2 ; age 76 -> Level 1
        ("", 3, 1, 1, 0, 70, None, "Level 2", 5),
        ("", 3, 1, 1, 0, 76, None, "Level 1", 5),
        # total 1 -> Level 4
        ("", 1, 0, 0, 0, 65, None, "Level 4", 1),
        # Red flag with scores present -> Level 0
        ("chest_pain", 0, 0, 0, 0, 70, None, "Level 0", 0),
        # Red-flag fast path (scores None) -> Level 0, total None
        ("two_or_more_recent_falls", None, None, None, None, 70, None, "Level 0", None),
        # Preference never raises
        ("", 2, 1, 0, 0, 70, "Level 4", "Level 3", 3),
        # Preference lowers by one step only
        ("", 2, 1, 0, 0, 70, "Level 0", "Level 2", 3),
        # Preference equal -> no change
        ("", 2, 1, 0, 0, 70, "Level 3", "Level 3", 3),
    ],
)
def test_compute_final_level(red_flags, sarc_f, calf, bal, chair, age,
                             pref, exp_level, exp_total):
    level, total = compute_final_level(red_flags, sarc_f, calf, bal, chair, age, pref)
    assert level == exp_level
    assert total == exp_total