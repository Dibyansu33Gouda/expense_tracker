"""Error logging to a text file (file handling: append mode)."""

from datetime import datetime

from config import LOG_FILE


class FileLogger:
    """Appends timestamped lines to a log file."""

    def __init__(self, path):
        self.path = path

    def _write(self, level, message):
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} [{level}] {message}\n"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # "a" = append. Old log lines stay, new ones go at the end.
            with open(self.path, "a", encoding="utf-8") as file:
                file.write(line)
        except OSError:
            # A broken logger must never take the whole program down.
            pass

    def info(self, message):
        self._write("INFO", message)

    def error(self, message):
        self._write("ERROR", message)


# One shared logger that other modules import.
logger = FileLogger(LOG_FILE)
