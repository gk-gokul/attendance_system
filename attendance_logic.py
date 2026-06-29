import csv
import datetime

# Change this to adjust the late arrival cutoff time
LATE_CUTOFF = datetime.time(9, 0)


def get_attendance_status(checkin_time: datetime.datetime, cutoff: datetime.time = LATE_CUTOFF) -> str:
    """Return 'Late' if checkin_time is after cutoff, else 'On Time'."""
    return "Late" if checkin_time.time() > cutoff else "On Time"


def build_csv_row(name: str, timestamp: str, photo_path: str, status: str) -> list:
    """Build a CSV row for the attendance log."""
    return [name, timestamp, photo_path, status]


def append_log_row(log_file: str, name: str, timestamp: str, photo_path: str, status: str) -> list:
    """Append a single 4-column attendance row to ``log_file`` and return it.

    Uses :func:`build_csv_row` so the column order is single-sourced. Opening in
    append mode keeps any pre-existing 3-column log intact — no header rewrite or
    migration — so this stays backward-compatible with older logs.
    """
    row = build_csv_row(name, timestamp, photo_path, status)
    with open(log_file, "a", newline="") as f:
        csv.writer(f).writerow(row)
    return row
