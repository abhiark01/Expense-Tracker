from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db, get_user_by_email, get_expenses_by_user, get_summary_stats, get_category_breakdown, get_monthly_trend

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key-change-in-production"

# ------------------------------------------------------------------ #
# Context processors — make current user available to all templates   #
# ------------------------------------------------------------------ #

@app.context_processor
def inject_user():
    """Make current user available in all templates."""
    user_id = session.get("user_id")
    if user_id:
        db = get_db()
        user = db.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        db.close()
        if user:
            return {"user": dict(user)}
    return {"user": None}

# ------------------------------------------------------------------ #
# Database setup — run once at startup so tables and seed data       #
# exist before any route is used.                                    #
# ------------------------------------------------------------------ #
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not name or not email or not password or not confirm_password:
            return render_template("register.html", error="Missing data")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

        if existing_user:
            db.close()
            return render_template("register.html", error="Email already registered")

        password_hash = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        db.commit()
        db.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="Missing data")

        user = get_user_by_email(email)

        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password")

        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out")
    return redirect(url_for("landing"))


@app.route("/profile")

def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user_info = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "avatar": "DU",
        "member_since": "2022-01-15",
    }
    summary_stats = {
        "total_spent": 795.50,
        "tx_count": 12,
        "top_category": "Food",
        "avg_monthly": 450.25,
    }
    transactions = [
        {"date": "2026-10-01", "description": "Lunch with colleague", "category": "Food", "amount": 7.5},
        {"date": "2026-10-02", "description": "Movie night", "category": "Entertainment", "amount": 55.0},
        {"date": "2026-10-03", "description": "Coffee", "category": "Food", "amount": 3.25},
        {"date": "2026-10-04", "description": "Grocery shopping", "category": "Food", "amount": 42.5},
        {"date": "2026-10-05", "description": "Bus pass", "category": "Transport", "amount": 18.0},
        {"date": "2026-10-06", "description": "Electricity bill", "category": "Bills", "amount": 120.0},
        {"date": "2026-10-07", "description": "Pharmacy", "category": "Health", "amount": 35.0},
        {"date": "2026-10-08", "description": "Concert tickets", "category": "Entertainment", "amount": 85.0},
        {"date": "2026-10-09", "description": "New headphones", "category": "Shopping", "amount": 89.99},
        {"date": "2026-10-10", "description": "Charity donation", "category": "Other", "amount": 12.5},
    ]
    category_breakdown = [
        {"category": "Food", "total": 245.50, "color": "var(--accent)"},
        {"category": "Transport", "total": 180.00, "color": "var(--accent-2)"},
        {"category": "Bills", "total": 450.00, "color": "var(--danger)"},
        {"category": "Health", "total": 85.00, "color": "var(--accent-3, #9b59b6)"},
        {"category": "Entertainment", "total": 120.00, "color": "var(--accent-4, #e74c3c)"},
        {"category": "Shopping", "total": 210.00, "color": "var(--accent-5, #2980b9)"},
        {"category": "Other", "total": 45.00, "color": "var(--ink-muted)"},
    ]
    monthly_trend = [
        {"month": "2026-05", "total": 420.00},
        {"month": "2026-06", "total": 510.50},
        {"month": "2026-07", "total": 380.00},
        {"month": "2026-08", "total": 620.75},
        {"month": "2026-09", "total": 450.25},
        {"month": "2026-10", "total": 795.50},
    ]
    category_totals = [
        {"category": "Food", "total": 245.50, "color": "var(--accent)"},
        {"category": "Transport", "total": 180.00, "color": "var(--accent-2)"},
        {"category": "Bills", "total": 450.00, "color": "var(--danger)"},
        {"category": "Health", "total": 85.00, "color": "var(--accent-3, #9b59b6)"},
        {"category": "Entertainment", "total": 120.00, "color": "var(--accent-4, #e74c3c)"},
        {"category": "Shopping", "total": 210.00, "color": "var(--accent-5, #2980b9)"},
        {"category": "Other", "total": 45.00, "color": "var(--ink-muted)"},
    ]
    return render_template(
        "profile.html",
        user=user_info,
        stats=summary_stats,
        transactions=transactions,
        categories=category_breakdown,
        monthly_trend=monthly_trend,
        category_totals=category_totals,
    )

# New profile sub‑routes

@app.route("/profile/transactions")
def profile_transactions():
    """Render the transaction history for the logged‑in user."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))
    expenses = get_expenses_by_user(user_id)
    return render_template("profile_transactions.html", expenses=expenses)

@app.route("/profile/summary")
def profile_summary():
    """Render summary statistics for the logged‑in user."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))
    stats = get_summary_stats(user_id)
    return render_template("profile_summary.html", stats=stats)

@app.route("/profile/categories")
def profile_categories():
    """Render category breakdown for the logged‑in user."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))
    categories = get_category_breakdown(user_id)
    return render_template("profile_categories.html", categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    # TODO: Implement expense editing - Step 8
    return f"Edit expense {id} — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    # TODO: Implement expense deletion - Step 9
    return f"Delete expense {id} — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
