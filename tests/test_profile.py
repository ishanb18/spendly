"""Tests for the /profile route (Step 4)."""

import pytest

from app import app as flask_app


@pytest.fixture
def client(db):
    """Flask test client; depends on `db` so DB_PATH is patched + seeded."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def login_as_demo(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"


def test_profile_logged_out_redirects_to_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_logged_in_returns_200(client):
    login_as_demo(client)
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"coming in Step 4" not in resp.data


def test_profile_shows_user_data(client):
    login_as_demo(client)
    html = client.get("/profile").data.decode()
    assert "Demo User" in html
    assert "demo@spendly.com" in html
    assert "Member since" in html


def test_profile_shows_spending_summary(client, db):
    login_as_demo(client)
    html = client.get("/profile").data.decode()
    total = db.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = 1"
    ).fetchone()[0]
    count = db.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = 1"
    ).fetchone()[0]
    assert "{:,.2f}".format(total) in html
    assert "₹" in html
    assert str(count) in html


def test_profile_shows_recent_transactions(client):
    login_as_demo(client)
    html = client.get("/profile").data.decode()
    assert "Recent Transactions" in html
    # A recent seeded expense description should appear in the table.
    assert "New running shoes" in html


def test_profile_shows_category_breakdown(client):
    login_as_demo(client)
    html = client.get("/profile").data.decode()
    assert "By Category" in html
    # Top Category stat card shows the highest-total category (Bills = 2200).
    assert "Bills" in html


def test_profile_never_exposes_password_hash(client, db):
    login_as_demo(client)
    html = client.get("/profile").data.decode()
    password_hash = db.execute(
        "SELECT password_hash FROM users WHERE id = 1"
    ).fetchone()[0]
    assert password_hash not in html
    assert "password_hash" not in html


def test_profile_missing_user_returns_404(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 9999
        sess["user_name"] = "Ghost"
    assert client.get("/profile").status_code == 404


def test_navbar_profile_link_only_when_logged_in(client):
    assert "/profile" not in client.get("/").data.decode()
    login_as_demo(client)
    assert "/profile" in client.get("/").data.decode()
