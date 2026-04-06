from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

SOURCE_AUTHOR_BASED = "author_based"


class CatalogBackend(StrEnum):
    """Which external catalog produced a candidate row."""

    GOOGLE_BOOKS = "google_books"
    # Persisted by older runs only; discovery no longer queries this backend.
    OPEN_LIBRARY = "open_library"


@dataclass(frozen=True, slots=True)
class AuthorRefreshState:
    """Per-author progress for a catalog (pagination cursor + refresh metadata)."""

    catalog: CatalogBackend
    author: str
    resume_cursor: int
    complete: bool
    last_completed_at: str | None
    last_attempt_at: str | None
    updated_at: str


@dataclass(frozen=True, slots=True)
class DiscoveredCandidate:
    """A book surfaced by discovery (not yet ranked)."""

    title: str
    author: str
    source: str
    catalog: CatalogBackend
    external_id: str
    publication_year: int | None
    release_date: str | None = None
    raw_json: str | None = None
