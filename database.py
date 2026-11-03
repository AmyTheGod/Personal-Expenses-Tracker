import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).with_name("expenses.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spent_on TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                UNIQUE (month, category)
            )
            """
        )


def get_expenses():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, spent_on, amount, category, payment_method, note
            FROM expenses
            ORDER BY spent_on DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def add_expense(spent_on, amount, category, payment_method, note=""):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO expenses (spent_on, amount, category, payment_method, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (spent_on.isoformat(), amount, category, payment_method, note.strip()),
        )


def update_expense(expense_id, spent_on, amount, category, payment_method, note=""):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE expenses
            SET spent_on = ?, amount = ?, category = ?, payment_method = ?, note = ?
            WHERE id = ?
            """,
            (
                spent_on.isoformat(),
                amount,
                category,
                payment_method,
                note.strip(),
                expense_id,
            ),
        )


def delete_expense(expense_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def get_budgets(month):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT category, amount FROM budgets WHERE month = ? ORDER BY category",
            (month,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_budget(month, category, amount):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO budgets (month, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, category) DO UPDATE SET amount = excluded.amount
            """,
            (month, category, amount),
        )


def add_demo_expenses():
    demo_rows = [
        (_date_months_ago(2, 5), 420.00, "Food", "UPI", "Weekly groceries"),
        (_date_months_ago(2, 13), 180.00, "Transport", "Cash", "Metro and bus"),
        (_date_months_ago(2, 21), 899.00, "Bills", "Card", "Internet bill"),
        (_date_months_ago(1, 4), 260.00, "Food", "UPI", "Lunch with friends"),
        (_date_months_ago(1, 12), 650.00, "Shopping", "Card", "Everyday essentials"),
        (_date_months_ago(1, 20), 150.00, "Health", "UPI", "Pharmacy"),
        (_date_months_ago(0, 3), 320.00, "Transport", "UPI", "Auto fare"),
        (_date_months_ago(0, 11), 240.00, "Food", "Cash", "Coffee and snacks"),
        (_date_months_ago(0, 19), 500.00, "Education", "UPI", "Course materials"),
    ]
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO expenses (spent_on, amount, category, payment_method, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (spent_on.isoformat(), amount, category, method, note)
                for spent_on, amount, category, method, note in demo_rows
            ],
        )


def _date_months_ago(months_ago, day):
    today = date.today()
    month_number = today.year * 12 + today.month - 1 - months_ago
    year, month_index = divmod(month_number, 12)
    return date(year, month_index + 1, day)