"""Per-locale UI-string access — Phase 7 activation layer.

data/ui_strings.json is the EN base file; ui_strings.{locale}.json per
locale (7.3 per-locale files). Per-locale caches, process-lifetime —
dev-server restart after edits, like every data cache. Views call
tr("hub.title").format(...): templates carry the census placeholder
names, and placeholder parity is machine-checked by
tests/test_ui_strings.py.

tr_locale() serves explicit-locale call sites that resolve earlier
than the session (app.py's set_page_config, which runs at first script
load before boot resolution; it resolves from ?lang= directly).

level_display() maps the STORED EN values ("Level 0".."Level 4" — never
localized, per the level-display decision) to the active locale's
display name; unknown values fail loud.
"""
from __future__ import annotations

import json
from pathlib import Path

from utils.locale import safe_locale

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_strings_caches: dict[str, dict] = {}


def _load(locale: str) -> dict:
    if locale not in _strings_caches:
        name = ("ui_strings.json" if locale == "en"
                else f"ui_strings.{locale}.json")
        with open(DATA_DIR / name, encoding="utf-8") as f:
            _strings_caches[locale] = json.load(f)
    return _strings_caches[locale]


def tr(key: str) -> str:
    """Active-locale UI template. KeyError on a missing key — fail-loud
    reads (the #13 discipline): a missing translation must crash the
    render in dev, never silently fall back to EN."""
    doc = _load(safe_locale())
    section, _, name = key.partition(".")
    return doc[section][name]


def tr_locale(locale: str, key: str) -> str:
    """Template for an EXPLICIT locale — for call sites that resolve
    earlier than the session (app.py's set_page_config runs at first
    script load, before boot resolution; it resolves from ?lang=
    directly). Same fail-loud contract as tr()."""
    doc = _load(locale)
    section, _, name = key.partition(".")
    return doc[section][name]


def level_display(level_value: str) -> str:
    """Display name for a stored level value, in the active locale."""
    doc = _load(safe_locale())
    try:
        return doc["levels"][level_value]
    except KeyError as exc:
        raise KeyError(f"no display name for level {level_value!r}") from exc