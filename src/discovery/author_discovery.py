from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from pathlib import Path

from reading_history import GoodreadsLibraryClient
from reading_history.goodreads_export.models import LibraryExportRow

from discovery.authors import unique_primary_author_names
from discovery.catalog import AuthorWorksCatalog
from discovery.models import DiscoveredCandidate
from discovery.open_library import OpenLibraryCatalog


def discover_author_based_candidates(
    read_books: Iterable[LibraryExportRow],
    catalog: AuthorWorksCatalog,
    *,
    pause_between_authors_sec: float = 1.0,
    logger: Callable[[str], None] | None = None,
) -> list[DiscoveredCandidate]:
    """Collect candidates for each distinct primary author on the read shelf.

    Deduplicates by (catalog, external_id) across all authors.
    """
    authors = unique_primary_author_names(read_books)
    if logger:
        if not authors:
            logger("No primary authors on the read shelf; nothing to query.")
        else:
            logger(
                f"Querying catalog for {len(authors)} unique primary author(s) "
                f"(pause {pause_between_authors_sec:g}s between authors when > 0)."
            )
    seen: set[tuple[str, str]] = set()
    results: list[DiscoveredCandidate] = []
    for i, name in enumerate(authors):
        if logger:
            logger(f"[{i + 1}/{len(authors)}] {name} …")
        n_before = len(results)
        for c in catalog.works_by_author(name):
            key = (c.catalog, c.external_id)
            if key in seen:
                continue
            seen.add(key)
            results.append(c)
        added = len(results) - n_before
        if logger:
            logger(
                f"    → {added} new candidate(s) this author; "
                f"{len(results)} unique total so far."
            )
        if pause_between_authors_sec > 0 and i + 1 < len(authors):
            time.sleep(pause_between_authors_sec)
    if logger and authors:
        logger(f"Catalog pass finished: {len(results)} candidate(s) collected.")
    return results


def load_read_books(csv_path: Path):
    client = GoodreadsLibraryClient.from_path(csv_path)
    return client.read_books()


def run_author_discovery_to_list(
    csv_path: Path,
    *,
    catalog: AuthorWorksCatalog | None = None,
    pause_between_authors_sec: float = 1.0,
    logger: Callable[[str], None] | None = None,
) -> list[DiscoveredCandidate]:
    """Load Goodreads read shelf and return merged author-based candidates."""
    if logger:
        logger(f"Loading read shelf from {csv_path} …")
    books = load_read_books(csv_path)
    n_read = len(books)
    if logger:
        logger(f"Found {n_read} book(s) on the read shelf.")
    cat = catalog if catalog is not None else OpenLibraryCatalog()
    return discover_author_based_candidates(
        books,
        cat,
        pause_between_authors_sec=pause_between_authors_sec,
        logger=logger,
    )
