# Project Reference Document

## 1. Executive Summary & Tech Stack
- **Language:** Python
- **Database:** SQLite
- **Generated On:** Automated Script

## 2. Project Directory Tree Structure
```text
elderly_training_system/
├── .pytest_cache/
│   ├── v/
│   │   └── cache/
│   └── README.md
├── .streamlit/
├── assets/
│   ├── exercises/
├── components/
│   ├── debug/
│   │   └── dev_controls.py
│   ├── locked/
│   │   ├── baseline_timers.py
│   │   ├── onboarding_wizard.py
│   │   └── sarc_f_assessment.py
│   ├── views/
│   │   ├── auth_view.py
│   │   ├── breathing_view.py
│   │   ├── daily_hub.py
│   │   ├── program_complete.py
│   │   ├── rest_view.py
│   │   ├── summary_view.py
│   │   ├── training_view.py
│   │   └── training_view_container.py
├── data/
│   ├── breathing_sequences.json
│   ├── exercise_cards.json
│   ├── prescriptions.json
│   └── scoring_rubrics.json
├── db/
│   ├── database.py
│   ├── queries.py
│   └── schema_sqlite.sql
├── docs/
│   ├── AGENT_CONTEXT_PACK.md
│   ├── DECISIONS.md
│   ├── README.md
│   └── STATE.md
├── instance/
├── styles/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── helpers_e2e.py
│   ├── test_assement_logic.py
│   ├── test_autoregulation_logic.py
│   ├── test_compute_final_level.py
│   ├── test_data_integrity.py
│   ├── test_e2e_onboarding.py
│   ├── test_e2e_workout_loop.py
│   ├── test_environment.py
│   ├── test_exercise_logic.py
│   ├── test_session_logic.py
│   └── test_state_machine.py
├── utils/
│   ├── assessment_logic.py
│   ├── autoregulation_logic.py
│   ├── breathing_logic.py
│   ├── exercise_logic.py
│   ├── session_logic.py
│   └── state_machine.py
├── app.py
├── bundle_project.py
├── pytest.ini
└── requirements.txt
```

## 3. Complete Source Code
### File: `app.py`
```python
"""Elderly Online Training System — entry point & state router (Phase 4)."""
from __future__ import annotations
import warnings
warnings.filterwarnings(
    "ignore", message="coroutine 'expire_cache' was never awaited",
    category=RuntimeWarning,
)
import streamlit as st

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

st.set_page_config(page_title="Elderly Training", page_icon="🏃",
                   layout="centered", initial_sidebar_state="collapsed")

from pathlib import Path   # add to imports

CSS_PATH = Path(__file__).resolve().parent / "styles" / "custom.css"
with open(CSS_PATH) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main() -> None:
    init_db()
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user_email", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("current_state", "UNAUTHENTICATED")
    st.session_state.setdefault("session_flags", {})
    st.session_state.setdefault("debug", st.query_params.get("debug", "false").lower() == "true")

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
    else:  # DAILY_HUB
        st.session_state["current_state"] = "DAILY_HUB"
        render_daily_hub(user)
    maybe_render_debug()


if __name__ == "__main__":
    main()
```

### File: `bundle_project.py`
```python
import os
from pathlib import Path

def bundle_project_to_markdown(output_filename="project_reference.md", ignore_dirs=None, extensions=None):
    """
    Bundles local project files into a single, clean Markdown document.
    """
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules', '.idea', '.vscode'}
    if extensions is None:
        extensions = {'.py', '.sql', '.md', '.txt', '.json', '.ini', '.yaml', '.yml'}
        
    project_root = Path.cwd()
    
    def generate_tree(dir_path, prefix=""):
        """Generates a visual text-based directory tree."""
        tree_lines = []
        try:
            items = sorted(list(dir_path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return tree_lines
            
        items = [item for item in items if item.name not in ignore_dirs]
        
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                tree_lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                tree_lines.extend(generate_tree(item, new_prefix))
            else:
                if item.suffix.lower() in extensions:
                    tree_lines.append(f"{prefix}{connector}{item.name}")
        return tree_lines

    markdown_sections = []
    
    # 1. Header & Summary
    markdown_sections.append("# Project Reference Document\n")
    markdown_sections.append("## 1. Executive Summary & Tech Stack\n- **Language:** Python\n- **Database:** SQLite\n- **Generated On:** Automated Script\n")
    
    # 2. Directory Tree
    markdown_sections.append("## 2. Project Directory Tree Structure\n```text")
    markdown_sections.append(project_root.name + "/")
    markdown_sections.extend(generate_tree(project_root))
    markdown_sections.append("```\n")
    
    # 3. Source Code Files
    markdown_sections.append("## 3. Complete Source Code")
    
    # Walk through files to grab code
    for root, dirs, files in os.walk(project_root):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in sorted(files):
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions and file_path.name != output_filename:
                relative_path = file_path.relative_to(project_root)
                
                # Determine language for markdown syntax highlighting
                lang = file_path.suffix.lower().replace('.', '')
                if lang in ['txt', 'ini']:
                    lang = 'text'
                elif lang == 'sql':
                    lang = 'sql'
                elif lang == 'py':
                    lang = 'python'
                
                markdown_sections.append(f"### File: `{relative_path}`")
                markdown_sections.append(f"```{lang}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    markdown_sections.append(content)
                except Exception as e:
                    markdown_sections.append(f"/* Error reading file: {str(e)} */")
                    
                markdown_sections.append("```\n")
                
    # 4. Templates for placeholder fields
    markdown_sections.append("## 4. Modification Log")
    markdown_sections.append("| Date | Change Summary | Author | Impact |\n|---|---|---|---|\n| [Date] | Initial code bundling | Automation | Compiled all local modules |\n")
    markdown_sections.append("## 5. Run & Verification Guide\n1. **Environment Setup:** Ensure Python 3.x is installed.\n2. **Database Initialization:** The SQLite database will auto-initialize upon running the main entry script.\n3. **Execution:** Run the primary application file (e.g., `python app.py`).")

    # Write out the Markdown file
    output_path = project_root / output_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_sections))
        
    print(f"Successfully generated reference document at: {output_path}")

if __name__ == '__main__':
    bundle_project_to_markdown()

```

### File: `pytest.ini`
```text
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
filterwarnings =
    ignore:Type google\.protobuf:DeprecationWarning
    ignore:datetime\.datetime\.utcfromtimestamp:DeprecationWarning
    ignore:coroutine 'expire_cache' was never awaited:RuntimeWarning
```

### File: `requirements.txt`
```text
streamlit>=1.62.0
jsonschema==4.23.0
pytest==8.3.3
# Minimum validated runtime: Streamlit 1.28 (enforced by tests/test_environment.py).
# The pin above is the release target — run the full suite on it before sign-off.
```

### File: `.pytest_cache/README.md`
```md
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

```

### File: `tests/__init__.py`
```python

```

### File: `tests/conftest.py`
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

### File: `tests/helpers_e2e.py`
```python
"""Shared AppTest helpers for E2E tests.

STRATEGY (v4.1, post-4-rounds-of-AppTest-quirks): AppTest is used only for
flows that do NOT UI-drive the multi-step wizard (st.form + per-step
st.rerun() replay is unreliable in this Streamlit version range — stale
keyed-widget state across internal reruns). Onboarded users are SEEDED
directly via the DB layer; wizard logic is covered hermetically by
test_compute_final_level / test_assessment_logic.

Widget lookup matches the .label attribute by iteration (WidgetList(label=)
is unsupported here). Raw sqlite3 reads bypass Streamlit caching."""
from pathlib import Path
import sqlite3

import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def _find(widget_list, label):
    for el in widget_list:
        if getattr(el, "label", None) == label:
            return el
    raise AssertionError(
        f"widget not found with label={label!r}; available labels: "
        f"{[getattr(e, 'label', None) for e in widget_list]}")


def _find_button(at, label):
    for accessor in ("form_submit_button", "button"):
        wl = getattr(at, accessor, None)
        if wl is None:
            continue
        for el in wl:
            if getattr(el, "label", None) == label:
                return el
    raise AssertionError(f"button not found: {label!r}")


def _click(at, label):
    _find_button(at, label).click()


def has_button(at, label) -> bool:
    for accessor in ("form_submit_button", "button"):
        wl = getattr(at, accessor, None)
        if wl is None:
            continue
        for el in wl:
            if getattr(el, "label", None) == label:
                return True
    return False


def rendered_text(at) -> str:
    parts: list[str] = []
    for attr in ("title", "header", "subheader", "markdown", "text", "caption",
                 "info", "success", "warning", "error"):
        try:
            for el in getattr(at, attr):
                parts.append(getattr(el, "value", "") or "")
        except Exception:
            pass
    return "\n".join(parts)


def make_app(tmp_path, monkeypatch):
    """Fresh AppTest bound to an isolated per-test SQLite DB."""
    from db import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "e2e.db")
    st.cache_resource.clear()
    at = AppTest.from_file(str(APP_PATH), default_timeout=20)
    at.run()
    return at


def seed_user(email, level, age=70, sex="F",
              sarc_f=0, calf=0, balance=0, chair=0):
    """Create an already-onboarded user directly via the DB layer.
    Keyword args mandatory (signature-drift guard). Call AFTER make_app."""
    from db import queries
    queries.create_user(email=email, username="tester", age=age, sex=sex)
    queries.update_user_level(
        email=email, level=level, total_score=sarc_f + calf + balance + chair,
        sarc_f=sarc_f, calf=calf, balance=balance,
        chair_stand=chair, red_flags="")


def register(at, email, age=70, sex="Female"):
    _find(at.text_input, "Email *").input(email)
    _find(at.text_input, "Username *").input("tester")
    _find(at.number_input, "Age *").set_value(age)
    _find(at.selectbox, "Sex (used for calf & chair-stand norms)").select(sex)
    _click(at, "Create Account")
    at.run()


def login(at, email, username="tester"):
    _find(at.text_input, "Email").input(email)
    _find(at.text_input, "Username").input(username)
    _click(at, "Log In")
    at.run()


def db(tmp_path):
    conn = sqlite3.connect(tmp_path / "e2e.db")
    conn.row_factory = sqlite3.Row
    return conn
```

### File: `tests/test_assement_logic.py`
```python
"""Truth-table contract for the locked assessment module.
These tests ARE the change contract: modifying the ladder or rubrics requires
updating these rows AND clinical sign-off."""
import pytest
from utils.assessment_logic import (
    calculate_total_score, score_calf, score_sls, score_chair_stand,
    assign_level, apply_preference_override,
)


# --- Level assignment ladder (§3.7.4) ---
@pytest.mark.parametrize("red_flags,sarc_f,total,age,expected", [
    ("chest_pain", 0, 0, 60, "Level 0"),   # red flag
    ("", 4, 4, 62, "Level 0"),             # SARC-F override
    ("", 6, 6, 68, "Level 0"),             # SARC-F override
    ("", 3, 9, 70, "Level 0"),             # total >= 8
    ("", 0, 6, 80, "Level 0"),             # age >= 80
    ("", 3, 5, 70, "Level 2"),             # total>=5, age<75
    ("", 3, 5, 76, "Level 1"),             # total>=5, age>=75
    ("", 2, 3, 70, "Level 3"),             # total>=3, age<75
    ("", 2, 3, 76, "Level 2"),             # total>=3, age>=75
    ("", 1, 1, 65, "Level 4"),             # floor
])
def test_assign_level(red_flags, sarc_f, total, age, expected):
    assert assign_level(total, sarc_f, age, red_flags) == expected


# --- Calf circumference rubric ---
@pytest.mark.parametrize("cm,sex,expected", [
    (36.0, "M", 0), (35.9, "M", 1), (34.0, "M", 1), (33.9, "M", 2),
    (34.0, "F", 0), (33.9, "F", 1), (33.0, "F", 1), (32.9, "F", 2),
    (35.0, "U", 1),    # M:1, F:0 -> max 1
    (33.5, "U", 2),    # M:2, F:1 -> max 2
    (36.5, "U", 0),    # both 0
])
def test_score_calf(cm, sex, expected):
    assert score_calf(cm, sex) == expected


# --- Single-leg stance rubric (unisex) ---
@pytest.mark.parametrize("sec,expected", [
    (20.0, 0), (19.9, 1), (10.0, 1), (9.9, 2), (0.0, 2), (32.0, 0),
])
def test_score_sls(sec, expected):
    assert score_sls(sec) == expected


# --- 30-second chair stand rubric ---
@pytest.mark.parametrize("reps,sex,expected", [
    (14, "M", 0), (13, "M", 1), (11, "M", 1), (10, "M", 2),
    (12, "F", 0), (11, "F", 1), (9, "F", 1), (8, "F", 2),
    (12, "U", 1),    # M:1, F:0 -> 1
    (11, "U", 1),    # both 1
    (10, "U", 2),    # both 2
])
def test_score_chair_stand(reps, sex, expected):
    assert score_chair_stand(reps, sex) == expected


# --- Preference override (OQ-10) ---
@pytest.mark.parametrize("level,preference,expected", [
    ("Level 3", "Level 0", "Level 2"),   # lower by one step only
    ("Level 3", "Level 4", "Level 3"),   # never raise
    ("Level 3", "Level 3", "Level 3"),   # same
    ("Level 0", "Level 0", "Level 0"),   # floor
    ("Level 4", "Level 1", "Level 3"),   # one step down
])
def test_apply_preference_override(level, preference, expected):
    assert apply_preference_override(level, preference) == expected


def test_total_score():
    assert calculate_total_score(4, 2, 2, 2) == 10
    assert calculate_total_score(0, 0, 0, 0) == 0
    assert calculate_total_score(10, 2, 2, 2) == 16
```

### File: `tests/test_autoregulation_logic.py`
```python
"""Phase 4 contract — auto-regulation rules, regression, cycle restart."""
import sqlite3
from pathlib import Path
import pytest

from db import queries
from utils.autoregulation_logic import (
    classify, weekly_average_rpe, apply_rule, effective_prescription,
    hard_streak, regression_due, day7_plan,
)
from utils.session_logic import compute_current_position
from utils.exercise_logic import format_prescription


