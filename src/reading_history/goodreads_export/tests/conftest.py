from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def goodreads_export_csv() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "goodreads_library_export.csv"
