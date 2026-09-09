"""Shared static-asset helpers: path resolution + placeholder-safe rendering.

Image references live in data/*.json as paths RELATIVE TO THE PROJECT ROOT
(e.g. "assets/exercises/DB01.jpeg"); audio references follow the same
convention (e.g. "assets/audio/C01.mp3", change #12). Per-locale audio
paths (assets/audio/{locale}/{code}.mp3) follow the same rule — a missing
file renders nothing (supplementary content).

Rendering philosophy differs by medium:
- IMAGES are structural content: a missing file/field renders the shared
  placeholder (visual continuity).
- AUDIO is SUPPLEMENTARY content (change #12 decision: narration alongside
  text, verbatim, instruction-only): the instruction text is authoritative,
  so a missing file/field renders NOTHING rather than a placeholder.
  Completeness — and the manifest drift guard — is enforced at test time
  by tests/test_assets.py (images) and tests/test_audio_contract.py (audio).

Asset paths are PRESENTATION concerns, not clinical values (constraint 2).
All element sizing uses the pinned Streamlit 1.62 unified API
(width="stretch"). use_container_width / use_column_width are banned.

Phase 7 (view conversion): the audio hint and image-fallback notices
render via utils.strings (tr); the fallback {label} stays the caller's
locale data (card title / practice title).
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.strings import tr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
PLACEHOLDER = ASSETS_DIR / "card_placeholder.jpeg"


def resolve_asset_path(path: str | Path) -> Path:
    """Resolve a str/Path asset reference to an absolute Path.

    Absolute paths pass through; relative paths resolve against
    PROJECT_ROOT (CWD-independence — Phase 5 decision).
    """
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def render_image(path: str | Path | None, label: str,
                 caption: str | None = None) -> None:
    """Render an image with placeholder fallback; never raises.

    A missing/empty reference is treated exactly like a missing file:
    shared placeholder first, inline notice last.
    """
    resolved = resolve_asset_path(path) if path else None
    if resolved is not None and resolved.is_file():
        st.image(str(resolved), width="stretch", caption=caption)
    elif PLACEHOLDER.is_file():
        st.image(str(PLACEHOLDER), width="stretch", caption=caption)
    else:
        st.info(tr("assets.image_fallback").format(label=label))


def render_audio(path: str | Path | None) -> None:
    """Render a native audio player with a listen hint; silent if absent.

    Change #12 (B1): one always-visible native player per instruction —
    no autoplay (unreliable on 1.62 beyond first mount), no session flags,
    nothing auto-starts (WCAG 2.2.2 inherent). Pause is native per player.
    The 48px touch-target floor is enforced by the `audio` CSS rule in
    styles/custom.css (native control measures 382x40 unpached).
    """
    resolved = resolve_asset_path(path) if path else None
    if resolved is None or not resolved.is_file():
        return  # narration is supplementary — text is authoritative
    st.caption(tr("assets.audio_hint"))
    st.audio(str(resolved), width="stretch")