@pytest.fixture
def iso_db(tmp_path, monkeypatch):
    conn = sqlite3.connect(str(tmp_path / "p4.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    schema = (Path(__file__).resolve().parent.parent / "db" / "schema_sqlite.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    monkeypatch.setattr(queries, "get_connection", lambda: conn)
    queries.create_user("u@t.test", "tester", 65, "F")
    queries.update_user_level(
    email="u@t.test", level="Level 2", total_score=5,
    sarc_f=2, calf=1, balance=1, chair_stand=1, red_flags="")
    return conn


def _seed_week(email, cycle, week, rpe_value):
    for day in range(1, 7):
        ids = f"C{day:02d},PC{day:02d},G{day:02d}"
        rpes = ",".join(f"{i}:{rpe_value}" for i in ids.split(","))
        queries.upsert_training_progress(email, cycle, week, day, ids, rpes)


# --- classification boundaries (spec §3.11) ---
@pytest.mark.parametrize("avg,expected", [
    (2.49, "low"), (2.5, "maintain"), (2.6, "maintain"),
    (3.99, "maintain"), (4.0, "high"), (5.0, "high"),
])
def test_classify_boundaries(avg, expected):
    assert classify(avg) == expected


def test_weekly_average_rpe(iso_db):
    _seed_week("u@t.test", 1, 1, 4)          # 18 values of 4
    assert weekly_average_rpe("u@t.test", 1, 1) == pytest.approx(4.0)


def test_weekly_average_rpe_empty(iso_db):
    assert weekly_average_rpe("u@t.test", 1, 3) is None


# --- rule application ---
def test_apply_high_reduces_reps_20pct():
    rx = {"sets": 2, "reps_min": 8, "reps_max": 10, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "high")
    assert (out["reps_min"], out["reps_max"]) == (6, 8)
    assert out["sets"] == 2


def test_apply_high_sets_fallback_at_reps_floor():
    rx = {"sets": 2, "reps_min": 4, "reps_max": 6, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "high")
    assert out["sets"] == 1
    assert out["reps_min"] == 4


def test_apply_low_adds_2_reps():
    rx = {"sets": 2, "reps_min": 8, "reps_max": 10, "hold_s": None,
          "rest_s_min": 60, "rest_s_max": 60}
    out = apply_rule(rx, "low")
    assert (out["reps_min"], out["reps_max"]) == (10, 12)


def test_apply_low_increases_hold_only_when_defined():
    rx0 = {"sets": 2, "reps_min": 6, "reps_max": 8, "hold_s": 10,
           "rest_s_min": 60, "rest_s_max": 90}
    assert apply_rule(rx0, "low")["hold_s"] == 14
    assert apply_rule(dict(rx0, hold_s=None), "low")["hold_s"] is None


def test_apply_maintain_noop():
    rx = {"sets": 3, "reps_min": 12, "reps_max": 15, "hold_s": None,
          "rest_s_min": 30, "rest_s_max": 45}
    assert apply_rule(rx, "maintain") == rx


def test_reps_cap():
    rx = {"sets": 3, "reps_min": 20, "reps_max": 20, "hold_s": None,
          "rest_s_min": 30, "rest_s_max": 45}
    assert apply_rule(rx, "low")["reps_max"] == 20


# --- effective prescription fold ---
def test_effective_prescription_weeks_0_1_are_base(iso_db):
    base = effective_prescription("u@t.test", 1, 0, 2)
    assert (base["reps_min"], base["reps_max"], base["sets"]) == (10, 12, 2)
    assert effective_prescription("u@t.test", 1, 1, 2) == base


def test_effective_prescription_fold_after_hard_week(iso_db):
    _seed_week("u@t.test", 1, 1, 5)          # week 1 high
    rx = effective_prescription("u@t.test", 1, 2, 2)
    assert (rx["reps_min"], rx["reps_max"]) == (8, 9)   # floor(10*.8), floor(12*.8)


def test_effective_prescription_caps(iso_db):
    for w in (1, 2, 3):
        _seed_week("u@t.test", 1, w, 5)
    rx = effective_prescription("u@t.test", 1, 4, 2)    # folds weeks 1-3
    assert (rx["reps_min"], rx["reps_max"], rx["sets"]) == (4, 5, 2)


def test_week0_average_does_not_adjust_week1(iso_db):
    _seed_week("u@t.test", 1, 0, 5)          # week 0 high
    base = effective_prescription("u@t.test", 1, 0, 2)
    assert effective_prescription("u@t.test", 1, 1, 2)["reps_min"] == base["reps_min"]

# --- regression (spec: 2 consecutive weeks >= 4.0; floor Level 0) ---
def test_regression_due_two_high_weeks(iso_db):
    _seed_week("u@t.test", 1, 0, 5)
    _seed_week("u@t.test", 1, 1, 4)
    assert regression_due("u@t.test", 1, 1, 2) == 1


def test_regression_not_due_single_high(iso_db):
    _seed_week("u@t.test", 1, 0, 2)
    _seed_week("u@t.test", 1, 1, 5)
    assert regression_due("u@t.test", 1, 1, 2) is None


def test_regression_boundary_exactly_4(iso_db):
    _seed_week("u@t.test", 1, 0, 4)
    _seed_week("u@t.test", 1, 1, 4)
    assert regression_due("u@t.test", 1, 1, 3) == 2


def test_regression_floor_level0(iso_db):
    _seed_week("u@t.test", 1, 0, 5)
    _seed_week("u@t.test", 1, 1, 5)
    assert regression_due("u@t.test", 1, 1, 0) is None
    assert hard_streak("u@t.test", 1, 1) is True   # streak detected anyway


def test_day7_plan_uses_regressed_level_for_next_rx(iso_db):
    _seed_week("u@t.test", 1, 1, 5)
    _seed_week("u@t.test", 1, 2, 5)
    plan = day7_plan("u@t.test", 1, 2, "Level 2")
    assert plan["regression_to"] == 1
    # next rx from Level 1 base (8,10), folded twice high -> (4,6)
    assert plan["next_week_prescription"]["reps_min"] == 4


# --- cycle restart ---
def test_cycle_restart_preserves_history(iso_db):
    for w in range(5):
        _seed_week("u@t.test", 1, w, 3)
        queries.upsert_rest_assessment("u@t.test", 1, w, 3, "ok", 12, 20, 22)
    assert compute_current_position("u@t.test")["is_program_complete"]
    queries.advance_cycle("u@t.test")
    assert compute_current_position("u@t.test") == {
        "cycle": 2, "week": 0, "day": 1,
        "is_rest_day": False, "is_program_complete": False}
    assert iso_db.execute(
        "SELECT COUNT(*) AS n FROM training_progress").fetchone()["n"] == 30
    assert iso_db.execute(
        "SELECT COUNT(*) AS n FROM rest_assessments").fetchone()["n"] == 5


def test_new_cycle_resets_adjustments(iso_db):
    _seed_week("u@t.test", 1, 1, 5)
    assert effective_prescription("u@t.test", 1, 2, 2)["reps_min"] == 8
    queries.advance_cycle("u@t.test")
    assert effective_prescription("u@t.test", 2, 2, 2)["reps_min"] == 10


def test_set_user_level(iso_db):
    queries.set_user_level("u@t.test", "Level 1")
    assert queries.get_user("u@t.test")["level"] == "Level 1"


def test_count_completed_workouts(iso_db):
    _seed_week("u@t.test", 1, 0, 3)
    assert queries.count_completed_workouts("u@t.test", 1) == 6


# --- display formatting ---
def test_format_prescription():
    rx = {"sets": 2, "reps_min": 6, "reps_max": 8, "hold_s": 10,
          "rest_s_min": 60, "rest_s_max": 90}
    s = format_prescription(rx)
    assert "2 sets" in s and "6–8 reps" in s and "10s hold" in s and "60–90s" in s
    s2 = format_prescription(dict(rx, hold_s=None, rest_s_min=60, rest_s_max=60))
    assert "hold" not in s2 and "60s" in s2
```

### File: `tests/test_compute_final_level.py`
```python
"""Phase 1 safety contract — pure-function tests for onboarding level
computation. Hermetic (no Streamlit runtime, no DB). This IS the change
contract for the locked wizard; modifying the ladder requires updating these
rows AND clinical sign-off."""
import pytest
from components.locked.onboarding_wizard import compute_final_level


@pytest.mark.parametrize(
    "red_flags,sarc_f,calf,bal,chair,age,pref,exp_level,exp_total",
    [
        # SARC-F clinical override (>= 4) -> Level 0
        ("", 6, 0, 0, 0, 70, None, "Level 0", 6),
        ("", 4, 0, 0, 0, 62, None, "Level 0", 4),
        # Total >= 8 -> Level 0
        ("", 3, 2, 2, 1, 70, None, "Level 0", 8),
        # Age >= 80 -> Level 0
        ("", 0, 0, 0, 0, 80, None, "Level 0", 0),
        # total 3, age 70 -> Level 3 ; age 76 -> Level 2
        ("", 2, 1, 0, 0, 70, None, "Level 3", 3),
        ("", 2, 1, 0, 0, 76, None, "Level 2", 3),
        # total 5, age 70 -> Level 2 ; age 76 -> Level 1
        ("", 3, 1, 1, 0, 70, None, "Level 2", 5),
        ("", 3, 1, 1, 0, 76, None, "Level 1", 5),
        # total 1 -> Level 4
        ("", 1, 0, 0, 0, 65, None, "Level 4", 1),
        # Red flag with scores present -> Level 0
        ("chest_pain", 0, 0, 0, 0, 70, None, "Level 0", 0),
        # Red-flag fast path (scores None) -> Level 0, total None
        ("two_or_more_recent_falls", None, None, None, None, 70, None, "Level 0", None),
        # Preference never raises
        ("", 2, 1, 0, 0, 70, "Level 4", "Level 3", 3),
        # Preference lowers by one step only
        ("", 2, 1, 0, 0, 70, "Level 0", "Level 2", 3),
        # Preference equal -> no change
        ("", 2, 1, 0, 0, 70, "Level 3", "Level 3", 3),
    ],
)
def test_compute_final_level(red_flags, sarc_f, calf, bal, chair, age,
                             pref, exp_level, exp_total):
    level, total = compute_final_level(red_flags, sarc_f, calf, bal, chair, age, pref)
    assert level == exp_level
    assert total == exp_total
```

### File: `tests/test_data_integrity.py`
```python
"""Data-contract integrity tests. These run before the logic tests so a
malformed JSON file fails with a clear, localised message instead of
cascading JSONDecodeErrors across the whole suite."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> dict:
    with open(DATA_DIR / name) as f:
        return json.load(f)


def test_scoring_rubrics_loads_and_has_top_level_keys():
    rub = _load("scoring_rubrics.json")
    assert set(rub) >= {
        "sarc_f", "calf_circumference_cm", "single_leg_stance_sec",
        "chair_stand_30s", "level_assignment", "red_flags",
    }


def test_scoring_rubrics_level_thresholds_present():
    la = _load("scoring_rubrics.json")["level_assignment"]
    for key in ("sarc_f_override", "total_high", "age_high",
                "total_mid", "age_mid", "total_low"):
        assert key in la, f"missing level_assignment threshold: {key}"


def test_scoring_rubrics_band_ordering():
    """normal_min must exceed risk_max, otherwise the 0/1/2 bands invert."""
    calf = _load("scoring_rubrics.json")["calf_circumference_cm"]
    for sex in ("M", "F"):
        assert calf[sex]["normal_min"] > calf[sex]["risk_max"]
    chair = _load("scoring_rubrics.json")["chair_stand_30s"]
    for sex in ("M", "F"):
        assert chair[sex]["normal_min"] > chair[sex]["risk_max"]
    sls = _load("scoring_rubrics.json")["single_leg_stance_sec"]["unisex"]
    assert sls["normal_min"] > sls["risk_max"]


def test_sarc_f_has_five_scored_items():
    items = _load("scoring_rubrics.json")["sarc_f"]["items"]
    assert len(items) == 5
    for it in items:
        assert set(it) == {"name", "label", "options"}
        assert len(it["options"]) == 3  # 0, 1, 2


def test_exercise_cards_count_and_shape():
    cards = _load("exercise_cards.json")
    assert len(cards) == 24
    ids = [c["card_id"] for c in cards]
    assert len(ids) == len(set(ids)), "duplicate card_id detected"
    for c in cards:
        assert set(c) >= {"card_id", "title", "category", "base_level",
                          "image", "isometric", "instructions", "position_cues"}
        assert set(c["position_cues"]) == {"0", "1", "2", "3", "4"}


def test_cm01_renamed_and_level_2():
    cards = {c["card_id"]: c for c in _load("exercise_cards.json")}
    assert cards["CM01"]["title"] == "Seated Rhythm March & Arm Drive"
    assert cards["CM01"]["base_level"] == 2


def test_breathing_sequences_structure():
    bs = _load("breathing_sequences.json")
    practices = {p["code"] for p in bs["practices"]}
    assert practices == {"DB01", "DB02", "DB03", "DB04", "DB05"}
    assert len(bs["schedule"]) == 5  # weeks 0-4
    for entry in bs["schedule"]:
        assert set(entry) == {"week", "days_1_3", "days_4_6", "day_7"}
    assert set(bs["safety_text"]) >= {
        "lightheadedness_valve", "orthostatic_warning", "chair_standard",
    }


def test_db05_introduced_week_2_days_4_6():
    """OQ-04 confirmation: DB05 introduced W2 D4-6, not D1-6."""
    schedule = {s["week"]: s for s in _load("breathing_sequences.json")["schedule"]}
    assert schedule[2]["days_1_3"] == ["DB04"]
    assert schedule[2]["days_4_6"] == ["DB05"]

def test_prescriptions_loads():
    p = _load("prescriptions.json")
    assert set(p) == {"0", "1", "2", "3", "4"}
    for lvl, val in p.items():
        assert {"sets", "reps_min", "reps_max", "hold_s",
                "rest_s_min", "rest_s_max"} <= set(val)
        assert val["reps_min"] <= val["reps_max"]
        assert val["rest_s_min"] <= val["rest_s_max"]
    assert p["0"]["hold_s"] == 10            # spec: '6-8 reps (or 10s hold)'
    for lvl in ("1", "2", "3", "4"):
        assert p[lvl]["hold_s"] is None      # spec defines holds for L0 only
```

### File: `tests/test_e2e_onboarding.py`
```python
"""E2E — registration, and routing for seeded onboarded users.
Wizard step logic is covered hermetically (test_compute_final_level,
test_assessment_logic); these tests verify the app SHELL: account creation,
login, and level-aware routing to the Daily Hub."""
from tests.helpers_e2e import (make_app, register, login, seed_user, db,
                               rendered_text, has_button)


def test_registration_creates_user_and_lands_on_wizard(tmp_path, monkeypatch):
    at = make_app(tmp_path, monkeypatch)
    register(at, "e2e1@test", age=70, sex="Female")
    assert "Step 1 of 4" in rendered_text(at)          # wizard safety screening
    row = db(tmp_path).execute(
        "SELECT sex, level FROM users WHERE email=?", ("e2e1@test",)).fetchone()
    assert row["sex"] == "F"
    assert row["level"] is None                        # assessment not yet done


def test_level0_user_login_routes_to_hub(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    seed_user("e2e2@test", "Level 0", sarc_f=6)
    at = make_app(tmp_path, monkeypatch)               # fresh session, same DB
    login(at, "e2e2@test")
    assert "Level 0" in rendered_text(at)
    assert has_button(at, "Start Today's Workout")


def test_level4_user_login_routes_to_hub(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    seed_user("e2e3@test", "Level 4")
    at = make_app(tmp_path, monkeypatch)
    login(at, "e2e3@test")
    assert "Level 4" in rendered_text(at)
    assert has_button(at, "Start Today's Workout")
```

### File: `tests/test_e2e_workout_loop.py`
```python
"""E2E — one full workout day for a seeded user: login → hub → breathing →
exercises → RPE → summary; verified against the DB. Deliberately stops at
WORKOUT_SUMMARY (no click back to hub): each rerun crossing multiplies
AppTest replay risk, and the day-advance is proven by the DB row +
test_session_logic's position tests."""
from tests.helpers_e2e import (make_app, login, seed_user, db,
                               rendered_text, _click)

RPE_HARD = "😣 4 — Hard"


def test_workout_loop_records_session(tmp_path, monkeypatch):
    email = "e2e4@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2", age=70, sex="F")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)

    # DAILY_HUB -> BREATHING_SESSION
    _click(at, "Start Today's Workout"); at.run()
    assert "Stage 1 — Breathing" in rendered_text(at)

    # BREATHING_SESSION -> EXERCISE_SESSION
    _click(at, "Start Exercises"); at.run()
    assert "Stage 2 — Exercises" in rendered_text(at)

    # 3 per-exercise RPE selectboxes -> all Hard
    rpe_boxes = [sb for sb in at.selectbox
                 if (getattr(sb, "label", "") or "").startswith("How hard did that feel?")]
    assert len(rpe_boxes) == 3
    for sb in rpe_boxes:
        sb.select(RPE_HARD)

    # EXERCISE_SESSION -> WORKOUT_SUMMARY
    _click(at, "Submit Workout"); at.run()
    assert "Workout Complete" in rendered_text(at)

    # DB verification (raw reads)
    rows = db(tmp_path).execute(
        "SELECT week, day, exercise_ids, rpe_scores FROM training_progress "
        "WHERE user_email=?", (email,)).fetchall()
    assert len(rows) == 1                              # UPSERT idempotency
    row = rows[0]
    assert (row["week"], row["day"]) == (0, 1)
    ids = row["exercise_ids"].split(",")
    assert len(ids) == 3 and len(set(ids)) == 3
    assert row["rpe_scores"] == ",".join(f"{i}:4" for i in ids)


