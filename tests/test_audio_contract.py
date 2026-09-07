"""tests/test_audio_contract.py — change #12: narration contract.

Contract:
  1. every exercise card and breathing practice carries an "audio" field
     resolving to an existing mp3, and assets/audio/ holds exactly 29;
  2. manifest.json (written by tools/generate_audio.py) covers every code;
  3. DRIFT GUARD: each manifest text_sha256 equals the sha256 of the
     CURRENT instruction string — a copy change without regenerating the
     mp3 fails here (stale narration becomes a red pytest, not an
     unheard defect);
  4. each manifest mp3_sha256 matches the file on disk (accidental
     replacement/edit fails here).

mp3 CONTENT is unverifiable automatically; the manifest is the chain of
custody. Spot-listening remains a delivery-time manual QA line.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from utils.assets import resolve_asset_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
MANIFEST_PATH = AUDIO_DIR / "manifest.json"

EXPECTED_FILES = 29  # 24 exercise cards + 5 breathing practices


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _cards() -> list:
    with open(DATA_DIR / "exercise_cards.json") as f:
        return json.load(f)


def _practices() -> list:
    with open(DATA_DIR / "breathing_sequences.json") as f:
        return json.load(f)["practices"]


def _manifest() -> dict:
    assert MANIFEST_PATH.is_file(), (
        f"missing {MANIFEST_PATH} — run tools/generate_audio.py")
    return json.loads(MANIFEST_PATH.read_text())


def _instruction_texts() -> dict:
    texts = {c["card_id"]: c["instructions"] for c in _cards()}
    texts.update({p["code"]: p["instruction"] for p in _practices()})
    return texts


def test_every_card_audio_field_resolves():
    problems = []
    for c in _cards():
        if not c.get("audio"):
            problems.append(f"{c['card_id']}: missing 'audio' field")
        elif not resolve_asset_path(c["audio"]).is_file():
            problems.append(f"{c['card_id']}: {c['audio']} not found")
    assert not problems, "; ".join(problems)


def test_every_practice_audio_field_resolves():
    problems = []
    for p in _practices():
        if not p.get("audio"):
            problems.append(f"{p['code']}: missing 'audio' field")
        elif not resolve_asset_path(p["audio"]).is_file():
            problems.append(f"{p['code']}: {p['audio']} not found")
    assert not problems, "; ".join(problems)


def test_audio_file_count():
    mp3s = list(AUDIO_DIR.glob("*.mp3"))
    assert len(mp3s) == EXPECTED_FILES, (
        f"expected {EXPECTED_FILES} mp3s in {AUDIO_DIR}, found {len(mp3s)}: "
        f"{sorted(m.name for m in mp3s)}")


def test_manifest_covers_all_codes():
    codes = set(_instruction_texts())
    covered = set(_manifest()) - {"_meta"}
    assert covered == codes, (
        f"manifest/code mismatch: missing={sorted(codes - covered)}, "
        f"extra={sorted(covered - codes)}")


def test_manifest_text_hashes_match_current_instructions():
    """THE drift guard: copy changed but mp3 not regenerated -> stale."""
    manifest, texts = _manifest(), _instruction_texts()
    stale = [code for code, text in texts.items()
             if manifest[code]["text_sha256"] != _sha_text(text)]
    assert not stale, (
        f"stale narration (instruction copy changed, mp3 not regenerated) "
        f"for: {stale} — run tools/generate_audio.py --filter "
        f"{','.join(sorted(stale))}")


def test_manifest_mp3_hashes_match_files():
    manifest = _manifest()
    mismatches = [code for code in set(_manifest()) - {"_meta"}
                  if manifest[code]["mp3_sha256"]
                  != _sha_file(AUDIO_DIR / f"{code}.mp3")]
    assert not mismatches, (
        f"mp3 file does not match manifest (replaced/edited?): {mismatches}")