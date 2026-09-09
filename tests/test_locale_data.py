"""Per-locale data-file completeness contracts (decision 7.5).

v3: re-issued as ONE complete file. The v2 delivery was sent as
"additions" and the original 8 tests + helpers were dropped on apply —
caught by count reconciliation (281 collected vs 289 predicted; the two
_load NameErrors were the symptom). The full-file-replacement rule
applies to test files too. v3 adds the exercise-cards completeness test
(2 params) and extends the corrected-strings pins to the exercise
corrections (SP01 / TW HF02 / G03).

Asserts per document class: structure mirrors EN exactly; localizable
fields non-empty, CJK-bearing, and differing from EN (no leakage);
never-localize fields copied verbatim (thresholds, cadences, schedule,
codes, category/base_level/isometric/image); no "DRAFT"; SARC-F option
ORDER preserved (score = options.index — the contract pins count and
position; translation fidelity is the signed doc's guarantee).
"""
import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
LOCALES = ["zh-HK", "zh-TW"]


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


@pytest.mark.parametrize("loc", LOCALES)
def test_consent_locale_completeness(loc):
    en = _load("consent.json")
    zh = _load(f"consent.{loc}.json")
    assert set(zh) == set(en)                       # version, full_text, micro
    assert zh["version"] == f'{en["version"]}-{loc}'
    assert set(zh["micro"]) == set(en["micro"])
    for k in ("heading", "lead", "checkbox_label", "required_note"):
        assert _cjk(zh["micro"][k]) and zh["micro"][k] != en["micro"][k]
    assert len(zh["micro"]["points"]) == len(en["micro"]["points"]) == 3
    for a, b in zip(zh["micro"]["points"], en["micro"]["points"]):
        assert _cjk(a) and a != b
    assert _cjk(zh["full_text"])
    assert "DRAFT" not in zh["full_text"]


@pytest.mark.parametrize("loc", LOCALES)
def test_rubrics_locale_completeness(loc):
    en = _load("scoring_rubrics.json")
    zh = _load(f"scoring_rubrics.{loc}.json")
    for k in ("calf_circumference_cm", "single_leg_stance_sec",
              "chair_stand_30s", "level_assignment"):
        assert zh[k] == en[k]                       # never-localize thresholds
    assert zh["sarc_f"]["max"] == en["sarc_f"]["max"] == 10
    assert [i["name"] for i in zh["sarc_f"]["items"]] == \
           [i["name"] for i in en["sarc_f"]["items"]]
    for a, b in zip(zh["sarc_f"]["items"], en["sarc_f"]["items"]):
        assert len(a["options"]) == len(b["options"]) == 3   # ORDER contract
        assert _cjk(a["label"]) and a["label"] != b["label"]
        for x, y in zip(a["options"], b["options"]):
            assert _cjk(x) and x != y
    assert zh["red_flags"] == en["red_flags"]       # codes, never localized
    assert set(zh["red_flag_labels"]) == set(en["red_flags"])
    assert all(_cjk(v) for v in zh["red_flag_labels"].values())
    assert _cjk(zh["notes"])


@pytest.mark.parametrize("loc", LOCALES)
def test_baseline_locale_completeness(loc):
    en = _load("baseline_instructions.json")
    zh = _load(f"baseline_instructions.{loc}.json")
    assert set(zh) == set(en)
    assert set(zh["measures"]) == set(en["measures"])
    for m, fields in en["measures"].items():
        assert set(zh["measures"][m]) == set(fields)
        for f in fields:
            assert _cjk(zh["measures"][m][f])
            assert zh["measures"][m][f] != fields[f]
    assert _cjk(zh["intro"])
    assert "DRAFT" not in json.dumps(zh, ensure_ascii=False)


@pytest.mark.parametrize("loc", LOCALES)
def test_breathing_locale_completeness(loc):
    en = _load("breathing_sequences.json")
    zh = _load(f"breathing_sequences.{loc}.json")
    assert zh["schedule"] == en["schedule"]         # never-localize
    assert set(zh["safety_text"]) == set(en["safety_text"])
    for k, v in zh["safety_text"].items():
        assert _cjk(v) and v != en["safety_text"][k]
    assert [p["code"] for p in zh["practices"]] == \
           [p["code"] for p in en["practices"]]
    for a, b in zip(zh["practices"], en["practices"]):
        for k in ("inhale_s", "hold_s", "exhale_s", "cycles"):
            assert a[k] == b[k]                     # clinical cadences
        assert a["image"] == b["image"]             # shared illustrations
        assert a["audio"] == f"assets/audio/{loc}/{a['code']}.mp3"
        for k in ("title", "focus", "purpose", "instruction"):
            assert _cjk(a[k]) and a[k] != b[k]


