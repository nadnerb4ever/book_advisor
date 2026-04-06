from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from discovery.author_discovery import shelf_author_names_for_discovery
from discovery.catalog_factory import build_author_works_catalog
from discovery.google_books.catalog import GoogleBooksCatalog
from discovery.models import AuthorRefreshState, CatalogBackend
from discovery.store import CandidateStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class DiscoveryUpdateResult:
    upserted_rows: int
    authors_targeted: int
    resume_message: str | None = None


def run_discovery_update(
    *,
    csv_path: Path,
    out_db: Path,
    only_author: str | None,
    logger: Callable[[str], None] | None,
    max_authors: int | None = None,
    max_api_requests: int | None = None,
    pause_between_authors_sec: float = 1.0,
) -> DiscoveryUpdateResult:
    """Resumable author-based discovery via Google Books: per-page API calls and cursors.

    Raises:
        MissingGoogleBooksApiKeyError: from ``build_author_works_catalog`` when key missing.
    """
    backend = CatalogBackend.GOOGLE_BOOKS
    store = CandidateStore(out_db)
    authors = shelf_author_names_for_discovery(csv_path, only_author)
    if not authors:
        if logger:
            logger("No primary authors on the read shelf; nothing to query.")
        return DiscoveryUpdateResult(0, 0, None)

    to_process = store.select_authors_for_run(backend, authors, limit=max_authors)
    if not to_process:
        if logger:
            logger(
                "No authors to process (all complete for this catalog), "
                "or --max-authors produced an empty batch."
            )
        return DiscoveryUpdateResult(0, 0, None)

    if logger:
        cap = f", max {max_authors} author(s)" if max_authors is not None else ""
        logger(
            f"Processing {len(to_process)} author(s) for {backend.value}{cap} "
            f"(incomplete / stale first)."
        )

    cat = build_author_works_catalog()
    if not isinstance(cat, GoogleBooksCatalog):
        msg = f"Expected GoogleBooksCatalog for {backend!r}, got {type(cat)!r}"
        raise TypeError(msg)

    gb = cat

    total_upserts = 0
    api_used = 0
    resume_message: str | None = None
    hit_api_cap = False

    for i, name in enumerate(to_process):
        if hit_api_cap:
            break
        if max_api_requests is not None and api_used >= max_api_requests:
            resume_message = (
                f"Stopped after {api_used} API request(s) (--max-api-requests). "
                "Re-run the same command to continue."
            )
            if logger:
                logger(resume_message)
            break

        row = store.get_author_refresh_state(backend, name)
        if row and row.complete:
            continue

        cursor = row.resume_cursor if row else 0
        last_completed_at = row.last_completed_at if row else None
        accumulated_session = 0

        if logger:
            logger(f"[{i + 1}/{len(to_process)}] {name} … (startIndex={cursor})")

        while True:
            if max_api_requests is not None and api_used >= max_api_requests:
                now = _utc_now_iso()
                store.put_author_refresh_state(
                    AuthorRefreshState(
                        catalog=backend,
                        author=name,
                        resume_cursor=cursor,
                        complete=False,
                        last_completed_at=last_completed_at,
                        last_attempt_at=now,
                        updated_at=now,
                    )
                )
                resume_message = (
                    f"Stopped after {api_used} API request(s) (--max-api-requests); "
                    f"progress saved for {name!r}. Re-run to continue."
                )
                if logger:
                    logger(resume_message)
                hit_api_cap = True
                break

            page = gb.fetch_author_page(name, start_index=cursor)
            api_used += 1

            n = store.upsert_candidates(page.candidates)
            total_upserts += n
            accumulated_session += len(page.candidates)
            cursor = page.next_start_index
            now = _utc_now_iso()

            if page.exhausted:
                store.put_author_refresh_state(
                    AuthorRefreshState(
                        catalog=backend,
                        author=name,
                        resume_cursor=0,
                        complete=True,
                        last_completed_at=now,
                        last_attempt_at=now,
                        updated_at=now,
                    )
                )
                if logger:
                    logger(
                        f"    → page: {len(page.candidates)} candidate(s), "
                        f"upserted {n} row(s); author complete for API."
                    )
                break

            if accumulated_session >= gb.max_volumes_per_author:
                store.put_author_refresh_state(
                    AuthorRefreshState(
                        catalog=backend,
                        author=name,
                        resume_cursor=cursor,
                        complete=False,
                        last_completed_at=last_completed_at,
                        last_attempt_at=now,
                        updated_at=now,
                    )
                )
                if logger:
                    logger(
                        f"    → reached max volumes per author ({gb.max_volumes_per_author}); "
                        f"next startIndex={cursor} saved."
                    )
                break

            store.put_author_refresh_state(
                AuthorRefreshState(
                    catalog=backend,
                    author=name,
                    resume_cursor=cursor,
                    complete=False,
                    last_completed_at=last_completed_at,
                    last_attempt_at=now,
                    updated_at=now,
                )
            )
            if logger:
                logger(
                    f"    → page: {len(page.candidates)} candidate(s), "
                    f"upserted {n} row(s); next startIndex={cursor}"
                )

            if gb.pause_between_pages_sec > 0:
                time.sleep(gb.pause_between_pages_sec)

        if pause_between_authors_sec > 0 and i + 1 < len(to_process) and not hit_api_cap:
            time.sleep(pause_between_authors_sec)

    return DiscoveryUpdateResult(
        upserted_rows=total_upserts,
        authors_targeted=len(to_process),
        resume_message=resume_message,
    )
