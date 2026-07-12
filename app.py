import re
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)

# Required for session + flash. DEV ONLY — replace via env var in production.
app.secret_key = "dev-secret-change-me"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Initialize and seed the database before any route can be hit.
# Module-level so it runs for `python app.py`, `flask run`, and WSGI runners.
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # If user is already logged in, redirect to landing page.
    if session.get("user_id"):
        return redirect(url_for("landing"))

    # GET: render the form, restoring any one-shot prefill from a prior POST.
    if request.method == "GET":
        prefill = session.pop("register_form", None) or {}
        return render_template(
            "register.html",
            name=prefill.get("name", ""),
            email=prefill.get("email", ""),
        )

    # POST: validate → insert → login.
    name = (request.form.get("name") or "").strip()
    email_raw = (request.form.get("email") or "").strip()
    email = email_raw.lower()
    password = request.form.get("password") or ""

    def fail(message):
        # Preserve the user's typed values across the redirect; never prefill password.
        session["register_form"] = {"name": name, "email": email_raw}
        flash(message, "error")
        return redirect(url_for("register"))

    # Validation
    if len(name) < 2 or len(name) > 80:
        return fail("Name must be between 2 and 80 characters.")
    if not EMAIL_RE.match(email):
        return fail("Please enter a valid email address.")
    if len(password) < 8:
        return fail("Password must be at least 8 characters.")

    # Insert
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return fail("An account with that email already exists.")
    except sqlite3.DatabaseError:
        conn.close()
        return fail("Something went wrong. Please try again.")
    else:
        conn.close()

    # Log the user in immediately.
    session.clear()  # wipes register_form and any stale session data
    session["user_id"] = user_id
    session["user_name"] = name
    return redirect(url_for("landing"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect to landing page.
    if session.get("user_id"):
        return redirect(url_for("landing"))

    # GET: render the form, restoring any one‑shot prefill from a prior POST.
    if request.method == "GET":
        prefill = session.pop("login_form", None) or {}
        return render_template(
            "login.html",
            email=prefill.get("email", ""),
        )

    # POST: look up user, verify password, set session.
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    def fail(message):
        # Preserve the user's typed email across the redirect; never prefill password.
        session["login_form"] = {"email": email}
        flash(message, "error")
        return redirect(url_for("login"))

    if not email or not password:
        return fail("Email and password are required.")

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    except sqlite3.DatabaseError:
        conn.close()
        return fail("Something went wrong. Please try again.")
    else:
        conn.close()

    # Constant‑time check – always run check_password_hash, even when the user is missing.
    password_hash = row["password_hash"] if row else generate_password_hash("")
    if row is None or not check_password_hash(password_hash, password):
        return fail("Invalid email or password.")

    # Log the user in.
    session.clear()
    session["user_id"] = row["id"]
    session["user_name"] = row["name"]
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
