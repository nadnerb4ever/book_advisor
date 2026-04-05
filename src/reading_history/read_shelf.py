from __future__ import annotations

from pathlib import Path

from common.authors import (
    author_text_matches_query,
    format_known_strings_preview,
    unique_primary_author_names,
)
from reading_history.goodreads_export import GoodreadsLibraryClient
from reading_history.goodreads_export.models import LibraryExportRow


def load_read_shelf_books(
    csv_path: Path,
    *,
    author_query: str | None,
) -> list[LibraryExportRow]:
    """Load read-shelf rows from the Goodreads export; optional author filter.

    Raises:
        ValueError: if ``author_query`` is set and no read-shelf row matches.
    """
    client = GoodreadsLibraryClient.from_path(csv_path)
    books = client.read_books()
    if author_query is None:
        return books

    shelf = books
    books = [b for b in books if author_text_matches_query(b.author, author_query)]
    if not books:
        known = unique_primary_author_names(shelf)
        preview = format_known_strings_preview(known)
        msg = (
            f"No read-shelf books match author {author_query!r} "
            f"(matches export `Author`, natural or 'Last, First' order). "
            f"Known primary authors: {preview}"
        )
        raise ValueError(msg)
    return books
