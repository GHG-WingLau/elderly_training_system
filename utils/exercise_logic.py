"""Phase 2 — curriculum engine.
Loads/validates exercise_cards.json, injects level position cues, generates
the weekly pool, selects the daily 3-exercise set, and looks up prescriptions.

Design (resolves the spec's 'random from active pool' into a constraint-
satisfying form):
  - Weekly pool = 2 cards from each of 3 categories (6 total). This GUARANTEES
    daily 3-distinct-category selection with no consecutive-day repeats is
    always feasible. (A fully random 6-from-active-pool could yield <3
    categories and make daily selection impossible.)
  - W0/W1 categories fixed {C, PC, G}; W1 = complement of W0 within each
    category (honors 'remaining unused from initial pool').
  - W2 introduces HF, W3 introduces SP, W4 introduces CM (+ 2 seeded
    categories from the previously-introduced set).
  - Daily selection = alternating pattern per category (odd days card A,
    even days card B) -> no exercise on consecutive days.
  - All RNG seeded by sha256(email|cycle|week|salt) -> deterministic across
    Streamlit reruns. Weekly pool persisted to weekly_plan as primary safety.
"""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
from typing import Optional

from db import queries

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_cards_cache: Optional[list] = None
_prescriptions_cache: Optional[dict] = None
_cards_by_cat_cache: Optional[dict] = None

CATEGORY_INTRO = {
    0: {"C", "PC", "G"},
    1: {"C", "PC", "G"},
    2: {"C", "PC", "G", "HF"},
    3: {"C", "PC", "G", "HF", "SP"},
    4: {"C", "PC", "G", "HF", "SP", "CM"},
}
NEW_CATEGORY = {0: None, 1: None, 2: "HF", 3: "SP", 4: "CM"}


def _seed(email: str, cycle: int, week: int, salt: str = "") -> int:
    return int(hashlib.sha256(
        f"{email}|{cycle}|{week}|{salt}".encode()).hexdigest(), 16) % (2**32)


def _load_cards() -> list[dict]:
    global _cards_cache
    if _cards_cache is None:
        with open(DATA_DIR / "exercise_cards.json") as f:
            _cards_cache = json.load(f)
        for c in _cards_cache:
            for k in ("card_id", "title", "category", "base_level", "image",
                      "isometric", "instructions", "position_cues"):
                if k not in c:
                    raise ValueError(f"exercise card missing '{k}': {c.get('card_id')}")
    return _cards_cache


def _load_prescriptions() -> dict:
    global _prescriptions_cache
    if _prescriptions_cache is None:
        with open(DATA_DIR / "prescriptions.json") as f:
            _prescriptions_cache = json.load(f)
    return _prescriptions_cache


def _cards_by_category() -> dict[str, list[str]]:
    global _cards_by_cat_cache
    if _cards_by_cat_cache is None:
        out: dict[str, list[str]] = {}
        for c in _load_cards():
            out.setdefault(c["category"], []).append(c["card_id"])
        for cat in out:
            out[cat].sort()
        _cards_by_cat_cache = out
    return _cards_by_cat_cache


def _level_int(level) -> int:
    return level if isinstance(level, int) else int(str(level).split()[-1])


def get_card(card_id: str) -> dict:
    for c in _load_cards():
        if c["card_id"] == card_id:
            return c
    raise KeyError(card_id)


def _card_category(card_id: str) -> str:
    return get_card(card_id)["category"]


def apply_position_cue(card: dict, level) -> dict:
    """Return a copy of card with 'position_cue' set for the given level."""
    out = dict(card)
    out["position_cue"] = card["position_cues"][str(_level_int(level))]
    return out


def get_prescription(level) -> dict:
    return _load_prescriptions()[str(_level_int(level))]


def _pick_categories(week: int, rng: random.Random) -> list[str]:
    new_cat = NEW_CATEGORY[week]
    if new_cat is None:
        return ["C", "PC", "G"]
    prior = sorted(CATEGORY_INTRO[week] - {new_cat})
    return [new_cat] + rng.sample(prior, 2)


def _pick_two(category: str, rng: random.Random,
              exclude: Optional[set] = None) -> list[str]:
    ex = exclude or set()
    pool = [c for c in _cards_by_category()[category] if c not in ex]
    return rng.sample(pool, 2)


def _generate_weekly_pool_ids(email: str, cycle: int, week: int) -> list[str]:
    rng = random.Random(_seed(email, cycle, week))
    if week == 1:
        # complement of W0 within {C, PC, G}
        w0 = get_weekly_pool(email, cycle, 0)
        used: dict[str, set[str]] = {}
        for cid in w0:
            used.setdefault(_card_category(cid), set()).add(cid)
        pool: list[str] = []
        for cat in ("C", "PC", "G"):
            pool.extend(_pick_two(cat, rng, exclude=used.get(cat, set())))
    else:
        pool = []
        for cat in _pick_categories(week, rng):
            pool.extend(_pick_two(cat, rng))
    rng.shuffle(pool)
    return pool


def get_weekly_pool(email: str, cycle: int, week: int) -> list[str]:
    """Return the 6 card IDs for the week. Persisted on first generation."""
    existing = queries.get_weekly_plan(email, cycle, week)
    if existing:
        return existing.split(",")
    pool = _generate_weekly_pool_ids(email, cycle, week)
    queries.upsert_weekly_plan(email, cycle, week, ",".join(pool))
    return pool


def select_daily_set(email: str, cycle: int, week: int, day: int) -> list[str]:
    """Return 3 card IDs for the day: one per category, no consecutive-day repeat."""
    pool = get_weekly_pool(email, cycle, week)
    by_cat: dict[str, list[str]] = {}
    for cid in pool:
        by_cat.setdefault(_card_category(cid), []).append(cid)
    rng = random.Random(_seed(email, cycle, week, salt="daily"))
    cat_order: dict[str, list[str]] = {}
    for cat in sorted(by_cat):
        c = list(by_cat[cat]); rng.shuffle(c)
        cat_order[cat] = c
    slot = 0 if (day - 1) % 2 == 0 else 1   # odd days (1,3,5) -> index 0
    return [cat_order[cat][slot] for cat in sorted(cat_order)]

def format_prescription(rx: dict) -> str:
    """Build the display string from a numeric prescription dict."""
    reps = f"{rx['reps_min']}–{rx['reps_max']} reps"
    if rx.get("hold_s"):
        reps += f" (or {rx['hold_s']}s hold)"
    if rx["rest_s_min"] == rx["rest_s_max"]:
        rest = f"{rx['rest_s_min']}s"
    else:
        rest = f"{rx['rest_s_min']}–{rx['rest_s_max']}s"
    return f"{rx['sets']} sets · {reps} · rest {rest}"