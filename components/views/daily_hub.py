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
"""
from __future__ import annotations

import streamlit as st

from utils.session_logic import get_session_position
from utils.auth import TOKEN_PARAM, clear_session_state

BOOKMARK_TIP = ("💡 Stay logged in: bookmark this page now — on your phone, "
                "use Add to Home Screen. Next time, your bookmark opens "
                "straight to this page, with no need to log in again.")


def render_daily_hub(user: dict) -> None:
    pos = get_session_position(user["email"])
    if pos["is_program_complete"]:
        st.session_state["current_state"] = "PROGRAM_COMPLETE"
        st.rerun()
        return
    st.title(f"Welcome, {user['username']} 👋")
    st.info(f"**Level:** {user['level']} · **Cycle** {pos['cycle']} · "
            f"**Week** {pos['week']} · **Day** {pos['day']}")
    if pos["is_rest_day"]:
        st.write("Today is your **rest & review day**. Light movement only.")
        if st.button("Start Weekly Review", key="btn_start_review",
                     width="stretch", type="primary"):
            st.session_state["current_state"] = "DAY_7_REST"
            st.rerun()
    else:
        st.write("Today's session: **breathing + 3 exercises** (~15–30 min).")
        if st.button("Start Today's Workout", key="btn_start_workout",
                     width="stretch", type="primary"):
            st.session_state["current_state"] = "BREATHING_SESSION"
            st.rerun()
    if st.query_params.get(TOKEN_PARAM):
        st.info(BOOKMARK_TIP)  # targeted: token present = bookmark works
    st.divider()
    if st.button("Log out", key="btn_logout"):
        clear_session_state()
        st.rerun()