"""Phase 3 — BREATHING_SESSION. Paced breathing metronome (pure CSS, no JS).

Change #4: per-practice illustrations — "image" field in
data/breathing_sequences.json, rendered via utils.assets.render_image.

Change #5: approved clinical copy — "purpose" renders directly after the
title, before the illustration; the approved "instruction" renders after
the cadence line, plain (not italic).

Change #6: per-practice Start/Stop with auto-stop (iteration-count =
prescribed cycles; fill-mode forwards parks the ring at rest); mutual
exclusion (starting one practice clears any other's flag); Stop unmounts;
Start restarts from the first breath; ring aria-hidden. Animation runs
UNCONDITIONALLY (product decision — the prefers-reduced-motion override
is retained only as a commented-out block; the static cadence text is the
non-animated fallback; Start/Stop satisfy WCAG 2.2.2). Vehicle: POSITIONAL
st.iframe — validated on 1.62 ("srcdoc=" is not a parameter; never used).
Geometry: margin 40px auto + RING_HEIGHT 240 (scale(1.6) paints +/-36px
around the 120px box; overflow above the iframe origin is unrecoverable
by height).

Label copy (user-approved, B+D): buttons name the on-screen object —
"▶ Start the breathing circle — {title}" / "⏹ Stop the breathing circle
— {title}" — with symbol assists; code prefix dropped from labels (the
subheader keeps DBxx for support referencing). Guidance copy names the
same object ("tap Start — the circle will move with your breath").

Change #12: narration — a native st.audio player renders directly under
each instruction (utils.assets.render_audio; B1: always visible, no
autoplay, no session flags; missing audio renders nothing — text is
authoritative; 48px floor via the audio rule in styles/custom.css).

Localization thread (team decision): the cadence line's "(~2 min)"
approximate-duration tail is DROPPED — each practice's data instruction
carries its own duration; the code-side approximation was redundant and
not per-practice-accurate. Narration unaffected (the manifest binds
instruction text, not the cadence line).

Phase 7 (view conversion): all chrome renders via utils.strings —
under EN, tr returns the exact pinned label-contract literals; widget
keys and the subheader/code structure are unchanged.
"""
from __future__ import annotations

import streamlit as st

from utils.session_logic import get_session_position
from utils.breathing_logic import get_breathing_practices, get_safety_text
from utils.assets import render_image, render_audio
from utils.strings import tr

STARTED_KEY = "breathing_started"  # STATE.md: dict[str, bool] code -> running

# 40px top margin + 120px ring + 36px bottom scale overflow + slack.
RING_HEIGHT = 240


def _metronome_html(practice: dict, suffix: str) -> str:
    """Self-contained metronome fragment for st.iframe.

    Auto-stopping ring: iteration count = prescribed cycles; parks at the
    resting scale (fill-mode forwards). Deliberately script-free (pure
    CSS). The prefers-reduced-motion override is intentionally disabled
    (product decision) — see module docstring and DECISIONS.md.
    """
    total = practice["inhale_s"] + practice["hold_s"] + practice["exhale_s"]
    inhale_end = (practice["inhale_s"] / total) * 100 if total else 50
    hold_end = ((practice["inhale_s"] + practice["hold_s"]) / total) * 100 \
        if total else 50
    name = f"breathe-{suffix}"
    return f"""
<style>
html, body {{ margin: 0; padding: 0; }}
.{name}-circle {{
width: 120px; height: 120px; border-radius: 50%;
background: #4a90d9; margin: 40px auto;
animation-name: {name};
animation-duration: {total}s;
animation-timing-function: ease-in-out;
animation-iteration-count: {practice['cycles']};
animation-fill-mode: forwards;
}}
@keyframes {name} {{
0% {{ transform: scale(1); }}
{inhale_end:.1f}% {{ transform: scale(1.6); }}
{hold_end:.1f}% {{ transform: scale(1.6); }}
100% {{ transform: scale(1); }}
}}
/* Disabled by product decision (change #6): the ring is essential pacing
content and runs unconditionally; Start/Stop satisfy WCAG 2.2.2 and the
static cadence text is the non-animated fallback. See DECISIONS.md.
@media (prefers-reduced-motion: reduce) {{
.{name}-circle {{ animation: none; }}
}}
*/
</style>
<div class="{name}-circle" aria-hidden="true"></div>
"""


def _pruned_started(practices: list, started: dict) -> dict:
    """Pure helper: drop started-flags for codes not in today's schedule."""
    valid = {p["code"] for p in practices}
    return {code: flag for code, flag in started.items() if code in valid}


def render_breathing_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    practices = get_breathing_practices(pos["week"], pos["day"])
    safety = get_safety_text()
    st.title(tr("breathing.title"))
    if not practices:
        st.warning(tr("breathing.no_session"))

    # Self-heal the started-flags to today's schedule (STATE.md rule).
    st.session_state[STARTED_KEY] = _pruned_started(
        practices, st.session_state.get(STARTED_KEY, {}))

    for p in practices:
        started = bool(st.session_state[STARTED_KEY].get(p["code"]))
        st.subheader(f"{p['code']} — {p['title']}")
        st.write(p["purpose"])  # brief description before presentation
        render_image(p.get("image"), label=p["title"],
                     caption=tr("breathing.illustration_caption").format(
                         title=p["title"]))
        st.write(f"_{p['focus']}_")
        st.write(tr("breathing.cadence").format(
            inhale_s=p["inhale_s"], hold_s=p["hold_s"],
            exhale_s=p["exhale_s"], cycles=p["cycles"]))
        st.write(p["instruction"])  # approved copy; plain, not italic
        render_audio(p.get("audio"))  # change #12 — narration alongside
        if started:
            if st.button(tr("breathing.stop_circle").format(title=p["title"]),
                         key=f"btn_breath_stop_{p['code']}", width="stretch"):
                st.session_state[STARTED_KEY][p["code"]] = False
                st.rerun()
        else:
            if st.button(tr("breathing.start_circle").format(title=p["title"]),
                         key=f"btn_breath_start_{p['code']}", width="stretch"):
                # Mutual exclusion: one running ring at a time —
                # simultaneous rings would give conflicting pace cues.
                st.session_state[STARTED_KEY] = {p["code"]: True}
                st.rerun()
        if started:
            st.write(tr("breathing.running_guidance").format(
                cycles=p["cycles"]))
            st.iframe(_metronome_html(p, p["code"].lower()),
                      height=RING_HEIGHT)
        else:
            st.write(tr("breathing.start_guidance").format(
                cycles=p["cycles"]))
        st.info(f"🪑 {safety['chair_standard']}")
        st.info(f"⚠ {safety['orthostatic_warning']}")
        if any(p["code"] == "DB05" for p in practices):
            st.warning(f"⚠ {safety['lightheadedness_valve']}")
    if st.button(tr("breathing.start_exercises"), key="btn_start_exercises",
                 width="stretch", type="primary"):
        st.session_state.pop(STARTED_KEY, None)  # leaving the page clears flags
        st.session_state["current_state"] = "EXERCISE_SESSION"
        st.rerun()