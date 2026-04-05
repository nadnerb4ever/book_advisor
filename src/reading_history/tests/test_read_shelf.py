from __future__ import annotations

from pathlib import Path

import pytest

from reading_history.read_shelf import load_read_shelf_books

_FIXTURE_CSV = (
    Path(__file__).resolve().parent.parent
    / "goodreads_export"
    / "tests"
    / "fixtures"
    / "goodreads_library_export.csv"
)


def test_load_read_shelf_without_filter() -> None:
    books = load_read_shelf_books(_FIXTURE_CSV, author_query=None)
    assert {b.book_id for b in books} == {1, 3}


def test_load_read_shelf_author_filter_natural_matches_export() -> None:
    books = load_read_shelf_books(_FIXTURE_CSV, author_query="Anna Author")
    assert len(books) == 1
    assert books[0].book_id == 1


def test_load_read_shelf_author_filter_no_match_raises() -> None:
    with pytest.raises(ValueError, match="No read-shelf books match"):
        load_read_shelf_books(_FIXTURE_CSV, author_query="Nobody Here")
