"""tests/test_assets.py — changes #4 and #8: JSON-carried + baseline assets.

Contract:
  1. every practice in data/breathing_sequences.json carries an "image"
     resolving to an existing file (direct load AND via the schedule
     lookup the view uses);
  2. the five documented DB illustrations exist on disk;
  3. the four baseline measurement illustrations (change #8) exist on
     disk AND are exactly the constants referenced by the locked
     baseline_timers module (catches asset renames that bypass the
     module);
  4. the shared placeholder exists.

Runtime rendering is deliberately forgiving (missing file/field renders
the placeholder); THIS file is the enforcement point. AppTest cannot
observe st.image output — visual rendering is covered by the manual QA
checklists of the respective changes.
"""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from utils.assets import PLACEHOLDER, resolve_asset_path
from utils.breathing_logic import get_breathing_practices

DATA_PATH = (Path(__file__).resolve().parent.parent
             / "data" / "breathing_sequences.json")

DOCUMENTED_ASSETS = [
    "assets/exercises/DB01.jpeg",
    "assets/exercises/DB02.jpeg",
    "assets/exercises/DB03.jpeg",
    "assets/exercises/DB04.jpeg",
    "assets/exercises/DB05.jpeg",
]

BASELINE_ASSETS = [
    "assets/exercises/ASSESS_Calf_Measurement.jpeg",
    "assets/exercises/ASSESS_SLS_Left_Foot_Stand.jpeg",
    "assets/exercises/ASSESS_SLS_Right_Foot_Stand.jpeg",
    "assets/exercises/ASSESS_Sit_To_Stand.jpeg",
]


def _load_practices() -> list:
    with open(DATA_PATH) as f:
        return json.load(f)["practices"]


@pytest.mark.parametrize("rel_path", DOCUMENTED_ASSETS)
def test_documented_practice_image_exists(rel_path: str):
    p = resolve_asset_path(rel_path)
    assert p.is_file(), f"missing breathing illustration: {p}"


@pytest.mark.parametrize("rel_path", BASELINE_ASSETS)
def test_baseline_illustration_exists(rel_path: str):
    p = resolve_asset_path(rel_path)
    assert p.is_file(), f"missing baseline illustration: {p}"


def test_baseline_module_references_resolvable_assets():
    """The locked module's constants must point at existing files —
    catches asset renames that bypass the module (paste-artifact lesson:
    '.pjeg', duplicated card entries)."""
    from components.locked.baseline_timers import (
        ASSESS_CALF, ASSESS_SLS_L, ASSESS_SLS_R, ASSESS_CHAIR,
    )
    for p in (ASSESS_CALF, ASSESS_SLS_L, ASSESS_SLS_R, ASSESS_CHAIR):
        assert resolve_asset_path(p).is_file(), f"unresolved asset ref: {p}"


def test_placeholder_exists():
    assert PLACEHOLDER.is_file(), f"missing shared placeholder: {PLACEHOLDER}"


def test_every_practice_in_json_has_resolvable_image():
    practices = _load_practices()
    assert practices, "breathing_sequences.json: no practices found"
    problems: list[str] = []
    for p in practices:
        if not p.get("image"):
            problems.append(f"{p['code']}: missing 'image' field")
        elif not resolve_asset_path(p["image"]).is_file():
            problems.append(f"{p['code']}: {p['image']} not found")
    assert not problems, "; ".join(problems)


def test_every_schedulable_practice_has_an_illustration():
    scheduled: set[str] = set()
    problems: list[str] = []
    for week in range(5):          # weeks 0-4
        for day in range(1, 8):    # days 1-7 (rest days return [])
            for p in get_breathing_practices(week, day):
                scheduled.add(p["code"])
                if not p.get("image"):
                    problems.append(f"{p['code']}: missing 'image' field")
                elif not resolve_asset_path(p["image"]).is_file():
                    problems.append(f"{p['code']}: {p['image']} not found")
    assert scheduled, "expected at least one scheduled breathing practice"
    assert not problems, "; ".join(problems)