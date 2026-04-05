from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LibraryExportRow:
    """One row from Goodreads `goodreads_library_export.csv`."""

    book_id: int
    title: str
    author: str
    author_lf: str | None = None
    additional_authors: str | None = None
    isbn: str | None = None
    isbn13: str | None = None
    my_rating: int | None = None
    average_rating: float | None = None
    publisher: str | None = None
    binding: str | None = None
    number_of_pages: int | None = None
    year_published: int | None = None
    original_publication_year: int | None = None
    date_read: date | None = None
    date_added: date | None = None
    bookshelves: str | None = None
    exclusive_shelf: str | None = None
    my_review: str | None = None
    spoiler: str | None = None
    private_notes: str | None = None
    read_count: int | None = None
    owned_copies: int | None = None
