"""Phase 3 — pure state-machine contract. UI routing in app.py MUST go through
transition()/is_valid(). Modifying the transition set requires updating
test_state_machine.py and sign-off."""
VALID_TRANSITIONS = {
    ("UNAUTHENTICATED", "login_register"): "CHECK_ONBOARDING",
    ("CHECK_ONBOARDING", "sarc_f_incomplete"): "ONBOARDING_SARC_F",
    ("CHECK_ONBOARDING", "assessment_complete"): "DAILY_HUB",
    ("ONBOARDING_SARC_F", "complete_assessment"): "DAILY_HUB",
    ("DAILY_HUB", "start_breathing"): "BREATHING_SESSION",
    ("BREATHING_SESSION", "start_exercises"): "EXERCISE_SESSION",
    ("EXERCISE_SESSION", "submit_workout"): "WORKOUT_SUMMARY",
    ("WORKOUT_SUMMARY", "return_to_hub"): "DAILY_HUB",
    ("DAILY_HUB", "start_weekly_review"): "DAY_7_REST",
    ("DAY_7_REST", "complete_weekly_review"): "DAILY_HUB",
    ("PROGRAM_COMPLETE", "retake_assessment"): "ONBOARDING_SARC_F",
    ("PROGRAM_COMPLETE", "restart_current_level"): "DAILY_HUB",
    ("DAY_7_REST", "complete_program"): "PROGRAM_COMPLETE",
}


def transition(current: str, action: str) -> str:
    key = (current, action)
    if key not in VALID_TRANSITIONS:
        raise ValueError(f"invalid transition: {current!r} + {action!r}")
    return VALID_TRANSITIONS[key]


def is_valid(current: str, action: str) -> bool:
    return (current, action) in VALID_TRANSITIONS