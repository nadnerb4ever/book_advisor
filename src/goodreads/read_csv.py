from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any

from goodreads.models import LibraryExportRow

_CSV_ENCODING = "utf-8-sig"


def _strip_cell(value: str | None) -> str | None:
    if value is None:
        return None
    s = value.strip()
    return s if s else None


def _parse_optional_int(raw: str | None) -> int | None:
    s = _strip_cell(raw)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_optional_float(raw: str | None) -> float | None:
    s = _strip_cell(raw)
    if s is None:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_optional_date(raw: str | None) -> date | None:
    s = _strip_cell(raw)
    if s is None:
        return None
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_my_rating(raw: str | None) -> int | None:
    value = _parse_optional_int(raw)
    if value is None or value <= 0:
        return None
    return value


def _normalize_header(name: str) -> str:
    return name.strip()


def _row_from_mapping(row: dict[str, Any]) -> LibraryExportRow:
    normalized = {_normalize_header(k): v for k, v in row.items()}

    def cell(key: str) -> str | None:
        val = normalized.get(key)
        if val is None:
            return None
        if not isinstance(val, str):
            return str(val)
        return val

    book_id_raw = cell("Book Id")
    if book_id_raw is None or not book_id_raw.strip():
        msg = "Row missing required 'Book Id'"
        raise ValueError(msg)
    try:
        book_id = int(book_id_raw.strip())
    except ValueError as exc:
        msg = f"Invalid 'Book Id': {book_id_raw!r}"
        raise ValueError(msg) from exc

    title = cell("Title") or ""
    author = cell("Author") or ""

    return LibraryExportRow(
        book_id=book_id,
        title=title,
        author=author,
        author_lf=_strip_cell(cell("Author l-f")),
        additional_authors=_strip_cell(cell("Additional Authors")),
        isbn=_strip_cell(cell("ISBN")),
        isbn13=_strip_cell(cell("ISBN13")),
        my_rating=_parse_my_rating(cell("My Rating")),
        average_rating=_parse_optional_float(cell("Average Rating")),
        publisher=_strip_cell(cell("Publisher")),
        binding=_strip_cell(cell("Binding")),
        number_of_pages=_parse_optional_int(cell("Number of Pages")),
        year_published=_parse_optional_int(cell("Year Published")),
        original_publication_year=_parse_optional_int(cell("Original Publication Year")),
        date_read=_parse_optional_date(cell("Date Read")),
        date_added=_parse_optional_date(cell("Date Added")),
        bookshelves=_strip_cell(cell("Bookshelves")),
        exclusive_shelf=_strip_cell(cell("Exclusive Shelf")),
        my_review=_strip_cell(cell("My Review")),
        spoiler=_strip_cell(cell("Spoiler")),
        private_notes=_strip_cell(cell("Private Notes")),
        read_count=_parse_optional_int(cell("Read Count")),
        owned_copies=_parse_optional_int(cell("Owned Copies")),
    )


def parse_library_csv(path: str | Path) -> list[LibraryExportRow]:
    """Parse a Goodreads desktop library CSV file (e.g. `goodreads_library_export.csv`) into rows."""
    p = Path(path)
    with p.open(newline="", encoding=_CSV_ENCODING) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return []
        return [_row_from_mapping(dict(row)) for row in reader]
