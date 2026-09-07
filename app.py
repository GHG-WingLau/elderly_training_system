"""Elderly Online Training System — entry point & state router (Phase 5).

Change #9: transition-gated scroll reset (fingerprint compared after each
completed render; instant scrollTo(0,0) via st.iframe on change; plain
reruns preserve the viewport).

Change #11-B: support-contact footer rendered centrally after the routed
view.

Step 2b: try_restore_session() before routing — a valid ?t= session
token restores authentication at boot (st.session_state dies with the
WebSocket session; the URL token survives reload/reopen-with-full-URL).

Step 3: ?debug=true is honored only when the server-side dev_tools
secret is enabled (utils.dev_gate). On Streamlit Cloud the secret is
absent — the parameter is fully inert; debug controls are stripped in
production. Local dev: dev_tools = true in .streamlit/secrets.toml.

Vehicle note (final record): the POSITIONAL st.iframe argument is the
validated vehicle for raw HTML on pinned Streamlit 1.62.0. "srcdoc=" is
not a parameter of st.iframe on 1.62 — never used. st.html is not
usable on 1.62; the deprecated st.components.v1.html is not shipped.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings(
    "ignore", message="coroutine 'expire_cache' was never awaited",
    category=RuntimeWarning,
)
import streamlit as st
from pathlib import Path
from db.database import init_db
from components.views.auth_view import render_auth
from components.debug.dev_controls import maybe_render_debug
from components.locked.onboarding_wizard import render_onboarding_wizard
from components.views.daily_hub import render_daily_hub
from components.views.breathing_view import render_breathing_session
from components.views.training_view import render_training_session
from components.views.summary_view import render_summary
from components.views.rest_view import render_rest_view
from components.views.program_complete import render_program_complete
from utils.contact import render_support_footer
from utils.auth import try_restore_session
from utils.dev_gate import dev_tools_enabled

st.set_page_config(page_title="Elderly Training", page_icon="🏃",
                   layout="centered", initial_sidebar_state="collapsed")

# Inject WCAG baseline CSS (absolute path — CWD-independent)
CSS_PATH = Path(__file__).resolve().parent / "styles" / "custom.css"
with open(CSS_PATH) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Change #9: transition-gated scroll-to-top -----------------------------
SCROLL_TOP_HTML = r"""
<script>
(function () {
  try {
    var w = (window.parent !== window) ? window.parent : window;
    var doc = w.document;
    var moved = [];
    function toTop(el, name) {
      if (el && el.scrollTop > 0) {
        if (el.scrollTo) { el.scrollTo({ top: 0, left: 0, behavior: "auto" }); }
        else { el.scrollTop = 0; }
        moved.push(name);
      }
    }
    if (doc.scrollingElement) { toTop(doc.scrollingElement, "document"); }
    ["[data-testid='stAppViewContainer']", ".stApp",
     "[data-testid='stMain']", "section.main"].forEach(function (sel) {
      toTop(doc.querySelector(sel), sel);
    });
    w.scrollTo(0, 0);
    console.log("[scroll-reset] fired → moved: " +
                (moved.join(", ") || "(already at top)"));
  } catch (e) {
    console.log("[scroll-reset] blocked:", e);
  }
})();
</script>
"""


def _reset_scroll_on_transition() -> None:
    """Emit scroll-to-top once when the rendered page changed.

    Fingerprint = (authenticated, current_state, onboarding_step). Emission
    failure is swallowed: a UX nicety must never break a render — which
    also means vehicle wiring is invisible to pytest, so "transitions snap
    to top + a [scroll-reset] console line" is a permanent manual-QA line.
    """
    fp = (
        st.session_state.get("authenticated"),
        st.session_state.get("current_state"),
        st.session_state.get("onboarding_step"),
    )
    if fp != st.session_state.get("prev_fingerprint"):
        st.session_state["prev_fingerprint"] = fp
        try:
            st.iframe(SCROLL_TOP_HTML, height=1)
        except Exception:
            pass  # scroll reset is never worth crashing a render for


def _route() -> None:
    """Render the current view (routing logic unchanged from Phase 5)."""
    if not st.session_state["authenticated"]:
        render_auth()
        maybe_render_debug()
        return
    user = st.session_state["user"]
    if not user or not user.get("level"):
        st.session_state["current_state"] = "ONBOARDING_SARC_F"
        render_onboarding_wizard(user)
        maybe_render_debug()
        return
    state = st.session_state.get("current_state", "DAILY_HUB")
    if state == "BREATHING_SESSION":
        render_breathing_session(user)
    elif state == "EXERCISE_SESSION":
        render_training_session(user)
    elif state == "WORKOUT_SUMMARY":
        render_summary(user)
    elif state == "DAY_7_REST":
        render_rest_view(user)
    elif state == "PROGRAM_COMPLETE":
        render_program_complete(user)
    else:  # DAILY_HUB (default)
        st.session_state["current_state"] = "DAILY_HUB"
        render_daily_hub(user)
    maybe_render_debug()


def main() -> None:
    init_db()
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user_email", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("current_state", "UNAUTHENTICATED")
    st.session_state.setdefault("session_flags", {})
    # Step 3: ?debug honored only with the server-side dev_tools secret —
    # inert on Cloud (no secret), opt-in locally via secrets.toml.
    st.session_state.setdefault(
        "debug",
        dev_tools_enabled() and
        st.query_params.get("debug", "false").lower() == "true")
    if not st.session_state["authenticated"]:
        try_restore_session()  # Step 2b — ?t= token survives reload
    _route()
    render_support_footer()  # change #11-B — every page, one central call
    # Emitted last, on every completed render (change #9).
    _reset_scroll_on_transition()


if __name__ == "__main__":
    main()