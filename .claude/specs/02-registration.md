# Spec: Registration

## Overview
Add a working user registration flow to Spendly. The `/register` route currently renders a static form; this step wires the form submission to the database: validate user input, hash the password with `werkzeug`, insert a new row into the `users` table, and log the new user in immediately. This is the entry point for the entire authenticated experience — every later feature (login, expenses, profile) requires a registered user.

## Depends on
- Step 1 — Database setup (users table with `name`, `email`, `password_hash`, `created_at`)

## Routes
- `GET /register` — render the existing `register.html` form (already wired in `app.py`)
- `POST /register` — validate input, create user, log them in, redirect to dashboard (public)

## Database changes
No database changes. The `users` table from Step 1 already has every column needed (`name`, `email`, `password_hash`, `created_at`) and the `email` UNIQUE constraint is what we rely on for duplicate detection.

## Templates
- **Create:** none
- **Modify:** none (the existing `templates/register.html` already posts to `/register` and renders an `error` block — reuse as-is)

## Files to change
- `app.py` — convert `register()` from a GET-only stub to handle both GET (render form) and POST (create user + login + redirect). Add `session` imports.

## Files to create
- `database/__init__.py` already exists; no new files.

## New dependencies
No new dependencies. `werkzeug.security` (`generate_password_hash`) and Flask's built-in `session` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use `%` or `f""` string formatting in SQL
- Hash passwords with `from werkzeug.security import generate_password_hash`
- Set `app.secret_key` in `app.py` (use a fixed dev value, e.g. `"dev-secret-change-me"`, with a comment noting it must be replaced for production)
- Use `flash()` from Flask for success/error messages that survive the redirect
- Use CSS variables — never hardcode hex values in any new styles
- All templates extend `base.html` (the existing `register.html` already does)
- Email is normalised to lowercase + stripped before validation/insert
- After successful insert, set `session["user_id"]` and `session["user_name"]` so the user is logged in immediately (Login is Step 3 — registration is the first place we set the session)
- On duplicate email, re-render the form with the user-typed values preserved (`name`, `email`) but not `password`
- After successful registration, redirect to `/` (landing) — a real dashboard is a later step

### Validation rules
- `name`: required, trimmed, 2–80 chars
- `email`: required, must match a basic email regex, lowercased before insert
- `password`: required, minimum 8 characters

### Error handling
- Validation failure → re-render `register.html` with `error` set and form values preserved (except password)
- Duplicate email (`sqlite3.IntegrityError`) → re-render with a friendly "An account with that email already exists." message
- Any other DB error → re-render with a generic error; do not leak internal details

## Definition of done
- [ ] `GET /register` renders the existing form
- [ ] Submitting an empty form re-renders with validation errors
- [ ] Submitting a name shorter than 2 chars or longer than 80 chars shows an error
- [ ] Submitting an invalid email format shows an error
- [ ] Submitting a password shorter than 8 chars shows an error
- [ ] Submitting valid data creates a row in `users` with a hashed password (verify via `sqlite3` query)
- [ ] Submitting a duplicate email shows a friendly error and does NOT create a row
- [ ] After successful registration, the user is redirected (302) to `/`
- [ ] After successful registration, `session["user_id"]` and `session["user_name"]` are set
- [ ] The new user's password is NOT stored in plain text (verify by inspecting the `password_hash` column)
- [ ] App starts without errors and no unhandled exceptions are logged
- [ ] No new pip packages required
