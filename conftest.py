"""Make repo-root modules (attendance_logic) importable under ``pytest tests/``."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
