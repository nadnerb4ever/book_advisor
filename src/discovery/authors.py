from __future__ import annotations

from collections.abc import Iterable

from reading_history.goodreads_export.models import LibraryExportRow


def author_display_variants(display: str) -> frozenset[str]:
    """Lowercase spellings that identify the same primary author string from the export.

    Goodreads ``Author`` is sometimes natural order (``Jim Butcher``) and sometimes
    ``Last, First`` (``Butcher, Jim``). Matching compares the union of these forms.
    """
    s = " ".join(display.strip().split())
    if not s:
        return frozenset()
    out: set[str] = {s.lower()}
    if "," in s:
        last, _, rest = s.partition(",")
        last_n = " ".join(last.strip().split())
        first_n = " ".join(rest.strip().split())
        if first_n and last_n:
            out.add(f"{first_n} {last_n}".lower())
    return frozenset(out)


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
