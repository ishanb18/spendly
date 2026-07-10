"""SQLite helpers for Spendly: get_db(), init_db(), seed_db()."""

import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

# Project root = parent of the database/ package. spendly.db lives in the root
# so the file is easy to find and easy to .gitignore.
DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "spendly.db"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def get_db():
    """Return a SQLite connection with Row factory + foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # PRAGMA foreign_keys is per-connection in SQLite; must be set every time.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create both tables if they don't exist. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert one demo user + 8 sample expenses, but only on first run.

    Guard: if the users table already has any row, do nothing. This makes the
    function safe to call on every app startup.
    """
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        # Demo user. demo123 is hashed via werkzeug's PBKDF2-based helper.
        user_cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        demo_user_id = user_cursor.lastrowid

        # 8 sample expenses covering all 7 categories (Food appears twice).
        # Dates are spread across the current month in YYYY-MM-DD format.
        today = date.today()
        year, month = today.year, today.month

        sample_expenses = [
            (450.0, "Food", f"{year:04d}-{month:02d}-02", "Lunch at office canteen"),
            (820.0, "Food", f"{year:04d}-{month:02d}-09", "Groceries from supermarket"),
            (150.0, "Transport", f"{year:04d}-{month:02d}-03", "Uber to airport"),
            (2200.0, "Bills", f"{year:04d}-{month:02d}-05", "Electricity bill"),
            (650.0, "Health", f"{year:04d}-{month:02d}-08", "Pharmacy and checkup"),
            (499.0, "Entertainment", f"{year:04d}-{month:02d}-11", "Movie tickets"),
            (1800.0, "Shopping", f"{year:04d}-{month:02d}-14", "New running shoes"),
            (320.0, "Other", f"{year:04d}-{month:02d}-17", "Gift for friend"),
        ]
        conn.executemany(
            "INSERT INTO expenses "
            "(user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [(demo_user_id, *row) for row in sample_expenses],
        )

        conn.commit()
    finally:
        conn.close()
