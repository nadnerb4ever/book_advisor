from __future__ import annotations

import os

from path_constants import GOOGLE_BOOKS_API_KEY_PATH

_GOOGLE_BOOKS_API_KEY_ENV = "GOOGLE_BOOKS_API_KEY"


def _read_api_key_from_file() -> str | None:
    """First non-empty, non-comment line from the default key file, or ``None`` if missing/empty."""
    if not GOOGLE_BOOKS_API_KEY_PATH.is_file():
        return None
    text = GOOGLE_BOOKS_API_KEY_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return None


def read_google_books_api_key() -> str | None:
    """Resolve API key from environment, then default key file (repository layer only)."""
    raw = os.environ.get(_GOOGLE_BOOKS_API_KEY_ENV)
    if raw is not None and raw.strip():
        return raw.strip()
    return _read_api_key_from_file()
