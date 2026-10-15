import calendar
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"


def get_db():
    """Open a connection to spendly.db.

    Every connection gets dictionary-like row access (row_factory) and
    foreign key enforcement (SQLite foreign keys are off by default).
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def get_user_by_email(email):
    """Return the user row for the given email, or None if not found."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    return user


def get_expenses_by_user(user_id):
    """Return all expenses for the given user, ordered by date descending."""
    db = get_db()
    expenses = db.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()
    db.close()
    return [dict(expense) for expense in expenses]

# Fixed category list — must match the values used across the app.
CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def init_db():
    """Create the users and expenses tables if they do not exist.

    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
    """
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.commit()
    db.close()


def seed_db():
    """Insert demo data exactly once.

    Returns early if the users table already contains data, so repeated
    calls (e.g. on app restart) never duplicate records.
    """
    db = get_db()
    existing = db.execute("SELECT 1 FROM users LIMIT 1").fetchone()
    if existing:
        db.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    # Dates spread across the current month (YYYY-MM-DD format).
    # Days are clamped to the last valid day so the seed works in any
    # month, including February.
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    days = [min(d, last_day) for d in (1, 3, 5, 7, 9, 11, 13, 15)]
    expenses = [
        (user_id, 42.50, "Food", f"{today.year}-{today.month:02d}-{days[0]:02d}", "Weekly grocery run"),
        (user_id, 18.00, "Transport", f"{today.year}-{today.month:02d}-{days[1]:02d}", "Bus and metro pass"),
        (user_id, 120.00, "Bills", f"{today.year}-{today.month:02d}-{days[2]:02d}", "Electricity bill"),
        (user_id, 35.00, "Health", f"{today.year}-{today.month:02d}-{days[3]:02d}", "Pharmacy"),
        (user_id, 55.00, "Entertainment", f"{today.year}-{today.month:02d}-{days[4]:02d}", "Movie night"),
        (user_id, 89.99, "Shopping", f"{today.year}-{today.month:02d}-{days[5]:02d}", "New headphones"),
        (user_id, 12.50, "Other", f"{today.year}-{today.month:02d}-{days[6]:02d}", "Donation to charity"),
        (user_id, 7.50, "Food", f"{today.year}-{today.month:02d}-{days[7]:02d}", "Lunch with colleague"),
    ]
    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    db.commit()
    db.close()

# --------------------------------------------------------------------------
# New helper functions for profile page
# --------------------------------------------------------------------------

def get_summary_stats(user_id: int):
    """Return summary statistics for a user's expenses.

    Returns a dict with keys:
        total_spent, tx_count, top_category, avg_monthly
    """
    db = get_db()
    # Total spent
    total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]
    # Transaction count
    count = db.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]
    # Top category by total amount
    top_row = db.execute(
        "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    top_category = top_row[0] if top_row else None
    # Average monthly spend: sum per month then average across months
    month_totals = db.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? GROUP BY strftime('%Y-%m', date)",
        (user_id,)
    ).fetchall()
    # month_totals is list of tuples like (sum,)
    month_values = [row[0] for row in month_totals]
    avg_monthly = sum(month_values) / len(month_values) if month_values else 0
    db.close()
    return {
        "total_spent": float(total),
        "tx_count": int(count),
        "top_category": top_category,
        "avg_monthly": float(avg_monthly),
    }

def get_category_breakdown(user_id: int):
    """Return a list of category breakdowns with totals and colour vars.

    Each dict contains: category, total, color.
    """
    colour_palette = [
        "var(--accent)",
        "var(--accent-2)",
        "var(--accent-3)",
        "var(--accent-4)",
        "var(--accent-5)",
        "var(--accent-6)",
    ]
    db = get_db()
    results = []
    for idx, cat in enumerate(CATEGORIES):
        total = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ? AND category = ?",
            (user_id, cat)
        ).fetchone()[0]
        results.append({
            "category": cat,
            "total": float(total),
            "color": colour_palette[idx % len(colour_palette)],
        })
    db.close()
    return results
