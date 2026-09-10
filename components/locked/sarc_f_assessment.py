"""LOCKED COMPONENT — sign-off required to modify.
Renders the 5-item SARC-F questionnaire. Item text and options are NEVER
hardcoded — always read from the ACTIVE LOCALE's rubrics file.

Phase 7 (localization; signed off via the localization thread):
locale-aware loader — per-locale caches; EN keeps the base filename;
locales use scoring_rubrics.{locale}.json. Scoring remains
score = options.index(choice): option ORDER is the scoring contract
(3 options per item, order per the signed translation docs, pinned by
tests/test_locale_data.py). Thresholds are NOT read here —
utils.assessment_logic deliberately reads the EN rubrics for all
threshold scoring (locale-independent by construction: the
never-localize rule enforced in code, not only by tests).

Phase 7 ACTIVATION (team sign-off, localization thread): subheader/
caption/submit chrome renders via utils.strings ("Continue" is the
shared wizard string — one key, four call sites). EN rendering is
byte-identical; the form id and sarcf_{name} widget keys are unchanged.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import streamlit as st

from utils.locale import safe_locale
from utils.strings import tr

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_rubrics_caches: dict[str, dict] = {}


def _filename(locale: str) -> str:
    return ("scoring_rubrics.json" if locale == "en"
            else f"scoring_rubrics.{locale}.json")


def _load_rubrics() -> dict:
    locale = safe_locale()
    if locale not in _rubrics_caches:
        with open(DATA_DIR / _filename(locale), encoding="utf-8") as f:
            _rubrics_caches[locale] = json.load(f)
    return _rubrics_caches[locale]


def get_rubrics() -> dict:
    """Active-locale rubrics for DISPLAY surfaces (SARC-F item labels/
    options, red_flag_labels — onboarding_wizard consumes the latter)."""
    return _load_rubrics()


def render_sarc_f_form() -> Optional[dict]:
    """Return {'sarc_f_score': int, 'item_scores': {name: 0-2}} on submit, else None."""
    items = _load_rubrics()["sarc_f"]["items"]
    st.subheader(tr("sarc_f.subheader"))
    st.caption(tr("sarc_f.caption"))
    with st.form("sarc_f_form"):
        item_scores: dict[str, int] = {}
        for it in items:
            choice = st.selectbox(it["label"], it["options"],
                                  key=f"sarcf_{it['name']}_{safe_locale()}")
        submitted = st.form_submit_button(tr("wizard.continue"), width="stretch")
    if not submitted:
        return None
    return {"sarc_f_score": sum(item_scores.values()), "item_scores": item_scores}