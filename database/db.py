import calendar
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

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


def get_db():
    """Open a connection to spendly.db.

    Every connection gets dictionary-like row access (row_factory) and
    foreign key enforcement (SQLite foreign keys are off by default).
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


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