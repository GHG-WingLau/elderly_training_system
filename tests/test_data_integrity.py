"""Data-contract integrity tests. These run before the logic tests so a
malformed JSON file fails with a clear, localised message instead of
cascading JSONDecodeErrors across the whole suite."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> dict:
    with open(DATA_DIR / name) as f:
        return json.load(f)


def test_scoring_rubrics_loads_and_has_top_level_keys():
    rub = _load("scoring_rubrics.json")
    assert set(rub) >= {
        "sarc_f", "calf_circumference_cm", "single_leg_stance_sec",
        "chair_stand_30s", "level_assignment", "red_flags",
    }


def test_scoring_rubrics_level_thresholds_present():
    la = _load("scoring_rubrics.json")["level_assignment"]
    for key in ("sarc_f_override", "total_high", "age_high",
                "total_mid", "age_mid", "total_low"):
        assert key in la, f"missing level_assignment threshold: {key}"


def test_scoring_rubrics_band_ordering():
    """normal_min must exceed risk_max, otherwise the 0/1/2 bands invert."""
    calf = _load("scoring_rubrics.json")["calf_circumference_cm"]
    for sex in ("M", "F"):
        assert calf[sex]["normal_min"] > calf[sex]["risk_max"]
    chair = _load("scoring_rubrics.json")["chair_stand_30s"]
    for sex in ("M", "F"):
        assert chair[sex]["normal_min"] > chair[sex]["risk_max"]
    sls = _load("scoring_rubrics.json")["single_leg_stance_sec"]["unisex"]
    assert sls["normal_min"] > sls["risk_max"]


def test_sarc_f_has_five_scored_items():
    items = _load("scoring_rubrics.json")["sarc_f"]["items"]
    assert len(items) == 5
    for it in items:
        assert set(it) == {"name", "label", "options"}
        assert len(it["options"]) == 3  # 0, 1, 2


def test_exercise_cards_count_and_shape():
    cards = _load("exercise_cards.json")
    assert len(cards) == 24
    ids = [c["card_id"] for c in cards]
    assert len(ids) == len(set(ids)), "duplicate card_id detected"
    for c in cards:
        assert set(c) >= {"card_id", "title", "category", "base_level",
                          "image", "isometric", "instructions", "position_cues"}
        assert set(c["position_cues"]) == {"0", "1", "2", "3", "4"}


def test_cm01_renamed_and_level_2():
    cards = {c["card_id"]: c for c in _load("exercise_cards.json")}
    assert cards["CM01"]["title"] == "Seated Rhythm March & Arm Drive"
    assert cards["CM01"]["base_level"] == 2


def test_breathing_sequences_structure():
    bs = _load("breathing_sequences.json")
    practices = {p["code"] for p in bs["practices"]}
    assert practices == {"DB01", "DB02", "DB03", "DB04", "DB05"}
    assert len(bs["schedule"]) == 5  # weeks 0-4
    for entry in bs["schedule"]:
        assert set(entry) == {"week", "days_1_3", "days_4_6", "day_7"}
    assert set(bs["safety_text"]) >= {
        "lightheadedness_valve", "orthostatic_warning", "chair_standard",
    }


def test_db05_introduced_week_2_days_4_6():
    """OQ-04 confirmation: DB05 introduced W2 D4-6, not D1-6."""
    schedule = {s["week"]: s for s in _load("breathing_sequences.json")["schedule"]}
    assert schedule[2]["days_1_3"] == ["DB04"]
    assert schedule[2]["days_4_6"] == ["DB05"]

def test_prescriptions_loads():
    p = _load("prescriptions.json")
    assert set(p) == {"0", "1", "2", "3", "4"}
    for lvl, val in p.items():
        assert {"sets", "reps_min", "reps_max", "hold_s",
                "rest_s_min", "rest_s_max"} <= set(val)
        assert val["reps_min"] <= val["reps_max"]
        assert val["rest_s_min"] <= val["rest_s_max"]
    assert p["0"]["hold_s"] == 10            # spec: '6-8 reps (or 10s hold)'
    for lvl in ("1", "2", "3", "4"):
        assert p[lvl]["hold_s"] is None      # spec defines holds for L0 only