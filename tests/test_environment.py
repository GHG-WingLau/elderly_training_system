"""Environment guard: documents the minimum validated Streamlit and the
Postgres driver requirement; fails with actionable guidance if the runtime
drifts."""
import re

import streamlit


def test_streamlit_meets_minimum():
    m = re.match(r"(\d+)\.(\d+)", streamlit.__version__)
    assert m, f"unparseable streamlit version: {streamlit.__version__}"
    major, minor = int(m.group(1)), int(m.group(2))
    assert (major, minor) >= (1, 28), (
        f"Streamlit >= 1.28 required (AppTest + form support); found "
        f"{streamlit.__version__}. Use the pinned environment: "
        f"python3.12 -m venv .venv && source .venv/bin/activate && "
        f"pip install -r requirements.txt"
    )


def test_psycopg_driver_available():
    """Phase 6 Step 1: the DB layer runs on psycopg (strategy A — one
    dialect, Docker/Neon Postgres)."""
    import psycopg
    m = re.match(r"(\d+)\.(\d+)", psycopg.__version__)
    assert m, f"unparseable psycopg version: {psycopg.__version__}"
    major, minor = int(m.group(1)), int(m.group(2))
    assert (major, minor) >= (3, 1), (
        f"psycopg >= 3.1 required; found {psycopg.__version__}. "
        f"pip install -r requirements.txt"
    )