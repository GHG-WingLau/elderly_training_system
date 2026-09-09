#!/usr/bin/env python3
"""tools/generate_audio.py — narration generator (change #12 + Phase 7).

NOT part of the app runtime or requirements.txt (dev-only dependency,
user-approved):

    pip install edge-tts

Generates, from the VERBATIM instruction text in the locale's data
files (29 entries per locale: 24 exercise cards + 5 breathing
practices):
  - en:     assets/audio/{code}.mp3 + assets/audio/manifest.json
  - zh-HK:  assets/audio/zh-HK/{code}.mp3 + .../zh-HK/manifest.json
  - zh-TW:  assets/audio/zh-TW/{code}.mp3 + .../zh-TW/manifest.json

EN keeps the TOP-LEVEL layout (filenames are contract — pinned by
tests); locales use per-locale subdirectories matching the audio paths
in the locale JSONs (missing files render silently by design until
generated).

Phase 7 (team decisions): voices — en en-US-AriaNeural (locked),
zh-HK zh-HK-HiuMaanNeural, zh-TW zh-TW-HsiaoChenNeural; rate -15% for
ALL locales to start (evaluate by spot-listening; per-language tuning
later — every manifest entry records voice+rate, so a rate change is
auditable and regenerates only the affected locale).

Because text is read from the locale's JSON at generation time,
narration is verbatim by construction, per locale. GOVERNANCE RULE
(DECISIONS.md, extended per locale): any change to instruction copy in
ANY locale file MUST regenerate that locale's affected mp3s in the same
change — the per-locale manifest drift guard makes stale audio a
pytest failure instead of an unheard defect.

Usage:
    python tools/generate_audio.py                     # EN (as before)
    python tools/generate_audio.py --lang zh-HK        # one locale
    python tools/generate_audio.py --lang all          # all three
    python tools/generate_audio.py --lang zh-TW --filter DB01
    python tools/generate_audio.py --list --lang zh-HK

Requires internet. Retry logic: 3 attempts per file; on total failure
the locale's manifest is NOT written (no partial-state manifests).
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

LOCALES = ("en", "zh-HK", "zh-TW")
VOICES = {
    "en": "en-US-AriaNeural",         # locked (change #12)
    "zh-HK": "zh-HK-HiuMaanNeural",   # team decision (Phase 7)
    "zh-TW": "zh-TW-HsiaoChenNeural"  # team decision (Phase 7)
}
DEFAULT_RATE = "-15%"                 # all locales to start (team decision)
DEFAULT_CONCURRENCY = 4               # files at a time (user decision)
RETRIES = 3


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _data_filename(locale: str, base: str) -> str:
    return base if locale == "en" else base.replace(".json", f".{locale}.json")


def _out_dir(locale: str) -> Path:
    """EN keeps the top-level layout (filenames are contract); locales
    use per-locale subdirectories (matching the locale JSONs' audio
    paths)."""
    return OUT_DIR if locale == "en" else OUT_DIR / locale


def _load_items(locale: str) -> list[dict]:
    """(code, text) pairs from the LOCALE's data files — instruction
    text only (purpose is not narrated)."""
    items: list[dict] = []
    with open(DATA_DIR / _data_filename(locale, "exercise_cards.json"),
              encoding="utf-8") as f:
        for card in json.load(f):
            items.append({"code": card["card_id"],
                          "text": card["instructions"]})
    with open(DATA_DIR / _data_filename(locale, "breathing_sequences.json"),
              encoding="utf-8") as f:
        for p in json.load(f)["practices"]:
            items.append({"code": p["code"], "text": p["instruction"]})
    for it in items:
        if not it["text"].strip():
            sys.exit(f"[{locale}] empty instruction text for "
                     f"{it['code']} — check the locale's data/*.json")
    return items


async def _generate_one(sem: asyncio.Semaphore, item: dict, locale: str,
                        voice: str, rate: str, manifest: dict) -> None:
    async with sem:
        dest = _out_dir(locale) / f"{item['code']}.mp3"
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
                print(f"  ok [{locale}] {item['code']}.mp3 "
                      f"({len(item['text'])} chars)")
                return
            except Exception as e:  # transient network/service errors
                last_err = e
                await asyncio.sleep(1.5 * attempt)
        dest.unlink(missing_ok=True)  # never leave a partial file
        raise RuntimeError(
            f"[{locale}] {item['code']}: {last_err}") from last_err


def _run_locale(locale: str, voice: str, rate: str, concurrency: int,
                filter_codes: str) -> bool:
    """Generate one locale's set; True on success. On any file failure
    the locale's manifest is NOT written (no partial-state manifests)."""
    items = _load_items(locale)
    if filter_codes:
        wanted = {c.strip() for c in filter_codes.split(",") if c.strip()}
        unknown = wanted - {i["code"] for i in items}
        if unknown:
            sys.exit(f"[{locale}] unknown codes: {sorted(unknown)}")
        items = [i for i in items if i["code"] in wanted]

    out = _out_dir(locale)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    # --filter updates a subset: preserve existing entries for others.
    manifest: dict = (json.loads(manifest_path.read_text(encoding="utf-8"))
                      if manifest_path.is_file() else {})

    print(f"[{locale}] generating {len(items)} file(s) — "
          f"voice {voice}, rate {rate}, {concurrency} at a time")
    sem = asyncio.Semaphore(concurrency)
    errors: list[BaseException] = []

    async def run() -> None:
        tasks = [_generate_one(sem, it, locale, voice, rate, manifest)
                 for it in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors.extend(r for r in results if isinstance(r, BaseException))

    asyncio.run(run())

    if errors:
        for e in errors:
            print(f"  FAILED {e}", file=sys.stderr)
        print(f"[{locale}] {len(errors)} file(s) failed — manifest NOT "
              "written; rerun (optionally with --filter) to retry",
              file=sys.stderr)
        return False

    entries = {k: v for k, v in manifest.items() if not k.startswith("_")}
    manifest["_meta"] = {
        "locale": locale,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voice": voice,
        "rate": rate,
        "engine": "edge-tts",
        "note": ("text_sha256 binds each mp3 to the exact instruction "
                 "string it was generated from; a mismatch with the "
                 "locale's data/*.json means stale audio — regenerate."),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")
    print(f"[{locale}] manifest written: {manifest_path} "
          f"({len(entries)} entries total)")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate narration mp3s per locale (edge-tts).")
    ap.add_argument("--lang", default="en",
                    help="en | zh-HK | zh-TW | all (default: en)")
    ap.add_argument("--voice", default="",
                    help="override the locale's default voice")
    ap.add_argument("--rate", default=DEFAULT_RATE,
                    help='edge-tts rate string, e.g. "-15%%"')
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    ap.add_argument("--filter", default="",
                    help="comma-separated codes, e.g. C01,DB03")
    ap.add_argument("--list", action="store_true",
                    help="list targets and exit")
    args = ap.parse_args()

    langs = list(LOCALES) if args.lang == "all" else [args.lang]
    if any(l not in LOCALES for l in langs):
        sys.exit(f"unknown --lang {args.lang!r}; "
                 f"choose from {LOCALES} or all")

    if args.list:
        for locale in langs:
            print(f"[{locale}]")
            for i in _load_items(locale):
                print(f"  {i['code']}  {len(i['text'])} chars")
        return

    failures = []
    for locale in langs:
        voice = args.voice or VOICES[locale]
        if not _run_locale(locale, voice, args.rate,
                           args.concurrency, args.filter):
            failures.append(locale)
    if failures:
        sys.exit(f"locale(s) failed: {failures}")


if __name__ == "__main__":
    main()