def test_hub_advances_with_seeded_progress(tmp_path, monkeypatch):
    """Position rendering without live crossings: seed two completed days,
    login, hub must show Day 3."""
    email = "e2e5@test"
    make_app(tmp_path, monkeypatch)
    seed_user(email, "Level 2")
    from db import queries
    for day in (1, 2):
        queries.upsert_training_progress(
            email=email, cycle=1, week=0, day=day,
            exercise_ids="C01,PC01,G01", rpe_scores="C01:3,PC01:3,G01:3")
    at = make_app(tmp_path, monkeypatch)
    login(at, email)
    assert "Day** 3" in rendered_text(at)
```

### File: `tests/test_environment.py`
```python
"""Environment guard: documents the minimum validated Streamlit and fails
with actionable guidance if the runtime drifts below it."""
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
```

### File: `tests/test_exercise_logic.py`
```python
"""Phase 2 contract — curriculum engine. Hermetic: uses an in-memory-style
SQLite temp DB with queries.get_connection patched to bypass @st.cache_resource."""
import sqlite3
from pathlib import Path
from collections import Counter

import pytest

from db import queries
from utils import exercise_logic as el


@pytest.fixture
def iso_db(tmp_path, monkeypatch):
    conn = sqlite3.connect(str(tmp_path / "p2.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    schema = (Path(__file__).resolve().parent.parent / "db" / "schema_sqlite.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    monkeypatch.setattr(queries, "get_connection", lambda: conn)
    queries.create_user("u@t.test", "tester", 65, "F")
    queries.create_user("v@t.test", "tester2", 70, "M")
    return conn


def test_apply_position_cue():
    cards = {c["card_id"]: c for c in el._load_cards()}
    out = el.apply_position_cue(cards["C01"], "Level 3")
    assert out["position_cue"] == cards["C01"]["position_cues"]["3"]
    assert out["card_id"] == "C01"
    assert "position_cue" not in cards["C01"]  # original untouched


def test_get_prescription_all_levels():
    for lvl in range(5):
        p = el.get_prescription(lvl)
        assert {"sets", "reps_min", "reps_max", "hold_s",
                "rest_s_min", "rest_s_max"} <= set(p)


def test_weekly_pool_shape_all_weeks(iso_db):
    for week in range(5):
        pool = el.get_weekly_pool("u@t.test", 1, week)
        assert len(pool) == 6, f"week {week}: {pool}"
        counts = Counter(el._card_category(c) for c in pool)
        assert len(counts) == 3, f"week {week}: {list(counts)}"
        assert all(v == 2 for v in counts.values()), f"week {week}: {dict(counts)}"


def test_week0_week1_are_complement(iso_db):
    w0 = set(el.get_weekly_pool("u@t.test", 1, 0))
    w1 = set(el.get_weekly_pool("u@t.test", 1, 1))
    assert w0.isdisjoint(w1)
    union = w0 | w1
    assert len(union) == 12
    assert all(el._card_category(c) in {"C", "PC", "G"} for c in union)


def test_new_category_introduced(iso_db):
    assert "HF" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 2)}
    assert "SP" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 3)}
    assert "CM" in {el._card_category(c) for c in el.get_weekly_pool("u@t.test", 1, 4)}


def test_daily_set_constraints(iso_db):
    for week in range(5):
        prev = None
        for day in range(1, 7):
            ds = el.select_daily_set("u@t.test", 1, week, day)
            assert len(ds) == 3
            assert len(set(ds)) == 3                          # unique
            cats = [el._card_category(c) for c in ds]
            assert len(set(cats)) == 3                       # distinct categories
            if prev is not None:
                assert set(ds).isdisjoint(prev), f"w{week} d{day}: {ds} ∩ {prev}"
            prev = set(ds)


def test_determinism_same_inputs(iso_db):
    pool1 = el.get_weekly_pool("u@t.test", 1, 2)
    pool2 = el.get_weekly_pool("u@t.test", 1, 2)             # second call reads DB
    assert pool1 == pool2
    for day in range(1, 7):
        a = el.select_daily_set("u@t.test", 1, 2, day)
        b = el.select_daily_set("u@t.test", 1, 2, day)
        assert a == b


def test_pool_persistence(iso_db):
    el.get_weekly_pool("u@t.test", 1, 3)
    row = queries.get_weekly_plan("u@t.test", 1, 3)
    assert row is not None
    assert el.get_weekly_pool("u@t.test", 1, 3) == row.split(",")


def test_two_users_both_valid(iso_db):
    a = el.get_weekly_pool("u@t.test", 1, 2)
    b = el.get_weekly_pool("v@t.test", 1, 2)
    assert len(a) == 6 and len(b) == 6
    assert len({el._card_category(c) for c in a}) == 3
    assert len({el._card_category(c) for c in b}) == 3
```

### File: `tests/test_session_logic.py`
```python
"""Phase 3 contract — RPE serialization, position computation, UPSERT idempotency."""
import sqlite3
from pathlib import Path
import pytest

from db import queries
from utils.session_logic import format_rpe_scores, parse_rpe_scores, compute_current_position


# --- RPE serialization (pure) ---
def test_format_rpe_scores():
    assert format_rpe_scores({"C01": 2, "PC01": 3, "G02": 4}) == "C01:2,PC01:3,G02:4"


def test_format_rpe_empty():
    assert format_rpe_scores({}) == ""


def test_parse_rpe_scores():
    assert parse_rpe_scores("C01:2,PC01:3,G02:4") == {"C01": 2, "PC01": 3, "G02": 4}


def test_parse_rpe_empty():
    assert parse_rpe_scores("") == {}
    assert parse_rpe_scores(None) == {}


def test_rpe_roundtrip():
    m = {"C01": 1, "PC01": 5, "G02": 3}
    assert parse_rpe_scores(format_rpe_scores(m)) == m


