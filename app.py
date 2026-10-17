from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime

from database.db import get_db, init_db, seed_db, get_user_by_email, get_expenses_by_user, get_summary_stats, get_category_breakdown, add_expense, get_expense_by_id, update_expense , delete_expense_by_id , CATEGORIES

import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-key-change-in-production")

# ------------------------------------------------------------------ #
# Context processors — make current user available to all templates   #
# ------------------------------------------------------------------ #

@app.context_processor
def inject_user():
    """Make current user available in all templates, plus the current request path for active menu highlighting."""
    user_id = session.get("user_id")
    if user_id:
        db = get_db()
        user = db.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        db.close()
        if user:
            return {"user": dict(user), "request_path": request.path}
    return {"user": None, "request_path": request.path}

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

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    """Log the user out, clear the session and redirect to the landing page."""
    session.clear()
    flash("You have been logged out")
    return redirect(url_for("landing"))




@app.route("/analytics")
def analytics():
    """Render the Coming‑Soon analytics page.

    The page is only visible to logged‑in users. Unauthenticated visitors are
    redirected to the login page, matching the behaviour of the other protected
    routes in the app.
    """
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


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

    # Parse optional date range filters
    # Support both old param names (start_date/end_date) and new preset names (date_from/date_to)
    start_date_str = request.args.get('start_date') or request.args.get('date_from')
    end_date_str = request.args.get('end_date') or request.args.get('date_to')

    start_date_val = None
    end_date_val = None
    try:
        if start_date_str:
            start_date_val = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date_val = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date_val = None
        end_date_val = None

    if start_date_val and end_date_val and start_date_val > end_date_val:
        start_date_val, end_date_val = None, None

    expenses = get_expenses_by_user(
        user_id,
        start_date_val.isoformat() if start_date_val else None,
        end_date_val.isoformat() if end_date_val else None
    )

    # Compute summary stats and category breakdown based on filtered expenses
    total_spent = sum(float(exp.get("amount", 0)) for exp in expenses)
    tx_count = len(expenses)
    avg_transaction = total_spent / tx_count if tx_count else 0.0

    # Top category from filtered expenses
    cat_totals = {}
    for exp in expenses:
        cat = exp.get("category", "Other")
        cat_totals[cat] = cat_totals.get(cat, 0.0) + float(exp.get("amount", 0))

    top_category = max("cat_totals", "key=cat_totals.get") if cat_totals else None

    # This month's spending within filtered expenses or overall? Usually within filtered or current month. Let's compute based on filtered expenses matching current month or just general.
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
        "top_category": top_category,
    }

    # Category breakdown for filtered expenses
    colour_palette = [
        "var(--accent)",
        "var(--accent-2)",
        "var(--accent-3)",
        "var(--accent-4)",
        "var(--accent-5)",
        "var(--accent-6)",
    ]
    categories = []
    for idx, cat_name in enumerate(CATEGORIES):
        amt = cat_totals.get(cat_name, 0.0)
        pct = (amt / total_spent * 100) if total_spent > 0 else 0.0
        categories.append({
            "name": cat_name,
            "amount": amt,
            "percentage": pct,
            "color": colour_palette[idx % len(colour_palette)]
        })

    # Compute date presets for quick filters
    today = date.today()
    # Helper to get start date of month given offset months from today
    def month_start(offset_months):
        # offset_months: 0 for this month, -1 for last month, etc.
        total_months = today.year * 12 + today.month - 1 + offset_months
        year = total_months // 12
        month = total_months % 12 + 1
        return date(year, month, 1)

    presets = {
        'all_time': {'date_from': None, 'date_to': None},
        'this_month': {'date_from': month_start(0), 'date_to': today},
        'last_3_months': {'date_from': month_start(-2), 'date_to': today},
        'last_6_months': {'date_from': month_start(-5), 'date_to': today},
    }

    return render_template(
        "profile.html",
        user=user_info,
        stats=stats,
        transactions=expenses,
        categories=categories,
        presets=presets,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
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


@app.route("/expenses/add", methods=["GET", "POST"], endpoint="add_expense")
def add_expense_route():
    """Render the Add Expense form or process a new expense submission."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to add expenses.", "warning")
        return redirect(url_for("login"))

    today_str = date.today().isoformat()

    if request.method == "POST":
        amount_str = request.form.get("amount")
        category = request.form.get("category")
        exp_date = request.form.get("date") or today_str
        description = request.form.get("description", "").strip()

        # Validate amount
        try:
            if amount_str is None or not amount_str.strip():
                raise ValueError
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return render_template(
                "add_expense.html",
                categories=CATEGORIES,
                today=today_str,
                error="Amount must be a positive number."
            )

        # Validate category
        if category not in CATEGORIES:
            return render_template(
                "add_expense.html",
                categories=CATEGORIES,
                today=today_str,
                error="Invalid category selected."
            )

        # Insert into database using helper from database/db.py
        add_expense(user_id, amount, category, exp_date, description)

        flash("Expense added successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("add_expense.html", categories=CATEGORIES, today=today_str)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to edit expenses.", "warning")
        return redirect(url_for("login"))

    # Fetch the expense with ownership check
    expense = get_expense_by_id(id, user_id)
    if not expense:
        flash("Expense not found or you don't own it.", "error")
        return redirect(url_for("profile"))

    today_str = date.today().isoformat()

    if request.method == "POST":
        amount_str = request.form.get("amount")
        category = request.form.get("category")
        exp_date = request.form.get("date") or today_str
        description = request.form.get("description", "").strip()

        # Validate amount
        try:
            if amount_str is None or not amount_str.strip():
                raise ValueError
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=CATEGORIES,
                today=today_str,
                error="Amount must be a positive number."
            )

        # Validate category
        if category not in CATEGORIES:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=CATEGORIES,
                today=today_str,
                error="Invalid category selected."
            )

        # Validate date format
        try:
            datetime.strptime(exp_date, '%Y-%m-%d')
        except ValueError:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=CATEGORIES,
                today=today_str,
                error="Invalid date format."
            )

        # Update expense
        update_expense(id, user_id, amount, category, exp_date, description)
        flash("Expense updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=CATEGORIES,
        today=today_str
    )


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to delete expenses.", "warning")
        return redirect(url_for("login"))

    # Check ownership using existing helper
    expense = get_expense_by_id(id, user_id)
    if not expense:
        flash("Expense not found or you don't own it.", "error")
        return redirect(url_for("profile"))

    # Delete the expense
    delete_expense_by_id(id, user_id)
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    # Debug mode should be disabled in production
    # Use FLASK_ENV=development to enable debug mode
    app.run(port=5001)
