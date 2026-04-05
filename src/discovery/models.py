from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

SOURCE_AUTHOR_BASED = "author_based"


class CatalogBackend(StrEnum):
    """Which external catalog produced a candidate row."""

    GOOGLE_BOOKS = "google_books"
    OPEN_LIBRARY = "open_library"


@dataclass(frozen=True, slots=True)
class DiscoveredCandidate:
    """A book surfaced by discovery (not yet ranked)."""

    title: str
    author: str
    source: str
    catalog: CatalogBackend
    external_id: str
    publication_year: int | None
    raw_json: str | None = None
