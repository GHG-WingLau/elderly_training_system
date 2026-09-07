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