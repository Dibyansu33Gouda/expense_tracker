"""ExpenseManager: the business logic.

It does not know whether data lives in a CSV file or in memory. It is
handed a Storage object and uses it (composition: "has-a" relationship).
"""

from exceptions import ExpenseTrackerError, TransactionNotFoundError
from transaction import Expense, Income


class ExpenseManager:
    def __init__(self, storage):
        self._storage = storage
        self._transactions = storage.load()

    # ---------- dunder methods ----------

    def __len__(self):
        return len(self._transactions)

    def __iter__(self):
        """Lets you write `for txn in manager` and get date order."""
        return iter(sorted(self._transactions))

    # ---------- create / read / delete ----------

    def _next_id(self):
        return max((t.txn_id for t in self._transactions), default=0) + 1

    def add(self, kind, amount, category, txn_date=None, note=""):
        classes = {"expense": Expense, "income": Income}
        transaction_class = classes.get(str(kind).lower())
        if transaction_class is None:
            raise ExpenseTrackerError("Type must be 'expense' or 'income'.")

        transaction = transaction_class(
            amount, category, txn_date, note, txn_id=self._next_id()
        )
        self._transactions.append(transaction)
        try:
            self._storage.save(self._transactions)
        except ExpenseTrackerError:
            # Saving failed, so undo the in-memory change to stay in sync.
            self._transactions.remove(transaction)
            raise
        return transaction

    def get(self, txn_id):
        for transaction in self._transactions:
            if transaction.txn_id == txn_id:
                return transaction
        raise TransactionNotFoundError(f"No transaction with id {txn_id}.")

    def delete(self, txn_id):
        transaction = self.get(txn_id)
        self._transactions.remove(transaction)
        try:
            self._storage.save(self._transactions)
        except ExpenseTrackerError:
            self._transactions.append(transaction)
            raise
        return transaction

    def all(self):
        return sorted(self._transactions)

    # ---------- filters ----------

    def for_month(self, year, month):
        return sorted(
            t for t in self._transactions
            if t.txn_date.year == year and t.txn_date.month == month
        )

    def for_category(self, category):
        wanted = category.strip().lower()
        return sorted(t for t in self._transactions if t.category.lower() == wanted)

    def search(self, keyword):
        word = keyword.strip().lower()
        return sorted(
            t for t in self._transactions
            if word in t.note.lower() or word in t.category.lower()
        )

    # ---------- calculations ----------

    @staticmethod
    def totals(transactions):
        income = sum(t.amount for t in transactions if isinstance(t, Income))
        expense = sum(t.amount for t in transactions if isinstance(t, Expense))
        return {"income": income, "expense": expense, "balance": income - expense}

    @staticmethod
    def category_breakdown(transactions):
        """Spending per category, biggest first. Income is ignored."""
        result = {}
        for t in transactions:
            if isinstance(t, Expense):
                result[t.category] = result.get(t.category, 0) + t.amount
        return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
