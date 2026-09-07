"""Support contact footer (change #11-B, v3: sandbox-safe + mobile fit).

v3 fixes two v2 defects found in QA:
  - NAVIGATION: st.iframe is sandboxed WITHOUT allow-top-navigation on
    1.62 (parent DOM access IS allowed — the #9 scroll reset relies on
    it — but top-window navigation throws SecurityError). Fix: the
    script assembles the mailto URL AT LOAD onto a real anchor; the
    user's click navigates the IFRAME ITSELF (self-navigation is always
    permitted), launching the mail handler. No click handler, no
    top-window access. Long-press on the anchor offers "copy link" on
    mobile.
  - LAYOUT: v2's fixed-width 360px SVG overflowed phone viewports and
    the long lead line wrapped; fix: short lead, responsive SVG
    (viewBox + width:100%/max-width), height recomputed, overflow:hidden.

v3.1 (test alignment, no functional change): the JS comment below the
assembly was reworded — it previously contained the literal phrase
"window.top", which tripped the test banning that reference. Comments
are not contract surface; tests now strip comments (see
tests/test_support_contact.py).

Anti-harvest scheme unchanged in substance: the SERVED fragment contains
only dot-split parts (neither the local part nor the domain contiguous);
the assembled address exists only in the runtime DOM (accepted residual
risk: script-executing harvesters). The address image is a base64 SVG
data-URI (WCAG 1.4.5 deviation recorded with rationale); runtime
aria-label carries the assembled address for screen readers.
"""
from __future__ import annotations

import base64
from urllib.parse import quote

import streamlit as st

SUPPORT_EMAIL = "Sheepandfish.fit@gmail.com"
SUPPORT_SUBJECT = "Enquiry and Comment"

# 12px padding + ~22px lead line + 48px anchor + 1px border + slack.
_FOOTER_HEIGHT = 110


def _address_image_data_uri(address: str) -> str:
    """Render the address as an opaque base64 SVG image (responsive)."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 336 48">'
        '<text x="50%" y="55%" text-anchor="middle" '
        'dominant-baseline="middle" font-family="Arial, Helvetica, '
        'sans-serif" font-size="18" fill="#333333" '
        f'text-decoration="underline">{address}</text></svg>'
    )
    return ("data:image/svg+xml;base64,"
            + base64.b64encode(svg.encode("utf-8")).decode("ascii"))


def build_support_fragment() -> str:
    """Pure builder for the st.iframe footer fragment (no Streamlit)."""
    local, _, domain = SUPPORT_EMAIL.partition("@")
    # Dots re-joined at runtime — neither the local part nor the domain
    # appears contiguously in the fragment source.
    u_js = '["' + '","'.join(local.split(".")) + '"].join(".")'
    d_js = '["' + '","'.join(domain.split(".")) + '"].join(".")'
    return f"""
<style>
  html, body {{ margin: 0; padding: 0; overflow: hidden; }}
  .footer {{
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 Helvetica, Arial, sans-serif;
    font-size: 18px;
    color: #333333;
    padding-top: 12px;
    border-top: 1px solid rgba(128, 128, 128, 0.4);
  }}
  a.mail {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;
    max-width: 100%;
    padding: 0 8px;
    cursor: pointer;
  }}
  a.mail img {{ display: block; width: 100%; max-width: 336px; height: auto; }}
</style>
<div class="footer">
  Need help? Email us at<br>
  <a class="mail" href="#" aria-label="Email the training team"
     title="Email the training team">
    <img alt="Email address of the support team"
         src="{_address_image_data_uri(SUPPORT_EMAIL)}">
  </a>
</div>
<script>
(function () {{
  var user = {u_js};       // parts joined at runtime
  var domain = {d_js};     // parts joined at runtime
  var addr = user + "@" + domain;
  var a = document.querySelector("a.mail");
  a.setAttribute("aria-label", "Email us at " + addr);
  /* Self-navigation only: the sandbox permits a frame to navigate
     ITSELF; top-window navigation is blocked (the sandbox has no
     allow-top-navigation flag on 1.62). A real anchor click navigates
     this iframe to the mailto: handler. */
  a.setAttribute("href", "mailto:" + addr +
                 "?subject={quote(SUPPORT_SUBJECT)}");
}})();
</script>
"""


def render_support_footer() -> None:
    st.iframe(build_support_fragment(), height=_FOOTER_HEIGHT)