# --- Position computation + idempotency (isolated DB) ---
@pytest.fixture
def iso_db(tmp_path, monkeypatch):
    conn = sqlite3.connect(str(tmp_path / "p3.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    schema = (Path(__file__).resolve().parent.parent / "db" / "schema_sqlite.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    monkeypatch.setattr(queries, "get_connection", lambda: conn)
    queries.create_user("u@t.test", "tester", 65, "F")
    return conn


def test_position_fresh(iso_db):
    pos = compute_current_position("u@t.test")
    assert pos == {"cycle": 1, "week": 0, "day": 1,
                   "is_rest_day": False, "is_program_complete": False}


def test_position_after_day1(iso_db):
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:2,PC01:3,G01:2")
    assert compute_current_position("u@t.test")["day"] == 2


def test_position_after_days1_6_routes_day7(iso_db):
    for d in range(1, 7):
        queries.upsert_training_progress("u@t.test", 1, 0, d, "C01", "C01:2")
    pos = compute_current_position("u@t.test")
    assert pos["week"] == 0 and pos["day"] == 7 and pos["is_rest_day"]
    assert not pos["is_program_complete"]


def test_position_after_day7_advances_week(iso_db):
    for d in range(1, 7):
        queries.upsert_training_progress("u@t.test", 1, 0, d, "C01", "C01:2")
    queries.upsert_rest_assessment("u@t.test", 1, 0, 3, "ok", 12, 20, 22)
    pos = compute_current_position("u@t.test")
    assert pos["week"] == 1 and pos["day"] == 1 and not pos["is_rest_day"]


def test_position_resumes_earliest_gap(iso_db):
    # did days 1 and 3 but skipped 2 -> resume at day 2 (OQ-07)
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01", "C01:2")
    queries.upsert_training_progress("u@t.test", 1, 0, 3, "C01", "C01:2")
    assert compute_current_position("u@t.test")["day"] == 2


def test_position_program_complete(iso_db):
    for w in range(5):
        for d in range(1, 7):
            queries.upsert_training_progress("u@t.test", 1, w, d, "C01", "C01:2")
        queries.upsert_rest_assessment("u@t.test", 1, w, 3, "ok", 12, 20, 22)
    assert compute_current_position("u@t.test")["is_program_complete"]


def test_upsert_idempotency(iso_db):
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:2,PC01:3,G01:4")
    queries.upsert_training_progress("u@t.test", 1, 0, 1, "C01,PC01,G01", "C01:5,PC01:5,G01:5")
    n = iso_db.execute(
        "SELECT COUNT(*) AS n FROM training_progress "
        "WHERE user_email=? AND cycle=1 AND week=0 AND day=1", ("u@t.test",)).fetchone()
    assert n["n"] == 1
    r = iso_db.execute(
        "SELECT rpe_scores FROM training_progress "
        "WHERE user_email=? AND cycle=1 AND week=0 AND day=1", ("u@t.test",)).fetchone()
    assert r["rpe_scores"] == "C01:5,PC01:5,G01:5"

from utils.session_logic import normalize_rpe_score

@pytest.mark.parametrize("value,expected", [
    (1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
    ("3", 3),
    ("😃 1 — Very Easy", 1),
    ("😐 3 — Moderate", 3),
    ("😫 5 — Very Hard", 5),
])
def test_normalize_rpe_valid(value, expected):
    assert normalize_rpe_score(value) == expected


@pytest.mark.parametrize("value", [
    0, 6, -1, "no digit here", "6 reps", None, True, 3.5, ["3"],
])
def test_normalize_rpe_invalid_raises(value):
    with pytest.raises(ValueError):
        normalize_rpe_score(value)

def test_override_training_day():
    pos = compute_current_position("x@t.test",
                                   override={"cycle": 1, "week": 0, "day": 1})
    assert pos == {"cycle": 1, "week": 0, "day": 1,
                   "is_rest_day": False, "is_program_complete": False}

def test_override_day7_is_rest():
    pos = compute_current_position("x@t.test",
                                   override={"cycle": 2, "week": 3, "day": 7})
    assert pos["is_rest_day"] is True
    assert pos["is_program_complete"] is False


@pytest.mark.parametrize("ov", [
    {"cycle": 1, "week": 5, "day": 1},
    {"cycle": 1, "week": -1, "day": 1},
    {"cycle": 1, "week": 0, "day": 0},
    {"cycle": 1, "week": 0, "day": 8},
    {"cycle": 0, "week": 0, "day": 1},
])
def test_override_invalid_raises(ov):
    with pytest.raises(ValueError):
        compute_current_position("x@t.test", override=ov)    
```

### File: `tests/test_state_machine.py`
```python
"""Phase 3 contract — state-machine transitions (pure, no Streamlit)."""
import pytest
from utils.state_machine import transition, is_valid


@pytest.mark.parametrize("current,action,expected", [
    ("UNAUTHENTICATED", "login_register", "CHECK_ONBOARDING"),
    ("CHECK_ONBOARDING", "sarc_f_incomplete", "ONBOARDING_SARC_F"),
    ("CHECK_ONBOARDING", "assessment_complete", "DAILY_HUB"),
    ("ONBOARDING_SARC_F", "complete_assessment", "DAILY_HUB"),
    ("DAILY_HUB", "start_breathing", "BREATHING_SESSION"),
    ("BREATHING_SESSION", "start_exercises", "EXERCISE_SESSION"),
    ("EXERCISE_SESSION", "submit_workout", "WORKOUT_SUMMARY"),
    ("WORKOUT_SUMMARY", "return_to_hub", "DAILY_HUB"),
    ("DAILY_HUB", "start_weekly_review", "DAY_7_REST"),
    ("DAY_7_REST", "complete_weekly_review", "DAILY_HUB"),
    ("PROGRAM_COMPLETE", "retake_assessment", "ONBOARDING_SARC_F"),
    ("PROGRAM_COMPLETE", "restart_current_level", "DAILY_HUB"),
    ("DAY_7_REST", "complete_program", "PROGRAM_COMPLETE"),
])
def test_valid_transitions(current, action, expected):
    assert transition(current, action) == expected
    assert is_valid(current, action)


@pytest.mark.parametrize("current,action", [
    ("DAILY_HUB", "submit_workout"),
    ("EXERCISE_SESSION", "return_to_hub"),
    ("BREATHING_SESSION", "start_breathing"),
    ("WORKOUT_SUMMARY", "start_exercises"),
    ("UNAUTHENTICATED", "start_breathing"),
    ("DAY_7_REST", "start_breathing"),
    ("DAILY_HUB", "complete_program"),
    ("WORKOUT_SUMMARY", "complete_program"),
])
def test_invalid_transitions_raise(current, action):
    assert not is_valid(current, action)
    with pytest.raises(ValueError):
        transition(current, action)
```

### File: `utils/assessment_logic.py`
```python
"""Safety-critical locked module: SARC-F scoring, baseline rubric scoring,
and level assignment. Clinical thresholds are READ FROM data/scoring_rubrics.json
(never hardcoded). If a threshold appears missing, halt and ask — do not invent."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_rubrics_cache: Optional[dict] = None

LEVELS = ["Level 0", "Level 1", "Level 2", "Level 3", "Level 4"]
LEVEL_TO_INT = {lvl: i for i, lvl in enumerate(LEVELS)}


def _load_rubrics() -> dict:
    global _rubrics_cache
    if _rubrics_cache is None:
        with open(DATA_DIR / "scoring_rubrics.json") as f:
            _rubrics_cache = json.load(f)
    return _rubrics_cache


def _band_score(value: float, normal_min: float, risk_max: float) -> int:
    """0 if value >= normal_min; 2 if value < risk_max; else 1."""
    if value >= normal_min:
        return 0
    if value < risk_max:
        return 2
    return 1


def calculate_total_score(sarc_f: int, calf: int, balance: int, chair_stand: int) -> int:
    if not (0 <= sarc_f <= 10):
        raise ValueError(f"SARC-F score out of range: {sarc_f}")
    for name, v in (("calf", calf), ("balance", balance), ("chair_stand", chair_stand)):
        if not (0 <= v <= 2):
            raise ValueError(f"{name} sub-score out of range: {v}")
    return sarc_f + calf + balance + chair_stand


def score_calf(measurement_cm: float, sex: str) -> int:
    rub = _load_rubrics()["calf_circumference_cm"]
    if sex == "M":
        return _band_score(measurement_cm, rub["M"]["normal_min"], rub["M"]["risk_max"])
    if sex == "F":
        return _band_score(measurement_cm, rub["F"]["normal_min"], rub["F"]["risk_max"])
    # 'U' = unspecified → conservative max(male_score, female_score)
    return max(
        _band_score(measurement_cm, rub["M"]["normal_min"], rub["M"]["risk_max"]),
        _band_score(measurement_cm, rub["F"]["normal_min"], rub["F"]["risk_max"]),
    )


def score_sls(seconds: float) -> int:
    band = _load_rubrics()["single_leg_stance_sec"]["unisex"]
    return _band_score(seconds, band["normal_min"], band["risk_max"])


def score_chair_stand(reps: int, sex: str) -> int:
    rub = _load_rubrics()["chair_stand_30s"]
    if sex == "M":
        return _band_score(reps, rub["M"]["normal_min"], rub["M"]["risk_max"])
    if sex == "F":
        return _band_score(reps, rub["F"]["normal_min"], rub["F"]["risk_max"])
    return max(
        _band_score(reps, rub["M"]["normal_min"], rub["M"]["risk_max"]),
        _band_score(reps, rub["F"]["normal_min"], rub["F"]["risk_max"]),
    )


def _has_red_flags(red_flags: Optional[str]) -> bool:
    if not red_flags:
        return False
    return any(token.strip() for token in red_flags.split(","))


def assign_level(total: int, sarc_f: int, age: int, red_flags: Optional[str]) -> str:
    """Priority ladder (first match wins). Thresholds from scoring_rubrics.json."""
    la = _load_rubrics()["level_assignment"]
    if _has_red_flags(red_flags):
        return "Level 0"
    if sarc_f >= la["sarc_f_override"]:            # clinical override
        return "Level 0"
    if total >= la["total_high"] or age >= la["age_high"]:
        return "Level 0"
    if total >= la["total_mid"]:
        return "Level 1" if age >= la["age_mid"] else "Level 2"
    if total >= la["total_low"]:
        return "Level 2" if age >= la["age_mid"] else "Level 3"
    return "Level 4"


def apply_preference_override(computed_level: str, preference_level: str) -> str:
    """Preference may lower the level by at most one step; never raise it."""
    c = LEVEL_TO_INT[computed_level]
    p = LEVEL_TO_INT[preference_level]
    if p >= c:
        return computed_level           # never raise
    return LEVELS[max(c - 1, 0)]        # one step down max, floor Level 0


def assign_level_with_preference(total: int, sarc_f: int, age: int,
                                 red_flags: Optional[str],
                                 preference_level: Optional[str]) -> str:
    level = assign_level(total, sarc_f, age, red_flags)
    if preference_level:
        level = apply_preference_override(level, preference_level)
    return level
```

### File: `utils/autoregulation_logic.py`
```python
"""Phase 4 — auto-regulation engine (spec §3.11).
Thresholds and caps are spec/decision constants — do not tune without
clinical sign-off. Deterministic: a pure function of stored RPE history +
current level; no extra state, so it is rerun-safe by construction."""
from __future__ import annotations
import math
from typing import Optional

from db import queries
from utils.session_logic import parse_rpe_scores
from utils.exercise_logic import get_prescription

HIGH_THRESHOLD = 4.0
LOW_THRESHOLD = 2.5
REPS_FLOOR, REPS_CAP = 4, 20
HOLD_FLOOR, HOLD_CAP = 5, 20
SETS_FLOOR = 1


def classify(avg: float) -> str:
    if avg >= HIGH_THRESHOLD:
        return "high"
    if avg >= LOW_THRESHOLD:
        return "maintain"
    return "low"


def weekly_average_rpe(email: str, cycle: int, week: int) -> Optional[float]:
    """Mean of all per-exercise RPE values across days 1-6; None if no data."""
    values: list[int] = []
    for s in queries.get_rpe_scores_for_week(email, cycle, week):
        values.extend(parse_rpe_scores(s).values())
    return sum(values) / len(values) if values else None


def apply_rule(rx: dict, classification: str) -> dict:
    """One adjustment step on a numeric prescription dict (returns a copy)."""
    rx = dict(rx)
    if classification == "maintain":
        return rx
    if classification == "high":
        if rx["reps_min"] <= REPS_FLOOR:
            rx["sets"] = max(SETS_FLOOR, rx["sets"] - 1)      # spec's 'or': sets fallback
        else:
            rx["reps_min"] = max(REPS_FLOOR, math.floor(rx["reps_min"] * 0.8))
            rx["reps_max"] = max(rx["reps_min"], math.floor(rx["reps_max"] * 0.8))
        if rx.get("hold_s"):
            rx["hold_s"] = max(HOLD_FLOOR, math.floor(rx["hold_s"] * 0.8))
    elif classification == "low":
        rx["reps_min"] = min(REPS_CAP, rx["reps_min"] + 2)
        rx["reps_max"] = min(REPS_CAP, rx["reps_max"] + 2)
        if rx.get("hold_s"):
            rx["hold_s"] = min(HOLD_CAP, rx["hold_s"] + 4)
    return rx


def effective_prescription(email: str, cycle: int, week: int, level) -> dict:
    """Prescription for `week` = base for current level, folded with the
    adjustment rule over completed weeks 1..week-1 (week 0 excluded per spec)."""
    rx = get_prescription(level)
    for w in range(1, week):
        avg = weekly_average_rpe(email, cycle, w)
        if avg is not None:
            rx = apply_rule(rx, classify(avg))
    return rx


def hard_streak(email: str, cycle: int, week: int) -> bool:
    """True if weeks week-1 and week both averaged >= 4.0 (week-1 may be 0)."""
    if week < 1:
        return False
    a = weekly_average_rpe(email, cycle, week)
    b = weekly_average_rpe(email, cycle, week - 1)
    return (a is not None and b is not None
            and a >= HIGH_THRESHOLD and b >= HIGH_THRESHOLD)


def regression_due(email: str, cycle: int, week: int,
                   current_level_int: int) -> Optional[int]:
    """New level int if a one-step regression should apply at Day 7 of `week`;
    None otherwise (including the Level 0 floor)."""
    if hard_streak(email, cycle, week) and current_level_int > 0:
        return current_level_int - 1
    return None


def day7_plan(email: str, cycle: int, week: int, level_str: str) -> dict:
    """Everything the Day 7 view needs. Read-only; no writes."""
    lvl = int(str(level_str).split()[-1])
    avg = weekly_average_rpe(email, cycle, week)
    new_level_int = regression_due(email, cycle, week, lvl)
    level_for_next = (f"Level {new_level_int}"
                      if new_level_int is not None else level_str)
    next_rx = (effective_prescription(email, cycle, week + 1, level_for_next)
               if week < 4 else None)
    return {
        "week": week,
        "avg_rpe": avg,
        "classification": classify(avg) if avg is not None else None,
        "hard_streak": hard_streak(email, cycle, week),
        "regression_to": new_level_int,
        "next_week_prescription": next_rx,
    }
```

### File: `utils/breathing_logic.py`
```python
"""Phase 3 — breathing schedule lookup from data/breathing_sequences.json."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_bs_cache: Optional[dict] = None


def _load() -> dict:
    global _bs_cache
    if _bs_cache is None:
        with open(DATA_DIR / "breathing_sequences.json") as f:
            _bs_cache = json.load(f)
    return _bs_cache


def get_breathing_practices(week: int, day: int) -> list[dict]:
    """Return practice dicts for the week/day. Day 7 (rest) -> []."""
    if day == 7:
        return []
    entry = _load()["schedule"][week]
    codes = entry["days_1_3"] if day <= 3 else entry["days_4_6"]
    by_code = {p["code"]: p for p in _load()["practices"]}
    return [by_code[c] for c in codes if c in by_code]


def get_safety_text() -> dict:
    return _load()["safety_text"]
```

### File: `utils/exercise_logic.py`
```python
"""Phase 2 — curriculum engine.
Loads/validates exercise_cards.json, injects level position cues, generates
the weekly pool, selects the daily 3-exercise set, and looks up prescriptions.

Design (resolves the spec's 'random from active pool' into a constraint-
satisfying form):
  - Weekly pool = 2 cards from each of 3 categories (6 total). This GUARANTEES
    daily 3-distinct-category selection with no consecutive-day repeats is
    always feasible. (A fully random 6-from-active-pool could yield <3
    categories and make daily selection impossible.)
  - W0/W1 categories fixed {C, PC, G}; W1 = complement of W0 within each
    category (honors 'remaining unused from initial pool').
  - W2 introduces HF, W3 introduces SP, W4 introduces CM (+ 2 seeded
    categories from the previously-introduced set).
  - Daily selection = alternating pattern per category (odd days card A,
    even days card B) -> no exercise on consecutive days.
  - All RNG seeded by sha256(email|cycle|week|salt) -> deterministic across
    Streamlit reruns. Weekly pool persisted to weekly_plan as primary safety.
"""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
from typing import Optional

from db import queries

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_cards_cache: Optional[list] = None
_prescriptions_cache: Optional[dict] = None
_cards_by_cat_cache: Optional[dict] = None

CATEGORY_INTRO = {
    0: {"C", "PC", "G"},
    1: {"C", "PC", "G"},
    2: {"C", "PC", "G", "HF"},
    3: {"C", "PC", "G", "HF", "SP"},
    4: {"C", "PC", "G", "HF", "SP", "CM"},
}
NEW_CATEGORY = {0: None, 1: None, 2: "HF", 3: "SP", 4: "CM"}


def _seed(email: str, cycle: int, week: int, salt: str = "") -> int:
    return int(hashlib.sha256(
        f"{email}|{cycle}|{week}|{salt}".encode()).hexdigest(), 16) % (2**32)


def _load_cards() -> list[dict]:
    global _cards_cache
    if _cards_cache is None:
        with open(DATA_DIR / "exercise_cards.json") as f:
            _cards_cache = json.load(f)
        for c in _cards_cache:
            for k in ("card_id", "title", "category", "base_level", "image",
                      "isometric", "instructions", "position_cues"):
                if k not in c:
                    raise ValueError(f"exercise card missing '{k}': {c.get('card_id')}")
    return _cards_cache


def _load_prescriptions() -> dict:
    global _prescriptions_cache
    if _prescriptions_cache is None:
        with open(DATA_DIR / "prescriptions.json") as f:
            _prescriptions_cache = json.load(f)
    return _prescriptions_cache


def _cards_by_category() -> dict[str, list[str]]:
    global _cards_by_cat_cache
    if _cards_by_cat_cache is None:
        out: dict[str, list[str]] = {}
        for c in _load_cards():
            out.setdefault(c["category"], []).append(c["card_id"])
        for cat in out:
            out[cat].sort()
        _cards_by_cat_cache = out
    return _cards_by_cat_cache


def _level_int(level) -> int:
    return level if isinstance(level, int) else int(str(level).split()[-1])


def get_card(card_id: str) -> dict:
    for c in _load_cards():
        if c["card_id"] == card_id:
            return c
    raise KeyError(card_id)


def _card_category(card_id: str) -> str:
    return get_card(card_id)["category"]


def apply_position_cue(card: dict, level) -> dict:
    """Return a copy of card with 'position_cue' set for the given level."""
    out = dict(card)
    out["position_cue"] = card["position_cues"][str(_level_int(level))]
    return out


def get_prescription(level) -> dict:
    return _load_prescriptions()[str(_level_int(level))]


def _pick_categories(week: int, rng: random.Random) -> list[str]:
    new_cat = NEW_CATEGORY[week]
    if new_cat is None:
        return ["C", "PC", "G"]
    prior = sorted(CATEGORY_INTRO[week] - {new_cat})
    return [new_cat] + rng.sample(prior, 2)


def _pick_two(category: str, rng: random.Random,
              exclude: Optional[set] = None) -> list[str]:
    ex = exclude or set()
    pool = [c for c in _cards_by_category()[category] if c not in ex]
    return rng.sample(pool, 2)


def _generate_weekly_pool_ids(email: str, cycle: int, week: int) -> list[str]:
    rng = random.Random(_seed(email, cycle, week))
    if week == 1:
        # complement of W0 within {C, PC, G}
        w0 = get_weekly_pool(email, cycle, 0)
        used: dict[str, set[str]] = {}
        for cid in w0:
            used.setdefault(_card_category(cid), set()).add(cid)
        pool: list[str] = []
        for cat in ("C", "PC", "G"):
            pool.extend(_pick_two(cat, rng, exclude=used.get(cat, set())))
    else:
        pool = []
        for cat in _pick_categories(week, rng):
            pool.extend(_pick_two(cat, rng))
    rng.shuffle(pool)
    return pool


def get_weekly_pool(email: str, cycle: int, week: int) -> list[str]:
    """Return the 6 card IDs for the week. Persisted on first generation."""
    existing = queries.get_weekly_plan(email, cycle, week)
    if existing:
        return existing.split(",")
    pool = _generate_weekly_pool_ids(email, cycle, week)
    queries.upsert_weekly_plan(email, cycle, week, ",".join(pool))
    return pool


def select_daily_set(email: str, cycle: int, week: int, day: int) -> list[str]:
    """Return 3 card IDs for the day: one per category, no consecutive-day repeat."""
    pool = get_weekly_pool(email, cycle, week)
    by_cat: dict[str, list[str]] = {}
    for cid in pool:
        by_cat.setdefault(_card_category(cid), []).append(cid)
    rng = random.Random(_seed(email, cycle, week, salt="daily"))
    cat_order: dict[str, list[str]] = {}
    for cat in sorted(by_cat):
        c = list(by_cat[cat]); rng.shuffle(c)
        cat_order[cat] = c
    slot = 0 if (day - 1) % 2 == 0 else 1   # odd days (1,3,5) -> index 0
    return [cat_order[cat][slot] for cat in sorted(cat_order)]

def format_prescription(rx: dict) -> str:
    """Build the display string from a numeric prescription dict."""
    reps = f"{rx['reps_min']}–{rx['reps_max']} reps"
    if rx.get("hold_s"):
        reps += f" (or {rx['hold_s']}s hold)"
    if rx["rest_s_min"] == rx["rest_s_max"]:
        rest = f"{rx['rest_s_min']}s"
    else:
        rest = f"{rx['rest_s_min']}–{rx['rest_s_max']}s"
    return f"{rx['sets']} sets · {reps} · rest {rest}"
```

### File: `utils/session_logic.py`
```python
"""Phase 3/5 — session position computation and RPE (de)serialization."""
from __future__ import annotations
import re

import streamlit as st

from db import queries


def format_rpe_scores(rpe_map: dict) -> str:
    """{'C01':2,'PC01':3} -> 'C01:2,PC01:3' (insertion order preserved)."""
    return ",".join(f"{cid}:{score}" for cid, score in rpe_map.items())


def parse_rpe_scores(s: str) -> dict:
    s = (s or "").strip()
    if not s:
        return {}
    out: dict[str, int] = {}
    for pair in s.split(","):
        cid, _, score = pair.partition(":")
        out[cid.strip()] = int(score.strip())
    return out


def normalize_rpe_score(value) -> int:
    """Defensive RPE normalizer: int 1-5, numeric string, or full emoji label.
    Raises ValueError otherwise. Phase 4 auto-regulation consumes these values."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"unparseable RPE value: {value!r}")
    if isinstance(value, int):
        score = value
    elif isinstance(value, str):
        m = re.search(r"\b([1-5])\b", value)
        if not m:
            raise ValueError(f"unparseable RPE value: {value!r}")
        score = int(m.group(1))
    else:
        raise ValueError(f"unparseable RPE value: {value!r}")
    if not 1 <= score <= 5:
        raise ValueError(f"RPE out of range: {score}")
    return score


def compute_current_position(email: str, override: dict | None = None) -> dict:
    """Earliest incomplete day (OQ-07: resume, no auto-skip).
    If a debug override dict is supplied (QA only), validate it and return it
    directly; is_program_complete is always False under override so QA can
    reach the Day 7 views."""
    if override is not None:
        week, day, cycle = (int(override["week"]), int(override["day"]),
                            int(override["cycle"]))
        if not (0 <= week <= 4):
            raise ValueError(f"override week out of range: {week}")
        if not (1 <= day <= 7):
            raise ValueError(f"override day out of range: {day}")
        if cycle < 1:
            raise ValueError(f"override cycle out of range: {cycle}")
        return {"cycle": cycle, "week": week, "day": day,
                "is_rest_day": day == 7, "is_program_complete": False}
    user = queries.get_user(email)
    cycle = user["current_cycle"]
    done_days = queries.get_completed_days(email, cycle)
    done_rests = queries.get_completed_rests(email, cycle)
    for week in range(5):
        for day in range(1, 7):
            if (week, day) not in done_days:
                return {"cycle": cycle, "week": week, "day": day,
                        "is_rest_day": False, "is_program_complete": False}
        if week not in done_rests:
            return {"cycle": cycle, "week": week, "day": 7,
                    "is_rest_day": True, "is_program_complete": False}
    return {"cycle": cycle, "week": 4, "day": 7,
            "is_rest_day": True, "is_program_complete": True}


def get_session_position(email: str) -> dict:
    """View-facing wrapper: applies the debug override only when ?debug=true
    is active. Production behaviour is identical to compute_current_position."""
    override = None
    if st.session_state.get("debug") and st.session_state.get("debug_override"):
        override = st.session_state["debug_override"]
    return compute_current_position(email, override)
```

### File: `utils/state_machine.py`
```python
"""Phase 3 — pure state-machine contract. UI routing in app.py MUST go through
transition()/is_valid(). Modifying the transition set requires updating
test_state_machine.py and sign-off."""
VALID_TRANSITIONS = {
    ("UNAUTHENTICATED", "login_register"): "CHECK_ONBOARDING",
    ("CHECK_ONBOARDING", "sarc_f_incomplete"): "ONBOARDING_SARC_F",
    ("CHECK_ONBOARDING", "assessment_complete"): "DAILY_HUB",
    ("ONBOARDING_SARC_F", "complete_assessment"): "DAILY_HUB",
    ("DAILY_HUB", "start_breathing"): "BREATHING_SESSION",
    ("BREATHING_SESSION", "start_exercises"): "EXERCISE_SESSION",
    ("EXERCISE_SESSION", "submit_workout"): "WORKOUT_SUMMARY",
    ("WORKOUT_SUMMARY", "return_to_hub"): "DAILY_HUB",
    ("DAILY_HUB", "start_weekly_review"): "DAY_7_REST",
    ("DAY_7_REST", "complete_weekly_review"): "DAILY_HUB",
    ("PROGRAM_COMPLETE", "retake_assessment"): "ONBOARDING_SARC_F",
    ("PROGRAM_COMPLETE", "restart_current_level"): "DAILY_HUB",
    ("DAY_7_REST", "complete_program"): "PROGRAM_COMPLETE",
}


def transition(current: str, action: str) -> str:
    key = (current, action)
    if key not in VALID_TRANSITIONS:
        raise ValueError(f"invalid transition: {current!r} + {action!r}")
    return VALID_TRANSITIONS[key]


def is_valid(current: str, action: str) -> bool:
    return (current, action) in VALID_TRANSITIONS
```

### File: `docs/AGENT_CONTEXT_PACK.md`
```md
Agent Context Pack — Read This First
Project
Elderly Online Training System (v4.1 spec). Streamlit + SQLite, mobile-first,for adults 60+. Single source of truth: the v4.1 specification document.

Where things live
Spec/data: data/*.json (exercise cards, breathing sequences, scoring rubrics)
Schema: db/schema_sqlite.sql · DB layer: db/database.py, db/queries.py
Safety logic: utils/assessment_logic.py (LOCKED — sign-off to modify)
Tests as contract: tests/test_assessment_logic.py
Session state keys: docs/STATE.md · Assumptions: docs/DECISIONS.md
Rules of engagement
The v4.1 spec is the single source of truth. On conflict, STOP and ask.
Clinical thresholds (level ladder, rubrics, breathing cadences, safety copy)are READ FROM data/*.json or reproduced VERBATIM. Never derive, round, or"improve" them. If a value looks missing, halt.
One module per task. Each task prompt includes its spec section, datacontracts, required test cases, and an Out-of-Scope list.
components/locked/ is off-limits without an approved sign-off ticket.
Tests are deliverables. pytest must pass before declaring a task done.
No new dependencies, no schema changes, no refactors outside task scope.
All randomness must be seeded or persisted; all transitions go via the statemachine.
Log every assumption in docs/DECISIONS.md with a spec reference.
Banned APIs (do not use)
st.image(..., use_column_width=True) — deprecated/removed. Usewidth="stretch" instead.
Any Streamlit API not present in the pinned version (1.39.0). When in doubt,check against the pinned version before writing.
Run
App: streamlit run app.py (boots to login shell)
Tests: pytest (truth-table contract must pass)
Debug mode: append ?debug=true to the URL
STOP AND ASK (do not invent)
Any clinical threshold not present in scoring_rubrics.json.
Exercise instruction text (DRAFT in exercise_cards.json — content team owns).
Any state-machine transition not in the v4.1 state table.


"Never call st.rerun() inside a form context; always give form widgets explicit keys."

AppTest E2E must not UI-drive multi-step st.form wizards that advance via st.rerun(); seed DB state instead."
```

### File: `docs/DECISIONS.md`
```md
| v4.1 | Red-flag fast-path skips SARC-F/baseline/preference; level locked Level 0 | onboarding_wizard step 0 | Safety; data collection deferred to supervised intake || v4.1 | UPST uses best of left/right for scoring | baseline_timers | Single sub-score needed || v4.1 | Preference default = "Chair-Assisted" (safest); confirmation screen shows final level visibly before commit | onboarding_wizard step 3 | User sees the effect before confirming || v4.1 | compute_final_level extracted as pure function (no Streamlit) | onboarding_wizard | Stable, hermetic safety contract; UI coupling kept out of logic || v4.1 | Baseline entry is manual (no live-ticking timer) | baseline_timers | Streamlit rerun model; live timer deferred to Phase 5 polish |

Phase 2
| v4.1 | Weekly pool = 2-per-category × 3 categories (constrained specialization of spec's 'random') | exercise_logic | Guarantees daily 3-distinct-category + no-consecutive-repeat selection is always feasible || v4.1 | W1 = complement of W0 within {C,PC,G} | exercise_logic | Honors 'remaining unused from initial pool' || v4.1 | Daily selection = alternating pattern per category (odd/even days) | exercise_logic | No exercise appears on consecutive days by construction || v4.1 | RNG seeded by sha256(email|cycle|week|salt); weekly pool persisted | exercise_logic | Deterministic across Streamlit reruns || v4.1 | Prescriptions stored in data/prescriptions.json (data, not code) | exercise_logic | Tunable without code change |

Phase 3
| v4.1 | Position = earliest incomplete day (resume, no auto-skip) | session_logic | OQ-07 || v4.1 | RPE stored as "C01:2,PC01:3" string in training_progress | session_logic | Spec format || v4.1 | Breathing metronome = pure CSS @keyframes (no JS/deps) | breathing_view | Avoids streamlit-autorefresh || v4.1 | Day 6 completion → Day 7 rest (position computes day 7 is_rest) | session_logic | Phase 4 implements rest_view || v4.1 | RPE widget keys position-tagged to prevent cross-day value leak | training_view | Streamlit key persistence quirk |

| v4.1 | RPE selectbox holds int 1–5 via format_func; normalize_rpe_score guards reads | training_view, session_logic | Bugfix: session_state stores widget VALUE (label string), not index; Phase 4 depends on valid 1–5 |

Phase 4
| v4.1 | prescriptions.json restructured numeric (reps_min/max, hold_s, rest_s_min/max); display built in code | Phase 4 | Arithmetic auto-regulation needs numbers; base display strings preserved verbatim || v4.1 | hold_s defined for Level 0 only (10s, per spec); L1–L4 isometric cards use reps | prescriptions.json | Invents no clinical values || v4.1 | 'Reduce sets OR reps −20%' resolved: reps −20% primary (floor 4); sets −1 fallback (floor 1) | autoregulation_logic | Deterministic choice of spec's 'or' || v4.1 | 'Maintain' = carry adjusted volume forward; cumulative fold over weeks 1..w−1 with caps (reps 4–20, hold 5–20s, sets ≥1); no reset on regression | autoregulation_logic | Caps bound compounding; avoids untracked level-history state || v4.1 | Week 0 average excluded from volume fold (spec default) but counts toward the 2-week regression streak | autoregulation_logic | Safety; week 0 has real RPE data || v4.1 | Regression applied at Day 7 completion with mandatory acknowledgment checkbox; floor Level 0 (volume reduction continues instead) | rest_view | Elderly-safe, auditable || v4.1 | Day 7 of Week 4 → PROGRAM_COMPLETE (new state-machine transition) | state_machine | Spec §3.4 || v4.1 | Cycle restart: advance_cycle on either action; re-assessment overwrites users scores (latest wins); history preserved via cycle-keyed tables | program_complete | OQ-06 || v4.1 | user session dict must be refreshed from DB after any level/cycle change | STATE.md | Prevents stale cached level |

Phase 5
| v4.1 | Debug override: session-only, validated (week 0–4, day 1–7, cycle ≥1), affects reads AND writes; cleared when ?debug absent | dev_controls, session_logic | QA traversal; is_program_complete always False under override || v4.1 | RPE selectbox: raw options = emoji labels (format_func removed); per-exercise distinct labels; normalize_rpe_score parses | training_view | AppTest selectability + screen-reader distinct labels || v4.1 | Sex selectbox: raw options = display labels | auth_view | Same rationale || v4.1 | CSS/asset paths absolutized from file | app.py, training_view | CWD-independence || v4.1 | Light theme default via .streamlit/config.toml; dark via Settings menu (Streamlit dark palette #0e1117; spec's #121212 deferred) | config.toml | CSS is size/contrast-only so both themes work || v4.1 | tests/init.py + helpers_e2e.py; E2E DB verified via raw sqlite3 reads | tests | Assertions independent of Streamlit runtime/caching |

| v4.1 | E2E widget lookup via .label iteration (WidgetList(label=) unsupported in pinned Streamlit); form submits searched in form_submit_button then button | tests/helpers_e2e.py | Version-agnostic AppTest access || v4.1 | compute_current_position body restored — Phase 5 "insert above existing body" instruction was applied with the body dropped | utils/session_logic.py | Process fix: shared modules always get full-file replacements |

| v4.1 | AMENDED RULE: explicit keys on form INPUT widgets only. form_submit_button takes NO key (unsupported on minimum-validated Streamlit 1.28) — located by label in tests | auth_view, baseline_timers, rest_view | Corrects Phase 5 overreach that crash-looped the app on key= || v4.1 | Minimum validated Streamlit: 1.28; release pin 1.39.0; tests/test_environment.py guards the floor | requirements, tests | Three E2E failures traced to running anaconda's unpinned Streamlit |

| v4.1 | E2E STRATEGY: AppTest no longer UI-drives the onboarding wizard (st.form + per-step st.rerun() replay unreliable — 4 distinct failure modes incl. stale keyed-widget state). Wizard logic covered hermetically; E2E covers registration, login/routing, workout loop, seeded-position rendering | tests | AppTest limitation, not an app bug; browser QA green throughout || v4.1 | Plain st.button widgets in views get explicit keys (btn_start_workout, btn_start_exercises, btn_submit_workout, btn_return_hub, btn_start_review, btn_retake, btn_restart) | views | Consistent keyed-widget profile across rerun crossings || v4.1 | Workout E2E stops at WORKOUT_SUMMARY (no return-to-hub click); day-advance proven via DB + position unit tests | tests | Each rerun crossing multiplies replay risk for zero added coverage |




```

### File: `docs/README.md`
```md
Elderly Online Training System
Mobile-responsive exercise & breathing platform for adults 60+.

Setup
python3.12 -m venv .venv && source .venv/bin/activatepip install -r requirements.txtstreamlit run app.py            # boots to login shell; creates instance/local_test.dbpytest                          # truth-table contract must pass
Open http://localhost:8501. Append ?debug=true for QA controls.

Architecture
See docs/AGENT_CONTEXT_PACK.md (read first), docs/STATE.md (session keys),
and docs/DECISIONS.md (decisions log). The v4.1 specification is the single
source of truth.

Status
Phase 0 (foundation) — complete, this commit.
Phase 1 (auth & onboarding locked components) — next.
```

### File: `docs/STATE.md`
```md
Session-State Key Contract
All Streamlit code MUST use these keys (set in app.py). Do not introduce newsession keys without documenting here.

Key	Type	Purpose
authenticated	bool	User has logged in (testing-phase auth)
user_email	str|None	Logged-in user's email (PK)
user	dict|None	Full users row (mirrors DB)
current_state	str	Current state-machine state (see v4.1 §3.4)
session_flags	dict	In-workout flags (current exercise index, RPE collected, etc.)
debug	bool	?debug=true present in URL
Rules:

A day/week/cycle advance is computed from the DB (latest training_progress /rest_assessments row), NEVER from session state alone.
Every successful write transitions current_state via the state machine.
session_flags is reset on WORKOUT_SUMMARY → DAILY_HUB.

Phase 2
| onboarding_step | int (0-4) | Current wizard step || onboarding_data | dict | Accumulated partial results across steps || pending_level | str|None | Level awaiting confirmation on step 4 || pending_total | int|None | Total score awaiting confirmation |

Routing rule: after login, app.py sets current_state = "ONBOARDING_SARC_F" if user.level is null, else "DAILY_HUB". On wizard confirm, the wizard sets current_state = "DAILY_HUB" and clears the onboarding keys.

Phase 3
| session_flags.last_rpe | str|None | RPE string from the just-submitted workout || session_flags.last_daily | list|None | Card IDs from the just-submitted workout |

Rule: session_flags is reset to {} on WORKOUT_SUMMARY → DAILY_HUB. RPE widget keys are position-tagged (rpe_{cycle}_{week}_{day}_{cid}) so values never leak across days.

Phase 4
| regression_ack | bool | Day 7 acknowledgment checkbox when a level regression is due |

Rule: after any set_user_level / advance_cycle write, refresh st.session_state["user"] from the DB before the next render.

Phase 5
| debug_override | dict|None | {"cycle","week","day"} when a QA override is applied |


```

### File: `components/locked/baseline_timers.py`
```python
"""LOCKED COMPONENT — sign-off required to modify.
Renders baseline measures: calf circumference, single-leg stance (L/R),
30-second chair stand. Sub-scores computed via utils.assessment_logic
(sex-aware rubric scoring). Instruction copy is DRAFT pending clinical sign-off.
Widget labels below are mandated for AppTest stability — do not rename.

Phase 5 note (NON-CLINICAL, key-only change): explicit keys added to all form
widgets to avoid auto-generated $$WIDGET_ID session-state keys, which break
AppTest replay. No logic, wording, scoring, or validation changed — the
Phase 1 truth-table suite is unchanged and must remain green."""
from __future__ import annotations
from typing import Optional
import streamlit as st

from utils.assessment_logic import score_calf, score_sls, score_chair_stand

LABEL_CALF = "Calf circumference (cm)"
LABEL_SLS_L = "Single-leg stance — left (sec)"
LABEL_SLS_R = "Single-leg stance — right (sec)"
LABEL_CHAIR = "30-second chair stand (reps)"


def render_baseline_form(sex: str) -> Optional[dict]:
    """Return sub-scores + raw measures on submit, else None."""
    st.subheader("Baseline Measures")
    st.caption("DRAFT — clinical review required. Use a sturdy, non-wheeled chair on a non-slip surface.")
    with st.form("baseline_form"):
        calf_cm = st.number_input(LABEL_CALF, min_value=20.0, max_value=60.0,
                                  value=34.0, step=0.1, format="%.1f",
                                  key="base_calf")
        sls_l = st.number_input(LABEL_SLS_L, min_value=0.0, max_value=120.0,
                                value=10.0, step=0.1, format="%.1f",
                                key="base_sls_l")
        sls_r = st.number_input(LABEL_SLS_R, min_value=0.0, max_value=120.0,
                                value=10.0, step=0.1, format="%.1f",
                                key="base_sls_r")
        chair = st.number_input(LABEL_CHAIR, min_value=0, max_value=60,
                                value=12, step=1, key="base_chair")
        submitted = st.form_submit_button("Continue", width="stretch")
    if not submitted:
        return None
    return {
        "calf_cm": calf_cm,
        "sls_left_sec": sls_l,
        "sls_right_sec": sls_r,
        "chair_stand_reps": chair,
        "calf_score": score_calf(calf_cm, sex),
        "balance_score": score_sls(max(sls_l, sls_r)),   # UPST: best of L/R
        "chair_stand_score": score_chair_stand(chair, sex),
    }
```

### File: `components/locked/onboarding_wizard.py`
```python
"""LOCKED COMPONENT — sign-off required to modify.
Orchestrates onboarding:
  Step 0  red-flag screening        (any flag -> Level 0 fast-path to step 4)
  Step 1  SARC-F                    (sarc_f_assessment)
  Step 2  baseline                  (baseline_timers)
  Step 3  support preference
  Step 4  confirmation -> update_user_level -> DAILY_HUB

compute_final_level() is a pure function (no Streamlit) and is the unit-tested
safety contract for this phase."""
from __future__ import annotations
from typing import Optional
import streamlit as st

from db import queries
from utils.assessment_logic import calculate_total_score, assign_level_with_preference
from components.locked.sarc_f_assessment import render_sarc_f_form
from components.locked.baseline_timers import render_baseline_form

RED_FLAGS = [
    ("chest_pain", "Chest pain"),
    ("joint_replacement_under_6mo", "Joint replacement (< 6 months)"),
    ("uncontrolled_bp_over_160_100", "Uncontrolled BP (> 160/100)"),
    ("two_or_more_recent_falls", "2+ falls in past 12 months"),
]
PREFERENCE_OPTIONS = [
    ("Level 0", "Chair-Assisted"),
    ("Level 1", "Seated"),
    ("Level 2", "Supported Standing"),
    ("Level 3", "Independent Standing"),
    ("Level 4", "Dynamic Standing"),
]


def compute_final_level(red_flags: Optional[str], sarc_f: Optional[int],
                        calf_score: Optional[int], balance_score: Optional[int],
                        chair_stand_score: Optional[int], age: int,
                        preference_level: Optional[str] = None
                        ) -> tuple[str, Optional[int]]:
    """Pure safety contract. Returns (final_level, total_score).
    Red-flag fast-path (scores None) -> ('Level 0', None)."""
    if red_flags and None in (sarc_f, calf_score, balance_score, chair_stand_score):
        return "Level 0", None
    total = calculate_total_score(sarc_f, calf_score, balance_score, chair_stand_score)
    level = assign_level_with_preference(total, sarc_f, age, red_flags, preference_level)
    return level, total


def _flags_to_str(flags: dict) -> str:
    return ",".join(code for code, _ in RED_FLAGS if flags.get(code))


def render_onboarding_wizard(user: dict) -> None:
    st.title("Welcome! Let's complete your assessment.")
    st.session_state.setdefault("onboarding_step", 0)
    st.session_state.setdefault("onboarding_data", {})
    data = st.session_state["onboarding_data"]
    step = st.session_state["onboarding_step"]
    age, sex = user["age"], user.get("sex", "U")

    # Step 0 — red flags
    if step == 0:
        st.subheader("Step 1 of 4 — Safety screening")
        with st.form("red_flags_form"):
            flags = {code: st.checkbox(label, key=f"rf_{code}") for code, label in RED_FLAGS}
            submitted = st.form_submit_button("Continue", width="stretch")
        if submitted:
            data["red_flags"] = _flags_to_str(flags)
            st.session_state["onboarding_step"] = 4 if data["red_flags"] else 1
            st.rerun()
        return

    # Step 1 — SARC-F
    if step == 1:
        result = render_sarc_f_form()
        if result:
            data["sarc_f"] = result["sarc_f_score"]
            data["sarc_f_items"] = result["item_scores"]
            st.session_state["onboarding_step"] = 2
            st.rerun()
        return

    # Step 2 — baseline
    if step == 2:
        result = render_baseline_form(sex)
        if result:
            data.update(result)
            st.session_state["onboarding_step"] = 3
            st.rerun()
        return

    # Step 3 — preference
    if step == 3:
        st.subheader("Step 4 of 4 — Your comfort preference")
        with st.form("preference_form"):
            pref_label = st.selectbox("Your comfort preference",
                                      [lbl for _, lbl in PREFERENCE_OPTIONS],
                                      key="pref_label")
            submitted = st.form_submit_button("Continue", width="stretch")
        if submitted:
            data["preference_level"] = next(
                lvl for lvl, lbl in PREFERENCE_OPTIONS if lbl == pref_label)
            st.session_state["onboarding_step"] = 4
            st.rerun()
        return

    # Step 4 — confirmation
    if step == 4:
        st.subheader("Review and confirm")
        rf = data.get("red_flags", "")
        st.write(f"**Red flags:** {rf if rf else 'None'}")
        if rf:
            st.warning("A safety red flag was reported. Your level is set to "
                       "**Level 0 (Chair-Assisted)** for your safety.")
            final_level, total = "Level 0", None
        else:
            sarc_f = data["sarc_f"]
            calf, bal, chair = data["calf_score"], data["balance_score"], data["chair_stand_score"]
            pref = data.get("preference_level")
            total = calculate_total_score(sarc_f, calf, bal, chair)
            final_level = assign_level_with_preference(total, sarc_f, age, rf, pref)
            st.write(f"**SARC-F:** {sarc_f}/10  ·  **Calf:** {calf}  ·  "
                     f"**Balance:** {bal}  ·  **Chair-stand:** {chair}")
            st.write(f"**Total:** {total}/16  (lower = higher function)")
            if pref:
                st.write(f"**Your preference:** {pref}")
        st.write(f"### Assigned level: {final_level}")
        if st.button("Confirm and start training", width="stretch", type="primary"):
            queries.update_user_level(
                user["email"], final_level, total,
                data.get("sarc_f"), data.get("calf_score"),
                data.get("balance_score"), data.get("chair_stand_score"),
                data.get("red_flags", ""),
            )
            user["level"] = final_level
            user["total_score"] = total
            st.session_state["user"] = user
            st.session_state["current_state"] = "DAILY_HUB"
            for k in ("onboarding_step", "onboarding_data"):
                st.session_state.pop(k, None)
            st.rerun()
```

### File: `components/locked/sarc_f_assessment.py`
```python
"""LOCKED COMPONENT — sign-off required to modify.
Renders the 5-item SARC-F questionnaire. Item text and options are NEVER
hardcoded — always read from data/scoring_rubrics.json."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_rubrics_cache: Optional[dict] = None


def _load_rubrics() -> dict:
    global _rubrics_cache
    if _rubrics_cache is None:
        with open(DATA_DIR / "scoring_rubrics.json") as f:
            _rubrics_cache = json.load(f)
    return _rubrics_cache


def render_sarc_f_form() -> Optional[dict]:
    """Return {'sarc_f_score': int, 'item_scores': {name: 0-2}} on submit, else None."""
    items = _load_rubrics()["sarc_f"]["items"]
    st.subheader("SARC-F Questionnaire")
    st.caption("Answer each question based on your current ability.")
    with st.form("sarc_f_form"):
        item_scores: dict[str, int] = {}
        for it in items:
            choice = st.selectbox(it["label"], it["options"], key=f"sarcf_{it['name']}")
            item_scores[it["name"]] = it["options"].index(choice)
        submitted = st.form_submit_button("Continue", width="stretch")
    if not submitted:
        return None
    return {"sarc_f_score": sum(item_scores.values()), "item_scores": item_scores}
```

### File: `components/views/auth_view.py`
```python
"""Authentication view — MVP testing-phase auth (username + email match).

Phase 5 hardening (AppTest compatibility):
  - Every widget inside st.form carries an explicit key (auto-generated
    $$WIDGET_ID state keys break AppTest replay).
  - st.rerun() is raised OUTSIDE the form context via a flag. Rerun-inside-
    form triggers AppTest's '$$WIDGET_ID' KeyError; the flag pattern is
    behaviour-identical in the browser."""
from __future__ import annotations
import streamlit as st

from db import queries

SEX_OPTIONS = {"Prefer not to say": "U", "Male": "M", "Female": "F"}


def render_auth() -> None:
    st.title("🏃 Elderly Online Training System")
    tab_return, tab_new = st.tabs(["Returning User", "New User"])

    with tab_return:
        login_user = None
        with st.form("login"):
            email = st.text_input("Email", key="login_email")
            username = st.text_input("Username", key="login_username")
            submitted = st.form_submit_button("Log In", width="stretch")
            if submitted:
                login_user = queries.get_user_by_credentials(
                    email.strip(), username.strip())
                if login_user is None:
                    st.error("No matching account. Check email and username.")
        if login_user is not None:
            st.session_state.update(
                authenticated=True, user_email=login_user["email"],
                user=login_user, current_state="CHECK_ONBOARDING")
            st.rerun()

    with tab_new:
        do_register = False
        with st.form("register"):
            email = st.text_input("Email *", key="reg_email")
            username = st.text_input("Username *", key="reg_user")
            age = st.number_input("Age *", min_value=18, max_value=110,
                                  value=65, step=1, key="reg_age")
            sex_label = st.selectbox("Sex (used for calf & chair-stand norms)",
                                     list(SEX_OPTIONS), key="reg_sex")
            submitted = st.form_submit_button("Create Account", width="stretch")
            if submitted:
                if not email.strip() or not username.strip():
                    st.error("Email and username are required.")
                else:
                    do_register = True
        if do_register:
            sex = SEX_OPTIONS[sex_label]
            queries.create_user(email.strip(), username.strip(), int(age), sex)
            user = queries.get_user_by_credentials(email.strip(), username.strip())
            st.session_state.update(
                authenticated=True, user_email=user["email"],
                user=user, current_state="CHECK_ONBOARDING")
            st.rerun()
```

### File: `components/views/breathing_view.py`
```python
"""Phase 3 — BREATHING_SESSION. Pure-CSS pulsing metronome (no JS/deps)."""
from __future__ import annotations
import streamlit as st
from utils.session_logic import get_session_position
from utils.breathing_logic import get_breathing_practices, get_safety_text


def _metronome_css(practice: dict, suffix: str) -> str:
    total = practice["inhale_s"] + practice["hold_s"] + practice["exhale_s"]
    inhale_end = (practice["inhale_s"] / total) * 100 if total else 50
    hold_end = ((practice["inhale_s"] + practice["hold_s"]) / total) * 100 if total else 50
    name = f"breathe-{suffix}"
    return f"""
    <style>
    .{name}-circle {{
      width: 120px; height: 120px; border-radius: 50%;
      background: #4a90d9; margin: 20px auto;
      animation: {name} {total}s ease-in-out infinite;
    }}
    @keyframes {name} {{
      0% {{ transform: scale(1); }}
      {inhale_end:.1f}% {{ transform: scale(1.6); }}
      {hold_end:.1f}% {{ transform: scale(1.6); }}
      100% {{ transform: scale(1); }}
    }}
    </style>
    <div class="{name}-circle"></div>
    """


def render_breathing_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    practices = get_breathing_practices(pos["week"], pos["day"])
    safety = get_safety_text()
    st.title("Stage 1 — Breathing")
    if not practices:
        st.warning("No breathing session scheduled for today.")
    for p in practices:
        st.subheader(f"{p['code']} — {p['title']}")
        st.write(f"_{p['focus']}_")
        st.write(f"**Inhale** {p['inhale_s']}s  ·  **Hold** {p['hold_s']}s  ·  "
                 f"**Exhale** {p['exhale_s']}s  ·  **{p['cycles']} cycles** (~2 min)")
        st.markdown(_metronome_css(p, p["code"].lower()), unsafe_allow_html=True)
    st.info(f"🪑 {safety['chair_standard']}")
    st.info(f"⚠️ {safety['orthostatic_warning']}")
    if any(p["code"] == "DB05" for p in practices):
        st.warning(f"⚠️ {safety['lightheadedness_valve']}")
    if st.button("Start Exercises", key="btn_start_exercises", width="stretch", type="primary"):
        st.session_state["current_state"] = "EXERCISE_SESSION"
        st.rerun()
```

### File: `components/views/daily_hub.py`
```python
"""Phase 3 — DAILY_HUB view."""
from __future__ import annotations
import streamlit as st
from utils.session_logic import get_session_position


def render_daily_hub(user: dict) -> None:
    pos = get_session_position(user["email"])
    if pos["is_program_complete"]:
        st.session_state["current_state"] = "PROGRAM_COMPLETE"
        st.rerun()
        return
    st.title(f"Welcome, {user['username']} 👋")
    st.info(f"**Level:** {user['level']}  ·  **Cycle** {pos['cycle']}  ·  "
            f"**Week** {pos['week']}  ·  **Day** {pos['day']}")
    if pos["is_rest_day"]:
        st.write("Today is your **rest & review day**. Light movement only.")
        if st.button("Start Weekly Review", key="btn_start_review", width="stretch", type="primary"):
            st.session_state["current_state"] = "DAY_7_REST"
            st.rerun()
    else:
        st.write("Today's session: **breathing + 3 exercises** (~15–30 min).")
        if st.button("Start Today's Workout", key="btn_start_workout", width="stretch", type="primary"):
            st.session_state["current_state"] = "BREATHING_SESSION"
            st.rerun()
```

### File: `components/views/program_complete.py`
```python
"""Phase 4 — PROGRAM_COMPLETE view: summary + cycle restart actions."""
from __future__ import annotations
import streamlit as st

from db import queries


def _restart(user: dict, reassess: bool) -> None:
    email = user["email"]
    queries.advance_cycle(email)
    st.session_state["user"] = queries.get_user(email)   # refresh cached user
    for k in ("onboarding_step", "onboarding_data", "regression_ack"):
        st.session_state.pop(k, None)
    st.session_state["current_state"] = (
        "ONBOARDING_SARC_F" if reassess else "DAILY_HUB")
    st.rerun()


def render_program_complete(user: dict) -> None:
    st.title("🎉 Program Complete!")
    st.balloons()
    n = queries.count_completed_workouts(user["email"], user["current_cycle"])
    st.write(f"You completed **{n} workouts** across 5 weeks, "
             f"{user['username']} — outstanding work!")
    st.write("Choose how you'd like to continue:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Retake Assessment & Restart", key="btn_retake", width="stretch"):
            _restart(user, reassess=True)
    with c2:
        if st.button("Restart with Current Level", key="btn_restart", width="stretch"):
            _restart(user, reassess=False)
```

### File: `components/views/rest_view.py`
```python
"""Phase 4 — DAY_7_REST view: recovery checks, reflection, auto-regulation."""
from __future__ import annotations
import streamlit as st

from db import queries
from utils.session_logic import get_session_position
from utils.autoregulation_logic import day7_plan
from utils.breathing_logic import get_safety_text
from utils.exercise_logic import format_prescription


def render_rest_view(user: dict) -> None:
    pos = get_session_position(user["email"])
    if not pos["is_rest_day"] or pos["is_program_complete"]:
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()
        return
    week, cycle = pos["week"], pos["cycle"]
    plan = day7_plan(user["email"], cycle, week, user["level"])
    safety = get_safety_text()

    st.title(f"Rest & Review — Week {week}")
    st.info(f"🪑 {safety['chair_standard']}")
    st.write("Light movement only. Complete the checks below to finish your week.")

    if plan["avg_rpe"] is not None:
        st.metric("Average effort this week (RPE)", f"{plan['avg_rpe']:.1f} / 5")
    if week == 0:
        st.caption("Induction week — checks are recorded as your baseline. "
                   "No adjustment is applied to Week 1.")
    elif plan["classification"] == "high":
        st.warning("This week felt hard — next week's volume will be reduced.")
    elif plan["classification"] == "low":
        st.success("This week felt easy — next week's volume will increase slightly.")
    else:
        st.info("This week felt just right — volume stays the same.")
    if plan["next_week_prescription"] is not None:
        st.write("**Next week's prescription:** "
                 f"{format_prescription(plan['next_week_prescription'])}")

    # Regression prompt (mandatory acknowledgment)
    ack_ok = True
    if plan["regression_to"] is not None:
        st.warning("⚠️ You've reported high effort for **two weeks in a row**. "
                   f"For your comfort and safety, your level will be adjusted "
                   f"from **{user['level']}** to **Level {plan['regression_to']}**.")
        ack_ok = st.checkbox(
            f"I understand my level will change to Level {plan['regression_to']}.",
            key="regression_ack")
    elif plan["hard_streak"]:
        st.warning("Two hard weeks in a row — you are already at the safest "
                   "level (Level 0). Your volume will be reduced instead.")

    with st.form("rest_form"):
        recall = st.number_input(
            "How many exercises can you remember learning this week?",
            0, 6, 0, key="rest_recall")
        reflection = st.text_area("How does your body feel? (optional)",
                                  key="rest_reflection")
        sts = st.number_input("Chair sit-to-stand — cycles in 15 seconds",
                              0, 30, 0, key="rest_sts")
        sls_l = st.number_input("Single-leg stance — left (sec)",
                                0.0, 120.0, 0.0, 0.5, key="rest_sls_l")
        sls_r = st.number_input("Single-leg stance — right (sec)",
                                0.0, 120.0, 0.0, 0.5, key="rest_sls_r")
        submitted = st.form_submit_button("Complete Weekly Review", width="stretch", type="primary")
    if not submitted:
        return
    if not ack_ok:
        st.error("Please confirm the level change above to continue.")
        return

    queries.upsert_rest_assessment(user["email"], cycle, week, int(recall),
                                   reflection, int(sts), int(sls_l), int(sls_r))
    if plan["regression_to"] is not None:
        new_level = f"Level {plan['regression_to']}"
        queries.set_user_level(user["email"], new_level)
        user["level"] = new_level
        st.session_state["user"] = user
    st.session_state.pop("regression_ack", None)
    st.session_state["current_state"] = (
        "PROGRAM_COMPLETE" if week == 4 else "DAILY_HUB")
    st.rerun()
```

### File: `components/views/summary_view.py`
```python
"""Phase 3 — WORKOUT_SUMMARY."""
from __future__ import annotations
import streamlit as st
from utils.session_logic import parse_rpe_scores


def render_summary(user: dict) -> None:
    flags = st.session_state.get("session_flags", {})
    rpe_str = flags.get("last_rpe", "")
    daily = flags.get("last_daily", [])
    rpe_map = parse_rpe_scores(rpe_str)
    avg = (sum(rpe_map.values()) / len(rpe_map)) if rpe_map else 0
    st.title("Workout Complete! 🎉")
    st.balloons()
    st.write(f"**Exercises completed:** {len(daily)}")
    if rpe_map:
        st.write(f"**Average RPE:** {avg:.1f} / 5")
        for cid, score in rpe_map.items():
            st.write(f"- {cid}: {score}/5")
    if st.button("Return to Daily Hub", key="btn_return_hub", width="stretch", type="primary"):
        st.session_state["session_flags"] = {}
        st.session_state["current_state"] = "DAILY_HUB"
        st.rerun()
```

### File: `components/views/training_view.py`
```python
"""Phase 3/4/5 — EXERCISE_SESSION. Effective (autoregulated) prescription,
distinct per-exercise RPE labels (a11y + AppTest-selectable), placeholder
fallback with absolute paths."""
from __future__ import annotations
from pathlib import Path
import streamlit as st
from utils.session_logic import (get_session_position, format_rpe_scores,
                                 normalize_rpe_score)
from utils.exercise_logic import (select_daily_set, get_card,
                                  apply_position_cue, format_prescription)
from utils.autoregulation_logic import effective_prescription
from db import queries

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLACEHOLDER = PROJECT_ROOT / "assets" / "card_placeholder.jpeg"

RPE_OPTIONS = [
    "😃 1 — Very Easy",
    "🙂 2 — Easy",
    "😐 3 — Moderate",
    "😣 4 — Hard",
    "😫 5 — Very Hard",
]


def _level_int(level: str) -> int:
    return int(level.split()[-1])


def _safe_image(path: str, label: str) -> None:
    p = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path
    if p.exists():
        st.image(str(p), width="stretch")
    elif PLACEHOLDER.exists():
        st.image(str(PLACEHOLDER), width="stretch")
    else:
        st.info(f"[image: {label}]")


def render_training_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    daily = select_daily_set(user["email"], pos["cycle"], pos["week"], pos["day"])
    lvl = _level_int(user["level"])
    rx = effective_prescription(user["email"], pos["cycle"], pos["week"], lvl)
    st.title("Stage 2 — Exercises")
    st.info(f"**Level** {user['level']}  ·  {format_prescription(rx)}")
    key_tag = f"{pos['cycle']}_{pos['week']}_{pos['day']}"
    for cid in daily:
        card = apply_position_cue(get_card(cid), lvl)
        with st.container(border=True):
            _safe_image(card["image"], card["title"])
            st.subheader(card["title"])
            st.write(f"**Position:** {card['position_cue']}")
            st.write(f"_{card['instructions']}_")
            st.selectbox(
                f"How hard did that feel? — {card['title']}",   # distinct label per exercise
                options=RPE_OPTIONS,                            # raw == displayed
                index=2,
                key=f"rpe_{key_tag}_{cid}",
            )
    if st.button("Submit Workout", key="btn_submit_workout", width="stretch", type="primary"):
        rpe_map = {cid: normalize_rpe_score(st.session_state[f"rpe_{key_tag}_{cid}"])
                   for cid in daily}
        rpe_str = format_rpe_scores(rpe_map)
        queries.upsert_training_progress(
            user["email"], pos["cycle"], pos["week"], pos["day"],
            ",".join(daily), rpe_str)
        st.session_state["session_flags"] = {"last_rpe": rpe_str, "last_daily": daily}
        st.session_state["current_state"] = "WORKOUT_SUMMARY"
        st.rerun()
```

### File: `components/views/training_view_container.py`
```python
"""Phase 3/4/5 — EXERCISE_SESSION. Effective (autoregulated) prescription,
distinct per-exercise RPE labels (a11y + AppTest-selectable), placeholder
fallback with absolute paths."""
from __future__ import annotations
from pathlib import Path
import streamlit as st
from utils.session_logic import (get_session_position, format_rpe_scores,
                                 normalize_rpe_score)
from utils.exercise_logic import (select_daily_set, get_card,
                                  apply_position_cue, format_prescription)
from utils.autoregulation_logic import effective_prescription
from db import queries

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLACEHOLDER = PROJECT_ROOT / "assets" / "card_placeholder.jpeg"

RPE_OPTIONS = [
    "😃 1 — Very Easy",
    "🙂 2 — Easy",
    "😐 3 — Moderate",
    "😣 4 — Hard",
    "😫 5 — Very Hard",
]


def _level_int(level: str) -> int:
    return int(level.split()[-1])


def _safe_image(path: str, label: str) -> None:
    p = Path(path) if Path(path).is_absolute() else PROJECT_ROOT / path
    if p.exists():
        st.image(str(p), width="stretch")
    elif PLACEHOLDER.exists():
        st.image(str(PLACEHOLDER), width="stretch")
    else:
        st.info(f"[image: {label}]")


def render_training_session(user: dict) -> None:
    pos = get_session_position(user["email"])
    daily = select_daily_set(user["email"], pos["cycle"], pos["week"], pos["day"])
    lvl = _level_int(user["level"])
    rx = effective_prescription(user["email"], pos["cycle"], pos["week"], lvl)
    st.title("Stage 2 — Exercises")
    st.info(f"**Level** {user['level']}  ·  {format_prescription(rx)}")
    key_tag = f"{pos['cycle']}_{pos['week']}_{pos['day']}"
    for cid in daily:
        card = apply_position_cue(get_card(cid), lvl)
        with st.container(border=True):
            _safe_image(card["image"], card["title"])
            st.subheader(card["title"])
            st.write(f"**Position:** {card['position_cue']}")
            st.write(f"_{card['instructions']}_")
            st.selectbox(
                f"How hard did that feel? — {card['title']}",   # distinct label per exercise
                options=RPE_OPTIONS,                            # raw == displayed
                index=2,
                key=f"rpe_{key_tag}_{cid}",
            )
    if st.button("Submit Workout", key="btn_submit_workout", width="stretch", type="primary"):
        rpe_map = {cid: normalize_rpe_score(st.session_state[f"rpe_{key_tag}_{cid}"])
                   for cid in daily}
        rpe_str = format_rpe_scores(rpe_map)
        queries.upsert_training_progress(
            user["email"], pos["cycle"], pos["week"], pos["day"],
            ",".join(daily), rpe_str)
        st.session_state["session_flags"] = {"last_rpe": rpe_str, "last_daily": daily}
        st.session_state["current_state"] = "WORKOUT_SUMMARY"
        st.rerun()
```

### File: `components/debug/dev_controls.py`
```python
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
```

### File: `db/database.py`
```python
"""SQLite connection handler. Driver-agnostic queries live in queries.py.

Note: Streamlit 1.39 on Python 3.12 may emit a cosmetic
RuntimeWarning('coroutine 'expire_cache' was never awaited') from
streamlit/util.py when @st.cache_resource is used with a DB connection.
It does not affect functionality. Suppressed at app startup (see app.py).
Revisit at Phase 6 (Neon router) where the connection pattern changes.
"""
import sqlite3
from pathlib import Path
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "local_test.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema_sqlite.sql"


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """Cached SQLite connection. Schema applied idempotently on first connect."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_PATH.read_text())  # CREATE IF NOT EXISTS — idempotent
    conn.commit()
    return conn


def init_db() -> None:
    """Ensure schema is applied. Cached underneath; safe to call every boot."""
    get_connection()
```

### File: `db/queries.py`
```python
"""CRUD + UPSERT helpers. All writes are idempotent via ON CONFLICT."""
from __future__ import annotations
from typing import Optional
import sqlite3

from db.database import get_connection


def _row_to_dict(row: sqlite3.Row) -> Optional[dict]:
    return dict(row) if row is not None else None


def create_user(email: str, username: str, age: int, sex: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (email, username, age, sex)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(email) DO UPDATE SET
             username=excluded.username, age=excluded.age, sex=excluded.sex""",
        (email, username, age, sex),
    )
    conn.commit()


def get_user_by_credentials(email: str, username: str) -> Optional[dict]:
    """Testing-phase auth: username + email must match."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? AND username = ?",
        (email, username),
    ).fetchone()
    return _row_to_dict(row)


def get_user(email: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _row_to_dict(row)


def update_user_level(email: str, level: str, total_score: int,
                      sarc_f: int, calf: int, balance: int, chair_stand: int,
                      red_flags: str) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE users SET
             level = ?, total_score = ?, sarc_f_score = ?, calf_score = ?,
             balance_score = ?, chair_stand_score = ?, red_flags = ?
           WHERE email = ?""",
        (level, total_score, sarc_f, calf, balance, chair_stand, red_flags, email),
    )
    conn.commit()


def get_current_cycle(email: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT current_cycle FROM users WHERE email = ?", (email,)
    ).fetchone()
    return row["current_cycle"] if row else 1


def advance_cycle(email: str) -> int:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET current_cycle = current_cycle + 1 WHERE email = ?",
        (email,),
    )
    conn.commit()
    return get_current_cycle(email)


