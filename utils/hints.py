"""First-run in-flow guidance (Phase 8, option B — team decision).

Dismiss-once hints rendered exactly where the action is — the
bookmark-tip / #14 in-flow guidance pattern, generalized. Backed by
users.ui_hints (JSONB: dismissed hint key -> ISO date; NULL = all
hints active). The persistent "How to use" expander on the hub is the
re-access path that makes dismiss-once safe.

v3 (translation round landed): all copy renders from ui_strings
(hints.* keys); the module constants remain as the EN contract values
(the REMEMBER_LABEL pattern — they equal the EN ui_strings values, and
the tests' equality against rendered output pins any drift). render_hint
is KEY-DRIVEN, with an explicit-body override for special cases; the
bookmark tip (STATE.md Phase 6 refinement, un-parked) rides the same
store as HINT_BOOKMARK — token-conditional, dismiss-once, localized
body from hub.bookmark_tip.

Design rules (elderly / WCAG): no auto-advance, no timeouts; dismiss
is the only required action; hints never block the flow; 48px dismiss
target via the existing button CSS.
"""
from __future__ import annotations

import streamlit as st

from db import queries
from utils.strings import tr

# Hint keys — DB-stable identifiers (part of the ui_hints contract;
# renaming one orphans existing dismissal state).
HINT_HUB = "hint_hub"
HINT_BREATHING = "hint_breathing"
HINT_TRAINING = "hint_training"
HINT_SUMMARY = "hint_summary"
HINT_REST = "hint_rest"
HINT_BOOKMARK = "bookmark_tip"

# ui_strings suffix per standard hint key (hints.{suffix}_title/_body).
_HINT_STRINGS = {
    HINT_HUB: "hub",
    HINT_BREATHING: "breathing",
    HINT_TRAINING: "training",
    HINT_SUMMARY: "summary",
    HINT_REST: "rest",
}

# EN contract constants — must equal the EN ui_strings values (tests
# assert these against rendered output; drift fails loudly).
GOT_IT_LABEL = "Got it"
HINT_HUB_TITLE = "Welcome! Here's how it works"
HINT_BREATHING_TITLE = "First time here? Follow the circle"
HINT_TRAINING_TITLE = "Your exercises for today"
HINT_SUMMARY_TITLE = "Well done — that's today's session complete!"
HINT_REST_TITLE = "Rest and review day"
HELP_LABEL = "How to use"


def is_dismissed(user: dict, key: str) -> bool:
    """Pure read from the user dict (ui_hints JSONB arrives as a dict
    via psycopg; NULL/absent = not dismissed)."""
    hints = (user or {}).get("ui_hints") or {}
    return key in hints


def render_hint(user: dict, key: str, title: str | None = None,
                body: str | None = None) -> None:
    """Render an in-flow hint with a dismiss-once button.

    Key-driven: title/body come from the locale's ui_strings
    (hints.{suffix}_title / _body). Explicit overrides serve special
    cases — the bookmark tip passes body=tr("hub.bookmark_tip") with no
    title, and its caller guards the ?t= condition.

    Dismiss = single DB write + session user refresh (the Phase 4
    rule) + rerun; the hint then stays hidden on every device.
    """
    if is_dismissed(user, key):
        return
    if title is None and body is None:
        suffix = _HINT_STRINGS[key]
        title = tr(f"hints.{suffix}_title")
        body = tr(f"hints.{suffix}_body")
    block = f"**{title}**\n\n{body}" if title else body
    st.info(block)
    if st.button(tr("hints.got_it"), key=f"btn_hint_{key}",
                 width="stretch"):
        queries.dismiss_ui_hint(user["email"], key)
        st.session_state["user"] = queries.get_user(user["email"])
        st.rerun()


def render_help_expander() -> None:
    """The persistent re-access path — always available, never
    dismissed."""
    with st.expander(tr("hints.help_label")):
        st.write(tr("hints.help_body"))