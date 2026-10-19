"""Custom exceptions.

All of them inherit from ExpenseTrackerError, so the menu can catch
every expected problem with a single `except ExpenseTrackerError`
while real bugs (like a typo in the code) still crash loudly.
"""


class ExpenseTrackerError(Exception):
    """Base class for every error this project raises on purpose."""


class InvalidAmountError(ExpenseTrackerError):
    """Amount is not a number, is zero or negative, or is too large."""


class InvalidCategoryError(ExpenseTrackerError):
    """Category is empty or too long."""


class InvalidDateError(ExpenseTrackerError):
    """A date or month could not be understood."""


class TransactionNotFoundError(ExpenseTrackerError):
    """No transaction exists with the requested id."""


class StorageError(ExpenseTrackerError):
    """The CSV file could not be read or written."""
