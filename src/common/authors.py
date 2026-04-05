from __future__ import annotations

from collections.abc import Iterable, Sequence

from reading_history.goodreads_export.models import LibraryExportRow


def author_display_variants(display: str) -> frozenset[str]:
    """Lowercase spellings that identify the same person for loose matching.

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


def author_text_matches_query(author_text: str, query: str) -> bool:
    """True if ``author_text`` and ``query`` refer to the same person (variant rules)."""
    q = query.strip()
    if not q:
        return False
    return bool(author_display_variants(author_text) & author_display_variants(q))


def filter_canonical_author_names(names: Sequence[str], query: str) -> list[str]:
    """Return members of ``names`` matching ``query``, preserving order.

    Raises:
        ValueError: if ``query`` is empty or whitespace-only.
    """
    needle = query.strip()
    if not needle:
        msg = "author query must be a non-empty string"
        raise ValueError(msg)
    want = author_display_variants(needle)
    return [n for n in names if want & author_display_variants(n)]


def format_known_strings_preview(values: Sequence[str], *, limit: int = 12) -> str:
    """Comma-separated repr()'d values, with ellipsis when truncated."""
    chunk = values[:limit]
    tail = " …" if len(values) > limit else ""
    return ", ".join(repr(v) for v in chunk) + tail


def unique_primary_author_names(books: Iterable[LibraryExportRow]) -> list[str]:
    """Distinct primary ``author`` strings from rows, stable sorted order.

    Uses the export's primary ``author`` field only (not ``additional_authors``).
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
