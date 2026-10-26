"""Lets the tests import the project modules (app files live one folder up)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
