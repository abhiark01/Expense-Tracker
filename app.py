from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

from database.db import get_db, init_db, seed_db, get_user_by_email, get_expenses_by_user, get_summary_stats, get_category_breakdown

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

    db = get_db()
    user_row = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    db.close()

    if not user_row:
        session.clear()
        flash("User not found.", "error")
        return redirect(url_for("login"))

    name = user_row["name"]
    if len(name) >= 2:
        avatar = name[0:2].upper()
    else:
        avatar = name[0].upper() if name else "?"

    # Format member_since as "Month YYYY" (e.g. "January 2026")
    created_at = user_row["created_at"]
    member_since = ""
    if created_at:
        try:
            parts = created_at.split("-")
            if len(parts) >= 2:
                month_names = [
                    "", "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]
                month_idx = int(parts[1])
                if 1 <= month_idx <= 12:
                    member_since = f"{month_names[month_idx]} {parts[0]}"
        except (ValueError, IndexError):
            member_since = created_at

    user_info = {
        "name": name,
        "email": user_row["email"],
        "avatar": avatar,
        "member_since": member_since or created_at
    }

    expenses = get_expenses_by_user(user_id)
    raw_stats = get_summary_stats(user_id)
    category_breakdown_data = get_category_breakdown(user_id)

    total_spent = float(raw_stats.get("total_spent", 0))
    tx_count = int(raw_stats.get("tx_count", 0))
    avg_transaction = total_spent / tx_count if tx_count else 0.0

    # This month's spending
    today = date.today()
    this_month_prefix = f"{today.year}-{today.month:02d}"
    this_month = 0.0
    for exp in expenses:
        if exp.get("date") and exp["date"].startswith(this_month_prefix):
            this_month += float(exp.get("amount", 0))

    stats = {
        "total_spent": total_spent,
        "tx_count": tx_count,
        "avg_transaction": avg_transaction,
        "this_month": this_month,
    }

    # Rename category keys for the template: name / amount
    categories = [
        {"name": c["category"], "amount": c["total"]}
        for c in category_breakdown_data
    ]

    return render_template(
        "profile.html",
        user=user_info,
        stats=stats,
        transactions=expenses,
        categories=categories,
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
