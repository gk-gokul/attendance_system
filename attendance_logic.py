import datetime

# Change this to adjust the late arrival cutoff time
LATE_CUTOFF = datetime.time(9, 0)


def get_attendance_status(checkin_time: datetime.datetime, cutoff: datetime.time = LATE_CUTOFF) -> str:
    """Return 'Late' if checkin_time is after cutoff, else 'On Time'."""
    return "Late" if checkin_time.time() > cutoff else "On Time"


def build_csv_row(name: str, timestamp: str, photo_path: str, status: str) -> list:
    """Build a CSV row for the attendance log."""
    return [name, timestamp, photo_path, status]
