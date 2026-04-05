from __future__ import annotations

from collections.abc import Iterable

from reading_history.goodreads_export.models import LibraryExportRow


def unique_primary_author_names(books: Iterable[LibraryExportRow]) -> list[str]:
    """Distinct primary `author` strings from read books, stable sorted order.

    v1 uses the export's primary `author` field only (not `additional_authors`).
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for book in books:
        name = (book.author or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return sorted(ordered)
