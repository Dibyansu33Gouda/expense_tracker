"""Project-wide settings.

Every path and constant lives here, so no other file has a hard-coded
"data/transactions.csv" string. Change a value once and the whole
project follows.
"""

from pathlib import Path

# Path(__file__) is this file. resolve().parent is the project folder,
# so the program works no matter which directory you run it from.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

DATA_FILE = DATA_DIR / "transactions.csv"
LOG_FILE = LOG_DIR / "error_log.txt"

CSV_HEADER = ["id", "type", "date", "category", "amount", "note"]
DATE_FORMAT = "%Y-%m-%d"
CURRENCY = "Rs."
MAX_AMOUNT = 10_000_000
MAX_CATEGORY_LENGTH = 15