def upsert_training_progress(email: str, cycle: int, week: int, day: int,
                            exercise_ids: str, rpe_scores: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO training_progress
             (user_email, cycle, week, day, exercise_ids, rpe_scores)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_email, cycle, week, day) DO UPDATE SET
             exercise_ids=excluded.exercise_ids, rpe_scores=excluded.rpe_scores""",
        (email, cycle, week, day, exercise_ids, rpe_scores),
    )
    conn.commit()


def upsert_weekly_plan(email: str, cycle: int, week: int, exercise_ids: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO weekly_plan (user_email, cycle, week, exercise_ids)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_email, cycle, week) DO UPDATE SET
             exercise_ids=excluded.exercise_ids""",
        (email, cycle, week, exercise_ids),
    )
    conn.commit()
def get_weekly_plan(email: str, cycle: int, week: int) -> Optional[str]:
    """Return persisted exercise_ids string for the week, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT exercise_ids FROM weekly_plan "
        "WHERE user_email = ? AND cycle = ? AND week = ?",
        (email, cycle, week),
    ).fetchone()
    return row["exercise_ids"] if row else None

def upsert_rest_assessment(email: str, cycle: int, week: int,
                           memory_recall_count: int, reflection: str,
                           sit_to_stand_15s: int, sls_left: int, sls_right: int) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO rest_assessments
             (user_email, cycle, week, memory_recall_count, reflection,
              sit_to_stand_15s_cycles, sls_left_sec, sls_right_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_email, cycle, week) DO UPDATE SET
             memory_recall_count=excluded.memory_recall_count,
             reflection=excluded.reflection,
             sit_to_stand_15s_cycles=excluded.sit_to_stand_15s_cycles,
             sls_left_sec=excluded.sls_left_sec,
             sls_right_sec=excluded.sls_right_sec""",
        (email, cycle, week, memory_recall_count, reflection,
         sit_to_stand_15s, sls_left, sls_right),
    )
    conn.commit()

