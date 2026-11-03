# Personal Expense Tracker & Analytics Dashboard

A desktop application for recording expenses, viewing spending charts, and setting monthly budgets. It uses Tkinter, SQLite, NumPy, pandas, and Matplotlib.

## Features

- Add, edit, and delete expenses with date, amount, category, payment method, and note.
- Overview with monthly totals, average spending, category chart, and monthly trend chart.
- Each expense category has its own color in the list and category chart.
- Filter expenses by category or note; edit, delete, or export them to CSV.
- Set monthly budgets for spending categories.
- Store records in SQLite. **Load demo data** adds sample expenses across the current and previous two months.

## How the app works

1. Tkinter displays the forms, tabs, and expense table.
2. `app.py` calls `database.py` when you add, edit, or delete an expense.
3. `database.py` stores the data in `expenses.db`.
4. pandas organizes the records, NumPy calculates the average, and Matplotlib draws the charts.

## Requirements

- Python 3.10 or newer with Tkinter enabled
- pip

## Run the project

From this folder, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the desktop app:

```powershell
python app.py
```

The tracker opens in a desktop window. Add an expense at the top, or choose **Load demo data** to explore the charts.

## Data and project files

`expenses.db` is created beside `app.py` the first time the app runs. It is local to this computer and can be backed up by copying that file. The database is excluded from version control.

- `app.py` — Tkinter interface, analytics, charts, and validation.
- `database.py` — SQLite schema and data operations.
- `requirements.txt` — Python package dependencies.