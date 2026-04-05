from __future__ import annotations

from discovery.authors import author_display_variants


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
