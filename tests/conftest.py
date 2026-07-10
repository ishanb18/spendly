"""Pytest fixtures for the Spendly test suite.

Each test runs against an isolated SQLite file under tmp_path, so the real
``spendly.db`` in the project root is never touched.
"""

import os
import sys

import pytest

# Make the project root importable when pytest is run from any directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import db as db_module  # noqa: E402


@pytest.fixture
def db(monkeypatch, tmp_path):
    """Yield a connection to a freshly-initialized test database.

    - Redirects ``db.DB_PATH`` to a unique tmp_path file.
    - Runs ``init_db()`` then ``seed_db()`` so each test starts with a
      known-good demo dataset.
    - Closes the connection on teardown; tmp_path auto-cleans the file.
    """
    test_db_path = tmp_path / "test_spendly.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(test_db_path))

    db_module.init_db()
    db_module.seed_db()

    conn = db_module.get_db()
    try:
        yield conn
    finally:
        conn.close()
