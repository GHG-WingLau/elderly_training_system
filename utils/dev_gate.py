"""Server-side dev-tools gate (Step 3) — ?debug=true is honored ONLY when
dev_tools is enabled in st.secrets. On Streamlit Cloud the secret is
deliberately absent -> the URL parameter is fully inert (debug controls
stripped in production, per the deployment decision). Local dev: set
dev_tools = true in .streamlit/secrets.toml to restore ?debug QA
traversal. st.secrets raises when no secrets file exists — swallowed to
False (default-deny)."""
from __future__ import annotations

import streamlit as st


def dev_tools_enabled() -> bool:
    try:
        return bool(st.secrets.get("dev_tools", False))
    except Exception:
        return False