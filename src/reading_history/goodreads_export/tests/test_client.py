from __future__ import annotations

from pathlib import Path

from reading_history.goodreads_export.client import GoodreadsLibraryClient


def test_read_books_filters_exclusive_shelf(goodreads_export_csv: Path) -> None:
    client = GoodreadsLibraryClient.from_path(goodreads_export_csv)
    read = client.read_books()
    assert {b.book_id for b in read} == {1, 3}


def test_books_property_loads_rows(goodreads_export_csv: Path) -> None:
    client = GoodreadsLibraryClient.from_path(goodreads_export_csv)
    assert len(client.books) == 3


def test_load_populates_books(goodreads_export_csv: Path) -> None:
    client = GoodreadsLibraryClient.from_path(goodreads_export_csv)
    loaded = client.load()
    assert len(loaded) == 3
    assert client.books is loaded


def test_iter_books_matches_books(goodreads_export_csv: Path) -> None:
    client = GoodreadsLibraryClient.from_path(goodreads_export_csv)
    assert list(client.iter_books()) == client.books
