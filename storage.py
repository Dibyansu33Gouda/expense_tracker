"""Storage layer: where transactions live between runs.

Storage is an abstract base class. It promises that every storage has
load() and save(), but it does not say how. CSVStorage keeps data in a
file; MemoryStorage keeps it in a list (used by the tests).
"""

import csv
from abc import ABC, abstractmethod
from pathlib import Path

from config import CSV_HEADER
from exceptions import ExpenseTrackerError, StorageError
from logger import logger
from transaction import Transaction


class Storage(ABC):
    """Contract that every storage class must follow."""

    @abstractmethod
    def load(self):
        """Return a list of Transaction objects."""

    @abstractmethod
    def save(self, transactions):
        """Write the full list of transactions."""


class CSVStorage(Storage):
    """Reads and writes transactions in a CSV file."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def load(self):
        # First run: no file yet. That is normal, not an error.
        if not self.file_path.exists():
            return []

        transactions = []
        try:
            # newline="" is what the csv module asks for, otherwise
            # Windows can insert blank lines between rows.
            with open(self.file_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                # Line 1 is the header, so data starts at line 2.
                for line_number, row in enumerate(reader, start=2):
                    try:
                        transactions.append(Transaction.from_row(row))
                    except (KeyError, ValueError, TypeError, ExpenseTrackerError) as err:
                        # Skip the damaged row, keep the good ones.
                        logger.error(
                            f"Skipped row {line_number} in "
                            f"{self.file_path.name}: {err}"
                        )
        except (OSError, UnicodeDecodeError, csv.Error) as err:
            logger.error(f"Could not read {self.file_path}: {err}")
            raise StorageError(f"Could not read {self.file_path.name}: {err}") from err
        return transactions

    def save(self, transactions):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_HEADER)
                writer.writeheader()
                for transaction in transactions:
                    writer.writerow(transaction.to_row())
        except OSError as err:
            logger.error(f"Could not write {self.file_path}: {err}")
            raise StorageError(f"Could not write {self.file_path.name}: {err}") from err


class MemoryStorage(Storage):
    """Keeps transactions in a list. Nothing touches the disk."""

    def __init__(self, transactions=None):
        self._transactions = list(transactions or [])

    def load(self):
        return list(self._transactions)

    def save(self, transactions):
        self._transactions = list(transactions)
