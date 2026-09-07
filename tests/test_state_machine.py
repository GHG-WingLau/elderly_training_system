"""Phase 3 contract — state-machine transitions (pure, no Streamlit)."""
import pytest
from utils.state_machine import transition, is_valid


@pytest.mark.parametrize("current,action,expected", [
    ("UNAUTHENTICATED", "login_register", "CHECK_ONBOARDING"),
    ("CHECK_ONBOARDING", "sarc_f_incomplete", "ONBOARDING_SARC_F"),
    ("CHECK_ONBOARDING", "assessment_complete", "DAILY_HUB"),
    ("ONBOARDING_SARC_F", "complete_assessment", "DAILY_HUB"),
    ("DAILY_HUB", "start_breathing", "BREATHING_SESSION"),
    ("BREATHING_SESSION", "start_exercises", "EXERCISE_SESSION"),
    ("EXERCISE_SESSION", "submit_workout", "WORKOUT_SUMMARY"),
    ("WORKOUT_SUMMARY", "return_to_hub", "DAILY_HUB"),
    ("DAILY_HUB", "start_weekly_review", "DAY_7_REST"),
    ("DAY_7_REST", "complete_weekly_review", "DAILY_HUB"),
    ("PROGRAM_COMPLETE", "retake_assessment", "ONBOARDING_SARC_F"),
    ("PROGRAM_COMPLETE", "restart_current_level", "DAILY_HUB"),
    ("DAY_7_REST", "complete_program", "PROGRAM_COMPLETE"),
])
def test_valid_transitions(current, action, expected):
    assert transition(current, action) == expected
    assert is_valid(current, action)


@pytest.mark.parametrize("current,action", [
    ("DAILY_HUB", "submit_workout"),
    ("EXERCISE_SESSION", "return_to_hub"),
    ("BREATHING_SESSION", "start_breathing"),
    ("WORKOUT_SUMMARY", "start_exercises"),
    ("UNAUTHENTICATED", "start_breathing"),
    ("DAY_7_REST", "start_breathing"),
    ("DAILY_HUB", "complete_program"),
    ("WORKOUT_SUMMARY", "complete_program"),
])
def test_invalid_transitions_raise(current, action):
    assert not is_valid(current, action)
    with pytest.raises(ValueError):
        transition(current, action)