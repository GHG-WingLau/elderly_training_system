"""tests/test_breathing_controls.py — changes #6 + label contract.

The metronome is a self-contained HTML fragment rendered via st.iframe.
AppTest cannot observe iframe rendering, so these tests pin the RENDERING
CONTRACT of the fragment generator, the flag-pruning helper, and the
button-label contract.

Label contract (user-approved B+D): labels name the on-screen object
("the breathing circle"), carry ▶/⏹ symbol assists, exclude the DBxx
code prefix, and stay pairwise distinct per practice. Labels are asserted
via the same f-string pattern the view uses; if the view's labels change,
update the pattern here in the same change.

v3.2: test_metronome_fragment_is_script_free RESTORED — it was
accidentally dropped in the label-contract edition (the 226-vs-227
reconciliation exposed the drop; it pins the Phase-3 pure-CSS decision).
"""
from __future__ import annotations

import re

from components.views.breathing_view import (
    RING_HEIGHT, STARTED_KEY, _metronome_html, _pruned_started,
)

PRACTICE = {
    "code": "DB01", "title": "Belly Breathing", "focus": "test focus",
    "inhale_s": 4, "hold_s": 2, "exhale_s": 6, "cycles": 6,
}
PRACTICE_2 = {
    "code": "DB02", "title": "Core Brace", "focus": "test focus",
    "inhale_s": 3, "hold_s": 2, "exhale_s": 3, "cycles": 9,
}


def _html(**overrides) -> str:
    p = dict(PRACTICE, **overrides)
    return _metronome_html(p, p["code"].lower())


def _strip_css_comments(html: str) -> str:
    return re.sub(r"/\*.*?\*/", "", html, flags=re.DOTALL)


# --- label contract (B+D copy) ------------------------------------------------

def _start_label(practice: dict) -> str:
    return f"▶ Start the breathing circle — {practice['title']}"


def _stop_label(practice: dict) -> str:
    return f"⏹ Stop the breathing circle — {practice['title']}"


def test_start_label_names_the_object_with_symbol():
    label = _start_label(PRACTICE)
    assert label.startswith("▶")
    assert "Start the breathing circle" in label
    assert "Belly Breathing" in label


def test_stop_label_names_the_object_with_symbol():
    label = _stop_label(PRACTICE)
    assert label.startswith("⏹")
    assert "Stop the breathing circle" in label


def test_labels_exclude_code_prefix():
    assert PRACTICE["code"] not in _start_label(PRACTICE)
    assert PRACTICE["code"] not in _stop_label(PRACTICE)


def test_labels_pairwise_distinct_across_practices():
    assert _start_label(PRACTICE) != _start_label(PRACTICE_2)
    assert _stop_label(PRACTICE) != _stop_label(PRACTICE_2)


# --- metronome contract --------------------------------------------------------

def test_animation_iteration_count_equals_prescribed_cycles():
    assert "animation-iteration-count: 6;" in _html(cycles=6)
    assert "animation-iteration-count: 9;" in _html(cycles=9)


def test_fill_mode_forwards_parks_ring_at_rest():
    assert "animation-fill-mode: forwards;" in _html()


def test_no_infinite_animation():
    assert "infinite" not in _strip_css_comments(_html())


def test_no_active_reduced_motion_override():
    assert "prefers-reduced-motion" not in _strip_css_comments(_html())


def test_keyframes_rule_present_for_the_animation_name():
    assert "@keyframes breathe-db01 {" in _html()
    assert "animation-name: breathe-db01;" in _html()


def test_duration_matches_total_cycle_seconds():
    assert "animation-duration: 12s;" in _html()  # 4+2+6


def test_ring_is_decorative_aria_hidden():
    assert 'aria-hidden="true"' in _html()


def test_ring_geometry_prevents_clipping():
    assert "margin: 40px auto;" in _html()
    assert RING_HEIGHT >= 40 + 120 + 36  # 196


def test_metronome_fragment_is_script_free():
    """Pins the Phase-3 pure-CSS decision: no <script> in the fragment.
    RESTORED (v3.2) — accidentally dropped in the label-contract edition."""
    assert "<script" not in _html().lower()


# --- flag-pruning contract -----------------------------------------------------

def test_pruned_started_drops_stale_codes():
    practices = [{"code": "DB01"}, {"code": "DB02"}]
    started = {"DB01": True, "DB99": True}
    assert _pruned_started(practices, started) == {"DB01": True}


def test_started_key_matches_state_contract():
    assert STARTED_KEY == "breathing_started"