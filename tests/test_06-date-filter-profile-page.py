"""
Tests for the date filter feature on the Spendly profile page.

These tests verify that:
- Unauthenticated users are redirected from /profile.
- Without date filters, all expenses are shown.
- A valid date range limits the displayed transactions and updates statistics.
- Invalid date formats fall back to showing all expenses.
- A start date after an end date falls back to showing all expenses.
- Category breakdown and summary cards also reflect the filtered data.
"""

import pytest
from datetime import date

from app import app as flask_app
from database.db import get_db, init_db, seed_db


@pytest.fixture
def app():
    """Create a fresh Flask app with an in‑memory SQLite DB."""
    flask_app.config.update(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with flask_app.app_context():
        init_db()
        seed_db()
        yield flask_app


@pytest.fixture
def client(app):
    """Test client without pre‑logged‑in session."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A client logged in as the seeded demo user."""
    with client.session_transaction() as session:
        session["user_id"] = 1
    return client


def _add_expense(user_id: int, amount: float, category: str, expense_date: str, description: str):
    """Insert a single expense for a given user_id."""
    db = get_db()
    db.execute(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, category, expense_date, description),
    )
    db.commit()
    db.close()


def _clear_expenses(user_id: int):
    """Remove all expenses for a given user_id."""
    db = get_db()
    db.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()


# ----------------------------------------------------------------------
# Authentication guard tests
# ----------------------------------------------------------------------


def test_profile_requires_auth_redirect(client):
    """Unauthenticated request to /profile must redirect to login."""
    resp = client.get("/profile")
    assert resp.status_code == 302, "Expected a redirect for unauthenticated access"
    assert "/login" in resp.headers["Location"] or resp.headers["Location"].endswith("/login")


# ----------------------------------------------------------------------
# Default (no filter) tests
# ----------------------------------------------------------------------


def test_profile_no_filter_shows_all_expenses(auth_client):
    """When no date parameters are supplied, all of the user's expenses are displayed."""
    _clear_expenses(1)
    _add_expense(1, 10.0, "Food", "2023-01-10", "Expense A")
    _add_expense(1, 20.0, "Transport", "2023-01-15", "Expense B")
    _add_expense(1, 30.0, "Bills", "2023-02-01", "Expense C")

    resp = auth_client.get("/profile")
    html = resp.get_data(as_text=True)

    for desc in ("Expense A", "Expense B", "Expense C"):
        assert desc in html, f"Expected description '{desc}' to be present without a filter"


# ----------------------------------------------------------------------
# Valid date range filter tests
# ----------------------------------------------------------------------


def test_profile_valid_date_range_filters_correctly(auth_client):
    """A correct start_date / end_date pair must limit the displayed transactions."""
    _clear_expenses(1)
    _add_expense(1, 5.0, "Food", "2023-01-05", "Alpha")
    _add_expense(1, 15.0, "Food", "2023-01-20", "Beta")
    _add_expense(1, 25.0, "Food", "2023-02-10", "Gamma")

    resp = auth_client.get("/profile?start_date=2023-01-01&end_date=2023-01-31")
    html = resp.get_data(as_text=True)

    for present in ("Alpha", "Beta"):
        assert present in html, f"Expected '{present}' to be shown within the date range"
    for absent in ("Gamma",):
        assert absent not in html, f"Did not expect '{absent}' to appear outside the date range"


# ----------------------------------------------------------------------
# Invalid date format tests
# ----------------------------------------------------------------------


def test_profile_invalid_date_ignores_filter(auth_client):
    """If a date cannot be parsed, the view must fall back to showing all expenses."""
    _clear_expenses(1)
    _add_expense(1, 8.0, "Food", "2023-03-01", "Delta")
    _add_expense(1, 12.0, "Food", "2023-04-01", "Epsilon")

    resp = auth_client.get("/profile?start_date=invalid-date&end_date=2023-04-30")
    html = resp.get_data(as_text=True)

    for desc in ("Delta", "Epsilon"):
        assert desc in html, f"Expected '{desc}' to appear when dates are invalid"


# ----------------------------------------------------------------------
# Start date after end date tests
# ----------------------------------------------------------------------


def test_profile_start_after_end_ignores_filter(auth_client):
    """When start_date is later than end_date, the filter is discarded and all data is shown."""
    _clear_expenses(1)
    _add_expense(1, 9.0, "Food", "2023-05-10", "Zeta")
    _add_expense(1, 19.0, "Food", "2023-06-15", "Eta")

    resp = auth_client.get("/profile?start_date=2023-06-01&end_date=2023-05-01")
    html = resp.get_data(as_text=True)

    for desc in ("Zeta", "Eta"):
        assert desc in html, f"Expected '{desc}' to be shown when start_date > end_date"


# ----------------------------------------------------------------------
# Category breakdown / stats should respect the filter
# ----------------------------------------------------------------------


def test_profile_filter_updates_summary_cards(auth_client):
    """Total spent, transaction count, and this month's spending must reflect the filtered data."""
    _clear_expenses(1)
    _add_expense(1, 50.0, "Food", "2023-01-15", "Jan food")
    _add_expense(1, 30.0, "Transport", "2023-02-20", "Feb transport")

    resp = auth_client.get("/profile?start_date=2023-01-01&end_date=2023-01-31")
    html = resp.get_data(as_text=True)

    assert "50.00" in html, "Expected total spent to reflect filtered data"
    assert "30.00" not in html, "Feb expense should not appear in Jan-only filter"


def test_profile_category_breakdown_respects_filter(auth_client):
    """Category totals must be computed only over the filtered expenses."""
    _clear_expenses(1)
    _add_expense(1, 20.0, "Food", "2023-01-10", "Jan food")
    _add_expense(1, 10.0, "Transport", "2023-01-20", "Jan transport")

    resp = auth_client.get("/profile?start_date=2023-01-01&end_date=2023-01-31")
    html = resp.get_data(as_text=True)

    assert "Food" in html, "Expected Food category in filtered view"
    assert "Transport" in html, "Expected Transport category in filtered view"
