from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.authors import author_text_matches_query

from discovery.models import CatalogBackend, DiscoveredCandidate
from discovery.store import CandidateStore


@dataclass(frozen=True, slots=True)
class ListedCandidates:
    """Result of listing discovery candidates with optional author filter."""

    rows: list[DiscoveredCandidate]
    summary_total: int


def list_discovery_candidates(
    db_path: Path,
    *,
    source_filter: str | None,
    catalog_scope: str,
    author_query: str | None,
    limit: int | None,
) -> ListedCandidates:
    """Load candidates from the store; optional author filter uses ``common.authors`` rules.

    Raises:
        ValueError: if ``author_query`` is set and no rows match after filtering.
    """
    if catalog_scope == "all":
        catalog_filter: CatalogBackend | None = None
    else:
        catalog_filter = CatalogBackend(catalog_scope)

    store = CandidateStore(db_path)

    if author_query is None:
        total = store.count(source=source_filter, catalog=catalog_filter)
        rows = list(
            store.iter_candidates(
                source=source_filter,
                catalog=catalog_filter,
                limit=limit,
            )
        )
        return ListedCandidates(rows=rows, summary_total=total)

    rows = list(
        store.iter_candidates(
            source=source_filter,
            catalog=catalog_filter,
            limit=None,
        )
    )
    filtered = [c for c in rows if author_text_matches_query(c.author, author_query)]
    total = len(filtered)
    if total == 0:
        msg = (
            f"No candidates match author {author_query!r} with the current "
            "catalog/source filters."
        )
        raise ValueError(msg)
    if limit is not None:
        filtered = filtered[:limit]
    return ListedCandidates(rows=filtered, summary_total=total)
