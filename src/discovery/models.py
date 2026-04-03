from __future__ import annotations

from dataclasses import dataclass

SOURCE_AUTHOR_BASED = "author_based"
CATALOG_OPEN_LIBRARY = "open_library"


@dataclass(frozen=True, slots=True)
class DiscoveredCandidate:
    """A book surfaced by discovery (not yet ranked)."""

    title: str
    author: str
    source: str
    catalog: str
    external_id: str
    publication_year: int | None
    raw_json: str | None = None
