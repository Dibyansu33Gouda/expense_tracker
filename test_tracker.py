"""Automated tests. Run with:  python test_tracker.py"""

import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

import logger as logger_module
from exceptions import (
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    TransactionNotFoundError,
)
from manager import ExpenseManager
from reports import ReportGenerator
from storage import CSVStorage, MemoryStorage
from transaction import Expense, Income, Transaction

# Send log lines to a temp file so tests do not fill the real log.
_temp_log_dir = tempfile.TemporaryDirectory()
logger_module.logger.path = Path(_temp_log_dir.name) / "test_log.txt"


class TestTransaction(unittest.TestCase):
    def test_amount_validation(self):
        for bad in (0, -5, "abc", "nan", "inf", None, 10**9):
            with self.assertRaises(InvalidAmountError, msg=str(bad)):
                Expense(bad, "Food")

    def test_category_is_cleaned_and_checked(self):
        self.assertEqual(Expense(10, "  food  ").category, "Food")
        with self.assertRaises(InvalidCategoryError):
            Expense(10, "   ")
        with self.assertRaises(InvalidCategoryError):
            Expense(10, "x" * 40)

    def test_date_parsing(self):
        self.assertEqual(Expense(10, "Food", "2026-10-19").txn_date, date(2026, 10, 19))
        with self.assertRaises(InvalidDateError):
            Expense(10, "Food", "19/10/2026")

    def test_signed_amount_polymorphism(self):
        self.assertEqual(Expense(100, "Food").signed_amount(), -100)
        self.assertEqual(Income(100, "Gift").signed_amount(), 100)
        with self.assertRaises(NotImplementedError):
            Transaction(100, "Food").signed_amount()

    def test_sorting_uses_lt(self):
        a = Expense(10, "Food", "2026-10-05", txn_id=1)
        b = Expense(10, "Food", "2026-10-01", txn_id=2)
        self.assertEqual(sorted([a, b]), [b, a])

    def test_equality_compares_content(self):
        self.assertEqual(Expense(10, "Food", "2026-10-01"), Expense(10, "food", "2026-10-01"))
        self.assertNotEqual(Expense(10, "Food", "2026-10-01"), Income(10, "Food", "2026-10-01"))

    def test_from_row_picks_subclass(self):
        row = {"id": "3", "type": "Income", "date": "2026-10-01",
               "category": "Gift", "amount": "50", "note": ""}
        self.assertIsInstance(Transaction.from_row(row), Income)


class TestManager(unittest.TestCase):
    def setUp(self):
        self.manager = ExpenseManager(MemoryStorage())

    def test_add_assigns_incrementing_ids(self):
        first = self.manager.add("expense", 50, "Food", "2026-10-01")
        second = self.manager.add("income", 500, "Gift", "2026-10-02")
        self.assertEqual((first.txn_id, second.txn_id), (1, 2))

    def test_totals_and_breakdown(self):
        self.manager.add("income", 1000, "Pocket Money", "2026-10-01")
        self.manager.add("expense", 300, "Food", "2026-10-02")
        self.manager.add("expense", 100, "Food", "2026-10-03")
        self.manager.add("expense", 50, "Books", "2026-10-04")
        totals = self.manager.totals(self.manager.all())
        self.assertEqual(totals, {"income": 1000, "expense": 450, "balance": 550})
        self.assertEqual(
            self.manager.category_breakdown(self.manager.all()),
            {"Food": 400, "Books": 50},
        )

    def test_delete_and_missing_id(self):
        txn = self.manager.add("expense", 50, "Food")
        self.manager.delete(txn.txn_id)
        self.assertEqual(len(self.manager), 0)
        with self.assertRaises(TransactionNotFoundError):
            self.manager.delete(99)

    def test_month_filter_and_search(self):
        self.manager.add("expense", 50, "Food", "2026-09-30", "late dinner")
        self.manager.add("expense", 60, "Food", "2026-10-01", "breakfast")
        self.assertEqual(len(self.manager.for_month(2026, 10)), 1)
        self.assertEqual(len(self.manager.search("DINNER")), 1)

    def test_bad_type_rejected(self):
        with self.assertRaises(Exception):
            self.manager.add("gift", 5, "Food")


class TestCSVStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "data.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(CSVStorage(self.path).load(), [])

    def test_round_trip_survives_restart(self):
        manager = ExpenseManager(CSVStorage(self.path))
        manager.add("expense", 99.5, "Food", "2026-10-01", "note, with comma")
        reloaded = ExpenseManager(CSVStorage(self.path))
        self.assertEqual(len(reloaded), 1)
        self.assertEqual(reloaded.all()[0].note, "note, with comma")

    def test_corrupted_rows_are_skipped(self):
        self.path.write_text(
            "id,type,date,category,amount,note\n"
            "1,Expense,2026-10-01,Food,50.00,ok\n"
            "2,Expense,not-a-date,Food,50.00,bad date\n"
            "3,Expense,2026-10-02,Food,-5,negative\n"
            "4,Loan,2026-10-02,Food,5,unknown type\n"
            "x,Expense,2026-10-02,Food,5,bad id\n"
            "5,Income\n",
            encoding="utf-8",
        )
        loaded = CSVStorage(self.path).load()
        self.assertEqual([t.txn_id for t in loaded], [1])

    def test_garbage_file_does_not_crash_the_load(self):
        self.path.write_bytes(b"\xff\xfe\x00\x00garbage\x81")
        with self.assertRaises(Exception) as ctx:
            CSVStorage(self.path).load()
        self.assertEqual(type(ctx.exception).__name__, "StorageError")


class TestReports(unittest.TestCase):
    def test_export_creates_two_csv_files(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = ExpenseManager(MemoryStorage())
            manager.add("income", 1000, "Gift", "2026-10-01")
            manager.add("expense", 250, "Food", "2026-10-02")
            reports = ReportGenerator(manager, report_dir=Path(folder))
            tx_path, summary_path = reports.export_month(2026, 10)
            with open(summary_path, newline="") as file:
                rows = list(csv.reader(file))
            self.assertEqual(rows[1], ["Food", "250.00", "100.0"])
            self.assertTrue(tx_path.exists())

    def test_empty_month_raises(self):
        reports = ReportGenerator(ExpenseManager(MemoryStorage()))
        with self.assertRaises(Exception):
            reports.monthly_summary(2026, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
