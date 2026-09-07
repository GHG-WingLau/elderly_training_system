"""tests/test_css_baseline.py — custom.css WCAG baseline contract.

The 18px font floor and 48px touch-target floor are sign-off conditions
(constraint 4). CSS is invisible to AppTest, so the contract is pinned
statically: parse styles/custom.css and assert the design tokens meet the
floors, the audio-player height rule exists (change #12; native control
measures 40px unpached), and braces balance.
"""
from __future__ import annotations

import re
from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / "styles" / "custom.css"


def _css() -> str:
    assert CSS_PATH.is_file(), f"missing custom.css: {CSS_PATH}"
    return CSS_PATH.read_text()


def _var_px(name: str) -> int:
    m = re.search(rf"--{name}:\s*(\d+)px", _css())
    assert m, f"--{name} not defined in custom.css"
    return int(m.group(1))


def test_base_font_meets_18px_floor():
    assert _var_px("font-base") >= 18


def test_caption_font_meets_18px_floor():
    assert _var_px("font-caption") >= 18


def test_touch_target_meets_48px_floor():
    assert _var_px("touch-min") >= 48


def test_audio_player_touch_target_rule_present():
    assert re.search(r"audio\s*\{[^}]*height:\s*48px", _css()), (
        "native audio player 48px height rule missing from custom.css"
    )


def test_css_braces_balance():
    stripped = re.sub(r"/\*.*?\*/", "", _css(), flags=re.DOTALL)
    opens, closes = stripped.count("{"), stripped.count("}")
    assert opens == closes, (
        f"unbalanced braces in custom.css: {opens} opening vs {closes} closing"
    )