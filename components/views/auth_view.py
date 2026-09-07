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
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st

from db import queries
from utils.auth import MIN_PASSWORD_LENGTH, TOKEN_PARAM, hash_password, verify_password

SEX_OPTIONS = {"Prefer not to say": "U", "Male": "M", "Female": "F"}

REMEMBER_LABEL = "Keep me logged in on this device (30 days)"

_CONSENT_PATH = (Path(__file__).resolve().parent.parent.parent
                 / "data" / "consent.json")
_consent_cache: Optional[dict] = None


def _load_consent() -> dict:
    global _consent_cache
    if _consent_cache is None:
        with open(_CONSENT_PATH) as f:
            _consent_cache = json.load(f)
    return _consent_cache


def render_auth() -> None:
    st.title("🏃 Elderly Online Training System")
    consent = _load_consent()
    micro = consent["micro"]
    tab_return, tab_new = st.tabs(["Returning User", "New User"])

    with tab_return:
        login_user = None
        remember = True
        with st.form("login"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", key="login_password",
                                     type="password")
            remember = st.checkbox(REMEMBER_LABEL, value=True,
                                   key="login_remember")
            submitted = st.form_submit_button("Log In", width="stretch")
            if submitted:
                user = (queries.get_user(email.strip())
                        if email.strip() else None)
                if (user and user.get("password_hash")
                        and verify_password(password,
                                            user["password_hash"])):
                    login_user = user
                else:
                    st.error("Email or password is incorrect.")
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
        with st.expander("Read the full Terms of Participation, Health "
                         "Waiver, and Privacy Notice"):
            st.write(consent["full_text"])
            st.download_button(
                "Download the full terms",
                data=consent["full_text"],
                file_name=f"terms_{consent['version']}.txt",
                mime="text/plain", width="stretch")
        with st.form("register"):
            email = st.text_input("Email *", key="reg_email")
            username = st.text_input("Username *", key="reg_user")
            age = st.number_input("Age *", min_value=18, max_value=110,
                                  value=65, step=1, key="reg_age")
            sex_label = st.selectbox(
                "Sex (used for calf & chair-stand norms)",
                list(SEX_OPTIONS), key="reg_sex")
            st.caption(f"Choose a password of at least "
                       f"{MIN_PASSWORD_LENGTH} characters. "
                       f"({micro['required_note']} below.)")
            password = st.text_input("Password *", key="reg_password",
                                     type="password")
            confirm = st.text_input("Confirm password *",
                                    key="reg_password2", type="password")
            consent_ok = st.checkbox(micro["checkbox_label"],
                                     key="reg_consent")
            submitted = st.form_submit_button("Create Account",
                                              width="stretch")
            if submitted:
                error = None
                if not email.strip() or not username.strip():
                    error = "Email and username are required."
                elif len(password) < MIN_PASSWORD_LENGTH:
                    error = (f"Password must be at least "
                             f"{MIN_PASSWORD_LENGTH} characters.")
                elif password != confirm:
                    error = "Passwords do not match."
                elif not consent_ok:
                    error = ("Please confirm the Health Waiver and "
                             "Privacy Terms to register.")
                elif queries.get_user(email.strip()) is not None:
                    error = ("An account with this email already exists. "
                             "Please log in instead.")
                if error:
                    st.error(error)
                else:
                    do_register = True
        if do_register:
            sex = SEX_OPTIONS[sex_label]
            queries.create_user(
                email.strip(), username.strip(), int(age), sex,
                password_hash=hash_password(password),
                consent_version=consent["version"],
                consent_accepted_at=datetime.now(timezone.utc))
            user = queries.get_user(email.strip())
            st.session_state.update(
                authenticated=True, user_email=user["email"],
                user=user, current_state="CHECK_ONBOARDING")
            st.rerun()