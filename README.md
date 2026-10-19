# Expense Tracker (CLI)

A command-line program that records income and expenses, saves them in a
CSV file, and prints or exports monthly reports. Written in plain Python
(no external libraries) to practise intermediate OOP and file handling.

## Run it

    python main.py            # start the program
    python test_tracker.py    # run the 18 automated tests

Needs Python 3.8 or newer. Run both commands from inside this folder.

## Folder layout

    expense_tracker/
    |-- main.py          entry point: creates the objects, starts the menu
    |-- config.py        paths and constants
    |-- exceptions.py    custom exception classes
    |-- transaction.py   Transaction, Expense, Income
    |-- storage.py       Storage (abstract), CSVStorage, MemoryStorage
    |-- manager.py       ExpenseManager: add, delete, filter, totals
    |-- reports.py       ReportGenerator: text summary and CSV export
    |-- menu.py          Menu: all printing and input
    |-- utils.py         input helpers
    |-- logger.py        FileLogger: appends errors to logs/error_log.txt
    |-- test_tracker.py  unit tests
    |-- data/transactions.csv   saved data (sample rows included)
    |-- reports/         exported monthly CSV files appear here
    `-- logs/            error_log.txt appears here

Delete the rows in data/transactions.csv (keep the header line) to start
with an empty tracker.

## Where each concept lives

| Concept | File |
|---|---|
| Encapsulation, @property, static and class methods | transaction.py |
| Inheritance and method overriding | transaction.py (Expense, Income) |
| Dunder methods (__str__, __repr__, __eq__, __lt__) | transaction.py |
| Abstract base class and polymorphism | storage.py |
| Composition | manager.py (holds a Storage), main.py |
| Custom exceptions | exceptions.py, used everywhere |
| File handling (read, write, append, csv module) | storage.py, reports.py, logger.py |

Dates are typed as YYYY-MM-DD and months as YYYY-MM.
