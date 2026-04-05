from __future__ import annotations

from pathlib import Path


def workspace_root() -> Path:
    """Book Advisor repo root (directory that contains ``src`` and ``data``)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def default_google_books_api_key_path() -> Path:
    """Default location for the on-disk API key file (gitignored)."""
    return workspace_root() / "data" / "google_books_api_key"


def read_api_key_from_file(path: Path | None = None) -> str | None:
    """First non-empty, non-comment line from the key file, or ``None`` if missing/empty."""
    key_path = path if path is not None else default_google_books_api_key_path()
    if not key_path.is_file():
        return None
    text = key_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return None
