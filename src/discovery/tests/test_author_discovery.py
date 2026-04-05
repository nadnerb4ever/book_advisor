from __future__ import annotations

from pathlib import Path

from reading_history.goodreads_export.models import LibraryExportRow

from discovery.author_discovery import discover_author_based_candidates
from discovery.models import (
    SOURCE_AUTHOR_BASED,
    CatalogBackend,
    DiscoveredCandidate,
)


class FakeCatalog:
    def __init__(self, by_author: dict[str, list[DiscoveredCandidate]]) -> None:
        self._by_author = by_author

    def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
        return list(self._by_author.get(author_name, []))


def test_dedupes_across_authors_by_catalog_and_external_id() -> None:
    shared = DiscoveredCandidate(
        title="Shared Work",
        author="Any",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/works/OL1W",
        publication_year=2010,
    )
    books = [
        LibraryExportRow(
            book_id=1,
            title="R1",
            author="Alice",
            exclusive_shelf="read",
        ),
        LibraryExportRow(
            book_id=2,
            title="R2",
            author="Bob",
            exclusive_shelf="read",
        ),
    ]
    cat = FakeCatalog(
        {
            "Alice": [shared],
            "Bob": [shared],
        }
    )
    out = discover_author_based_candidates(
        books,
        cat,
        pause_between_authors_sec=0.0,
    )
    assert len(out) == 1
    assert out[0].external_id == "/works/OL1W"


def test_unique_authors_sorted_and_merged() -> None:
    w1 = DiscoveredCandidate(
        title="W1",
        author="A",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/w1",
        publication_year=None,
    )
    w2 = DiscoveredCandidate(
        title="W2",
        author="B",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/w2",
        publication_year=None,
    )
    books = [
        LibraryExportRow(
            book_id=1,
            title="x",
            author="Zed",
            exclusive_shelf="read",
        ),
        LibraryExportRow(
            book_id=2,
            title="y",
            author="Amy",
            exclusive_shelf="read",
        ),
    ]
    cat = FakeCatalog({"Amy": [w1], "Zed": [w2]})
    out = discover_author_based_candidates(
        books,
        cat,
        pause_between_authors_sec=0.0,
    )
    assert [c.external_id for c in out] == ["/w1", "/w2"]


def test_only_author_matches_when_shelf_author_is_last_comma_first() -> None:
    books = [
        LibraryExportRow(
            book_id=1,
            title="Storm Front",
            author="Butcher, Jim",
            exclusive_shelf="read",
        ),
    ]

    class TrackCatalog:
        def __init__(self) -> None:
            self.seen: list[str] = []

        def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
            self.seen.append(author_name)
            return []

    cat = TrackCatalog()
    discover_author_based_candidates(
        books,
        cat,
        only_author="Jim Butcher",
        pause_between_authors_sec=0.0,
    )
    assert cat.seen == ["Butcher, Jim"]


def test_only_author_matches_when_user_enters_last_comma_first() -> None:
    books = [
        LibraryExportRow(
            book_id=1,
            title="Storm Front",
            author="Jim Butcher",
            exclusive_shelf="read",
        ),
    ]

    class TrackCatalog:
        def __init__(self) -> None:
            self.seen: list[str] = []

        def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
            self.seen.append(author_name)
            return []

    cat = TrackCatalog()
    discover_author_based_candidates(
        books,
        cat,
        only_author="Butcher, Jim",
        pause_between_authors_sec=0.0,
    )
    assert cat.seen == ["Jim Butcher"]


def test_only_author_restricts_to_matching_shelf_name() -> None:
    books = [
        LibraryExportRow(
            book_id=1,
            title="A",
            author="Alice Munro",
            exclusive_shelf="read",
        ),
        LibraryExportRow(
            book_id=2,
            title="B",
            author="Bob",
            exclusive_shelf="read",
        ),
    ]

    class TrackCatalog:
        def __init__(self) -> None:
            self.seen: list[str] = []

        def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
            self.seen.append(author_name)
            return []

    cat = TrackCatalog()
    discover_author_based_candidates(
        books,
        cat,
        only_author="alice munro",
        pause_between_authors_sec=0.0,
    )
    assert cat.seen == ["Alice Munro"]


def test_only_author_unknown_raises() -> None:
    books = [
        LibraryExportRow(
            book_id=1,
            title="A",
            author="Only One",
            exclusive_shelf="read",
        ),
    ]

    try:
        discover_author_based_candidates(
            books,
            FakeCatalog({}),
            only_author="Nobody",
            pause_between_authors_sec=0.0,
        )
    except ValueError as e:
        assert "Nobody" in str(e)
        assert "Only One" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_run_author_discovery_to_list_uses_csv_and_catalog(tmp_path: Path) -> None:
    from discovery.author_discovery import run_author_discovery_to_list

    csv = tmp_path / "lib.csv"
    csv.write_text(
        "Book Id,Title,Author,Author l-f,Additional Authors,ISBN,ISBN13,My Rating,"
        "Average Rating,Publisher,Binding,Number of Pages,Year Published,"
        "Original Publication Year,Date Read,Date Added,Bookshelves,Bookshelves with positions,"
        "Exclusive Shelf,My Review,Spoiler,Private Notes,Read Count,Owned Copies\n"
        '1,"Hello","Ada Lovelace",,,,,,,,,,,,,,,,read,,,,,\n',
        encoding="utf-8",
    )

    ada_book = DiscoveredCandidate(
        title="Lovelace Bio",
        author="Ada Lovelace",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/works/ada",
        publication_year=2020,
    )

    class AdaOnly:
        def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
            assert author_name == "Ada Lovelace"
            return [ada_book]

    out = run_author_discovery_to_list(
        csv,
        catalog=AdaOnly(),
        pause_between_authors_sec=0.0,
    )
    assert out == [ada_book]
