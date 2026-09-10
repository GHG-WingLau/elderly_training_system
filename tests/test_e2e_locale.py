"""Per-locale E2E smoke (decision 7.5) — the zh-HK activation check.

v3: + test_sex_default_follows_locale — the Phase 10 v3 fix (the sex
selectbox key is locale-tagged; before it, a live locale switch left
the widget displaying the stale EN option).

[Phase 7 history unchanged — see prior docstring: data-driven label
reads; the REAL picker; the EN base-filename rule; zh-TW rides the
data/completeness contracts.]
"""
from __future__ import annotations

import json
from pathlib import Path

from tests.helpers_e2e import (_click, _find, db, make_app,
                               rendered_text, seed_user)

DATA = Path(__file__).resolve().parent.parent / "data"
HK = "zh-HK"


def _tr(locale: str, key: str) -> str:
    filename = ("ui_strings.json" if locale == "en"
                else f"ui_strings.{locale}.json")
    doc = json.loads((DATA / filename).read_text(encoding="utf-8"))
    section, _, leaf = key.partition(".")
    return doc[section][leaf]


def _consent_checkbox_label(locale: str) -> str:
    filename = ("consent.json" if locale == "en"
                else f"consent.{locale}.json")
    doc = json.loads((DATA / filename).read_text(encoding="utf-8"))
    return doc["micro"]["checkbox_label"]


def _select_locale(at, locale: str) -> None:
    """Switch via the REAL picker (the auth page renders EN at this
    moment — the picker label comes from the active locale's strings)."""
    box = _find(at.selectbox, _tr("en", "picker.label"))
    box.select(locale)
    at.run()


def test_zh_hk_registration_smoke(tmp_path, monkeypatch):
    """Register through the zh-HK UI: the wizard renders in zh; the
    evidence columns record locale zh-HK + consent_version v1.1-zh-HK
    (DB-verified — version-agnostic)."""
    at = make_app(tmp_path, monkeypatch)
    _select_locale(at, HK)          # picker writes ?lang= + session
    _find(at.text_input, _tr(HK, "auth.email_req")).input("zh-reg@test")
    _find(at.text_input, _tr(HK, "auth.username_req")).input("測試用戶")
    _find(at.number_input, _tr(HK, "auth.age_req")).set_value(70)
    _find(at.selectbox, _tr(HK, "auth.sex_label")).select(
        _tr(HK, "auth.sex_option_female"))
    _find(at.text_input, _tr(HK, "auth.password_req")).input("testpass123")
    _find(at.text_input, _tr(HK, "auth.confirm_req")).input("testpass123")
    _find(at.checkbox, _consent_checkbox_label(HK)).check()
    _click(at, _tr(HK, "auth.register_button"))
    at.run()
    # Fresh account -> onboarding wizard renders IN zh-HK.
    assert "歡迎你" in rendered_text(at)
    # Evidence columns (decision (a) + §7.8).
    conn = db()
    row = conn.execute(
        "SELECT locale, consent_version, consent_accepted_at "
        "FROM users WHERE email = %s", ("zh-reg@test",)).fetchone()
    assert row["locale"] == HK
    assert row["consent_version"] == "v1.1-zh-HK"
    assert row["consent_accepted_at"] is not None


def test_zh_hk_login_hub_smoke(tmp_path, monkeypatch):
    """Login through the zh-HK UI: the hub renders zh, including the
    level display-name map (等級 2 (扶物站立))."""
    email = "zh-hub@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    at = make_app(tmp_path, monkeypatch)
    _select_locale(at, HK)
    _find(at.text_input, _tr(HK, "auth.email")).input(email)
    _find(at.text_input, _tr(HK, "auth.password")).input("testpass123")
    _click(at, _tr(HK, "auth.login_button"))
    at.run()
    assert "歡迎" in rendered_text(at)
    assert "等級 2 (扶物站立)" in rendered_text(at)


def test_sex_default_follows_locale(tmp_path, monkeypatch):
    """Phase 10 v3: after a live locale switch, the sex selectbox
    defaults to the LOCALIZED first option — not the stale EN string
    (widget state persists by key while the option list changes with
    the locale; the key is locale-tagged — the picker/RPE class)."""
    at = make_app(tmp_path, monkeypatch)
    _select_locale(at, HK)
    box = _find(at.selectbox, _tr(HK, "auth.sex_label"))
    assert box.value == _tr(HK, "auth.sex_option_unspecified")