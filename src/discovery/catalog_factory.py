from __future__ import annotations

from discovery.catalog import AuthorWorksCatalog
from discovery.google_books.paths import default_google_books_api_key_path, read_api_key_from_file
from discovery.models import CatalogBackend


class MissingGoogleBooksApiKeyError(Exception):
    """Raised when Google Books is requested but no API key could be resolved."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def resolve_google_books_api_key(cli_or_env_key: str | None) -> str | None:
    if cli_or_env_key is not None and cli_or_env_key.strip():
        return cli_or_env_key.strip()
    return read_api_key_from_file()


def build_author_works_catalog(
    catalog_name: str,
    *,
    google_api_key: str | None,
) -> AuthorWorksCatalog:
    backend = CatalogBackend(catalog_name)
    if backend is CatalogBackend.OPEN_LIBRARY:
        from discovery.open_library import OpenLibraryCatalog

        return OpenLibraryCatalog()
    if backend is CatalogBackend.GOOGLE_BOOKS:
        key = resolve_google_books_api_key(google_api_key)
        if not key:
            key_file = default_google_books_api_key_path()
            msg = (
                "Google Books catalog requires an API key. Set GOOGLE_BOOKS_API_KEY, "
                f"put the key in {key_file} (first non-comment line), pass "
                "--google-api-key, or use --catalog open_library."
            )
            raise MissingGoogleBooksApiKeyError(msg)
        from discovery.google_books import GoogleBooksCatalog

        return GoogleBooksCatalog(key)
    raise AssertionError(f"Unhandled catalog {backend!r}")