@pytest.mark.parametrize("loc", LOCALES)
def test_exercise_cards_locale_completeness(loc):
    en = _load("exercise_cards.json")
    zh = _load(f"exercise_cards.{loc}.json")
    assert [c["card_id"] for c in zh] == [c["card_id"] for c in en]  # 24, order
    for a, b in zip(zh, en):
        for k in ("category", "base_level", "image", "isometric"):
            assert a[k] == b[k]                     # never-localize
        assert a["audio"] == f"assets/audio/{loc}/{a['card_id']}.mp3"
        assert set(a["position_cues"]) == set(b["position_cues"])
        for lvl, cue in a["position_cues"].items():
            assert _cjk(cue) and cue != b["position_cues"][lvl]
        for k in ("title", "instructions", "purpose"):
            assert _cjk(a[k]) and a[k] != b[k]


# --- loader routing (locale-aware loaders serve locale data) --------------

def test_breathing_loader_routes_locale(monkeypatch):
    import utils.breathing_logic as bl
    monkeypatch.setattr(bl, "safe_locale", lambda: "zh-HK")
    safety = bl.get_safety_text()
    assert any("\u4e00" <= ch <= "\u9fff" for ch in safety["chair_standard"])
    en = _load("breathing_sequences.json")
    assert safety["chair_standard"] != en["safety_text"]["chair_standard"]


def test_sarc_f_rubrics_loader_routes_locale(monkeypatch):
    import components.locked.sarc_f_assessment as sfa
    monkeypatch.setattr(sfa, "safe_locale", lambda: "zh-TW")
    label = sfa.get_rubrics()["sarc_f"]["items"][0]["label"]
    assert any("\u4e00" <= ch <= "\u9fff" for ch in label)


def test_baseline_loader_routes_locale(monkeypatch):
    import components.locked.baseline_timers as bt
    monkeypatch.setattr(bt, "safe_locale", lambda: "zh-HK")
    data = bt._load_instructions()
    assert any("\u4e00" <= ch <= "\u9fff" for ch in data["intro"])


def test_consent_loader_routes_locale(monkeypatch):
    import components.views.auth_view as av
    monkeypatch.setattr(av, "safe_locale", lambda: "zh-TW")
    consent = av._load_consent()
    assert consent["version"] == "v1.1-zh-TW"
    assert any("\u4e00" <= ch <= "\u9fff" for ch in consent["micro"]["checkbox_label"])


def test_red_flag_pairs_localize_from_rubrics(monkeypatch):
    import components.locked.sarc_f_assessment as sfa
    import components.locked.onboarding_wizard as ow
    monkeypatch.setattr(sfa, "safe_locale", lambda: "zh-HK")
    pairs = ow._red_flag_pairs()
    assert pairs[0] == ("chest_pain", "胸痛")
    assert [c for c, _ in pairs] == [c for c, _ in ow.RED_FLAGS]


def test_red_flag_pairs_en_fallback(monkeypatch):
    import components.locked.sarc_f_assessment as sfa
    import components.locked.onboarding_wizard as ow
    monkeypatch.setattr(sfa, "safe_locale", lambda: "en")
    assert ow._red_flag_pairs() == ow.RED_FLAGS


def test_team_corrected_strings_pinned():
    """Team corrections pinned verbatim — future edits fail loudly
    (copy-contract discipline). SP01 pins are robust to the open
    gloss-retention decision (assert the correction, not the gloss)."""
    hk = _load("breathing_sequences.zh-HK.json")
    assert hk["safety_text"]["lightheadedness_valve"] == (
        "如果你喺任何時候感到頭暈、氣促或頭昏眼花，請立即停止，並恢復正常同舒適嘅呼吸節奏。")
    tw = _load("consent.zh-TW.json")
    assert "諮詢醫師：" in tw["full_text"]
    assert "醫師諮詢" not in tw["full_text"]
    for name in ("exercise_cards.zh-HK.json", "exercise_cards.zh-TW.json"):
        cards = _load(name)
        sp01 = next(c for c in cards if c["card_id"] == "SP01")
        assert "坐姿背闊肌伸展與上伸" in sp01["title"]
        assert "向上向上" not in sp01["title"]
        g03 = next(c for c in cards if c["card_id"] == "G03")
        assert g03["position_cues"]["0"] == "靠椅子輔助，部分幅度"
    hf02_tw = next(c for c in _load("exercise_cards.zh-TW.json")
                   if c["card_id"] == "HF02")
    assert "膝蓋上方的大腿上" in hf02_tw["instructions"]
    assert "特大腿" not in hf02_tw["instructions"]