from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def default_goodreads_csv() -> Path:
    return repo_root() / "data" / "goodreads_library_export.csv"


def default_discovery_db() -> Path:
    return repo_root() / "data" / "discovery" / "candidates.sqlite"


def default_google_books_api_key_file() -> Path:
    return repo_root() / "data" / "google_books_api_key"
