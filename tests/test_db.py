"""Tests for database/db.py — covers the Step 1 Definition of Done."""

import sqlite3

import pytest
from werkzeug.security import check_password_hash


def test_init_db_creates_both_tables(db):
    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "ORDER BY name"
    ).fetchall()
    names = {row["name"] for row in rows}
    assert "users" in names
    assert "expenses" in names


def test_seed_db_inserts_demo_user_with_hashed_password(db):
    users = db.execute("SELECT * FROM users").fetchall()
    assert len(users) == 1

    user = users[0]
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    # Password must be hashed, not stored in plaintext.
    assert user["password_hash"] != "demo123"
    # Hashed value must verify the original password.
    assert check_password_hash(user["password_hash"], "demo123") is True


def test_seed_db_inserts_eight_expenses(db):
    expenses = db.execute("SELECT * FROM expenses").fetchall()
    assert len(expenses) == 8

    categories = {row["category"] for row in expenses}
    expected = {
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    }
    assert expected.issubset(categories)

    # Every expense is linked to the demo user.
    user_ids = {row["user_id"] for row in expenses}
    assert user_ids == {1}


def test_seed_db_is_idempotent(db):
    from database import db as db_module

    db_module.seed_db()  # second call should be a no-op

    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    expense_count = db.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    assert user_count == 1
    assert expense_count == 8


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date) "
            "VALUES (?, ?, ?, ?)",
            (9999, 1.0, "Food", "2026-07-10"),
        )
