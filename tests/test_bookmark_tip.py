"""tests/test_bookmark_tip.py — hub bookmark reminder targeting.

The tip renders only when the remember-me token is in the URL. Both
cases driven through the real login flow; token presence is the app's
own signal (st.query_params), set by auth_view on remember-login.

Note: if the "shown" test fails while the app works in a real browser,
the cause is AppTest query-param READBACK on 1.62 (writes are proven —
the 2b token-row tests pass); report it and the test converts to a
constant/param-injection form. Real-browser behavior is unaffected."""
from tests.helpers_e2e import (make_app, login, seed_user, rendered_text)
from components.views.auth_view import REMEMBER_LABEL
from components.views.daily_hub import BOOKMARK_TIP


def _find_checkbox(at, label):
    for el in at.checkbox:
        if getattr(el, "label", None) == label:
            return el
    raise AssertionError(f"checkbox not found: {label!r}")


def test_tip_shown_after_login_with_remember(tmp_path, monkeypatch):
    email = "tip1@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)  # remember defaults ON -> token in URL
    assert "Level 2" in rendered_text(at)          # at the hub
    assert "bookmark this page" in rendered_text(at)  # tip visible


def test_tip_not_shown_without_remember(tmp_path, monkeypatch):
    email = "tip2@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    at = make_app(tmp_path, monkeypatch)
    _find_checkbox(at, REMEMBER_LABEL).uncheck()
    login(at, email)  # no token -> advice wouldn't work -> no tip
    assert "Level 1" in rendered_text(at)
    assert "bookmark this page" not in rendered_text(at)