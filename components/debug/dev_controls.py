"""Debug controls — visible only with ?debug=true. QA traversal of the
5-week program. Overrides are session-only, validated, and affect BOTH reads
AND writes at the chosen position. Use a throwaway account for QA."""
from __future__ import annotations
import streamlit as st


def maybe_render_debug() -> None:
    if not st.session_state.get("debug", False):
        st.session_state.pop("debug_override", None)   # never leak into normal views
        return
    ov = st.session_state.get("debug_override")
    with st.expander("🛠 Debug controls (dev only)", expanded=ov is not None):
        st.caption("QA traversal. An active override changes the position the "
                   "app reads AND writes. Use a throwaway account.")
        if ov:
            st.warning(f"Override ACTIVE → Cycle {ov['cycle']}, "
                       f"Week {ov['week']}, Day {ov['day']}")
        w = st.number_input("Force week", 0, 4, 0, key="debug_week")
        d = st.number_input("Force day", 1, 7, 1, key="debug_day")
        c = st.number_input("Force cycle", 1, 99, 1, key="debug_cycle")
        col1, col2 = st.columns(2)
        if col1.button("Apply Override", width="stretch"):
            if 0 <= int(w) <= 4 and 1 <= int(d) <= 7 and 1 <= int(c) <= 99:
                st.session_state["debug_override"] = {
                    "cycle": int(c), "week": int(w), "day": int(d)}
                st.rerun()
            else:
                st.error("Invalid override values.")
        if col2.button("Clear Override", width="stretch"):
            st.session_state.pop("debug_override", None)
            st.rerun()