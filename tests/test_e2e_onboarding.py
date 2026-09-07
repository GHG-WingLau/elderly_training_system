"""E2E — registration, duplicate gate, consent evidence, routing, and the
remember-me token lifecycle (create on login, delete on logout).

Boot-restore itself is not AppTest-driven (query-param support unverified
on 1.62 — see tests/test_auth.py docstring); the token ROWS are asserted
here via raw reads, and the reload behavior is the manual QA check.

Dialect note (2b.1 fix): assertion SQL aggregates nothing — filter +
COUNT. SQLite tolerates MAX(boolean) via numeric coercion; Postgres has
no max(boolean) — the SQLite-ism was the 2b delivery's one-line defect,
caught by this run."""
from tests.helpers_e2e import (make_app, register, login, seed_user, db,
                               rendered_text, has_button, _click)
from components.views.auth_view import REMEMBER_LABEL


def test_registration_creates_user_and_lands_on_wizard(tmp_path,
                                                       monkeypatch):
    at = make_app(tmp_path, monkeypatch)
    register(at, "e2e1@test", age=70, sex="Female")
    assert "Step 1 of 4" in rendered_text(at)  # wizard safety screening
    row = db().execute(
        "SELECT sex, level, consent_version, consent_accepted_at "
        "FROM users WHERE email=%s", ("e2e1@test",)).fetchone()
    assert row["sex"] == "F"
    assert row["level"] is None  # assessment not yet done
    assert row["consent_version"] == "v1.1"   # consent evidence recorded
    assert row["consent_accepted_at"] is not None


def test_duplicate_registration_rejected(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    at = make_app(tmp_path, monkeypatch)
    register(at, "e2e1@test")
    at2 = make_app(tmp_path, monkeypatch)  # fresh session, same DB
    register(at2, "e2e1@test")
    assert "already exists" in rendered_text(at2)
    n = db().execute(
        "SELECT COUNT(*) AS n FROM users WHERE email=%s",
        ("e2e1@test",)).fetchone()["n"]
    assert n == 1  # no second account, no silent overwrite
    at3 = make_app(tmp_path, monkeypatch)
    login(at3, "e2e1@test")
    assert "Step 1 of 4" in rendered_text(at3)  # level None -> wizard


def test_level0_user_login_routes_to_hub(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    seed_user("e2e2@test", "Level 0", sarc_f=6)
    at = make_app(tmp_path, monkeypatch)  # fresh session, same DB
    login(at, "e2e2@test")
    assert "Level 0" in rendered_text(at)
    assert has_button(at, "Start Today's Workout")


def test_level4_user_login_routes_to_hub(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    seed_user("e2e3@test", "Level 4")
    at = make_app(tmp_path, monkeypatch)
    login(at, "e2e3@test")
    assert "Level 4" in rendered_text(at)
    assert has_button(at, "Start Today's Workout")


def test_login_with_remember_creates_session_token(tmp_path, monkeypatch):
    """Remember checkbox defaults ON — login must leave exactly one live
    30-day session row (filter + COUNT: two live rows -> 2, one expired
    row -> 0, both fail)."""
    email = "e2e6@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert "Level 2" in rendered_text(at)  # logged in, at the hub
    n = db().execute(
        "SELECT COUNT(*) AS n FROM sessions "
        "WHERE user_email=%s AND expires_at > now()", (email,)).fetchone()["n"]
    assert n == 1


def test_login_without_remember_creates_no_token(tmp_path, monkeypatch):
    email = "e2e7@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    at = make_app(tmp_path, monkeypatch)
    _find_checkbox(at, REMEMBER_LABEL).uncheck()
    login(at, email)
    assert "Level 1" in rendered_text(at)
    n = db().execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE user_email=%s",
        (email,)).fetchone()["n"]
    assert n == 0


def test_logout_deletes_token_and_returns_to_login(tmp_path, monkeypatch):
    email = "e2e8@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 3")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert db().execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE user_email=%s",
        (email,)).fetchone()["n"] == 1
    _click(at, "Log out")
    at.run()
    assert has_button(at, "Log In")           # back at the auth page
    assert at.session_state["authenticated"] is False
    assert db().execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE user_email=%s",
        (email,)).fetchone()["n"] == 0        # token row deleted


def _find_checkbox(at, label):
    for el in at.checkbox:
        if getattr(el, "label", None) == label:
            return el
    raise AssertionError(f"checkbox not found: {label!r}")