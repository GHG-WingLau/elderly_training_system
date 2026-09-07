"""Phase 3 — breathing schedule lookup from data/breathing_sequences.json."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_bs_cache: Optional[dict] = None


def _load() -> dict:
    global _bs_cache
    if _bs_cache is None:
        with open(DATA_DIR / "breathing_sequences.json") as f:
            _bs_cache = json.load(f)
    return _bs_cache


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