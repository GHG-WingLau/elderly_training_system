"""Environment guard: Streamlit floor + exact-pin enforcement + the
Postgres driver requirement; fails with actionable guidance."""
import re
from pathlib import Path

import streamlit

REQ_PATH = Path(__file__).resolve().parent.parent / "requirements.txt"


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


def test_streamlit_pin_is_exact():
    """Deploy lesson: Cloud resolved 'streamlit>=1.62.0' to 1.63.0 — an
    unvalidated runtime outside every platform fact recorded in
    DECISIONS.md. The pin must be exact; this guards against the file
    quietly re-loosening to a floor."""
    req = REQ_PATH.read_text()
    line = next((l for l in req.splitlines()
                 if l.strip().startswith("streamlit")), None)
    assert line is not None, "no streamlit entry in requirements.txt"
    assert line.strip() == "streamlit==1.62.0", (
        f"streamlit must be EXACTLY pinned (platform-fact envelope), "
        f"found: {line.strip()!r}")


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