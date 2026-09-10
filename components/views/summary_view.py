"""Phase 3 — WORKOUT_SUMMARY.

Phase 7: chrome via utils.strings.

Phase 9, Step 1 (debriefing redesign, user-approved): personalized
congratulation; "Today you trained:" body-region bullets with localized
TITLES + the RPE word/emoji the user tapped (reuses the localized
training.rpe_N descriptors); a DB-derived sessions-this-week counter;
the auto-adjust reassurance (states existing autoregulation — the #14
precedent class); a breathing habit line. The numeric average-RPE line
is dropped by design (ui_strings keys summary.completed /
summary.avg_rpe stay dormant).

v4 (translation round complete): ALL Step-1 strings now render from
ui_strings — adjust_note and habit_note joined (the earlier return was
short three strings; the completion round landed them). The constants
below remain as the EN contract values (equal the ui_strings EN
values — the tests' equality against rendered output pins drift).
"""
from __future__ import annotations

import streamlit as st

from db import queries
from utils.session_logic import parse_rpe_scores
from utils.exercise_logic import get_card
from utils.strings import tr

# EN contract constants — equal the ui_strings EN values.
ADJUST_NOTE = ("Your effort ratings are how the program adjusts itself "
               "for next week — there is nothing you need to change.")
HABIT_NOTE = ("The breathing practice at the start of every session helps "
              "you settle in — see you tomorrow!")


def _rating_word(score: int | None) -> str:
    """The RPE word + emoji the user just tapped — the same localized
    descriptor shown on the training page (words instead of numbers)."""
    return f" ({tr(f'training.rpe_{score}')})" if score else ""


def render_summary(user: dict) -> None:
    flags = st.session_state.get("session_flags", {})
    rpe_str = flags.get("last_rpe", "")
    daily = flags.get("last_daily", [])
    rpe_map = parse_rpe_scores(rpe_str)

    st.title(tr("summary.title"))
    st.balloons()
    st.write(tr("summary.congrats").format(username=user["username"]))

    st.write(tr("summary.trained_today"))
    for cid in daily:
        card = get_card(cid)
        region = tr(f"summary.region_{card['category']}")
        st.write(f"• {region} — **{card['title']}**"
                 f"{_rating_word(rpe_map.get(cid))}")

    # Real progress data — the just-submitted workout is already in the
    # DB when this renders; count the training days of its week.
    done = queries.get_completed_days(user["email"],
                                       user["current_cycle"])
    if done:
        week = max(w for w, _ in done)
        count = sum(1 for w, d in done if w == week and d <= 6)
        st.info(tr("summary.sessions_week").format(n=count))
    st.caption(tr("summary.adjust_note"))
    st.caption(tr("summary.habit_note"))

    if st.button(tr("summary.return_hub"), key="btn_return_hub",
                 width="stretch", type="primary"):
        st.session_state["session_flags"] = {}
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()