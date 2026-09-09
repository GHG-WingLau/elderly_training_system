"""Phase 3/5 — DAILY_HUB view.

Step 2a: logout control (btn_logout) → utils.auth.clear_session_state,
the single logout path.

Step 2b follow-up (bookmark reminder): shown ONLY when the remember-me
token is in the URL (?t=) — exactly the sessions where bookmarking the
current page captures persistent login. Users who declined "remember"
see no tip (the advice wouldn't work for them). Always-on-while-token-
present for beta; a dismiss-once variant needs DB state and is a
recorded post-beta refinement option. Known caveat (DECISIONS): a
bookmark made before a later logout holds a dead token — one re-login
and re-bookmark recovers.

Phase 7 (7.4): language picker below the title — the post-auth call
site; selections persist to users.locale here.

Phase 7 (view conversion): chrome via utils.strings; the info line
composes level_display (the accepted descriptor gain materializes for
EN here). BOOKMARK_TIP is retained as the EN contract constant — the
rendered tip comes from ui_strings.
"""
from __future__ import annotations

import streamlit as st

from utils.session_logic import get_session_position
from utils.auth import TOKEN_PARAM, clear_session_state
from utils.locale import render_language_picker
from utils.strings import tr, level_display

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
        st.info(tr("hub.bookmark_tip"))  # targeted: token present
    st.divider()
    if st.button(tr("hub.logout"), key="btn_logout"):
        clear_session_state()
        st.rerun()