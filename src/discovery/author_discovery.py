from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from pathlib import Path

from common.authors import (
    filter_canonical_author_names,
    format_known_strings_preview,
    unique_primary_author_names,
)
from reading_history import GoodreadsLibraryClient
from reading_history.goodreads_export.models import LibraryExportRow
from discovery.catalog import AuthorWorksCatalog
from discovery.catalog_factory import build_author_works_catalog
from discovery.models import DiscoveredCandidate


def _authors_restricted_to_only(
    authors: list[str],
    only_author: str,
) -> list[str]:
    """Return shelf ``Author`` strings that match ``only_author`` (see ``common.authors``)."""
    needle = only_author.strip()
    if not needle:
        msg = "only_author must be a non-empty string"
        raise ValueError(msg)
    matches = filter_canonical_author_names(authors, needle)
    if not matches:
        preview = format_known_strings_preview(authors)
        msg = (
            f"No read-shelf primary author matches {needle!r} "
            f"(try the exact `Author` column text, or natural vs 'Last, First' order). "
            f"Known authors: {preview}"
        )
        raise ValueError(msg)
    return matches


def discover_author_based_candidates(
    read_books: Iterable[LibraryExportRow],
    catalog: AuthorWorksCatalog,
    *,
    pause_between_authors_sec: float = 1.0,
    logger: Callable[[str], None] | None = None,
    only_author: str | None = None,
) -> list[DiscoveredCandidate]:
    """Collect candidates for each distinct primary author on the read shelf.

    Deduplicates by (catalog, external_id) across all authors.

    If ``only_author`` is set, only that name is queried (must match a primary
    author string from the read shelf, case-insensitive).
    """
    authors = unique_primary_author_names(read_books)
    if only_author is not None:
        authors = _authors_restricted_to_only(authors, only_author)
        if logger:
            logger(f"Single-author mode: querying only {authors[0]!r}.")
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


def shelf_author_names_for_discovery(
    csv_path: Path,
    only_author: str | None,
) -> list[str]:
    """Distinct read-shelf primary author strings, optionally filtered by ``--author``."""
    books = load_read_books(csv_path)
    authors = unique_primary_author_names(books)
    if only_author is not None:
        authors = _authors_restricted_to_only(authors, only_author)
    return authors


def run_author_discovery_to_list(
    csv_path: Path,
    *,
    catalog: AuthorWorksCatalog | None = None,
    pause_between_authors_sec: float = 1.0,
    logger: Callable[[str], None] | None = None,
    only_author: str | None = None,
) -> list[DiscoveredCandidate]:
    """Load Goodreads read shelf and return merged author-based candidates."""
    if logger:
        logger(f"Loading read shelf from {csv_path} …")
    books = load_read_books(csv_path)
    n_read = len(books)
    if logger:
        logger(f"Found {n_read} book(s) on the read shelf.")
    cat = catalog if catalog is not None else build_author_works_catalog()
    return discover_author_based_candidates(
        books,
        cat,
        pause_between_authors_sec=pause_between_authors_sec,
        logger=logger,
        only_author=only_author,
    )
