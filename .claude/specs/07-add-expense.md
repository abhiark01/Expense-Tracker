# Spec: Add Expense

## Overview
Step 7 introduces the ability for a logged‑in user to record a new expense.
The current `GET /expenses/add` route is a stub that returns a plain‑text
placeholder. This step turns it into a real route: `GET /expenses/add` renders
an input form and `POST /expenses/add` validates the submitted fields
(amount, category, date, description), inserts the row into the `expenses`
table, and redirects the user back to their profile page. The feature
completes the core CRUD cycle — create — and is required before the edit
(Step 8) and delete (Step 9) routes can be built.

## Depends on
- Step 1: Database setup (tables and `get_db()` exist)
- Step 2: Registration (users are stored in the database)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 4: Profile page static UI (the profile page exists and is the
  destination after a successful save)
- Step 5: Backend routes for profile page (the `expenses` table columns and
  `CATEGORIES` list are confirmed in `database/db.py`)

## Routes
- `GET /expenses/add` — Render the "Add Expense" form. **Logged‑in only**;
  unauthenticated visitors are redirected to `/login`.
- `POST /expenses/add` — Validate the submitted form fields, insert a new
  expense row for the current user, and redirect to `/profile` on success.
  **Logged‑in only**; unauthenticated visitors are redirected to `/login`.

## Database changes
No new tables or columns. The `expenses` table already has all required
columns (`user_id`, `amount`, `category`, `date`, `description`,
`created_at`). The route simply inserts a new row.

## Templates
- **Create:** `templates/add_expense.html`
  - Extends `base.html`.
  - A form posting to `url_for("add_expense")` with fields:
    - `amount` — number input, required, min 0.
    - `category` — `<select>` populated from the `CATEGORIES` list
      (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`,
      `Other`).
    - `date` — date input, required, defaulting to today.
    - `description` — text input, optional.
  - Shows a validation error message when one is passed in from the route.
- **Modify:** `templates/base.html` (or the navbar partial) — add a link to
  `url_for("add_expense")` in the logged‑in navigation so the form is
  reachable from every page.

## Files to change
- `app.py` — replace the `GET /expenses/add` stub with a full GET/POST route
  handler; add a `@login_required`‑style guard (check `session.get("user_id")`
  and redirect to `/login`).
- `templates/base.html` — add the "Add Expense" nav link for logged‑in users.

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string‑format values into SQL
- Foreign keys PRAGMA must be enabled on every connection (already done in
  `get_db()`)
- Passwords hashed with `werkzeug` (not applicable to this step, but the
  convention stands)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Currency must always display as ₹ — never £ or $
- The route must be logged‑in only — redirect unauthenticated requests to
  `/login` with a flash message
- Validate that `amount` is a positive number and that `category` is one of
  the allowed `CATEGORIES` values; reject invalid input by re‑rendering the
  form with an error message rather than crashing
- After a successful insert, redirect to `url_for("profile")` and flash a
  confirmation message
- The `date` field must default to today's date (`YYYY-MM-DD`)

## Definition of done
- [ ] `GET /expenses/add` while logged out redirects to `/login` (302)
- [ ] `GET /expenses/add` while logged in returns 200 and renders a form with
      amount, category, date, and description fields
- [ ] The category dropdown contains all 7 categories from `CATEGORIES`
- [ ] The date field defaults to today's date
- [ ] `POST /expenses/add` with valid data inserts a row into the `expenses`
      table for the current user and redirects to `/profile` (302)
- [ ] `POST /expenses/add` with an empty amount re‑renders the form with an
      error message (no crash, no insert)
- [ ] `POST /expenses/add` with an invalid category re‑renders the form with
      an error message (no crash, no insert)
- [ ] `POST /expenses/add` with a negative or zero amount re‑renders the form
      with an error message (no crash, no insert)
- [ ] `POST /expenses/add` while logged out redirects to `/login` (302)
- [ ] After a successful POST, the new expense appears on the `/profile`
      page (total spent and transaction count both increase)
- [ ] The new expense is reachable from the navbar on every logged‑in page