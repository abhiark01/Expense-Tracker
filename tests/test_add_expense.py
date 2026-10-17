import pytest
from app import app
from database.db import get_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            # Ensure database is initialized and seed data exists
            from database.db import init_db, seed_db
            init_db()
            seed_db()
        yield client


def login(client, email="demo@spendly.com", password="demo123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_get_add_expense_logged_out(client):
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_get_add_expense_logged_in(client):
    login(client)
    response = client.get("/expenses/add")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Add Expense" in html
    assert "Food" in html
    assert "Transport" in html
    assert "Bills" in html


def test_post_add_expense_valid(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "150.50",
        "category": "Food",
        "date": "2026-10-17",
        "description": "Dinner with friends"
    }, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dinner with friends" in html
    assert "150.5" in html


def test_post_add_expense_empty_amount(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "",
        "category": "Food",
        "date": "2026-10-17",
        "description": "Bad amount"
    })
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Amount must be a positive number" in html


def test_post_add_expense_negative_amount(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "-10.00",
        "category": "Food",
        "date": "2026-10-17",
        "description": "Negative amount"
    })
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Amount must be a positive number" in html


def test_post_add_expense_invalid_category(client):
    login(client)
    response = client.post("/expenses/add", data={
        "amount": "50.00",
        "category": "InvalidCategory",
        "date": "2026-10-17",
        "description": "Bad category"
    })
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid category selected" in html


def test_post_add_expense_logged_out(client):
    response = client.post("/expenses/add", data={
        "amount": "50.00",
        "category": "Food",
        "date": "2026-10-17"
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
