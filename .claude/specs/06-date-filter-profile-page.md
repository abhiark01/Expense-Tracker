---
# Spec: Date Filter for Profile Page

## Overview
Add a date range filter to the profile page, allowing users to view their transactions and spending statistics for a selected period. This enhances the user experience by enabling focused financial analysis without navigating away from the profile dashboard.

## Depends on
- Step 04: Profile page UI implementation (templates/profile.html, profile route in app.py) must be complete.
- Step 05: Backend routes for profile page (GET /profile) must be implemented and functional.

## Routes
- `GET /profile` — Updated to accept optional query parameters `start_date` and `end_date` to filter displayed transactions and statistics. Access level: logged-in users only.

## Database changes
No database changes required. Filtering will be performed via SQL `WHERE date BETWEEN ? AND ?` using existing `transactions` table.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date range input form (start and end date) that submits via GET to the same `/profile` route.
  - Display currently selected date range above the transaction table.

## Files to change
- `app.py` – Update the profile route to parse `start_date` and `end_date` query parameters, validate them, and adjust the SQL query accordingly.
- `templates/profile.html` – Add the date filter form and display logic.
- `static/css/profile.css` – Add styles for the new filter form, using CSS variables for colors.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Use parameterised SQLite queries with `?` placeholders.
- Passwords hashed with werkzeug (not relevant for this feature).
- Use CSS variables — never hardcode hex values.
- All templates must extend `base.html`.

## Definition of done
- [ ] The profile page displays a date range filter form with start and end date inputs.
- [ ] Submitting the form reloads the page, showing only transactions whose `date` falls within the selected range.
- [ ] Statistics (total spent, transaction count, average transaction, month spending) reflect the filtered data.
- [ ] Invalid or missing dates default to showing all transactions.
- [ ] No new templates are added; only `profile.html` is modified.
- [ ] All new code follows PEP8, uses parameterised queries, and passes existing unit tests.
---