"""Phase 3/5 — DAILY_HUB view.

Step 2a: logout control (btn_logout) → utils.auth.clear_session_state,
the single logout path.

Step 2b follow-up (bookmark reminder): shown ONLY when the remember-me
token is in the URL (?t=) — exactly the sessions where bookmarking the
current page captures persistent login. Users who declined "remember"
see no tip (the advice wouldn't work for them).

Phase 7 (7.4): language picker below the title; the info line composes
level_display. BOOKMARK_TIP is retained as the EN contract constant.

Phase 8 (first-run guidance, option B): the hub hint (first visit,
dismiss-once, profile-backed via users.ui_hints) renders above the
day's primary action; the persistent "How to use" expander below the
bookmark tip is the re-access path that makes dismissal safe. Copy is
provisional EN (utils/hints constants) — ui_strings migration with the
zh translations is the next change. The bookmark-tip dismiss-once
(un-parked) will ride the same hint store.
"""
from __future__ import annotations

import streamlit as st

from utils.session_logic import get_session_position
from utils.auth import TOKEN_PARAM, clear_session_state
from utils.locale import render_language_picker
from utils.strings import tr, level_display
from utils.hints import (HINT_BOOKMARK, HINT_HUB, render_help_expander,
                         render_hint)

BOOKMARK_TIP = ("💡 Stay logged in: bookmark this page now — on your phone, "
                "use Add to Home Screen. Next time, your bookmark opens "
                "straight to this page, with no need to log in again.")


def render_daily_hub(user: dict) -> None:
    pos = get_session_position(user["email"])
    if pos["is_program_complete"]:
        st.session_state["current_state"] = "PROGRAM_COMPLETE"
        st.rerun()
        return
    st.title(tr("hub.title").format(username=user["username"]))
    render_language_picker()  # Phase 7 (7.4)
    st.info(tr("hub.info").format(
        level=level_display(user["level"]), cycle=pos["cycle"],
        week=pos["week"], day=pos["day"]))
    render_hint(user, HINT_HUB)
    if pos["is_rest_day"]:
        st.write(tr("hub.rest_day"))
        if st.button(tr("hub.start_review"), key="btn_start_review",
                     width="stretch", type="primary"):
            st.session_state["current_state"] = "DAY_7_REST"
            st.rerun()
    else:
        st.write(tr("hub.workout_day"))
        if st.button(tr("hub.start_workout"), key="btn_start_workout",
                     width="stretch", type="primary"):
            st.session_state["current_state"] = "BREATHING_SESSION"
            st.rerun()
    if st.query_params.get(TOKEN_PARAM):
        # Phase 8: dismiss-once (un-parked) — still token-conditional.
        render_hint(user, HINT_BOOKMARK, body=tr("hub.bookmark_tip"))
    render_help_expander()  # Phase 8 — persistent, never dismissed
    st.divider()
    if st.button(tr("hub.logout"), key="btn_logout"):
        clear_session_state()
        st.rerun()