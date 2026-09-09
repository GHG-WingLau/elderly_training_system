#!/usr/bin/env bash
# Preflight — mechanical verification after any file apply, BEFORE pytest.
# Born from the macOS paste-clipping incidents (2026-09): tails clipped
# at arbitrary mid-line points; py_compile + JSON-parse name the file.
set -e
python -m compileall -q app.py components utils tests && echo ALL-COMPILE-OK
python - <<'EOF'
import json, pathlib
files = sorted(pathlib.Path("data").glob("*.json"))
fails = [f"{p.name}: {e}" for p in files
         for e in [None] if False]  # placeholder, see below
ok = True
for p in files:
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        ok = False
        print("FAIL", p.name, "->", e)
if not ok:
    raise SystemExit(1)
print(f"ALL-JSON-OK ({len(files)} files)")
EOF