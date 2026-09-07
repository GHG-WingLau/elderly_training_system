"""tests/test_auth.py — Steps 2a/2b: password hashing, consent recording,
session tokens.

Boot-restore (try_restore_session) is NOT AppTest-driven: AppTest
query-param support on 1.62 is unverified, and after the 2a.1
mime_type lesson we do not guess API surface. Coverage instead:
get_session_user round-trip/expiry (below) + login/logout E2E
(test_e2e_onboarding.py) + the manual QA reload check (which is
literally the user-reported symptom: reload lands on the hub)."""
from datetime import datetime, timezone

from utils.auth import (MIN_PASSWORD_LENGTH, TOKEN_PARAM, hash_password,
                        verify_password)
from db import queries
from db.database import get_connection


def _seed_user(email="auth@t.test"):
    queries.create_user(email=email, username="tester", age=65, sex="F",
                        password_hash=hash_password("secret-pass-1"))


def test_password_roundtrip():
    stored = hash_password("correct horse")
    assert verify_password("correct horse", stored) is True


def test_wrong_password_rejected():
    stored = hash_password("correct horse")
    assert verify_password("wrong horse", stored) is False


def test_hashes_are_salted():
    a = hash_password("same password")
    b = hash_password("same password")
    assert a != b
    assert verify_password("same password", a)
    assert verify_password("same password", b)


def test_stored_format_is_self_describing():
    stored = hash_password("x" * MIN_PASSWORD_LENGTH)
    parts = stored.split("$")
    assert parts[0] == "pbkdf2" and parts[1] == "sha256"
    assert int(parts[2]) >= 100_000  # iteration floor


def test_malformed_stored_hash_returns_false():
    assert verify_password("whatever", "not-a-valid-hash") is False
    assert verify_password("whatever", "") is False


def test_create_user_records_consent():
    queries.create_user(
        email="consent@t.test", username="tester", age=70, sex="F",
        password_hash=hash_password("abcdefgh"),
        consent_version="v1.1",
        consent_accepted_at=datetime.now(timezone.utc))
    user = queries.get_user("consent@t.test")
    assert user["consent_version"] == "v1.1"
    assert user["consent_accepted_at"] is not None


def test_session_token_roundtrip():
    _seed_user()
    token = queries.create_session_token("auth@t.test", days=30)
    assert queries.get_session_user(token)["email"] == "auth@t.test"


def test_session_token_delete():
    _seed_user()
    token = queries.create_session_token("auth@t.test")
    queries.delete_session_token(token)
    assert queries.get_session_user(token) is None


def test_expired_token_rejected():
    _seed_user()
    token = queries.create_session_token("auth@t.test", days=30)
    conn = get_connection()
    conn.execute("UPDATE sessions SET expires_at = now() - interval '1 hour' "
                 "WHERE token = %s", (token,))
    conn.commit()
    assert queries.get_session_user(token) is None


def test_create_session_token_purges_expired():
    _seed_user()
    stale = queries.create_session_token("auth@t.test")
    conn = get_connection()
    conn.execute("UPDATE sessions SET expires_at = now() - interval '1 day' "
                 "WHERE token = %s", (stale,))
    conn.commit()
    fresh = queries.create_session_token("auth@t.test")
    n = get_connection().execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE token = %s",
        (stale,)).fetchone()["n"]
    assert n == 0
    assert queries.get_session_user(fresh)["email"] == "auth@t.test"


def test_multiple_session_tokens_both_valid():
    """Two devices / two logins: both tokens remain valid (logout deletes
    only the current one)."""
    _seed_user()
    t1 = queries.create_session_token("auth@t.test")
    t2 = queries.create_session_token("auth@t.test")
    queries.delete_session_token(t1)
    assert queries.get_session_user(t1) is None
    assert queries.get_session_user(t2)["email"] == "auth@t.test"


def test_token_param_constant_is_stable():
    """The remember-me URL parameter name is a contract between app.py,
    auth_view, and clear_session_state — pin it."""
    assert TOKEN_PARAM == "t"