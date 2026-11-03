from datetime import date
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import (
    add_demo_expenses,
    add_expense,
    delete_expense,
    get_budgets,
    get_expenses,
    initialize_database,
    save_budget,
    update_expense,
)

CATEGORIES = [
    "Food", "Transport", "Bills", "Shopping", "Health",
    "Education", "Entertainment", "Travel", "Other",
]
PAYMENT_METHODS = ["UPI", "Card", "Cash", "Net banking", "Other"]
CATEGORY_COLORS = {
    "Food": ("#FCE4D6", "#D55E00"),
    "Transport": ("#DDEBF7", "#2878A0"),
    "Bills": ("#FFF2CC", "#B8860B"),
    "Shopping": ("#EADCF8", "#8056A8"),
    "Health": ("#DDEFE3", "#2A8061"),
    "Education": ("#FCE1C6", "#C66A13"),
    "Entertainment": ("#F6DDE5", "#B6496C"),
    "Travel": ("#D9E8E8", "#327C7C"),
    "Other": ("#E5E5E5", "#606060"),
}


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Expense Tracker")
        self.root.geometry("1050x720")
        self.root.minsize(850, 580)
        initialize_database()
        self.selected_id = None
        self.expenses = pd.DataFrame()

        self.build_form()
        self.build_tabs()
        self.refresh()

    def build_form(self):
        form = ttk.LabelFrame(self.root, text="Expense details", padding=10)
        form.pack(fill="x", padx=12, pady=10)

        self.spent_on = tk.StringVar(value=date.today().isoformat())
        self.amount = tk.StringVar()
        self.category = tk.StringVar(value=CATEGORIES[0])
        self.payment = tk.StringVar(value=PAYMENT_METHODS[0])
        self.note = tk.StringVar()

        fields = [
            ("Date (YYYY-MM-DD)", ttk.Entry(form, textvariable=self.spent_on, width=15)),
            ("Amount (₹)", ttk.Entry(form, textvariable=self.amount, width=12)),
            ("Category", ttk.Combobox(form, textvariable=self.category, values=CATEGORIES, state="readonly", width=15)),
            ("Payment", ttk.Combobox(form, textvariable=self.payment, values=PAYMENT_METHODS, state="readonly", width=13)),
            ("Note", ttk.Entry(form, textvariable=self.note, width=22)),
        ]
        for column, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=column, sticky="w", padx=4)
            widget.grid(row=1, column=column, sticky="ew", padx=4, pady=4)

        buttons = ttk.Frame(form)
        buttons.grid(row=1, column=len(fields), padx=5)
        ttk.Button(buttons, text="Add", command=self.add_expense).pack(side="left", padx=2)
        self.edit_button = ttk.Button(buttons, text="Update", command=self.update_expense, state="disabled")
        self.edit_button.pack(side="left", padx=2)
        self.delete_button = ttk.Button(buttons, text="Delete", command=self.delete_expense, state="disabled")
        self.delete_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=2)
        ttk.Button(form, text="Load demo data", command=self.load_demo_data).grid(
            row=2, column=0, sticky="w", padx=4, pady=5
        )

    def build_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.overview = ttk.Frame(self.tabs, padding=10)
        self.transactions = ttk.Frame(self.tabs, padding=10)
        self.budgets = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.overview, text="Overview")
        self.tabs.add(self.transactions, text="Transactions")
        self.tabs.add(self.budgets, text="Budgets")
        self.build_overview()
        self.build_transactions()
        self.build_budgets()

    def build_overview(self):
        self.summary = ttk.Label(self.overview, font=("Segoe UI", 11, "bold"))
        self.summary.pack(anchor="w", pady=5)
        self.figure = Figure(figsize=(9, 4), dpi=100)
        self.category_chart = self.figure.add_subplot(1, 2, 1)
        self.month_chart = self.figure.add_subplot(1, 2, 2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.overview)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def build_transactions(self):
        filters = ttk.Frame(self.transactions)
        filters.pack(fill="x", pady=5)
        self.category_filter = tk.StringVar(value="All")
        self.search = tk.StringVar()
        category_box = ttk.Combobox(
            filters, textvariable=self.category_filter,
            values=["All", *CATEGORIES], state="readonly", width=15,
        )
        category_box.pack(side="left", padx=4)
        category_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_table())
        search_box = ttk.Entry(filters, textvariable=self.search, width=24)
        search_box.pack(side="left", padx=4)
        search_box.bind("<KeyRelease>", lambda _event: self.refresh_table())
        ttk.Label(filters, text="Search note").pack(side="left", padx=4)
        ttk.Button(filters, text="Export CSV", command=self.export_csv).pack(side="right")

        columns = ("date", "amount", "category", "payment", "note")
        self.table = ttk.Treeview(self.transactions, columns=columns, show="headings")
        for column, title, width in zip(
            columns, ["Date", "Amount", "Category", "Payment", "Note"],
            [120, 120, 150, 120, 350],
        ):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, anchor="w")
        self.table.pack(fill="both", expand=True)
        for category, (row_color, _chart_color) in CATEGORY_COLORS.items():
            self.table.tag_configure(category, background=row_color)
        self.table.bind("<<TreeviewSelect>>", self.select_expense)

    def build_budgets(self):
        controls = ttk.Frame(self.budgets)
        controls.pack(fill="x", pady=5)
        self.budget_month = tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.budget_category = tk.StringVar(value=CATEGORIES[0])
        self.budget_amount = tk.StringVar()
        ttk.Label(controls, text="Month (YYYY-MM)").pack(side="left")
        ttk.Entry(controls, textvariable=self.budget_month, width=12).pack(side="left", padx=5)
        ttk.Combobox(
            controls, textvariable=self.budget_category,
            values=CATEGORIES, state="readonly", width=15,
        ).pack(side="left", padx=5)
        ttk.Label(controls, text="Limit (₹)").pack(side="left")
        ttk.Entry(controls, textvariable=self.budget_amount, width=12).pack(side="left", padx=5)
        ttk.Button(controls, text="Save budget", command=self.save_budget).pack(side="left", padx=5)

        columns = ("category", "limit", "spent", "remaining", "used")
        self.budget_table = ttk.Treeview(self.budgets, columns=columns, show="headings")
        for column, title in zip(columns, ["Category", "Limit", "Spent", "Remaining", "Used"]):
            self.budget_table.heading(column, text=title)
            self.budget_table.column(column, width=150, anchor="w")
        self.budget_table.pack(fill="both", expand=True)

    def refresh(self):
        self.expenses = pd.DataFrame(get_expenses())
        if not self.expenses.empty:
            self.expenses["spent_on"] = pd.to_datetime(self.expenses["spent_on"])
            self.expenses["amount"] = self.expenses["amount"].astype(float)
        self.refresh_overview()
        self.refresh_table()
        self.refresh_budgets()

    def refresh_overview(self):
        self.category_chart.clear()
        self.month_chart.clear()
        if self.expenses.empty:
            self.summary.config(text="No expenses yet. Add one above or load demo data.")
            self.category_chart.set_title("Spending by category")
            self.month_chart.set_title("Monthly spending")
            self.canvas.draw()
            return

        today = date.today()
        current = self.expenses[
            (self.expenses["spent_on"].dt.year == today.year)
            & (self.expenses["spent_on"].dt.month == today.month)
        ]
        average = float(np.mean(current["amount"])) if not current.empty else 0
        self.summary.config(
            text=(
                f"This month: ₹{current['amount'].sum():,.2f}  |  "
                f"Transactions: {len(current)}  |  Average: ₹{average:,.2f}  |  "
                f"All-time: ₹{self.expenses['amount'].sum():,.2f}"
            )
        )

        categories = self.expenses.groupby("category")["amount"].sum().sort_values()
        colors = [CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])[1] for category in categories.index]
        self.category_chart.barh(categories.index, categories.values, color=colors)
        self.category_chart.set_title("Spending by category")
        self.category_chart.set_xlabel("Rupees")

        monthly = self.expenses.set_index("spent_on").resample("MS")["amount"].sum().tail(6)
        labels = [month.strftime("%b %Y") for month in monthly.index]
        self.month_chart.plot(labels, monthly.values, marker="o", color="#2a9d8f")
        self.month_chart.set_title("Monthly spending")
        self.month_chart.set_ylabel("Rupees")
        self.month_chart.tick_params(axis="x", rotation=30)
        self.figure.tight_layout()
        self.canvas.draw()

    def refresh_table(self):
        for row in self.table.get_children():
            self.table.delete(row)
        if self.expenses.empty:
            return

        rows = self.expenses.copy()
        if self.category_filter.get() != "All":
            rows = rows[rows["category"] == self.category_filter.get()]
        search_text = self.search.get().strip()
        if search_text:
            rows = rows[rows["note"].str.contains(search_text, case=False, na=False)]

        for _, expense in rows.iterrows():
            self.table.insert(
                "", "end", iid=str(expense["id"]),
                values=(
                    expense["spent_on"].strftime("%Y-%m-%d"),
                    f"₹{expense['amount']:,.2f}", expense["category"],
                    expense["payment_method"], expense["note"],
                ),
                tags=(expense["category"],),
            )

    def refresh_budgets(self):
        for row in self.budget_table.get_children():
            self.budget_table.delete(row)
        try:
            year, month = map(int, self.budget_month.get().split("-"))
            date(year, month, 1)
        except ValueError:
            return

        if self.expenses.empty:
            spent = {}
        else:
            month_expenses = self.expenses[
                (self.expenses["spent_on"].dt.year == year)
                & (self.expenses["spent_on"].dt.month == month)
            ]
            spent = month_expenses.groupby("category")["amount"].sum().to_dict()

        for budget in get_budgets(self.budget_month.get()):
            limit = float(budget["amount"])
            amount_spent = float(spent.get(budget["category"], 0))
            remaining = limit - amount_spent
            percent = amount_spent / limit * 100 if limit else 0
            self.budget_table.insert(
                "", "end", values=(budget["category"], f"₹{limit:,.2f}",
                f"₹{amount_spent:,.2f}", f"₹{remaining:,.2f}", f"{percent:.0f}%"),
            )

    def get_form_values(self):
        try:
            spent_on = date.fromisoformat(self.spent_on.get().strip())
            amount = float(self.amount.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Enter a valid date and a positive amount.")
            return None
        return spent_on, amount, self.category.get(), self.payment.get(), self.note.get()

    def add_expense(self):
        values = self.get_form_values()
        if values:
            add_expense(*values)
            self.clear_form()
            self.refresh()

    def update_expense(self):
        values = self.get_form_values()
        if values and self.selected_id is not None:
            update_expense(self.selected_id, *values)
            self.clear_form()
            self.refresh()

    def delete_expense(self):
        if self.selected_id is not None and messagebox.askyesno("Delete", "Delete this expense?"):
            delete_expense(self.selected_id)
            self.clear_form()
            self.refresh()

    def select_expense(self, _event):
        selected = self.table.selection()
        if not selected:
            return
        self.selected_id = int(selected[0])
        row = self.expenses[self.expenses["id"] == self.selected_id].iloc[0]
        self.spent_on.set(row["spent_on"].strftime("%Y-%m-%d"))
        self.amount.set(str(row["amount"]))
        self.category.set(row["category"])
        self.payment.set(row["payment_method"])
        self.note.set(row["note"])
        self.edit_button.config(state="normal")
        self.delete_button.config(state="normal")

    def clear_form(self):
        self.selected_id = None
        self.spent_on.set(date.today().isoformat())
        self.amount.set("")
        self.category.set(CATEGORIES[0])
        self.payment.set(PAYMENT_METHODS[0])
        self.note.set("")
        self.edit_button.config(state="disabled")
        self.delete_button.config(state="disabled")
        for row in self.table.selection():
            self.table.selection_remove(row)

    def save_budget(self):
        try:
            year, month = map(int, self.budget_month.get().split("-"))
            date(year, month, 1)
            amount = float(self.budget_amount.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid budget", "Enter month as YYYY-MM and a positive limit.")
            return
        save_budget(self.budget_month.get(), self.budget_category.get(), amount)
        self.budget_amount.set("")
        self.refresh_budgets()

    def export_csv(self):
        if self.expenses.empty:
            messagebox.showinfo("Export", "There are no expenses to export.")
            return
        rows = self.expenses.copy()
        if self.category_filter.get() != "All":
            rows = rows[rows["category"] == self.category_filter.get()]
        search_text = self.search.get().strip()
        if search_text:
            rows = rows[rows["note"].str.contains(search_text, case=False, na=False)]
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if path:
            rows.to_csv(path, index=False)
            messagebox.showinfo("Export", "Expenses exported.")

    def load_demo_data(self):
        if messagebox.askyesno("Demo data", "Add sample expenses?"):
            add_demo_expenses()
            self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    ExpenseTracker(root)
    root.mainloop()
