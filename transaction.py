"""Transaction classes: the data model of the project.

Transaction  -> base class with validation and the dunder methods
Expense      -> money going out
Income       -> money coming in
"""

import math
from datetime import date, datetime

from config import DATE_FORMAT, MAX_AMOUNT, MAX_CATEGORY_LENGTH
from exceptions import (
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    StorageError,
)


class Transaction:
    """One row of money movement. Use Expense or Income, not this directly."""

    # Class attribute: shared by every object of the class and
    # overridden in each subclass.
    type_label = "Transaction"

    def __init__(self, amount, category, txn_date=None, note="", txn_id=None):
        self.txn_id = txn_id
        # These three assignments do not store the value straight away.
        # Python routes them through the property setters below, so bad
        # data is rejected at the moment the object is created.
        self.amount = amount
        self.category = category
        self.txn_date = txn_date if txn_date is not None else date.today()
        self.note = (note or "").strip()

    # ---------- validators (static: they need no object) ----------

    @staticmethod
    def validate_amount(value):
        """Return the amount as a rounded float or raise InvalidAmountError."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise InvalidAmountError(f"'{value}' is not a number.") from None
        # float("nan") and float("inf") are legal floats, so check them first.
        if not math.isfinite(number):
            raise InvalidAmountError("Amount must be a real number.")
        if number <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")
        if number > MAX_AMOUNT:
            raise InvalidAmountError(f"Amount cannot exceed {MAX_AMOUNT:,}.")
        return round(number, 2)

    @staticmethod
    def validate_category(value):
        text = str(value).strip()
        if not text:
            raise InvalidCategoryError("Category cannot be empty.")
        if len(text) > MAX_CATEGORY_LENGTH:
            raise InvalidCategoryError(
                f"Category can have at most {MAX_CATEGORY_LENGTH} characters."
            )
        return text.title()

    @staticmethod
    def parse_date(text):
        """Turn 'YYYY-MM-DD' into a date object."""
        try:
            return datetime.strptime(str(text).strip(), DATE_FORMAT).date()
        except ValueError:
            raise InvalidDateError(
                "Use the format YYYY-MM-DD, for example 2026-10-19."
            ) from None

    # ---------- properties (encapsulation) ----------

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = self.validate_amount(value)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = self.validate_category(value)

    @property
    def txn_date(self):
        return self._txn_date

    @txn_date.setter
    def txn_date(self, value):
        if isinstance(value, str):
            value = self.parse_date(value)
        elif isinstance(value, datetime):
            value = value.date()
        elif not isinstance(value, date):
            raise InvalidDateError("Date must be text like 2026-10-19.")
        self._txn_date = value

    # ---------- behaviour that subclasses must override ----------

    def signed_amount(self):
        """+amount for income, -amount for expense."""
        raise NotImplementedError("Subclasses must define signed_amount().")

    # ---------- converting to and from CSV rows ----------

    def to_row(self):
        """Dictionary in the shape csv.DictWriter expects."""
        return {
            "id": self.txn_id,
            "type": self.type_label,
            "date": self.txn_date.strftime(DATE_FORMAT),
            "category": self.category,
            "amount": f"{self.amount:.2f}",
            "note": self.note,
        }

    @classmethod
    def from_row(cls, row):
        """Factory: build the right subclass from one CSV row.

        The 'type' column decides whether we create an Expense or an
        Income. Missing or non-numeric fields raise KeyError/ValueError,
        which the storage layer catches so one bad row cannot kill the load.
        """
        kinds = {"Expense": Expense, "Income": Income}
        kind = kinds.get(row.get("type"))
        if kind is None:
            raise StorageError(f"Unknown transaction type: {row.get('type')!r}")
        return kind(
            amount=row["amount"],
            category=row["category"],
            txn_date=row["date"],
            note=row.get("note") or "",
            txn_id=int(row["id"]),
        )

    # ---------- dunder methods ----------

    @staticmethod
    def header():
        """Table header that lines up with __str__."""
        return f"{'ID':<5}{'Date':<12}{'Type':<9}{'Category':<16}{'Amount':>12}  Note"

    def __str__(self):
        id_text = "-" if self.txn_id is None else str(self.txn_id)
        return (
            f"{id_text:<5}{self.txn_date.isoformat():<12}"
            f"{self.type_label:<9}{self.category:<16}"
            f"{self.signed_amount():>+12,.2f}  {self.note}"
        )

    def __repr__(self):
        return (
            f"{type(self).__name__}(amount={self.amount}, "
            f"category={self.category!r}, "
            f"txn_date={self.txn_date.isoformat()!r}, "
            f"note={self.note!r}, txn_id={self.txn_id})"
        )

    def _key(self):
        return (self.type_label, self.txn_date, self.category, self.amount, self.note)

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self._key() == other._key()

    # Defining __eq__ without __hash__ makes the class unhashable on
    # purpose. These objects are mutable, and a mutable object whose hash
    # can change would corrupt sets and dictionaries.
    __hash__ = None

    def __lt__(self, other):
        """Lets sorted(transactions) order them by date, then by id."""
        if not isinstance(other, Transaction):
            return NotImplemented
        return (self.txn_date, self.txn_id or 0) < (other.txn_date, other.txn_id or 0)


class Expense(Transaction):
    """Money going out."""

    type_label = "Expense"
    suggested_categories = ["Food", "Transport", "Books", "Recharge", "Entertainment"]

    def signed_amount(self):
        return -self.amount


class Income(Transaction):
    """Money coming in."""

    type_label = "Income"
    suggested_categories = ["Pocket Money", "Scholarship", "Freelance", "Gift"]

    def signed_amount(self):
        return self.amount
