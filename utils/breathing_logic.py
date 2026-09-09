"""Phase 3 — breathing schedule lookup from data/breathing_sequences.json.

Phase 7 (localization): locale-aware loader. Per-locale caches
(process-lifetime — dev-server restart after data edits, as before);
the active locale resolves via utils.locale.safe_locale()
(session_state["locale"]; bare-mode/default -> "en"). EN keeps the base
filename; locales use breathing_sequences.{locale}.json. A missing
locale file fails loud (open() raises) — a locale is shippable only
when its data file exists. Cadences and schedule are never-localize
fields; tests/test_locale_data.py pins them equal to EN per locale.
"""
from __future__ import annotations
import json
from pathlib import Path

from utils.locale import safe_locale

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_bs_caches: dict[str, dict] = {}


def _filename(locale: str) -> str:
    return ("breathing_sequences.json" if locale == "en"
            else f"breathing_sequences.{locale}.json")


def _load() -> dict:
    locale = safe_locale()
    if locale not in _bs_caches:
        with open(DATA_DIR / _filename(locale), encoding="utf-8") as f:
            _bs_caches[locale] = json.load(f)
    return _bs_caches[locale]


def get_breathing_practices(week: int, day: int) -> list[dict]:
    """Return practice dicts for the week/day. Day 7 (rest) -> []."""
    if day == 7:
        return []
    entry = _load()["schedule"][week]
    codes = entry["days_1_3"] if day <= 3 else entry["days_4_6"]
    by_code = {p["code"]: p for p in _load()["practices"]}
    return [by_code[c] for c in codes if c in by_code]


def get_safety_text() -> dict:
    return _load()["safety_text"]