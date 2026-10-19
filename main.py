"""Entry point. Builds the objects and hands control to the menu."""

from config import DATA_FILE
from manager import ExpenseManager
from menu import Menu
from reports import ReportGenerator
from storage import CSVStorage


def main():
    storage = CSVStorage(DATA_FILE)       # where data lives
    manager = ExpenseManager(storage)     # the logic, using that storage
    reports = ReportGenerator(manager)    # reports, using that manager
    Menu(manager, reports).run()          # the screen, using both


if __name__ == "__main__":
    main()
