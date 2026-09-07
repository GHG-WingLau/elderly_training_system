"""Truth-table contract for the locked assessment module.
These tests ARE the change contract: modifying the ladder or rubrics requires
updating these rows AND clinical sign-off."""
import pytest
from utils.assessment_logic import (
    calculate_total_score, score_calf, score_sls, score_chair_stand,
    assign_level, apply_preference_override,
)


# --- Level assignment ladder (§3.7.4) ---
@pytest.mark.parametrize("red_flags,sarc_f,total,age,expected", [
    ("chest_pain", 0, 0, 60, "Level 0"),   # red flag
    ("", 4, 4, 62, "Level 0"),             # SARC-F override
    ("", 6, 6, 68, "Level 0"),             # SARC-F override
    ("", 3, 9, 70, "Level 0"),             # total >= 8
    ("", 0, 6, 80, "Level 0"),             # age >= 80
    ("", 3, 5, 70, "Level 2"),             # total>=5, age<75
    ("", 3, 5, 76, "Level 1"),             # total>=5, age>=75
    ("", 2, 3, 70, "Level 3"),             # total>=3, age<75
    ("", 2, 3, 76, "Level 2"),             # total>=3, age>=75
    ("", 1, 1, 65, "Level 4"),             # floor
])
def test_assign_level(red_flags, sarc_f, total, age, expected):
    assert assign_level(total, sarc_f, age, red_flags) == expected


# --- Calf circumference rubric ---
@pytest.mark.parametrize("cm,sex,expected", [
    (36.0, "M", 0), (35.9, "M", 1), (34.0, "M", 1), (33.9, "M", 2),
    (34.0, "F", 0), (33.9, "F", 1), (33.0, "F", 1), (32.9, "F", 2),
    (35.0, "U", 1),    # M:1, F:0 -> max 1
    (33.5, "U", 2),    # M:2, F:1 -> max 2
    (36.5, "U", 0),    # both 0
])
def test_score_calf(cm, sex, expected):
    assert score_calf(cm, sex) == expected


# --- Single-leg stance rubric (unisex) ---
@pytest.mark.parametrize("sec,expected", [
    (20.0, 0), (19.9, 1), (10.0, 1), (9.9, 2), (0.0, 2), (32.0, 0),
])
def test_score_sls(sec, expected):
    assert score_sls(sec) == expected


# --- 30-second chair stand rubric ---
@pytest.mark.parametrize("reps,sex,expected", [
    (14, "M", 0), (13, "M", 1), (11, "M", 1), (10, "M", 2),
    (12, "F", 0), (11, "F", 1), (9, "F", 1), (8, "F", 2),
    (12, "U", 1),    # M:1, F:0 -> 1
    (11, "U", 1),    # both 1
    (10, "U", 2),    # both 2
])
def test_score_chair_stand(reps, sex, expected):
    assert score_chair_stand(reps, sex) == expected


# --- Preference override (OQ-10) ---
@pytest.mark.parametrize("level,preference,expected", [
    ("Level 3", "Level 0", "Level 2"),   # lower by one step only
    ("Level 3", "Level 4", "Level 3"),   # never raise
    ("Level 3", "Level 3", "Level 3"),   # same
    ("Level 0", "Level 0", "Level 0"),   # floor
    ("Level 4", "Level 1", "Level 3"),   # one step down
])
def test_apply_preference_override(level, preference, expected):
    assert apply_preference_override(level, preference) == expected


def test_total_score():
    assert calculate_total_score(4, 2, 2, 2) == 10
    assert calculate_total_score(0, 0, 0, 0) == 0
    assert calculate_total_score(10, 2, 2, 2) == 16