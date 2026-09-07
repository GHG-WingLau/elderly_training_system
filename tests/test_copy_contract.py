"""tests/test_copy_contract.py — approved clinical copy + label contracts.

Contract:
  1. every exercise card carries non-empty "purpose" and "instructions";
  2. no DRAFT markers remain in any approved copy;
  3. card_id values are unique, 24 cards;
  4. every breathing practice carries non-empty "purpose" and "instruction";
  5. all five DB practice codes present;
  6. baseline copy (data/baseline_instructions.json): intro present, every
     measure carries description + instruction(s), no DRAFT, SLS left/right
     instructions distinct;
  7. baseline input labels (change #14, signed off): verb-first "Enter your"
     wording — pins the approved values so a future rename fails loudly
     (constraint 1: locked-component label changes need sign-off).

Verbatimness against the approved documents is reviewed via git diff; these
tests enforce completeness, DRAFT-purge, and the label contract.
"""
from __future__ import annotations
import json
from pathlib import Path

from components.locked.baseline_timers import (
    LABEL_CALF, LABEL_CHAIR, LABEL_SLS_L, LABEL_SLS_R,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASELINE_PATH = DATA_DIR / "baseline_instructions.json"


def _cards() -> list:
    with open(DATA_DIR / "exercise_cards.json") as f:
        return json.load(f)


def _practices() -> list:
    with open(DATA_DIR / "breathing_sequences.json") as f:
        return json.load(f)["practices"]


def _baseline() -> dict:
    with open(BASELINE_PATH) as f:
        return json.load(f)


def test_every_card_has_purpose_and_instructions():
    problems = []
    for c in _cards():
        if not c.get("purpose"):
            problems.append(f"{c['card_id']}: missing 'purpose'")
        if not c.get("instructions"):
            problems.append(f"{c['card_id']}: missing 'instructions'")
    assert not problems, "; ".join(problems)


def test_no_draft_markers_remain():
    problems = []
    for c in _cards():
        for field in ("purpose", "instructions"):
            if "DRAFT" in (c.get(field) or ""):
                problems.append(f"{c['card_id']}.{field}")
    for p in _practices():
        for field in ("purpose", "instruction"):
            if "DRAFT" in (p.get(field) or ""):
                problems.append(f"{p['code']}.{field}")
    assert not problems, f"DRAFT copy remains: {problems}"


def test_card_ids_unique_and_count_24():
    cards = _cards()
    ids = [c["card_id"] for c in cards]
    assert len(ids) == len(set(ids)), "duplicate card_id entries"
    assert len(cards) == 24


def test_every_practice_has_purpose_and_instruction():
    problems = []
    for p in _practices():
        if not p.get("purpose"):
            problems.append(f"{p['code']}: missing 'purpose'")
        if not p.get("instruction"):
            problems.append(f"{p['code']}: missing 'instruction'")
    assert not problems, "; ".join(problems)


def test_all_five_db_practices_present():
    codes = {p["code"] for p in _practices()}
    assert codes == {"DB01", "DB02", "DB03", "DB04", "DB05"}


def test_baseline_intro_present():
    assert _baseline().get("intro", "").strip(), "baseline intro missing"


def test_baseline_measures_have_description_and_instructions():
    m = _baseline()["measures"]
    problems = []
    for measure, fields in (
        ("calf", ("description", "instruction")),
        ("single_leg_stance",
         ("description", "instruction_left", "instruction_right")),
        ("chair_stand", ("description", "instruction")),
    ):
        for field in fields:
            if not m.get(measure, {}).get(field, "").strip():
                problems.append(f"{measure}.{field}")
    assert not problems, f"missing baseline copy: {problems}"


def test_no_draft_in_baseline_copy():
    data = _baseline()
    texts = [data.get("intro", "")]
    for m in data["measures"].values():
        texts.extend(v for v in m.values() if isinstance(v, str))
    assert not any("DRAFT" in t for t in texts)


def test_sls_left_right_instructions_differ():
    m = _baseline()["measures"]["single_leg_stance"]
    assert m["instruction_left"] != m["instruction_right"]


def test_baseline_labels_are_the_signed_off_values():
    """Change #14: verb-first label wording, approved and signed off —
    pinned so a future rename fails loudly (locked-component guard)."""
    assert LABEL_CALF == "Enter your calf circumference (cm)"
    assert LABEL_SLS_L == "Enter your single-leg stance time — left leg (sec)"
    assert LABEL_SLS_R == "Enter your single-leg stance time — right leg (sec)"
    assert LABEL_CHAIR == "Enter your 30-second chair stand count (reps)"
    for label in (LABEL_CALF, LABEL_SLS_L, LABEL_SLS_R, LABEL_CHAIR):
        assert label.startswith("Enter your ")