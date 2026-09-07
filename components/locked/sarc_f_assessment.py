"""LOCKED COMPONENT — sign-off required to modify.
Renders the 5-item SARC-F questionnaire. Item text and options are NEVER
hardcoded — always read from data/scoring_rubrics.json."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_rubrics_cache: Optional[dict] = None


def _load_rubrics() -> dict:
    global _rubrics_cache
    if _rubrics_cache is None:
        with open(DATA_DIR / "scoring_rubrics.json") as f:
            _rubrics_cache = json.load(f)
    return _rubrics_cache


def render_sarc_f_form() -> Optional[dict]:
    """Return {'sarc_f_score': int, 'item_scores': {name: 0-2}} on submit, else None."""
    items = _load_rubrics()["sarc_f"]["items"]
    st.subheader("SARC-F Questionnaire")
    st.caption("Answer each question based on your current ability.")
    with st.form("sarc_f_form"):
        item_scores: dict[str, int] = {}
        for it in items:
            choice = st.selectbox(it["label"], it["options"], key=f"sarcf_{it['name']}")
            item_scores[it["name"]] = it["options"].index(choice)
        submitted = st.form_submit_button("Continue", width="stretch")
    if not submitted:
        return None
    return {"sarc_f_score": sum(item_scores.values()), "item_scores": item_scores}