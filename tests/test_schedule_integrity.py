"""tests/test_schedule_integrity.py — breathing schedule contract.

Pins the two latent robustness quirks flagged during change #4:
  1. breathing_logic indexes the schedule POSITIONALLY (schedule[week]);
     the JSON must therefore list weeks 0-4 in exact order — a reordered
     or gapped schedule would silently serve the wrong practices.
  2. get_breathing_practices silently drops unknown codes
     ([by_code[c] for c in codes if c in by_code]); a typo'd schedule
     code would quietly shrink a day's practice list. These tests make
     that loud.

Also pins behavioural contracts: day 7 serves no practices (rest day);
days 1-3 / 4-6 map to their schedule slots, in order, with fields
passed through.

breathing_logic.py itself is unchanged — the JSON contract is guarded
by tests rather than refactoring a working module.
"""
from __future__ import annotations

import json
from pathlib import Path

from utils.breathing_logic import get_breathing_practices

DATA_PATH = (Path(__file__).resolve().parent.parent
             / "data" / "breathing_sequences.json")


def _load() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


def test_schedule_has_weeks_0_to_4_in_positional_order():
    schedule = _load()["schedule"]
    assert len(schedule) == 5, f"expected 5 schedule entries, got {len(schedule)}"
    for idx, entry in enumerate(schedule):
        assert entry["week"] == idx, (
            f"schedule[{idx}] has week={entry['week']}: breathing_logic indexes "
            f"POSITIONALLY (schedule[week]) — entries must be weeks 0-4 in order"
        )


def test_every_scheduled_code_exists_in_practices():
    data = _load()
    codes = {p["code"] for p in data["practices"]}
    problems: list[str] = []
    for entry in data["schedule"]:
        for key in ("days_1_3", "days_4_6", "day_7"):
            for c in entry.get(key, []):
                if c not in codes:
                    # breathing_logic drops unknown codes SILENTLY — this
                    # failure is the loud version of that quiet bug.
                    problems.append(
                        f"week {entry['week']} {key}: unknown practice code {c!r}")
    assert not problems, "; ".join(problems)


def test_practice_codes_unique():
    codes = [p["code"] for p in _load()["practices"]]
    assert len(codes) == len(set(codes)), f"duplicate practice codes: {codes}"


def test_all_practices_scheduled_somewhere():
    data = _load()
    scheduled: set[str] = set()
    for entry in data["schedule"]:
        scheduled.update(entry["days_1_3"], entry["days_4_6"],
                         entry.get("day_7", []))
    practices = {p["code"] for p in data["practices"]}
    unscheduled = practices - scheduled
    assert not unscheduled, f"practices never scheduled: {sorted(unscheduled)}"


def test_day_7_serves_no_practices():
    for week in range(5):
        assert get_breathing_practices(week, 7) == [], (
            f"week {week} day 7 must serve no practices (rest day)")


def test_days_1_3_and_4_6_map_to_schedule_slots_in_order():
    for entry in _load()["schedule"]:
        w = entry["week"]
        for d in (1, 2, 3):
            got = [p["code"] for p in get_breathing_practices(w, d)]
            assert got == entry["days_1_3"], (
                f"week {w} day {d}: served {got}, schedule says "
                f"{entry['days_1_3']}")
        for d in (4, 5, 6):
            got = [p["code"] for p in get_breathing_practices(w, d)]
            assert got == entry["days_4_6"], (
                f"week {w} day {d}: served {got}, schedule says "
                f"{entry['days_4_6']}")