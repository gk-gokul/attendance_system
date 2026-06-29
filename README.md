# attendance_system

A webcam-based sign-in kiosk for recording student attendance. Students
check in from a list, a photo is captured, and the arrival is logged to a
CSV file with an automatic "On Time" / "Late" status.

## Contents

- `sign_in_kiosk.py` — PyQt6 kiosk application (camera, student list, CSV log).
- `sing_in_updated.py` — updated kiosk UI with name formatting and animations.
- `attendance_logic.py` — pure logic for late detection and CSV row building.
- `students.txt` — roster of student names, one per line.
- `tests/` — pytest suite for `attendance_logic.py`.

## Running the tests

```bash
pip install pytest
pytest tests/ -v
```

Tests run automatically on push and pull requests via GitHub Actions (`.github/workflows`).
