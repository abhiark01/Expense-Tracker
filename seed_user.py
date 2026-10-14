import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db import get_db, generate_password_hash
import random
from datetime import datetime

# Common Indian first names and last names
first_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Shaurya",
    "Mohammed", "Abdul", "Rahul", "Priya", "Aisha", "Sneha", "Ananya", "Zara", "Myra", "Ira"
]
last_names = [
    "Sharma", "Verma", "Patel", "Singh", "Kumar", "Reddy", "Menon", "Iyer", "Chatterjee", "Banerjee",
    "Jain", "Agarwal", "Gupta", "Desai", "Joshi", "Pandey", "Tyagi", "Yadav", "Kaur", "Khanna"
]

def generate_unique_email():
    while True:
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"
        base = f"{first.lower()}.{last.lower()}"
        # Generate a random 2-3 digit number
        suffix = random.randint(10, 999)
        email = f"{base}{suffix}@gmail.com"

        # Check if email already exists
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if not existing:
            return name, email
        # else loop again

def main():
    name, email = generate_unique_email()
    password_hash = generate_password_hash("password123")
    created_at = datetime.now().isoformat()

    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, created_at)
    )
    user_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"id: {user_id}")
    print(f"name: {name}")
    print(f"email: {email}")

if __name__ == "__main__":
    main()