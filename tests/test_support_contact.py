"""tests/test_support_contact.py — change #11-B v3: sandbox-safe footer.

Root cause record (v2 defect): st.iframe on 1.62 is sandboxed WITHOUT
allow-top-navigation — top-window navigation from a fragment throws
SecurityError. Parent DOM access IS allowed (the #9 scroll reset depends
on it). v3 assembles the mailto at load onto a real anchor; the click
navigates the iframe itself.

v3.1 test fixes (both failures were TEST defects — the shipped fragment
was correct; device QA passed):
  - the "window.top" ban initially matched the phrase inside an
    explanatory JS COMMENT; assertions now run against comment-stripped
    code, and the comment was reworded so the phrase appears nowhere;
  - the layout test initially asserted 'viewBox=' against the raw
    fragment, but the SVG is base64-encoded inside the data URI —
    attribute assertions now decode first.

Standing lesson (with the change-#6 '#'-CSS-comment incident): contract
tests over generated HTML/CSS must target CODE, not comments, and must
DECODE embedded media before asserting their attributes.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path
from urllib.parse import quote

from streamlit.testing.v1 import AppTest

from utils.contact import SUPPORT_EMAIL, SUPPORT_SUBJECT, build_support_fragment

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def _strip_block_comments(frag: str) -> str:
    return re.sub(r"/\*.*?\*/", "", frag, flags=re.DOTALL)


def _decoded_address_svg(frag: str) -> str:
    m = re.search(r'src="data:image/svg\+xml;base64,([^"]+)"', frag)
    assert m, "SVG data URI not found in fragment"
    return base64.b64decode(m.group(1)).decode("utf-8")


def test_fragment_hides_cleartext_address():
    frag = build_support_fragment()
    assert SUPPORT_EMAIL not in frag, (
        "the contiguous address must never appear in the fragment source")
    local, _, domain = SUPPORT_EMAIL.partition("@")
    assert f"{local}@{domain}" not in frag


def test_fragment_embeds_svg_image_data_uri():
    assert "data:image/svg+xml;base64," in build_support_fragment()


def test_fragment_assembles_mailto_at_load_not_via_top_window():
    frag = build_support_fragment()
    assert 'setAttribute("href", "mailto:"' in frag
    assert quote(SUPPORT_SUBJECT) in frag
    # Ban top/parent navigation references in CODE — comments stripped
    # (the v3.1 defect: the ban matched an explanatory comment).
    code = _strip_block_comments(frag)
    for banned in ("window.top", "window.parent",
                   "top.location", "parent.location"):
        assert banned not in code, f"banned navigation reference: {banned}"


def test_fragment_accessibility_and_touch_target():
    frag = build_support_fragment()
    assert "aria-label" in frag          # runtime label for screen readers
    assert "min-height: 48px" in frag    # touch-target floor (inline CSS)
    assert "font-size: 18px" in frag     # font floor (inline CSS)


def test_fragment_layout_fits_narrow_viewports():
    frag = build_support_fragment()
    # CSS-level responsiveness — cleartext in the fragment.
    assert "width: 100%" in frag
    assert "max-width" in frag
    assert "overflow: hidden" in frag
    # SVG-level responsiveness — the SVG is base64-encoded inside the
    # data URI, so decode BEFORE asserting (the v3.1 defect: 'viewBox='
    # was asserted against the raw fragment and always failed).
    svg = _decoded_address_svg(frag)
    assert 'viewBox="0 0 336 48"' in svg, "SVG must use viewBox (responsive)"
    assert not re.search(r"<svg\b[^>]*\swidth=", svg), (
        "SVG must not carry a fixed width attribute "
        "(v2 mobile-overflow defect form)")


def test_login_page_markdown_contains_no_cleartext_address():
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    joined = "\n".join(m.value for m in at.markdown)
    assert SUPPORT_EMAIL not in joined, (
        "cleartext address found in page markdown — the footer must be "
        "the iframe fragment")