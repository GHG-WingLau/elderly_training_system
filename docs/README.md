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