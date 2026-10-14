import sys
import os
import random
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))

from database.db import get_db, CATEGORIES

def seed_expenses(user_id, count, months):
    db = get_db()

    # Verify user
    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        print(f"No user found with id {user_id}.")
        db.close()
        return

    # Category logic: Food most common, Health/Entertainment least
    # Weights for categories
    category_weights = {
        "Food": 30,
        "Transport": 20,
        "Bills": 15,
        "Shopping": 15,
        "Other": 10,
        "Health": 5,
        "Entertainment": 5
    }

    category_choices = list(category_weights.keys())
    weights = list(category_weights.values())

    # Descriptions
    descriptions = {
        "Food": ["Grocery run", "Swiggy order", "Lunch at office", "Cafe visit", "Vegetable market"],
        "Transport": ["Uber ride", "Auto rickshaw", "Fuel", "Bus fare", "Metro"],
        "Bills": ["Electricity bill", "Mobile recharge", "Internet bill", "Water bill"],
        "Health": ["Pharmacy", "Doctor consultation", "Lab test"],
        "Entertainment": ["Movie tickets", "Netflix sub", "Concert", "Gaming"],
        "Shopping": ["Clothes", "Amazon order", "Books", "Electronics"],
        "Other": ["Donation", "Gift", "Repair", "Misc"]
    }

    # Amounts
    amounts = {
        "Food": (50, 800),
        "Transport": (20, 500),
        "Bills": (200, 3000),
        "Health": (100, 2000),
        "Entertainment": (100, 1500),
        "Shopping": (200, 5000),
        "Other": (50, 1000)
    }

    expenses = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    for _ in range(count):
        cat = random.choices(category_choices, weights=weights, k=1)[0]
        amount = round(random.uniform(*amounts[cat]), 2)
        days_offset = random.randint(0, months * 30)
        date = (end_date - timedelta(days=days_offset)).strftime("%Y-%m-%d")
        desc = random.choice(descriptions[cat])
        expenses.append((user_id, amount, cat, date, desc))

    try:
        db.execute("BEGIN TRANSACTION")
        db.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error inserting expenses: {e}")
        db.close()
        return

    # Confirm
    inserted = db.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ? AND date >= ?", (user_id, start_date.strftime("%Y-%m-%d"))).fetchone()[0]
    sample = db.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,)).fetchall()

    print(f"Inserted {count} expenses.")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("\nSample records:")
    for row in sample:
        print(f"Date: {row['date']}, Category: {row['category']}, Amount: ₹{row['amount']}, Desc: {row['description']}")

    db.close()

if __name__ == "__main__":
    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
        seed_expenses(user_id, count, months)
    except (IndexError, ValueError):
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
