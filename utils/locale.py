"""Locale registry, resolution, and picker — Phase 7 localization (7.4).

Query-parameter persistence with an "en" fallback. Precedence (highest
wins), resolved on every main() pass:
  1. ?lang= URL parameter (validated against SUPPORTED_LOCALES)
  2. st.session_state["locale"] (the in-session explicit choice)
  3. users.locale (authenticated user's persisted profile preference)
  4. "en" (default — NEVER written to the session)

v2: resolve_locale's `supported` default is read at CALL time
    (monkeypatchable); boot_resolve_locale no longer writes the default
    into the session (a pre-auth "en" pass must not pin the session
    against a non-en profile after login — 7.4.3).

v3: the picker's selectbox key is LOCALE-TAGGED
    (f"locale_picker_{current}") — the RPE position-tagged-key precedent.
    Streamlit persists widget state by key and IGNORES `index` on
    remount, so a picker first mounted on the auth page (value "en")
    kept displaying "en" after the profile locale was adopted at login
    (desync caught by test_boot_resolves_profile_locale_into_picker;
    real-browser defect, not a test artifact).

v4 (ACTIVATION — team sign-off, localization thread): SUPPORTED_LOCALES
    ships all three locales; the picker is LIVE on the auth page and
    the hub. The picker label and display names render from
    ui_strings (each locale file carries all three display names).
    zh registrations record consent_version "v1.1-zh-HK"/"v1.1-zh-TW"
    (§7.8) and users.locale (decision (a)) through the flows already
    wired.

v5 (accessibility, localization thread): the picker LABEL is a FIXED
    bilingual wayfinding string — "Select your preferred language /
    請選擇你的語言" — IDENTICAL in every locale (a language switcher
    must be findable before the user understands the UI language —
    the cold-start problem). PICKER_LABEL is now the label itself and
    equals every locale file's picker.label, so the selector contract
    holds in every session. Display names remain per-locale autonyms;
    the label is pinned identical by test_picker_label_is_fixed_bilingual.

?lang= naming an unknown locale is ignored (not scrubbed; the ?t=
dead-token scrub precedent applies to secrets, not preferences). The
URL always overrides the profile at boot; the URL never writes the
profile. set_locale is the single write path for an explicit selection
(session + ?lang= always; users.locale when authenticated).
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

LOCALES = ("en", "zh-HK", "zh-TW")
SUPPORTED_LOCALES = ("en", "zh-HK", "zh-TW")   # ACTIVATED — all three ship
DEFAULT_LOCALE = "en"
LANG_PARAM = "lang"

# The picker label: a FIXED bilingual wayfinding string — identical in
# every locale file (accessibility: findable before the user
# understands the UI language). Mirrors every ui_strings picker.label.
PICKER_LABEL = "Select your preferred language / 請選擇你的語言"
# Display names remain per-locale autonyms (each locale file carries all
# three); this EN-side constant mirrors the EN file's picker section.
LOCALE_DISPLAY = {"en": "English",
                  "zh-HK": "繁體中文（香港）",
                  "zh-TW": "繁體中文（台灣）"}


def resolve_locale(url_lang: Optional[str], session_lang: Optional[str],
                   profile_lang: Optional[str],
                   supported: Optional[tuple] = None) -> str:
    """Pure resolution core (hermetic — compute_final_level precedent).

    `supported` defaults to the module-level SUPPORTED_LOCALES READ AT
    CALL TIME (a def-time default would bind the original tuple).
    """
    if supported is None:
        supported = SUPPORTED_LOCALES
    if url_lang in supported:
        return url_lang
    if session_lang in supported:
        return session_lang
    if profile_lang in supported:
        return profile_lang
    return DEFAULT_LOCALE


def get_locale() -> str:
    return st.session_state.get("locale", DEFAULT_LOCALE)


def safe_locale() -> str:
    """Locale for call sites without a guaranteed script-run context
    (data loaders, bare pytest): the session value when a session
    exists, else the default. Never raises — outside a script run there
    IS no session, and the default is the correct answer there."""
    try:
        return get_locale()
    except Exception:
        return DEFAULT_LOCALE


def boot_resolve_locale(user: Optional[dict]) -> str:
    """app.py main() calls this every pass (idempotent), AFTER
    try_restore_session (so the profile is available) and BEFORE any
    render — including the unauthenticated path.

    The session key is written ONLY for an explicit resolution (URL
    param or profile adoption) — never for the default: a pre-auth "en"
    pass must not pin the session against a non-en profile after login
    (session outranks profile; 7.4.3).
    """
    resolved = resolve_locale(
        st.query_params.get(LANG_PARAM),
        st.session_state.get("locale"),
        (user or {}).get("locale"),
    )
    if (resolved != DEFAULT_LOCALE
            and st.session_state.get("locale") != resolved):
        st.session_state["locale"] = resolved
    return resolved


def set_locale(code: str, persist_profile: bool = False) -> None:
    """Single write path for an explicit user selection. Writes the
    session key + query param always; the profile only when
    persist_profile AND the session is authenticated (hub vs auth page).
    Caller follows with st.rerun() (the ?t= write pattern)."""
    if code not in SUPPORTED_LOCALES:
        raise ValueError(f"unsupported locale: {code!r}")
    st.session_state["locale"] = code
    st.query_params[LANG_PARAM] = code
    if persist_profile and st.session_state.get("authenticated"):
        from db import queries  # local import — no import cycle
        queries.set_user_locale(st.session_state["user_email"], code)
        user = st.session_state.get("user")
        if user is not None:
            user["locale"] = code
            st.session_state["user"] = user


def render_language_picker() -> None:
    """Auth page + daily hub call site.

    Label: the FIXED bilingual wayfinding string (v5 — identical in
    every locale, so it is findable pre-comprehension). Display names
    render from ui_strings for the ACTIVE locale (local import —
    utils.strings imports utils.locale at module level; a module-level
    back-import would be circular). The selectbox key stays
    LOCALE-TAGGED (v3 desync fix).
    """
    if len(SUPPORTED_LOCALES) < 2:
        return
    from utils.strings import tr
    display_keys = {"en": "picker.display_en",
                    "zh-HK": "picker.display_zh_hk",
                    "zh-TW": "picker.display_zh_tw"}
    codes = list(SUPPORTED_LOCALES)
    current = get_locale()
    index = codes.index(current) if current in codes else 0
    chosen = st.selectbox(
        tr("picker.label"),
        options=codes,
        index=index,
        format_func=lambda c: tr(display_keys[c]),
        key=f"locale_picker_{current}",  # locale-tagged — v3 desync fix
    )
    if chosen != current:
        set_locale(chosen, persist_profile=True)
        st.rerun()