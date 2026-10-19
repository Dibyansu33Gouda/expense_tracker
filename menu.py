"""Menu: everything the user sees and types.

No money logic lives here. The menu collects input, calls the manager
or the report generator, and prints the result.
"""

from datetime import date

from config import CURRENCY
from exceptions import ExpenseTrackerError
from logger import logger
from transaction import Expense, Income, Transaction
from utils import ask, parse_id, parse_month, parse_yes_no


class Menu:
    def __init__(self, manager, reports):
        self.manager = manager
        self.reports = reports
        # Dictionary dispatch: option -> (label, method). Adding a feature
        # means adding one line here instead of another if/elif branch.
        self.actions = {
            "1": ("Add expense", self.add_expense),
            "2": ("Add income", self.add_income),
            "3": ("View all transactions", self.view_all),
            "4": ("View one month", self.view_month),
            "5": ("Filter by category", self.view_category),
            "6": ("Search notes and categories", self.search),
            "7": ("Delete a transaction", self.delete),
            "8": ("Monthly summary", self.summary),
            "9": ("Export monthly report to CSV", self.export),
        }

    # ---------- main loop ----------

    def run(self):
        print("\nEXPENSE TRACKER")
        try:
            while True:
                self._show_menu()
                choice = input("Choose an option: ").strip()
                if choice == "0":
                    print("Goodbye.")
                    return
                action = self.actions.get(choice)
                if action is None:
                    print("Pick a number from the menu.")
                    continue
                try:
                    action[1]()
                except ExpenseTrackerError as err:
                    print(f"Error: {err}")
                    logger.error(str(err))
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")

    def _show_menu(self):
        print("\n" + "-" * 34)
        for key, (label, _) in self.actions.items():
            print(f" {key}. {label}")
        print(" 0. Exit")
        print("-" * 34)

    # ---------- printing helper ----------

    def _print_table(self, transactions):
        if not transactions:
            print("Nothing to show.")
            return
        print(Transaction.header())
        print("-" * 70)
        for transaction in transactions:
            print(transaction)
        print("-" * 70)
        totals = self.manager.totals(transactions)
        print(
            f"{len(transactions)} rows | Income {CURRENCY} {totals['income']:,.2f} | "
            f"Expenses {CURRENCY} {totals['expense']:,.2f} | "
            f"Balance {CURRENCY} {totals['balance']:+,.2f}"
        )

    @staticmethod
    def _ask_month():
        today = date.today()
        return ask(
            "Month (YYYY-MM, Enter = this month): ",
            parse_month,
            default=(today.year, today.month),
        )

    # ---------- actions ----------

    def _add(self, kind, suggestions):
        print(f"Suggested categories: {', '.join(suggestions)}")
        amount = ask("Amount: ", Transaction.validate_amount)
        category = ask("Category: ", Transaction.validate_category)
        txn_date = ask(
            "Date (YYYY-MM-DD, Enter = today): ",
            Transaction.parse_date,
            default=date.today(),
        )
        note = ask("Note (optional): ")
        saved = self.manager.add(kind, amount, category, txn_date, note)
        print(f"Saved:\n{Transaction.header()}\n{saved}")

    def add_expense(self):
        self._add("expense", Expense.suggested_categories)

    def add_income(self):
        self._add("income", Income.suggested_categories)

    def view_all(self):
        self._print_table(self.manager.all())

    def view_month(self):
        year, month = self._ask_month()
        self._print_table(self.manager.for_month(year, month))

    def view_category(self):
        category = ask("Category: ", Transaction.validate_category)
        self._print_table(self.manager.for_category(category))

    def search(self):
        word = ask("Search for: ", lambda text: text or self._reject_blank())
        self._print_table(self.manager.search(word))

    @staticmethod
    def _reject_blank():
        raise ExpenseTrackerError("Type at least one character.")

    def delete(self):
        txn_id = ask("Id to delete: ", parse_id)
        transaction = self.manager.get(txn_id)
        print(f"{Transaction.header()}\n{transaction}")
        if ask("Delete this transaction? (y/n): ", parse_yes_no):
            self.manager.delete(txn_id)
            print("Deleted.")
        else:
            print("Cancelled.")

    def summary(self):
        year, month = self._ask_month()
        print(self.reports.monthly_summary(year, month))

    def export(self):
        year, month = self._ask_month()
        transactions_path, summary_path = self.reports.export_month(year, month)
        print(f"Saved {transactions_path}")
        print(f"Saved {summary_path}")
