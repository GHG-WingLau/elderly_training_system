#!/usr/bin/env python3
"""tools/generate_audio.py — narration generator for change #12 (dev tool).

NOT part of the app runtime or requirements.txt (dev-only dependency,
user-approved):

    pip install edge-tts

Generates, from the VERBATIM instruction text in data/*.json:
  - assets/audio/{card_id}.mp3   (24 exercise cards)
  - assets/audio/{code}.mp3      (5 breathing practices)
  - assets/audio/manifest.json   (drift guard — see below)

User decisions: edge-tts engine; gentle female voice (default
en-US-AriaNeural — calm/warm; alternatives: en-US-JennyNeural,
en-US-MichelleNeural, en-GB-SoniaNeural via --voice); rate -15%
(15% slow-down); 4 files at a time. Narration content = instruction
ONLY (purpose is not narrated).

Because text is read from the JSON at generation time, narration is
verbatim by construction. GOVERNANCE RULE (DECISIONS.md): any change to
instruction copy MUST regenerate the affected mp3s in the same change.
The manifest binds each mp3 to the sha256 of its exact source string;
the production test compares manifest hashes against the current JSON,
making stale audio a pytest failure instead of an unheard defect.

Usage:
    python tools/generate_audio.py                     # all 29 files
    python tools/generate_audio.py --filter DB01       # spot regeneration
    python tools/generate_audio.py --voice en-US-JennyNeural --rate "-20%"
    python tools/generate_audio.py --list              # show targets

Requires internet. Retry logic: 3 attempts per file; on total failure the
manifest is NOT written (no partial-state manifests).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import edge_tts

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUT_DIR = PROJECT_ROOT / "assets" / "audio"

DEFAULT_VOICE = "en-US-AriaNeural"   # gentle female (user decision)
DEFAULT_RATE = "-15%"                # 15% slow-down (user decision)
DEFAULT_CONCURRENCY = 4              # files at a time (user decision)
RETRIES = 3


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_items() -> list[dict]:
    """(code, text) pairs from both data files — instruction text only."""
    items: list[dict] = []
    with open(DATA_DIR / "exercise_cards.json") as f:
        for card in json.load(f):
            items.append({"code": card["card_id"],
                          "text": card["instructions"]})
    with open(DATA_DIR / "breathing_sequences.json") as f:
        for p in json.load(f)["practices"]:
            items.append({"code": p["code"], "text": p["instruction"]})
    for it in items:
        if not it["text"].strip():
            sys.exit(f"empty instruction text for {it['code']} — "
                     "check data/*.json")
    return items


async def _generate_one(sem: asyncio.Semaphore, item: dict, voice: str,
                        rate: str, manifest: dict) -> None:
    async with sem:
        dest = OUT_DIR / f"{item['code']}.mp3"
        last_err: Exception | None = None
        for attempt in range(1, RETRIES + 1):
            try:
                communicate = edge_tts.Communicate(item["text"], voice,
                                                   rate=rate)
                await communicate.save(str(dest))
                manifest[item["code"]] = {
                    "text_sha256": _sha256_text(item["text"]),
                    "mp3_sha256": _sha256_file(dest),
                    "chars": len(item["text"]),
                    "voice": voice,
                    "rate": rate,
                }
                print(f"  ok {item['code']}.mp3 ({len(item['text'])} chars)")
                return
            except Exception as e:  # transient network/service errors
                last_err = e
                await asyncio.sleep(1.5 * attempt)
        dest.unlink(missing_ok=True)  # never leave a partial file
        raise RuntimeError(f"{item['code']}: {last_err}") from last_err


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate narration mp3s from data/*.json (edge-tts).")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default=DEFAULT_RATE,
                    help='edge-tts rate string, e.g. "-15%%"')
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    ap.add_argument("--filter", default="",
                    help="comma-separated codes, e.g. C01,DB03")
    ap.add_argument("--list", action="store_true",
                    help="list targets and exit")
    args = ap.parse_args()

    items = _load_items()
    if args.filter:
        wanted = {c.strip() for c in args.filter.split(",") if c.strip()}
        unknown = wanted - {i["code"] for i in items}
        if unknown:
            sys.exit(f"unknown codes: {sorted(unknown)}")
        items = [i for i in items if i["code"] in wanted]
    if args.list:
        for i in items:
            print(f"{i['code']}  {len(i['text'])} chars")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest.json"
    # --filter updates a subset: preserve existing entries for others.
    manifest: dict = (json.loads(manifest_path.read_text())
                      if manifest_path.is_file() else {})

    print(f"Generating {len(items)} narration file(s) — "
          f"voice {args.voice}, rate {args.rate}, "
          f"{args.concurrency} at a time")
    sem = asyncio.Semaphore(args.concurrency)
    errors: list[BaseException] = []

    async def run() -> None:
        tasks = [_generate_one(sem, it, args.voice, args.rate, manifest)
                 for it in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors.extend(r for r in results if isinstance(r, BaseException))

    asyncio.run(run())

    if errors:
        for e in errors:
            print(f"  FAILED {e}", file=sys.stderr)
        sys.exit(f"{len(errors)} file(s) failed — manifest NOT written; "
                 "rerun (optionally with --filter) to retry")
    entries = {k: v for k, v in manifest.items() if not k.startswith("_")}
    manifest["_meta"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voice": args.voice,
        "rate": args.rate,
        "engine": "edge-tts",
        "note": ("text_sha256 binds each mp3 to the exact instruction "
                 "string it was generated from; a mismatch with "
                 "data/*.json means stale audio — regenerate."),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"manifest written: {manifest_path} "
          f"({len(entries)} entries total)")


if __name__ == "__main__":
    main()