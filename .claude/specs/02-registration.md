# Spec: Registration

## Overview
This feature implements the user registration system, allowing new users to create an account by providing their name, email, and password. It transitions the `/register` route from a static template to a functional form that validates input and persists user data to the database. This is a critical step in the roadmap as it enables personalization and secure data isolation for expense tracking.

## Depends on
- Step 1: Database Setup (Completed)

## Routes
- `GET /register` — Displays the registration form — Public
- `POST /register` — Processes registration data — Public

## Database changes
No database changes. The `users` table was already created in Step 1 with the following schema:
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `name` (TEXT, NOT NULL)
- `email` (TEXT, UNIQUE, NOT NULL)
- `password_hash` (TEXT, NOT NULL)
- `created_at` (TEXT, DEFAULT (datetime('now')))

## Templates
- **Modify:** `templates/register.html` — Add a form with fields for `name`, `email`, `password`, and `confirm_password`. Include error message display.

## Files to change
- `app.py` — Add POST handler for `/register`, implement validation logic, and call database insertion.
- `database/db.py` — No changes needed (uses existing `get_db`).

## Files to create
- None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only (`?` placeholders).
- Passwords hashed with `werkzeug.security.generate_password_hash`.
- Use CSS variables for styling.
- All templates extend `base.html`.
- Validate that:
  - All fields are filled.
  - Email is not already registered.
  - Password and Confirm Password match.
- On success: Redirect to `/login` with a success message.
- On failure: Re-render `/register` with specific error messages.

## Definition of done
- [ ] User can navigate to `/register`.
- [ ] Registration form contains fields: Name, Email, Password, Confirm Password.
- [ ] Submitting empty fields displays a "Missing data" error.
- [ ] Submitting mismatching passwords displays a "Passwords do not match" error.
- [ ] Submitting an email that already exists in the database displays an "Email already registered" error.
- [ ] Successful registration inserts a new row into the `users` table with a hashed password.
- [ ] Successful registration redirects the user to the `/login` page.
- [ ] Data persists across application restarts.