def get_completed_days(email: str, cycle: int) -> set:
    conn = get_connection()
    rows = conn.execute(
        "SELECT week, day FROM training_progress WHERE user_email = ? AND cycle = ?",
        (email, cycle)).fetchall()
    return {(r["week"], r["day"]) for r in rows}


def get_completed_rests(email: str, cycle: int) -> set:
    conn = get_connection()
    rows = conn.execute(
        "SELECT week FROM rest_assessments WHERE user_email = ? AND cycle = ?",
        (email, cycle)).fetchall()
    return {r["week"] for r in rows}

def get_rpe_scores_for_week(email: str, cycle: int, week: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT rpe_scores FROM training_progress "
        "WHERE user_email = ? AND cycle = ? AND week = ? AND day BETWEEN 1 AND 6",
        (email, cycle, week)).fetchall()
    return [r["rpe_scores"] for r in rows]


def set_user_level(email: str, level: str) -> None:
    """Light level update for mid-cycle regression (scores untouched)."""
    conn = get_connection()
    conn.execute("UPDATE users SET level = ? WHERE email = ?", (level, email))
    conn.commit()


def count_completed_workouts(email: str, cycle: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM training_progress "
        "WHERE user_email = ? AND cycle = ?", (email, cycle)).fetchone()
    return row["n"]


