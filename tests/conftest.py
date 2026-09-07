"""Pytest bootstrap: sys.path, DATABASE_URL resolution + safety guard,
autouse per-test truncation.

Strategy A (Phase 6 Step 1): ONE shared Postgres for the whole suite —
locally the docker-compose service; per-test isolation via TRUNCATE
(replacing the old per-test SQLite files). conftest is imported before
any test module, so setting DATABASE_URL here guarantees the app under
AppTest connects to the same test database.

SAFETY GUARD: reset_database() TRUNCATES every table. This module
refuses to let the suite run against a non-local database host (e.g. a
Neon URL left in DATABASE_URL) unless TEST_DB_CONFIRM_REMOTE=1 is set
deliberately.
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LOCAL_TEST_URL = "postgresql://elderly:elderly_dev@localhost:5432/elderly_test"
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")

# Default to the local docker-compose Postgres; an explicit DATABASE_URL
# always wins.
os.environ.setdefault("DATABASE_URL", LOCAL_TEST_URL)

_host = urlparse(os.environ["DATABASE_URL"]).hostname or ""
if (_host not in _LOCAL_HOSTS
        and os.environ.get("TEST_DB_CONFIRM_REMOTE") != "1"):
    raise RuntimeError(
        f"Refusing to run tests against non-local database host {_host!r} "
        f"— the suite TRUNCATES all tables. Use the local docker-compose "
        f"Postgres (unset DATABASE_URL, or set it to {LOCAL_TEST_URL!r}), "
        f"or set TEST_DB_CONFIRM_REMOTE=1 to override deliberately."
    )


@pytest.fixture(autouse=True)
def _reset_test_database():
    """Every test starts on a truncated database — strategy-A isolation.

    Runs for every test (any test may boot the app, which writes through
    the shared connection layer); adds a few seconds across the suite.
    """
    import psycopg
    from db.testing import reset_database
    try:
        reset_database()
    except psycopg.OperationalError as e:
        raise RuntimeError(
            f"Cannot reach the test Postgres ({os.environ['DATABASE_URL']}). "
            f"Start it: docker compose up -d  (original error: {e})"
        ) from e
    yield