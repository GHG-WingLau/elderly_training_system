"""UI-strings data contracts (Phase 7 activation layer).

v4: picker.label joins the identical-by-design set — the label is a
FIXED bilingual wayfinding string (accessibility decision; identical
in every locale so the switcher is findable pre-comprehension), pinned
identical by test_picker_label_is_fixed_bilingual. AUTONYM_KEYS renamed
IDENTICAL_BY_DESIGN_KEYS accordingly.

v3 history: 130 flattened keys; prescription is TWO whole templates
(template_hold / template_no_hold); PENDING_PARITY remains EMPTY
(level-composition normalization); pins for the team's corrected
strings; loader and format_prescription routing tests.

Contracts: key parity + count pinned (130); no EN leakage + CJK
presence except the identical-by-design keys; placeholder parity
(machine-checked, no exemptions); level display map complete; accessor
routes by locale and fails loud; corrected strings pinned.
"""
import json
import re
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
LOCALES = ["zh-HK", "zh-TW"]
TOKEN = re.compile(r"\{([a-z_]+)\}")
# Identical across all locale files BY DESIGN: the three picker display
# autonyms, and the picker label — the FIXED bilingual wayfinding string
# (accessibility: findable before the user understands the UI language).
IDENTICAL_BY_DESIGN_KEYS = {"picker.display_en", "picker.display_zh_hk",
                            "picker.display_zh_tw", "picker.label"}
# Emptied by the level-composition normalization (EN templates now carry
# {n}, matching zh). Retained for history; a new exemption requires a
# documented reason.
PENDING_PARITY: set = set()


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def _cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


@pytest.mark.parametrize("loc", LOCALES)
def test_ui_strings_key_parity_and_no_leakage(loc):
    en = _flatten(_load("ui_strings.json"))
    zh = _flatten(_load(f"ui_strings.{loc}.json"))
    assert len(en) == 175                       # count pinned
    assert set(zh) == set(en)
    for k, v in zh.items():
        assert isinstance(v, str) and v.strip()
        if k in IDENTICAL_BY_DESIGN_KEYS:
            continue                            # identical by design
        assert v != en[k], f"EN leakage in {loc} {k}"
        assert _cjk(v), f"no CJK in {loc} {k}"


@pytest.mark.parametrize("loc", LOCALES)
def test_ui_strings_placeholder_parity(loc):
    en = _flatten(_load("ui_strings.json"))
    zh = _flatten(_load(f"ui_strings.{loc}.json"))
    for k, v in zh.items():
        if k in PENDING_PARITY:
            continue
        assert set(TOKEN.findall(v)) == set(TOKEN.findall(en[k])), k


def test_level_display_map_complete():
    expected = {f"Level {i}" for i in range(5)}
    names = ["ui_strings.json"] + [f"ui_strings.{l}.json" for l in LOCALES]
    for name in names:
        assert set(_load(name)["levels"]) == expected


def test_accessor_routes_and_fails_loud(monkeypatch):
    import utils.strings as us
    monkeypatch.setattr(us, "safe_locale", lambda: "zh-HK")
    assert us.tr("hub.title") == "歡迎，{username} 👋"
    assert us.level_display("Level 2") == "等級 2 (扶物站立)"
    with pytest.raises(KeyError):
        us.tr("bogus.key")
    with pytest.raises(KeyError):
        us.level_display("Level 9")


def test_team_corrected_ui_strings_pinned():
    """Team corrections pinned verbatim — future edits fail loudly."""
    tw = _load("ui_strings.zh-TW.json")
    assert tw["sarc_f"]["caption"] == "請根據您目前的能力回答每個問題。"
    hk = _load("ui_strings.zh-HK.json")
    assert "撳入" in hk["hub"]["bookmark_tip"]
    assert "禁入" not in hk["hub"]["bookmark_tip"]
    for name in ("ui_strings.zh-HK.json", "ui_strings.zh-TW.json"):
        doc = _load(name)
        assert doc["auth"]["sex_label"] == "性別（用於小腿圍及坐姿起立常模）"
        assert doc["hub"]["start_review"] == "開始每週回顧"
        assert doc["prescription"]["template_no_hold"].endswith("休息 {rest} 秒")
        assert doc["prescription"]["template_hold"] == (
            "{sets} 組 · {reps_min}–{reps_max} 次（或維持 {hold} 秒）· 休息 {rest} 秒")


def test_picker_label_is_fixed_bilingual():
    """Accessibility decision (localization thread): the language
    switcher's label is a FIXED bilingual wayfinding string, identical
    in every locale — a non-English speaker must be able to find the
    switcher BEFORE understanding the UI language (the cold-start
    problem). Pinned so a future 'localization' of this label fails
    loudly."""
    docs = [_load(n) for n in
            ("ui_strings.json", "ui_strings.zh-HK.json",
             "ui_strings.zh-TW.json")]
    labels = {d["picker"]["label"] for d in docs}
    assert len(labels) == 1
    (label,) = labels
    assert "Select your preferred language" in label
    assert "請選擇你的語言" in label


def test_format_prescription_localizes(monkeypatch):
    """Phase 7: bare numbers in, units from the per-locale template; the
    hold template applies only when hold_s exists (Level 0 only); the
    hold-case composition is the SIGNED string (no extra space — the v2
    defect this test caught)."""
    import utils.strings as us
    monkeypatch.setattr(us, "safe_locale", lambda: "zh-HK")
    from utils.exercise_logic import format_prescription
    out = format_prescription({"sets": 3, "reps_min": 8, "reps_max": 12,
                               "rest_s_min": 60, "rest_s_max": 90})
    assert out == "3 組 · 8–12 次 · 休息 60–90 秒"
    out2 = format_prescription({"sets": 2, "reps_min": 8, "reps_max": 12,
                                "hold_s": 10, "rest_s_min": 60,
                                "rest_s_max": 60})
    assert out2 == "2 組 · 8–12 次（或維持 10 秒）· 休息 60 秒"


def test_exercise_cards_loader_routes_locale(monkeypatch):
    import utils.exercise_logic as el
    monkeypatch.setattr(el, "safe_locale", lambda: "zh-HK")
    card = el.get_card("C01")
    assert any("\u4e00" <= ch <= "\u9fff" for ch in card["title"])
    assert card["category"] == "C" and card["base_level"] == 1
    assert card["isometric"] is False