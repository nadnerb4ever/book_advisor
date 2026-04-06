from __future__ import annotations

from pathlib import Path

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_ROOT: Path = WORKSPACE_ROOT / "data"

GOOGLE_BOOKS_API_KEY_PATH: Path = DATA_ROOT / "google_books_api_key"
GOODREADS_LIBRARY_EXPORT_CSV: Path = DATA_ROOT / "goodreads_library_export.csv"
DISCOVERY_CANDIDATES_SQLITE: Path = DATA_ROOT / "discovery" / "candidates.sqlite"
