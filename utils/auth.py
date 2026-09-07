"""Password hashing, session restore, and logout (Steps 2a + 2b) — stdlib only.

Password hashing (2a): PBKDF2-HMAC-SHA256, 600,000 iterations (OWASP 2023
for SHA-256), 16-byte random salt per password. Stored self-describing:

    pbkdf2$sha256$600000$<salt-hex>$<hash-hex>

Verification is constant-time (hmac.compare_digest); a malformed stored
hash yields False. Policy: NIST SP 800-63B — min 8, no composition rules.

Remember-me (2b, mechanism (a) — prototype-driven): the session token
rides the URL as ?t=<token> (st.query_params) — the ONLY Python-readable
client-side persistence channel on 1.62. Prototype findings: iframe
fragments CAN write parent localStorage (P1) and rewrite the parent URL
via history.replaceState (P2), but CANNOT force a parent rerun (P3) —
and parent location.reload() is sandbox-blocked (navigation class, no
allow-top-navigation). A localStorage token can therefore never reach
Python at boot; the query-param design needs no iframe at all.

app.py calls try_restore_session() before routing. Logout is the single
path clear_session_state() — it deletes the DB token row and removes the
?t= param before wiping state.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

import streamlit as st

from db import queries

PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 64

TOKEN_PARAM = "t"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 salt, PBKDF2_ITERATIONS)
    return (f"pbkdf2$sha256${PBKDF2_ITERATIONS}$"
            f"{salt.hex()}${digest.hex()}")


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, algo, iterations, salt_hex, hash_hex = stored.split("$")
        if scheme != "pbkdf2" or algo != "sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                     bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def try_restore_session() -> bool:
    """Boot-time restore from the ?t= session token (app.py main()).

    Valid, unexpired token -> restore auth state and return True.
    Absent -> False. Present-but-dead -> remove the stale param (tidy
    URL) and return False. Called ONLY when unauthenticated.
    """
    token = st.query_params.get(TOKEN_PARAM)
    if not token:
        return False
    user = queries.get_session_user(token)
    if user is None:
        try:
            del st.query_params[TOKEN_PARAM]
        except Exception:
            pass  # URL cleanup must never break a render
        return False
    st.session_state.update(authenticated=True, user_email=user["email"],
                            user=user, current_state="CHECK_ONBOARDING")
    return True


def clear_session_state() -> None:
    """Logout: delete the DB session token, remove ?t=, reset auth state
    to the app.py boot defaults, and drop all flow-scoped keys (STATE.md
    logout rule). Single logout path — no view clears auth keys directly."""
    token = st.query_params.get(TOKEN_PARAM)
    if token:
        try:
            queries.delete_session_token(token)
        except Exception:
            pass  # token deletion must never block logout
    if TOKEN_PARAM in st.query_params:
        try:
            del st.query_params[TOKEN_PARAM]
        except Exception:
            pass
    st.session_state.update(authenticated=False, user_email=None, user=None,
                            current_state="UNAUTHENTICATED", session_flags={})
    for key in ("breathing_started", "regression_ack", "onboarding_step",
                "onboarding_data", "prev_fingerprint"):
        st.session_state.pop(key, None)