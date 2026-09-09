"""Localization — locale registry, resolution, and wiring contracts.

Pure-core tests (hermetic; resolve_locale is a pure function — the
compute_final_level precedent) plus AppTest/DB wiring tests that
monkeypatch SUPPORTED_LOCALES to a two-locale registry (a down-scoped
simulation; all three locales now ship — the shipped-set tests in
test_registry_invariants cover the real registry).

AppTest notes (1.62): selectbox options are raw locale codes
(format_func affects display only), so .select() takes the raw value;
the picker's query-param write rides the same proven channel as ?t=
(every auth E2E writes it). If .select-by-raw-value or .value
misbehaves on 1.62's AppTest, report it — these convert to a
param-injection form (the bookmark-tip test documents the same
fallback for query-param readback).

v4 (picker-label selector fix — constraint 3 localization extension):
the ACTIVATION change (utils.locale v4) renders the picker label via
tr() — the label is chrome that LOCALIZES, so under a zh session it is
「語言 / Language」, not "Language". The v4 delivery changed the
rendered label without updating this file's selector in the same
change; test_boot_resolves_profile_locale_into_picker then failed on
'Language' after the profile was adopted — the exact failure the rule
exists to prevent. Fix: the boot test locates the picker by the
SESSION locale's label, read data-driven from ui_strings
(_picker_label_for — the consent-checkbox pattern).
"""
import json
from pathlib import Path

from utils.locale import (DEFAULT_LOCALE, LOCALES, LOCALE_DISPLAY,
                          PICKER_LABEL, SUPPORTED_LOCALES, resolve_locale)
from tests.helpers_e2e import db, login, make_app, register, seed_user
from db import queries

TWO = ("en", "zh-HK")  # simulated two-locale registry
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _picker_label_for(locale: str) -> str:
    """The picker label as rendered under `locale` — the label localizes
    (utils.locale v4), so selectors must follow the session locale
    (constraint 3 localization extension: a localized label IS a label
    change; test selectors update with it)."""
    name = ("ui_strings.json" if locale == "en"
            else f"ui_strings.{locale}.json")
    doc = json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))
    return doc["picker"]["label"]


def test_registry_invariants():
    assert set(SUPPORTED_LOCALES) <= set(LOCALES)
    assert DEFAULT_LOCALE in SUPPORTED_LOCALES
    for code in SUPPORTED_LOCALES:
        assert LOCALE_DISPLAY[code].strip()
    assert PICKER_LABEL.strip()


def test_resolve_defaults_when_nothing_set():
    assert resolve_locale(None, None, None, supported=TWO) == "en"


def test_resolve_url_param_is_highest_precedence():
    assert resolve_locale("zh-HK", "en", "en", supported=TWO) == "zh-HK"


def test_resolve_unsupported_url_param_falls_through():
    assert resolve_locale("zh-TW", "en", "en", supported=TWO) == "en"
    assert resolve_locale("fr", "zh-HK", "en", supported=TWO) == "zh-HK"


def test_resolve_session_over_profile():
    assert resolve_locale(None, "zh-HK", "en", supported=TWO) == "zh-HK"


def test_resolve_profile_when_no_session():
    assert resolve_locale(None, None, "zh-HK", supported=TWO) == "zh-HK"


def test_resolve_unsupported_profile_falls_to_default():
    assert resolve_locale(None, None, "zh-TW", supported=("en",)) == "en"


def test_resolve_default_when_all_unsupported():
    assert resolve_locale("zh-TW", "zh-TW", "zh-TW", supported=("en",)) == "en"


def _find_selectbox(at, label):
    for el in at.selectbox:
        if getattr(el, "label", None) == label:
            return el
    raise AssertionError(f"selectbox not found: {label!r}")


def test_picker_selection_persists_profile_locale(tmp_path, monkeypatch):
    """7.4.2 + 7.4.3: a hub selection writes session + ?lang= and
    persists users.locale (DB verified via raw read — version-agnostic).
    The session is 'en' at find-time (no profile set), so the EN picker
    label applies here."""
    monkeypatch.setattr("utils.locale.SUPPORTED_LOCALES", ("en", "zh-HK"))
    email = "locale-persist@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)  # hub; picker visible (two supported locales)
    _find_selectbox(at, PICKER_LABEL).select("zh-HK")
    at.run()
    conn = db()
    row = conn.execute("SELECT locale FROM users WHERE email = %s",
                       (email,)).fetchone()
    assert row["locale"] == "zh-HK"


def test_boot_resolves_profile_locale_into_picker(tmp_path, monkeypatch):
    """7.4.3: with no ?lang= and no in-session choice, the profile locale
    is adopted at boot (pins the v2 fix: a pre-auth default pass must
    NOT pin the session against the profile). The session locale is
    zh-HK at assertion time, so the picker renders its zh label —
    located data-driven (see module docstring v4 note)."""
    monkeypatch.setattr("utils.locale.SUPPORTED_LOCALES", ("en", "zh-HK"))
    email = "locale-boot@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 1")
    queries.set_user_locale(email=email, locale="zh-HK")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert _find_selectbox(at, _picker_label_for("zh-HK")).value == "zh-HK"


def test_registration_captures_session_locale(tmp_path, monkeypatch):
    """Decision (a): create_user records the registration-session locale
    into users.locale ("en" in EN-default runs; a zh-HK registration
    captures zh-HK — pinned end-to-end by test_e2e_locale.py)."""
    email = "locale-reg@test"
    at = make_app(tmp_path, monkeypatch)
    register(at, email)
    conn = db()
    row = conn.execute("SELECT locale FROM users WHERE email = %s",
                       (email,)).fetchone()
    assert row["locale"] == "en"