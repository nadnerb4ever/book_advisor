from __future__ import annotations

import pytest

from common.authors import (
    author_display_variants,
    author_text_matches_query,
    filter_canonical_author_names,
    format_known_strings_preview,
    unique_primary_author_names,
)
from reading_history.goodreads_export.models import LibraryExportRow


def test_author_display_variants_natural_and_last_first_overlap() -> None:
    a = author_display_variants("Butcher, Jim")
    b = author_display_variants("Jim Butcher")
    assert a & b
    assert "jim butcher" in a
    assert "butcher, jim" in a


def test_author_display_variants_normalizes_whitespace() -> None:
    assert author_display_variants("  Jim   Butcher  ") == author_display_variants("Jim Butcher")


def test_author_display_variants_empty() -> None:
    assert author_display_variants("") == frozenset()
    assert author_display_variants("   ") == frozenset()


def test_author_text_matches_query() -> None:
    assert author_text_matches_query("Butcher, Jim", "Jim Butcher")
    assert author_text_matches_query("Jim Butcher", "jim butcher")
    assert not author_text_matches_query("Alice Munro", "Jim Butcher")
    assert not author_text_matches_query("Jim Butcher", "")


def test_filter_canonical_author_names_order_preserved() -> None:
    names = ["Zed", "Butcher, Jim", "Amy"]
    assert filter_canonical_author_names(names, "Jim Butcher") == ["Butcher, Jim"]


def test_filter_canonical_author_names_empty_query_raises() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        filter_canonical_author_names(["A"], "  ")


def test_format_known_strings_preview_truncates() -> None:
    s = format_known_strings_preview(["a", "b", "c"], limit=2)
    assert "'a', 'b' …" == s


def test_unique_primary_author_names_sorted_unique() -> None:
    books = [
        LibraryExportRow(book_id=1, title="x", author="Zed", exclusive_shelf="read"),
        LibraryExportRow(book_id=2, title="y", author="Amy", exclusive_shelf="read"),
        LibraryExportRow(book_id=3, title="z", author="Zed", exclusive_shelf="read"),
    ]
    assert unique_primary_author_names(books) == ["Amy", "Zed"]
