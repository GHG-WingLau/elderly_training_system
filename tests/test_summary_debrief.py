"""Phase 9, Step 1 — the summary debriefing contracts.

Drives the real flow (login → hub → breathing → training with default
RPE selections → submit) and asserts the debrief: personalized
congratulation, body-region bullets with TITLES (card codes and
numeric "/5" ratings are gone), the DB-derived sessions-this-week
counter, the reassurance line, and the RPE word rendered from the
descriptors the user tapped (default Moderate).
"""
from tests.helpers_e2e import (_click, login, make_app, rendered_text,
                               seed_user)


def test_summary_debrief(tmp_path, monkeypatch):
    email = "debrief@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    _click(at, "Start Today's Workout")
    at.run()
    _click(at, "Start Exercises")
    at.run()
    _click(at, "Submit Workout")
    at.run()
    text = rendered_text(at)
    assert "Well done, tester" in text            # personalized congrats
    assert "Today you trained:" in text           # the debrief lead
    assert "• Your" in text                       # body-region bullets
    assert "of 6" in text                         # DB-derived counter
    assert "Moderate" in text                     # default RPE word
    assert "/5" not in text                       # numeric ratings gone
    assert "nothing you need to change" in text   # auto-adjust reassurance