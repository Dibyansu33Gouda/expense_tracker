"""Small input helpers used by the menu."""

from datetime import datetime

from exceptions import ExpenseTrackerError, InvalidDateError


def ask(prompt, validator=None, default=None):
    """Keep asking until the validator accepts the answer.

    validator: a function that returns the cleaned value or raises an
               ExpenseTrackerError. The rules live in the model, not here.
    default:   returned when the user just presses Enter.
    """
    while True:
        text = input(prompt).strip()
        if not text and default is not None:
            return default
        try:
            return validator(text) if validator else text
        except ExpenseTrackerError as err:
            print(f"  Invalid input: {err}")


def parse_month(text):
    """'2026-10' -> (2026, 10)"""
    try:
        parsed = datetime.strptime(text.strip(), "%Y-%m")
    except ValueError:
        raise InvalidDateError("Use YYYY-MM, for example 2026-10.") from None
    return parsed.year, parsed.month


def parse_id(text):
    try:
        number = int(text)
    except ValueError:
        raise ExpenseTrackerError("Enter the id as a whole number.") from None
    if number <= 0:
        raise ExpenseTrackerError("Ids start at 1.")
    return number


def parse_yes_no(text):
    answer = text.strip().lower()
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    raise ExpenseTrackerError("Type y or n.")
