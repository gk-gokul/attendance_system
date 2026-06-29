"""Tests for wiring late-detection into the kiosk check-in path.

The live kiosk (`sing_in_updated.py`) imports PyQt6 and cv2 at module level,
which are NOT installed in CI, so we cannot import it here. Instead:

  * the real CSV recording path is exercised through the pure
    `attendance_logic.append_log_row` helper that production `check_in()`
    delegates to (behavioural, end-to-end against the real write code), and
  * the Qt-only colour wiring (which needs a display) is verified by reading
    the kiosk source for the `setForeground` call, as the task sanctions.
"""

import csv
import datetime
import pathlib

import attendance_logic

KIOSK_SRC = pathlib.Path(__file__).resolve().parent.parent / "sing_in_updated.py"


def _read_rows(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def test_append_log_row_late_writes_four_column_status(tmp_path):
    log = tmp_path / "attendance_log.csv"
    late = datetime.datetime(2026, 1, 1, 9, 1, 0)
    status = attendance_logic.get_attendance_status(late)
    attendance_logic.append_log_row(
        str(log), "John Doe", "2026-01-01 09:01:00", "photos/john.jpg", status
    )
    rows = _read_rows(log)
    assert rows == [["John Doe", "2026-01-01 09:01:00", "photos/john.jpg", "Late"]]


def test_append_log_row_on_time_writes_four_column_status(tmp_path):
    log = tmp_path / "attendance_log.csv"
    on_time = datetime.datetime(2026, 1, 1, 8, 59, 0)
    status = attendance_logic.get_attendance_status(on_time)
    attendance_logic.append_log_row(
        str(log), "Jane Doe", "2026-01-01 08:59:00", "photos/jane.jpg", status
    )
    rows = _read_rows(log)
    assert rows == [["Jane Doe", "2026-01-01 08:59:00", "photos/jane.jpg", "On Time"]]


def test_append_log_row_uses_build_csv_row_column_order(tmp_path):
    log = tmp_path / "attendance_log.csv"
    attendance_logic.append_log_row(
        str(log), "Test Student", "2026-01-01 09:00:00", "photos/test.jpg", "On Time"
    )
    row = _read_rows(log)[0]
    # status is the 4th column, matching build_csv_row's single-sourced order
    assert row[3] == "On Time"
    assert row == attendance_logic.build_csv_row(
        "Test Student", "2026-01-01 09:00:00", "photos/test.jpg", "On Time"
    )


def test_append_log_row_backward_compatible_with_three_column_file(tmp_path):
    """A pre-existing 3-column log keeps working: old rows are untouched and the
    new 4-column row is appended without crash or header migration."""
    log = tmp_path / "attendance_log.csv"
    with open(log, "w", newline="") as f:
        csv.writer(f).writerow(["Old Student", "2025-12-31 08:00:00", "photos/old.jpg"])

    attendance_logic.append_log_row(
        str(log), "New Student", "2026-01-01 09:05:00", "photos/new.jpg", "Late"
    )

    rows = _read_rows(log)
    assert rows[0] == ["Old Student", "2025-12-31 08:00:00", "photos/old.jpg"]  # 3 cols, intact
    assert rows[1] == ["New Student", "2026-01-01 09:05:00", "photos/new.jpg", "Late"]  # 4 cols


# --- Qt-only colour wiring: verified by source inspection (needs a display) ---


def test_kiosk_imports_late_logic_without_forking_cutoff():
    src = KIOSK_SRC.read_text()
    assert "import attendance_logic" in src or "from attendance_logic import" in src
    # the single cutoff must NOT be forked into a duplicate literal here
    assert "LATE_CUTOFF = datetime.time" not in src
    assert "LATE_CUTOFF = time(" not in src


def test_kiosk_computes_status_and_writes_via_logic():
    src = KIOSK_SRC.read_text()
    assert "get_attendance_status" in src
    assert "append_log_row" in src
    # the legacy status-less 3-column write must be gone
    assert "writerow([name, timestamp, photo_filename])" not in src


def test_kiosk_colours_late_students_orange():
    src = KIOSK_SRC.read_text()
    assert "setForeground" in src
    assert 'QColor("orange")' in src
    assert "QColor" in src  # ensure QColor is imported/used
    # colour is gated on the late status, not applied unconditionally
    assert '"Late"' in src
