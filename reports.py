"""Reports: a text summary on screen and CSV files on disk."""

import calendar
import csv

from config import CSV_HEADER, CURRENCY, REPORT_DIR
from exceptions import ExpenseTrackerError, StorageError
from transaction import Expense


class ReportGenerator:
    def __init__(self, manager, report_dir=REPORT_DIR):
        self.manager = manager
        self.report_dir = report_dir

    def _month_data(self, year, month):
        transactions = self.manager.for_month(year, month)
        if not transactions:
            raise ExpenseTrackerError(
                f"No transactions found for {calendar.month_name[month]} {year}."
            )
        return transactions

    def monthly_summary(self, year, month):
        """Return the summary as a printable string."""
        transactions = self._month_data(year, month)
        totals = self.manager.totals(transactions)
        breakdown = self.manager.category_breakdown(transactions)
        title = f"{calendar.month_name[month]} {year}"

        lines = [
            f"===== Report: {title} =====",
            f"Transactions : {len(transactions)}",
            f"Income       : {CURRENCY} {totals['income']:,.2f}",
            f"Expenses     : {CURRENCY} {totals['expense']:,.2f}",
            f"Balance      : {CURRENCY} {totals['balance']:+,.2f}",
            "",
            "Spending by category",
        ]
        if breakdown:
            for category, amount in breakdown.items():
                share = amount / totals["expense"] * 100
                lines.append(f"  {category:<16}{amount:>12,.2f}  {share:5.1f}%")
            expenses = [t for t in transactions if isinstance(t, Expense)]
            biggest = max(expenses, key=lambda t: t.amount)
            lines.append("")
            lines.append(
                f"Biggest expense: {biggest.category} on "
                f"{biggest.txn_date.isoformat()}, {CURRENCY} {biggest.amount:,.2f}"
            )
        else:
            lines.append("  No expenses this month.")
        return "\n".join(lines)

    def export_month(self, year, month):
        """Write two CSV files for the month and return their paths."""
        transactions = self._month_data(year, month)
        breakdown = self.manager.category_breakdown(transactions)
        total_spent = sum(breakdown.values())
        stamp = f"{year}_{month:02d}"

        transactions_path = self.report_dir / f"transactions_{stamp}.csv"
        summary_path = self.report_dir / f"category_summary_{stamp}.csv"

        try:
            self.report_dir.mkdir(parents=True, exist_ok=True)

            with open(transactions_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_HEADER)
                writer.writeheader()
                for t in transactions:
                    writer.writerow(t.to_row())

            with open(summary_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["category", "total_spent", "percent_of_spending"])
                for category, amount in breakdown.items():
                    percent = round(amount / total_spent * 100, 1)
                    writer.writerow([category, f"{amount:.2f}", percent])
        except OSError as err:
            raise StorageError(f"Could not write report files: {err}") from err

        return transactions_path, summary_path
