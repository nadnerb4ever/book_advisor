from __future__ import annotations

from path_constants import GOOGLE_BOOKS_API_KEY_PATH

from discovery.catalog import AuthorWorksCatalog
from discovery.google_books.paths import read_google_books_api_key


class MissingGoogleBooksApiKeyError(Exception):
    """Raised when Google Books is requested but no API key could be resolved."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def build_author_works_catalog() -> AuthorWorksCatalog:
    key = read_google_books_api_key()
    if not key:
        msg = (
            "Google Books catalog requires an API key. Set GOOGLE_BOOKS_API_KEY or "
            f"put the key in {GOOGLE_BOOKS_API_KEY_PATH} (first non-comment line)."
        )
        raise MissingGoogleBooksApiKeyError(msg)
    from discovery.google_books import GoogleBooksCatalog

    return GoogleBooksCatalog(key)
