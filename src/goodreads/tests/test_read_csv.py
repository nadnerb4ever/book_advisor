from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from goodreads.read_csv import parse_library_csv


def test_parse_library_csv_fixture(goodreads_export_csv: Path) -> None:
    rows = parse_library_csv(goodreads_export_csv)
    assert len(rows) == 3

    r0 = rows[0]
    assert r0.book_id == 1
    assert r0.title == "Prueba 🐍"
    assert r0.author == "Anna Author"
    assert r0.author_lf == "Author, Anna"
    assert r0.isbn == "1234567890"
    assert r0.isbn13 == "9780000000001"
    assert r0.my_rating == 5
    assert r0.average_rating == pytest.approx(4.25)
    assert r0.publisher == "Example Press"
    assert r0.binding == "Paperback"
    assert r0.number_of_pages == 300
    assert r0.year_published == 2020
    assert r0.original_publication_year == 2019
    assert r0.date_read == date(2024, 1, 15)
    assert r0.date_added == date(2023, 12, 1)
    assert r0.bookshelves == "fantasy, read"
    assert r0.exclusive_shelf == "read"
    assert r0.my_review == "Line one\nLine two"
    assert r0.read_count == 1

    r1 = rows[1]
    assert r1.book_id == 2
    assert r1.exclusive_shelf == "to-read"
    assert r1.my_rating is None

    r2 = rows[2]
    assert r2.book_id == 3
    assert r2.exclusive_shelf == "read"
    assert r2.my_rating is None


def test_utf8_bom_accepted(goodreads_export_csv: Path, tmp_path: Path) -> None:
    path = tmp_path / "library.csv"
    body = goodreads_export_csv.read_text(encoding="utf-8")
    path.write_bytes("\ufeff".encode("utf-8") + body.encode("utf-8"))
    rows = parse_library_csv(path)
    assert rows[0].title == "Prueba 🐍"


def test_parse_empty_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    assert parse_library_csv(path) == []


def test_parse_header_only_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "header.csv"
    path.write_text("Book Id,Title,Author\n", encoding="utf-8")
    assert parse_library_csv(path) == []


def test_invalid_book_id_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "Book Id,Title,Author\n"
        "not-an-id,X,Y\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid 'Book Id'"):
        parse_library_csv(path)
