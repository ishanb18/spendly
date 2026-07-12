# Spec: Login and Logout

## Overview
Add a working authentication boundary to Spendly. The `/login` route currently renders a static form; this step wires the form submission to authenticate a user against the `users` table using `werkzeug`'s password verification, set the same session keys that registration already sets (`user_id`, `user_name`), and redirect to a sensible landing target. The `/logout` route, currently a GET placeholder returning text, is replaced with a POST endpoint that clears the session and redirects to the landing page. The navbar in `base.html` is updated so logged-in users see their name and a sign-out control, and logged-out users see "Sign in / Get started" as today. Together with Step 2, this turns Spendly from a static site into a stateful app with a real auth boundary.

## Depends on
- Step 1 — Database setup (`users` table with `password_hash` column)
- Step 2 — Registration (sets the `user_id` / `user_name` session convention; without it, login has no shape to follow)

## Routes
- `GET /login` — render the existing `login.html` form (currently a stub in `app.py`)
- `POST /login` — verify credentials, set session, redirect (public)
- `POST /logout` — clear session, redirect to landing (logged-in only)
- `GET /logout` — **explicitly disallowed**: return 405 Method Not Allowed. Avoids CSRF via `<img src="/logout">` and link previews. Use a `<form method="POST">` button in the navbar instead.

## Database changes
No database changes. The `users` table from Step 1 is sufficient — login reads `id`, `name`, `email`, `password_hash` via a parameterised SELECT and verifies the password with `werkzeug.security.check_password_hash`.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — replace the `{% if error %}` block with a `get_flashed_messages(with_categories=true)` loop (matching the pattern from `templates/register.html`); add `value="{{ email|default('', true) }}"` to the email input for prefill on error. Password is never pre-filled.
  - `templates/base.html` — in the `.nav-links` div, branch on `session.user_id`: when logged in, show the user's name (e.g. `Hi, {{ session.user_name }}`) and a `<form method="POST" action="/logout" class="nav-logout-form"><button type="submit" class="nav-logout">Sign out</button></form>`. When logged out, show the existing "Sign in" link and "Get started" CTA. The form must POST (not be a link) so `GET /logout` is never the auth path.

## Files to change
- `app.py` — convert `login()` from a GET-only stub to a GET/POST handler that calls `check_password_hash`. Replace `logout()` with a POST-only handler that calls `session.clear()` and redirects. Add `check_password_hash` to the werkzeug import.
- `templates/login.html` — see above.
- `templates/base.html` — see above.
- `static/css/style.css` — add a small block of styles for the new `.nav-logout-form` (inline form, no bullet margin) and `.nav-logout` (button styled to match the existing `.nav-cta` look but as a subtle text/ghost button). All colors must reference existing CSS variables (e.g. `--ink`, `--ink-soft`, `--border`); no hardcoded hex values.

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is already available; we already use `generate_password_hash` in Step 2.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never use `%` or `f""` string formatting in SQL
- Hash passwords with `werkzeug.security.generate_password_hash` (registration) and verify with `werkzeug.security.check_password_hash` (login). Never compare hashes with `==`.
- Use `flash()` for error messages, with the same pattern as Step 2: store one-shot form prefill in a session key (`session["login_form"] = {"email": ...}`) on failure, pop it on the next GET
- Use CSS variables — never hardcode hex values in any new styles
- All templates extend `base.html` (the existing `login.html` already does)
- Email is normalised to lowercase + stripped before lookup, mirroring registration
- Generic error message on bad credentials: "Invalid email or password." — do NOT disclose whether the email exists (no enumeration leak)
- Constant-time comparison: rely on `check_password_hash` (which is constant-time). Do not pre-check user existence with a separate query and then short-circuit.
- After successful login, set `session["user_id"]` and `session["user_name"]`, then redirect. Do NOT carry forward any pre-existing session data.
- Logout must be POST only. The `GET /logout` route must return 405 (or be removed from the routing table; Flask returns 405 automatically if you register only the POST method).
- For the navbar form: use `request.method == "POST"` and `request.form` (Flask handles CSRF tokens via `flask_wtf` in a later step; for now, the POST-only design is the primary defense).
- Login redirect target: `/` (landing) — matches what registration does. A real `/dashboard` is a later step.

### Validation rules
- `email`: required, trimmed, lowercased before lookup. No format check at the form layer — if the user typed something we can't find, the "Invalid email or password" message is sufficient (also avoids leaking which emails exist via format rejection).
- `password`: required, non-empty. We do not re-validate length on login.

### Error handling
- Validation failure (empty fields) → re-render `login.html` with a clear error and the email prefilled
- User not found OR wrong password → SAME error message: "Invalid email or password." (no enumeration)
- Any other DB error → re-render with a generic error; do not leak internal details

## Definition of done
- [ ] `GET /login` renders the existing form
- [ ] Submitting empty form re-renders with a "Email and password are required." style error
- [ ] Submitting a non-existent email shows "Invalid email or password." (no enumeration)
- [ ] Submitting a valid email with a wrong password shows the same "Invalid email or password." message
- [ ] Submitting valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects (302) to `/`
- [ ] After login, `GET /` reflects the logged-in state in the navbar (user name + sign-out button)
- [ ] The email input is pre-filled on validation error; the password input is never pre-filled
- [ ] `GET /logout` returns 405 Method Not Allowed
- [ ] `POST /logout` clears the session (verify `session` is empty in the test client) and redirects to `/`
- [ ] After logout, the navbar returns to the logged-out state ("Sign in" / "Get started")
- [ ] After logout, attempting to access any logged-in route (future ones) returns the user to login
- [ ] App starts without errors and no unhandled exceptions are logged
- [ ] No new pip packages required
- [ ] No hardcoded hex values in new CSS — all colors come from existing CSS variables
