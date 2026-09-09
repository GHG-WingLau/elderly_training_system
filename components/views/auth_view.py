"""Authentication view — password auth + consent gate + remember me.

Phase 5 hardening history retained: explicit keys on all form INPUT
widgets; st.rerun() raised OUTSIDE the form context; submit buttons take
no key, located by label in tests.

Step 2a: password login (uniform failure message — no user enumeration;
legacy no-password accounts rejected); registration with Password +
Confirm (NIST 800-63B length policy) and DUPLICATE-EMAIL GATE before
create_user; consent gate from data/consent.json (v1.1) — micro-copy,
full text expander + download (mime= — see 2a.1 hotfix), harmonized
checkbox required; consent_version + consent_accepted_at recorded.

Step 2b (mechanism (a), prototype-driven): login checkbox
REMEMBER_LABEL (default ON — team decision; flip value=True to change)
creates a 30-day session token and places it in st.query_params["t"];
the URL then carries the token (bookmark = stay logged in); app.py's
try_restore_session() restores at boot. Unchecked = plain session.

Phase 7 localization (skeleton): language picker call added below the
title — INERT until a second locale ships (utils.locale gates on
SUPPORTED_LOCALES). View strings remain EN until the code-side
UI-strings source is signed off (§5 census).

Phase 7 decision (a): registration records the session locale
(users.locale) alongside the consent evidence columns — pinned by
test_registration_captures_session_locale.

Phase 7 (loader step): the consent gate renders the ACTIVE LOCALE's
document — per-locale caches; EN keeps the base filename; locales use
consent.{locale}.json. A zh-HK registration therefore records
consent_version "v1.1-zh-HK" (§7.8) once zh-HK activates. The
checkbox label is data-driven (the helpers_e2e precedent survives
localization for free).

Phase 7 (view conversion): all chrome renders via utils.strings (tr);
SEX option labels localize, their VALUES (U/M/F) never do;
REMEMBER_LABEL and SEX_OPTIONS are retained as the EN contract
constants — the rendered labels come from ui_strings. EN rendering is
byte-identical.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st

from db import queries
from utils.auth import MIN_PASSWORD_LENGTH, TOKEN_PARAM, hash_password, verify_password
from utils.locale import get_locale, render_language_picker, safe_locale
from utils.strings import tr

SEX_OPTIONS = {"Prefer not to say": "U", "Male": "M", "Female": "F"}

REMEMBER_LABEL = "Keep me logged in on this device (30 days)"

_CONSENT_DIR = (Path(__file__).resolve().parent.parent.parent / "data")
_consent_caches: dict[str, dict] = {}


def _load_consent() -> dict:
    locale = safe_locale()
    if locale not in _consent_caches:
        name = "consent.json" if locale == "en" else f"consent.{locale}.json"
        with open(_CONSENT_DIR / name) as f:
            _consent_caches[locale] = json.load(f)
    return _consent_caches[locale]


def _sex_options() -> dict:
    """Locale display labels -> stored values (U/M/F never localize)."""
    return {tr("auth.sex_option_unspecified"): "U",
            tr("auth.sex_option_male"): "M",
            tr("auth.sex_option_female"): "F"}


def render_auth() -> None:
    st.title(tr("auth.title"))
    render_language_picker()  # 7.4 — inert while only "en" ships
    consent = _load_consent()
    micro = consent["micro"]
    tab_return, tab_new = st.tabs([tr("auth.tab_returning"),
                                   tr("auth.tab_new")])

    with tab_return:
        login_user = None
        remember = True
        with st.form("login"):
            email = st.text_input(tr("auth.email"), key="login_email")
            password = st.text_input(tr("auth.password"), key="login_password",
                                     type="password")
            remember = st.checkbox(tr("auth.remember_label"), value=True,
                                   key="login_remember")
            submitted = st.form_submit_button(tr("auth.login_button"),
                                              width="stretch")
            if submitted:
                user = (queries.get_user(email.strip())
                        if email.strip() else None)
                if (user and user.get("password_hash")
                        and verify_password(password,
                                            user["password_hash"])):
                    login_user = user
                else:
                    st.error(tr("auth.login_error"))
        if login_user is not None:
            if remember:
                token = queries.create_session_token(login_user["email"])
                st.query_params[TOKEN_PARAM] = token
            st.session_state.update(
                authenticated=True, user_email=login_user["email"],
                user=login_user, current_state="CHECK_ONBOARDING")
            st.rerun()

    with tab_new:
        do_register = False
        # Consent block (micro-copy + full text + download) above the form
        st.write(f"**{micro['heading']}**")
        st.write(micro["lead"])
        for point in micro["points"]:
            st.write(f"• {point}")
        with st.expander(tr("auth.terms_expander")):
            st.write(consent["full_text"])
            st.download_button(
                tr("auth.terms_download"),
                data=consent["full_text"],
                file_name=f"terms_{consent['version']}.txt",
                mime="text/plain", width="stretch")
        with st.form("register"):
            email = st.text_input(tr("auth.email_req"), key="reg_email")
            username = st.text_input(tr("auth.username_req"), key="reg_user")
            age = st.number_input(tr("auth.age_req"), min_value=18,
                                  max_value=110, value=65, step=1, key="reg_age")
            sex_label = st.selectbox(
                tr("auth.sex_label"),
                list(_sex_options()), key="reg_sex")
            st.caption(tr("auth.password_caption").format(
                min_length=MIN_PASSWORD_LENGTH,
                required_note=micro["required_note"]))
            password = st.text_input(tr("auth.password_req"), key="reg_password",
                                     type="password")
            confirm = st.text_input(tr("auth.confirm_req"),
                                    key="reg_password2", type="password")
            consent_ok = st.checkbox(micro["checkbox_label"],
                                     key="reg_consent")
            submitted = st.form_submit_button(tr("auth.register_button"),
                                              width="stretch")
            if submitted:
                error = None
                if not email.strip() or not username.strip():
                    error = tr("auth.err_required")
                elif len(password) < MIN_PASSWORD_LENGTH:
                    error = tr("auth.err_pw_length").format(
                        min_length=MIN_PASSWORD_LENGTH)
                elif password != confirm:
                    error = tr("auth.err_pw_mismatch")
                elif not consent_ok:
                    error = tr("auth.err_consent")
                elif queries.get_user(email.strip()) is not None:
                    error = tr("auth.err_exists")
                if error:
                    st.error(error)
                else:
                    do_register = True
        if do_register:
            sex = _sex_options()[sex_label]
            queries.create_user(
                email.strip(), username.strip(), int(age), sex,
                password_hash=hash_password(password),
                consent_version=consent["version"],
                consent_accepted_at=datetime.now(timezone.utc),
                locale=get_locale())  # Phase 7 decision (a)
            user = queries.get_user(email.strip())
            st.session_state.update(
                authenticated=True, user_email=user["email"],
                user=user, current_state="CHECK_ONBOARDING")
            st.rerun()