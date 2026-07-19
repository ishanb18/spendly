# Spec: Profile Page Design

## Overview
The profile page gives a logged-in user a personal home inside Spendly where they can see their account details (name, email, join date) and a summary of their spending activity. It is the first authenticated, data-backed page in the roadmap and establishes the pattern for login-guarded routes that read user-scoped data from SQLite. It exists at Step 4 because login/logout (Step 3) is now complete, so we finally have a real session to build authenticated pages on top of before expense CRUD arrives in Steps 7–9.

## Depends on
- Step 1 — Database Setup (`get_db`, `init_db`, `seed_db`, `users` + `expenses` tables)
- Step 2 — Registration (creates users, sets `session["user_id"]` / `session["user_name"]`)
- Step 3 — Login and Logout (session lifecycle, navbar auth state)

## Routes
- `GET /profile` — render the authenticated profile page for the currently logged-in user; if no valid session, redirect to `/login`. Access level: logged-in.

No other new routes. The existing `/profile` stub (`return "Profile page — coming in Step 4"`) is replaced.

## Database changes
No schema changes. All required columns already exist:
- `users`: `id`, `name`, `email`, `created_at`
- `expenses`: `user_id`, `amount`, `category` (used only for read-only summary counts/totals)

Add read-only helper(s) in `database/db.py` for user-scoped lookups (see Rules). No new tables, columns, or constraints.

## Templates
- **Create:** `templates/profile.html` — extends `base.html`; shows account card (name, email, member-since date) and a small spending summary (total spent, number of expenses). Amounts shown in ₹ (INR).
- **Modify:** `templates/base.html` — add a "Profile" nav link (using `url_for('profile')`) inside the logged-in branch of `.nav-links`, next to the greeting/sign-out.

## Files to change
- `app.py` — implement the `/profile` route: login guard, fetch user + summary via `database/db.py` helpers, render `profile.html`.
- `database/db.py` — add parameterized read-only helper(s): fetch user by id, and fetch expense summary (count + total) for a user id.
- `templates/base.html` — add Profile nav link for logged-in users.
- `CLAUDE.md` — flip `GET /profile` from Stub to Implemented in the route table.

## Files to create
- `templates/profile.html`
- `static/css/profile.css` — page-specific styles for the profile layout (linked via the `head` block in `profile.html`).
- `tests/test_profile.py` — tests for the route (see Definition of done).

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only (`?` placeholders) — never f-strings in SQL.
- Passwords hashed with werkzeug (N/A here — no password handling on this page, but never expose `password_hash`).
- Use CSS variables from `style.css` — never hardcode hex values; put page-specific styles in `static/css/profile.css`, not inline `<style>`.
- All templates extend `base.html`.
- DB logic lives in `database/db.py` — no inline SQL in the route function.
- Login guard: `if not session.get("user_id"): return redirect(url_for("login"))`.
- Use `url_for()` for every internal link — no hardcoded paths.
- Use `abort()` for HTTP errors (e.g. `abort(404)` if the session user id no longer exists in the DB).
- Currency is INR (₹), consistent with the rest of Spendly — never `$`.
- App runs on port 5001.

## Definition of done
- Visiting `/profile` while logged out redirects to `/login`.
- Visiting `/profile` while logged in renders `profile.html` (HTTP 200), not the old stub string.
- The page displays the logged-in user's real `name`, `email`, and member-since date from the DB.
- The page shows a spending summary: total amount spent (formatted with ₹) and the count of expenses for that user.
- `password_hash` never appears in the rendered HTML.
- A "Profile" link appears in the navbar only when logged in and routes to `/profile` via `url_for`.
- No inline `<style>` tags; profile styles live in `static/css/profile.css` using existing CSS variables.
- `pytest tests/test_profile.py` passes: logged-out redirect, logged-in 200, and correct user data rendered.
