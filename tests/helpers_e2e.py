"""Shared AppTest helpers for E2E tests.
STRATEGY (v4.1): AppTest is used only for flows that do NOT UI-drive the
multi-step wizard. Onboarded users are SEEDED directly via the DB layer.
Widget lookup matches the .label attribute by iteration.

Phase 6: strategy A — ONE shared Postgres (conftest sets DATABASE_URL and
truncates per test). Step 2a updates: seed_user sets a password;
register() fills Password/Confirm + checks the consent checkbox (label
read from data/consent.json — single source, no duplication); login()
uses Email + Password (username field retired).
"""
from pathlib import Path
import json
import os

import psycopg
from psycopg.rows import dict_row
import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"
SEED_PASSWORD = "testpass123"


def _consent_checkbox_label() -> str:
    p = Path(__file__).resolve().parent.parent / "data" / "consent.json"
    return json.loads(p.read_text())["micro"]["checkbox_label"]


def _find(widget_list, label):
    for el in widget_list:
        if getattr(el, "label", None) == label:
            return el
    raise AssertionError(
        f"widget not found with label={label!r}; available labels: "
        f"{[getattr(e, 'label', None) for e in widget_list]}")


def _find_button(at, label):
    for accessor in ("form_submit_button", "button"):
        wl = getattr(at, accessor, None)
        if wl is None:
            continue
        for el in wl:
            if getattr(el, "label", None) == label:
                return el
    raise AssertionError(f"button not found: {label!r}")


def _click(at, label):
    _find_button(at, label).click()


def has_button(at, label) -> bool:
    for accessor in ("form_submit_button", "button"):
        wl = getattr(at, accessor, None)
        if wl is None:
            continue
        for el in wl:
            if getattr(el, "label", None) == label:
                return True
    return False


def rendered_text(at) -> str:
    parts: list[str] = []
    for attr in ("title", "header", "subheader", "markdown", "text",
                 "caption", "info", "success", "warning", "error"):
        try:
            for el in getattr(at, attr):
                parts.append(getattr(el, "value", "") or "")
        except Exception:
            pass
    return "\n".join(parts)


def make_app(tmp_path=None, monkeypatch=None):
    """Fresh AppTest against the shared test Postgres (truncated per test
    by conftest). tmp_path/monkeypatch accepted and ignored (signature
    compatibility with historical call sites)."""
    st.cache_resource.clear()
    at = AppTest.from_file(str(APP_PATH), default_timeout=20)
    at.run()
    return at


def seed_user(email, level, age=70, sex="F",
              sarc_f=0, calf=0, balance=0, chair=0):
    """Create an already-onboarded user directly via the DB layer.
    Keyword args mandatory (signature-drift guard). Call AFTER make_app."""
    from utils.auth import hash_password
    from db import queries
    queries.create_user(email=email, username="tester", age=age, sex=sex,
                        password_hash=hash_password(SEED_PASSWORD))
    queries.update_user_level(
        email=email, level=level, total_score=sarc_f + calf + balance + chair,
        sarc_f=sarc_f, calf=calf, balance=balance,
        chair_stand=chair, red_flags="")


def register(at, email, age=70, sex="Female"):
    _find(at.text_input, "Email *").input(email)
    _find(at.text_input, "Username *").input("tester")
    _find(at.number_input, "Age *").set_value(age)
    _find(at.selectbox, "Sex (used for calf & chair-stand norms)").select(sex)
    _find(at.text_input, "Password *").input(SEED_PASSWORD)
    _find(at.text_input, "Confirm password *").input(SEED_PASSWORD)
    _find(at.checkbox, _consent_checkbox_label()).check()
    _click(at, "Create Account")
    at.run()


def login(at, email, password=SEED_PASSWORD):
    _find(at.text_input, "Email").input(email)
    _find(at.text_input, "Password").input(password)
    _click(at, "Log In")
    at.run()


def db():
    """Fresh raw-read connection to the test Postgres (dict rows,
    autocommit)."""
    return psycopg.connect(os.environ["DATABASE_URL"],
                           row_factory=dict_row, autocommit=True)