import datetime
import pytest
from attendance_logic import (
    LATE_CUTOFF,
    CSV_HEADER,
    get_attendance_status,
    build_csv_row,
    build_csv_header,
)


def test_late_cutoff_is_9am():
    assert LATE_CUTOFF == datetime.time(9, 0)


def test_on_time_arrival():
    checkin = datetime.datetime(2026, 1, 1, 8, 59, 0)
    assert get_attendance_status(checkin) == "On Time"


def test_exactly_at_cutoff_is_on_time():
    checkin = datetime.datetime(2026, 1, 1, 9, 0, 0)
    assert get_attendance_status(checkin) == "On Time"


def test_late_arrival():
    checkin = datetime.datetime(2026, 1, 1, 9, 1, 0)
    assert get_attendance_status(checkin) == "Late"


def test_late_well_after_cutoff():
    checkin = datetime.datetime(2026, 1, 1, 11, 30, 0)
    assert get_attendance_status(checkin) == "Late"


def test_custom_cutoff_earlier():
    checkin = datetime.datetime(2026, 1, 1, 8, 30, 0)
    assert get_attendance_status(checkin, datetime.time(8, 0)) == "Late"
    assert get_attendance_status(checkin, datetime.time(9, 0)) == "On Time"


def test_build_csv_row_late():
    row = build_csv_row("John Doe", "2026-01-01 09:05:00", "photos/john.jpg", "Late")
    assert row == ["John Doe", "2026-01-01 09:05:00", "photos/john.jpg", "Late"]


def test_build_csv_row_on_time():
    row = build_csv_row("Jane Doe", "2026-01-01 08:55:00", "photos/jane.jpg", "On Time")
    assert row == ["Jane Doe", "2026-01-01 08:55:00", "photos/jane.jpg", "On Time"]


def test_build_csv_row_has_four_columns():
    row = build_csv_row("Test Student", "2026-01-01 09:00:00", "photos/test.jpg", "On Time")
    assert len(row) == 4


def test_csv_header_columns():
    assert build_csv_header() == ["Name", "Timestamp", "Photo", "Status"]


def test_csv_header_matches_row_width():
    header = build_csv_header()
    row = build_csv_row("Test Student", "2026-01-01 09:00:00", "photos/test.jpg", "On Time")
    assert len(header) == len(row)


def test_csv_header_constant_returns_a_copy():
    # Mutating a returned header must not corrupt the shared constant.
    build_csv_header().append("Tampered")
    assert build_csv_header() == ["Name", "Timestamp", "Photo", "Status"]
    assert CSV_HEADER == ["Name", "Timestamp", "Photo", "Status"]
