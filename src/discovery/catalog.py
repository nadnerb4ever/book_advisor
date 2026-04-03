from __future__ import annotations

from typing import Protocol

from discovery.models import DiscoveredCandidate


class AuthorWorksCatalog(Protocol):
    """Fetches candidate works for a human-readable author name."""

    def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
        """Return works associated with the author (may be incomplete / noisy)."""
        ...
