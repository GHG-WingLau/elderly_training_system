"""Safety-critical locked module: SARC-F scoring, baseline rubric scoring,
and level assignment. Clinical thresholds are READ FROM data/scoring_rubrics.json
(never hardcoded). If a threshold appears missing, halt and ask — do not invent."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_rubrics_cache: Optional[dict] = None

LEVELS = ["Level 0", "Level 1", "Level 2", "Level 3", "Level 4"]
LEVEL_TO_INT = {lvl: i for i, lvl in enumerate(LEVELS)}


def _load_rubrics() -> dict:
    global _rubrics_cache
    if _rubrics_cache is None:
        with open(DATA_DIR / "scoring_rubrics.json") as f:
            _rubrics_cache = json.load(f)
    return _rubrics_cache


def _band_score(value: float, normal_min: float, risk_max: float) -> int:
    """0 if value >= normal_min; 2 if value < risk_max; else 1."""
    if value >= normal_min:
        return 0
    if value < risk_max:
        return 2
    return 1


def calculate_total_score(sarc_f: int, calf: int, balance: int, chair_stand: int) -> int:
    if not (0 <= sarc_f <= 10):
        raise ValueError(f"SARC-F score out of range: {sarc_f}")
    for name, v in (("calf", calf), ("balance", balance), ("chair_stand", chair_stand)):
        if not (0 <= v <= 2):
            raise ValueError(f"{name} sub-score out of range: {v}")
    return sarc_f + calf + balance + chair_stand


def score_calf(measurement_cm: float, sex: str) -> int:
    rub = _load_rubrics()["calf_circumference_cm"]
    if sex == "M":
        return _band_score(measurement_cm, rub["M"]["normal_min"], rub["M"]["risk_max"])
    if sex == "F":
        return _band_score(measurement_cm, rub["F"]["normal_min"], rub["F"]["risk_max"])
    # 'U' = unspecified → conservative max(male_score, female_score)
    return max(
        _band_score(measurement_cm, rub["M"]["normal_min"], rub["M"]["risk_max"]),
        _band_score(measurement_cm, rub["F"]["normal_min"], rub["F"]["risk_max"]),
    )


def score_sls(seconds: float) -> int:
    band = _load_rubrics()["single_leg_stance_sec"]["unisex"]
    return _band_score(seconds, band["normal_min"], band["risk_max"])


def score_chair_stand(reps: int, sex: str) -> int:
    rub = _load_rubrics()["chair_stand_30s"]
    if sex == "M":
        return _band_score(reps, rub["M"]["normal_min"], rub["M"]["risk_max"])
    if sex == "F":
        return _band_score(reps, rub["F"]["normal_min"], rub["F"]["risk_max"])
    return max(
        _band_score(reps, rub["M"]["normal_min"], rub["M"]["risk_max"]),
        _band_score(reps, rub["F"]["normal_min"], rub["F"]["risk_max"]),
    )


def _has_red_flags(red_flags: Optional[str]) -> bool:
    if not red_flags:
        return False
    return any(token.strip() for token in red_flags.split(","))


def assign_level(total: int, sarc_f: int, age: int, red_flags: Optional[str]) -> str:
    """Priority ladder (first match wins). Thresholds from scoring_rubrics.json."""
    la = _load_rubrics()["level_assignment"]
    if _has_red_flags(red_flags):
        return "Level 0"
    if sarc_f >= la["sarc_f_override"]:            # clinical override
        return "Level 0"
    if total >= la["total_high"] or age >= la["age_high"]:
        return "Level 0"
    if total >= la["total_mid"]:
        return "Level 1" if age >= la["age_mid"] else "Level 2"
    if total >= la["total_low"]:
        return "Level 2" if age >= la["age_mid"] else "Level 3"
    return "Level 4"


def apply_preference_override(computed_level: str, preference_level: str) -> str:
    """Preference may lower the level by at most one step; never raise it."""
    c = LEVEL_TO_INT[computed_level]
    p = LEVEL_TO_INT[preference_level]
    if p >= c:
        return computed_level           # never raise
    return LEVELS[max(c - 1, 0)]        # one step down max, floor Level 0


def assign_level_with_preference(total: int, sarc_f: int, age: int,
                                 red_flags: Optional[str],
                                 preference_level: Optional[str]) -> str:
    level = assign_level(total, sarc_f, age, red_flags)
    if preference_level:
        level = apply_preference_override(level, preference_level)
    return level