```

### File: `db/schema_sqlite.sql`
```sql
-- Elderly Online Training System — SQLite DDL (v4.1)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 110),
  sex TEXT CHECK (sex IN ('M','F','U')) DEFAULT 'U',
  sarc_f_score INTEGER,
  calf_score INTEGER,
  balance_score INTEGER,
  chair_stand_score INTEGER,
  red_flags TEXT DEFAULT '',
  total_score INTEGER,
  level TEXT CHECK (level IN
    ('Level 0','Level 1','Level 2','Level 3','Level 4')),
  current_cycle INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS training_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL CHECK (week BETWEEN 0 AND 4),
  day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 7),
  exercise_ids TEXT NOT NULL,
  rpe_scores TEXT,
  UNIQUE (user_email, cycle, week, day)
);

CREATE TABLE IF NOT EXISTS weekly_plan (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  exercise_ids TEXT NOT NULL,
  UNIQUE (user_email, cycle, week)
);

CREATE TABLE IF NOT EXISTS rest_assessments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL REFERENCES users(email),
  cycle INTEGER NOT NULL DEFAULT 1,
  week INTEGER NOT NULL,
  memory_recall_count INTEGER,
  reflection TEXT,
  sit_to_stand_15s_cycles INTEGER,
  sls_left_sec INTEGER,
  sls_right_sec INTEGER,
  UNIQUE (user_email, cycle, week)
);
```

### File: `data/breathing_sequences.json`
```json
{
  "practices": [
    {"code": "DB01", "title": "Belly Breathing", "inhale_s": 3, "hold_s": 0, "exhale_s": 3, "cycles": 10, "focus": "Mind-muscle expansion awareness"},
    {"code": "DB02", "title": "Core Brace", "inhale_s": 3, "hold_s": 2, "exhale_s": 3, "cycles": 9, "focus": "Deep core engagement during breath"},
    {"code": "DB03", "title": "Breath_L1_L2", "inhale_s": 3, "hold_s": 0, "exhale_s": 5, "cycles": 9, "focus": "Parasympathetic relaxation"},
    {"code": "DB04", "title": "Breath_L3_Pause", "inhale_s": 4, "hold_s": 2, "exhale_s": 6, "cycles": 7, "focus": "Lung capacity & oxygenation"},
    {"code": "DB05", "title": "Breath_L4_8s", "inhale_s": 4, "hold_s": 0, "exhale_s": 8, "cycles": 6, "focus": "Peak lung exchange & deep core recoil"}
  ],
  "schedule": [
    {"week": 0, "days_1_3": ["DB01", "DB02"], "days_4_6": ["DB03"], "day_7": []},
    {"week": 1, "days_1_3": ["DB03"], "days_4_6": ["DB04"], "day_7": []},
    {"week": 2, "days_1_3": ["DB04"], "days_4_6": ["DB05"], "day_7": []},
    {"week": 3, "days_1_3": ["DB05"], "days_4_6": ["DB05"], "day_7": []},
    {"week": 4, "days_1_3": ["DB05"], "days_4_6": ["DB05"], "day_7": []}
  ],
  "safety_text": {
    "lightheadedness_valve": "If you feel lightheaded, breathless, or dizzy at any point, immediately stop counting and return to your normal, comfortable breathing pattern.",
    "orthostatic_warning": "When moving between lying down, seated, or standing positions, pause for 10-15 seconds while seated. If dizziness occurs, remain seated until fully recovered.",
    "chair_standard": "Use a sturdy, non-wheeled chair placed on a non-slip surface."
  }
}
```

### File: `data/exercise_cards.json`
```json
[
  {"card_id":"C01","title":"Seated Calf Raise","category":"C","base_level":1,"image":"assets/exercises/card_C01.jpeg","isometric":false,"instructions":"DRAFT — Sit tall, feet flat. Lift heels keeping toes down. Lower with control.","position_cues":{"0":"Seated with back support; small range.","1":"Seated upright; full range.","2":"Standing holding chair; full range.","3":"Standing independently; controlled tempo.","4":"Single-leg or tempo pauses."}},
  {"card_id":"C02","title":"Seated Toe Taps & Shin Lift","category":"C","base_level":1,"image":"assets/exercises/card_C02.jpeg","isometric":false,"instructions":"DRAFT — Tap toes then lift shins, alternating rhythm.","position_cues":{"0":"Seated with back support.","1":"Seated upright.","2":"Standing holding chair.","3":"Standing independently.","4":"Add tempo changes."}},
  {"card_id":"C03","title":"Standing Calf Raise (Chair)","category":"C","base_level":2,"image":"assets/exercises/card_C03.jpeg","isometric":false,"instructions":"DRAFT — Rise onto the balls of the feet, lower slowly.","position_cues":{"0":"Seated, gentle heel lifts.","1":"Seated upright, full heel lifts.","2":"Standing holding chair.","3":"Standing independently.","4":"Single-leg raises."}},
  {"card_id":"C04","title":"Supported Loaded Calf Stretch","category":"C","base_level":2,"image":"assets/exercises/card_C04.jpeg","isometric":true,"instructions":"DRAFT — Press rear heel down, hold stretch.","position_cues":{"0":"Seated, gentle ankle range.","1":"Seated upright, deeper range.","2":"Standing holding chair.","3":"Standing independently.","4":"Add rear-foot elevation."}},
  {"card_id":"PC01","title":"Seated Pelvic Tilt & Kegel","category":"PC","base_level":1,"image":"assets/exercises/card_PC01.jpeg","isometric":true,"instructions":"DRAFT — Tilt pelvis gently and engage pelvic floor.","position_cues":{"0":"Seated with back support.","1":"Seated upright.","2":"Supported standing.","3":"Independent standing.","4":"Add slow tempo holds."}},
  {"card_id":"PC02","title":"Seated Trunk Rotation","category":"PC","base_level":1,"image":"assets/exercises/card_PC02.jpeg","isometric":false,"instructions":"DRAFT — Rotate torso gently side to side.","position_cues":{"0":"Seated with back support; small range.","1":"Seated upright; full range.","2":"Supported standing; gentle.","3":"Independent standing.","4":"Add reach and pause."}},
  {"card_id":"PC03","title":"Supine Glute Bridge + Core Lock","category":"PC","base_level":3,"image":"assets/exercises/card_PC03.jpeg","isometric":true,"instructions":"DRAFT — Lie supine, lift hips, brace core.","position_cues":{"0":"Seated glute squeeze instead.","1":"Seated glute squeeze with hold.","2":"Bridge with smaller range.","3":"Full bridge with core lock.","4":"Single-leg bridge progression."}},
  {"card_id":"PC04","title":"Seated Diagonal Woodchopper","category":"PC","base_level":3,"image":"assets/exercises/card_PC04.jpeg","isometric":false,"instructions":"DRAFT — Diagonal reach across body with core rotation.","position_cues":{"0":"Seated with back support; small range.","1":"Seated upright.","2":"Supported standing.","3":"Independent standing.","4":"Add tempo and deeper range."}},
  {"card_id":"G01","title":"Seated Isometric Glute Squeeze","category":"G","base_level":1,"image":"assets/exercises/card_G01.jpeg","isometric":true,"instructions":"DRAFT — Squeeze glutes and hold.","position_cues":{"0":"Seated with back support.","1":"Seated upright.","2":"Supported standing squeeze.","3":"Independent standing squeeze.","4":"Add hold splits."}},
  {"card_id":"G02","title":"Standing Hip Extension (Chair)","category":"G","base_level":1,"image":"assets/exercises/card_G02.jpeg","isometric":false,"instructions":"DRAFT — Extend one leg back, return slowly.","position_cues":{"0":"Seated, gentle knee extension.","1":"Seated upright, fuller extension.","2":"Standing holding chair.","3":"Independent standing.","4":"Add ankle weights or tempo."}},
  {"card_id":"G03","title":"Supported Chair Sit-to-Stand","category":"G","base_level":2,"image":"assets/exercises/card_G03.jpeg","isometric":false,"instructions":"DRAFT — Stand up from chair, sit back controlled.","position_cues":{"0":"Chair-assisted, partial range.","1":"Seated upright, hands on chest.","2":"Standing hold for balance only.","3":"Independent, arms crossed.","4":"Slow tempo or pause at bottom."}},
  {"card_id":"G04","title":"Standing Side Hip Abduction","category":"G","base_level":2,"image":"assets/exercises/card_G04.jpeg","isometric":false,"instructions":"DRAFT — Lift leg out to side, lower slowly.","position_cues":{"0":"Seated, gentle leg slides.","1":"Seated upright, fuller range.","2":"Standing holding chair.","3":"Independent standing.","4":"Add hold at top."}},
  {"card_id":"HF01","title":"Seated High-Knee Holds","category":"HF","base_level":1,"image":"assets/exercises/card_HF01.jpeg","isometric":true,"instructions":"DRAFT — Lift knee and hold, alternate sides.","position_cues":{"0":"Seated with back support; small lift.","1":"Seated upright; hip-height.","2":"Standing holding chair.","3":"Independent standing.","4":"Add hold duration."}},
  {"card_id":"HF02","title":"Seated Resisted Leg Raise","category":"HF","base_level":1,"image":"assets/exercises/card_HF02.jpeg","isometric":false,"instructions":"DRAFT — Straight leg lift, lower controlled.","position_cues":{"0":"Seated with back support; small range.","1":"Seated upright.","2":"Supported standing march.","3":"Independent standing march.","4":"Add tempo or height."}},
  {"card_id":"HF03","title":"Standing Chair Marching","category":"HF","base_level":2,"image":"assets/exercises/card_HF03.jpeg","isometric":false,"instructions":"DRAFT — March in place, lift knees.","position_cues":{"0":"Seated marching.","1":"Seated upright marching.","2":"Standing holding chair.","3":"Independent standing.","4":"Add tempo or height."}},
  {"card_id":"HF04","title":"Static Supported Step Lunge","category":"HF","base_level":3,"image":"assets/exercises/card_HF04.jpeg","isometric":true,"instructions":"DRAFT — Step into lunge, hold, return.","position_cues":{"0":"Seated small knee bend.","1":"Seated upright knee bend.","2":"Standing holding chair; shallow lunge.","3":"Independent shallow lunge.","4":"Deeper range or hold."}},
  {"card_id":"SP01","title":"Seated Lat Stretch & Reach","category":"SP","base_level":1,"image":"assets/exercises/card_SP01.jpeg","isometric":true,"instructions":"DRAFT — Reach overhead, stretch lats.","position_cues":{"0":"Seated with back support; small reach.","1":"Seated upright; full reach.","2":"Supported standing reach.","3":"Independent standing reach.","4":"Add lateral flexion."}},
  {"card_id":"SP02","title":"Wall Slides / Arm Ladder","category":"SP","base_level":1,"image":"assets/exercises/card_SP02.jpeg","isometric":false,"instructions":"DRAFT — Slide arms up wall, lower slowly.","position_cues":{"0":"Seated, gentle arm raises.","1":"Seated upright, full raises.","2":"Standing wall slide.","3":"Standing independent.","4":"Add holds or resistance."}},
  {"card_id":"SP03","title":"Supported Wall Push-Offs","category":"SP","base_level":3,"image":"assets/exercises/card_SP03.jpeg","isometric":false,"instructions":"DRAFT — Push off wall, return controlled.","position_cues":{"0":"Seated chest press (no wall).","1":"Seated upright press.","2":"Standing wall push, hands higher.","3":"Standard wall push-off.","4":"Lower hand position or single-arm."}},
  {"card_id":"SP04","title":"Seated Goalpost Squeeze","category":"SP","base_level":2,"image":"assets/exercises/card_SP04.jpeg","isometric":true,"instructions":"DRAFT — Arms in goalpost, squeeze shoulder blades.","position_cues":{"0":"Seated with back support.","1":"Seated upright.","2":"Supported standing.","3":"Independent standing.","4":"Add hold and retraction."}},
  {"card_id":"CM01","title":"Seated Rhythm March & Arm Drive","category":"CM","base_level":2,"image":"assets/exercises/card_CM01.jpeg","isometric":false,"instructions":"DRAFT — March in place with rhythmic arm drive.","position_cues":{"0":"Seated with back support; gentle.","1":"Seated upright; full arm drive.","2":"Standing holding chair.","3":"Independent standing.","4":"Add tempo or range."}},
  {"card_id":"CM02","title":"Supine Spinal Twist","category":"CM","base_level":2,"image":"assets/exercises/card_CM02.jpeg","isometric":false,"instructions":"DRAFT — Lie supine, drop knees side to side.","position_cues":{"0":"Seated gentle rotation.","1":"Seated upright rotation.","2":"Supine, small range.","3":"Supine, full range.","4":"Add hold or deeper range."}},
  {"card_id":"CM03","title":"Standing Side-Step Taps","category":"CM","base_level":2,"image":"assets/exercises/card_CM03.jpeg","isometric":false,"instructions":"DRAFT — Step side to side, rhythmic taps.","position_cues":{"0":"Seated toe taps.","1":"Seated upright taps.","2":"Standing holding chair.","3":"Independent standing.","4":"Add tempo or wider steps."}},
  {"card_id":"CM04","title":"Supported Deep Squat Hold","category":"CM","base_level":3,"image":"assets/exercises/card_CM04.jpeg","isometric":true,"instructions":"DRAFT — Lower into squat, hold, rise.","position_cues":{"0":"Seated, small knee bends.","1":"Seated upright, partial stand.","2":"Standing holding chair; shallow.","3":"Independent shallow squat hold.","4":"Deeper hold or single-leg finish."}}
]
```

### File: `data/prescriptions.json`
```json
{
  "0": {"sets": 2, "reps_min": 6, "reps_max": 8, "hold_s": 10, "rest_s_min": 60, "rest_s_max": 90},
  "1": {"sets": 2, "reps_min": 8, "reps_max": 10, "hold_s": null, "rest_s_min": 60, "rest_s_max": 60},
  "2": {"sets": 2, "reps_min": 10, "reps_max": 12, "hold_s": null, "rest_s_min": 45, "rest_s_max": 60},
  "3": {"sets": 3, "reps_min": 10, "reps_max": 12, "hold_s": null, "rest_s_min": 45, "rest_s_max": 45},
  "4": {"sets": 3, "reps_min": 12, "reps_max": 15, "hold_s": null, "rest_s_min": 30, "rest_s_max": 45}
}
```

### File: `data/scoring_rubrics.json`
```json
{
  "sarc_f": {
    "items": [
      {"name": "strength", "label": "Lifting/carrying ~10 lbs", "options": ["No difficulty", "Some difficulty", "Much difficulty / unable"]},
      {"name": "walking", "label": "Walking across a room", "options": ["No difficulty", "Some difficulty", "Much difficulty / needs aid"]},
      {"name": "rise_chair", "label": "Rising from a chair (5x)", "options": ["No difficulty", "Some difficulty", "Much difficulty / unable"]},
      {"name": "climb_stairs", "label": "Climbing 10 steps", "options": ["No difficulty", "Some difficulty", "Much difficulty / unable"]},
      {"name": "falls", "label": "Falls in past 12 months", "options": ["None", "1-3", "4 or more"]}
    ],
    "max": 10
  },
  "calf_circumference_cm": {
    "M": {"normal_min": 36.0, "risk_max": 34.0},
    "F": {"normal_min": 34.0, "risk_max": 33.0},
    "unspecified_policy": "max"
  },
  "single_leg_stance_sec": {
    "unisex": {"normal_min": 20.0, "risk_max": 10.0}
  },
  "chair_stand_30s": {
    "M": {"normal_min": 14, "risk_max": 11},
    "F": {"normal_min": 12, "risk_max": 9},
    "unspecified_policy": "max"
  },
  "level_assignment": {
    "sarc_f_override": 4,
    "total_high": 8,
    "age_high": 80,
    "total_mid": 5,
    "age_mid": 75,
    "total_low": 3
  },
  "red_flags": ["chest_pain", "joint_replacement_under_6mo", "uncontrolled_bp_over_160_100", "two_or_more_recent_falls"],
  "notes": "0-band and 2-band anchors derived directly from supplied clinical reference data (60-69 cohort). 1-band is interpolated and requires clinical sign-off at the Phase 1 gate. For users 70+ these 60-69 norms may over-score impairment, erring toward a safer (lower) level."
}
```

## 4. Modification Log
| Date | Change Summary | Author | Impact |
|---|---|---|---|
| [Date] | Initial code bundling | Automation | Compiled all local modules |

## 5. Run & Verification Guide
1. **Environment Setup:** Ensure Python 3.x is installed.
2. **Database Initialization:** The SQLite database will auto-initialize upon running the main entry script.
3. **Execution:** Run the primary application file (e.g., `python app.py`).