from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from discovery.author_discovery import run_author_discovery_to_list
from discovery.catalog_factory import build_author_works_catalog
from discovery.store import CandidateStore


def run_discovery_update(
    *,
    csv_path: Path,
    out_db: Path,
    catalog_name: str,
    google_api_key: str | None,
    only_author: str | None,
    logger: Callable[[str], None] | None,
) -> tuple[int, int]:
    """Run author-based discovery and upsert into SQLite.

    Returns:
        ``(len(candidates), upsert_row_count)``.

    Raises:
        MissingGoogleBooksApiKeyError: from ``build_author_works_catalog`` when key missing.
        Other exceptions: from discovery or store (propagate to controller).
    """
    cat = build_author_works_catalog(
        catalog_name,
        google_api_key=google_api_key,
    )
    candidates = run_author_discovery_to_list(
        csv_path,
        catalog=cat,
        logger=logger,
        only_author=only_author,
    )
    store = CandidateStore(out_db)
    n = store.upsert_candidates(candidates)
    return len(candidates), n
