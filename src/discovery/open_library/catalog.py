from __future__ import annotations

import json
import time
from typing import Any

import requests

from discovery.models import (
    CATALOG_OPEN_LIBRARY,
    SOURCE_AUTHOR_BASED,
    DiscoveredCandidate,
)

_DEFAULT_BASE = "https://openlibrary.org"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_PAGE_SIZE = 100
_DEFAULT_MAX_WORKS_PER_AUTHOR = 400
_DEFAULT_PAUSE_SEC = 0.25


class OpenLibraryCatalog:
    """Open Library Search JSON API — author scoped (`/search.json?author=...`)."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        base_url: str = _DEFAULT_BASE,
        timeout: float = _DEFAULT_TIMEOUT,
        page_size: int = _DEFAULT_PAGE_SIZE,
        max_works_per_author: int = _DEFAULT_MAX_WORKS_PER_AUTHOR,
        pause_between_pages_sec: float = _DEFAULT_PAUSE_SEC,
    ) -> None:
        self._session = session or requests.Session()
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._page_size = min(page_size, 1000)
        self._max_works = max_works_per_author
        self._pause = pause_between_pages_sec

    def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
        out: list[DiscoveredCandidate] = []
        seen_ids: set[str] = set()
        offset = 0
        while len(out) < self._max_works:
            resp = self._session.get(
                f"{self._base}/search.json",
                params={
                    "author": author_name,
                    "limit": self._page_size,
                    "offset": offset,
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            docs = data.get("docs") or []
            if not docs:
                break
            for doc in docs:
                if len(out) >= self._max_works:
                    break
                cand = _doc_to_candidate(doc, author_name)
                if cand is None:
                    continue
                if cand.external_id in seen_ids:
                    continue
                seen_ids.add(cand.external_id)
                out.append(cand)
            if len(docs) < self._page_size:
                break
            offset += self._page_size
            if self._pause > 0:
                time.sleep(self._pause)
        return out


def _doc_to_candidate(doc: dict[str, Any], query_author: str) -> DiscoveredCandidate | None:
    key = doc.get("key")
    if not isinstance(key, str) or not key:
        return None
    title = doc.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    year: int | None = None
    fp = doc.get("first_publish_year")
    if isinstance(fp, int):
        year = fp
    author_display = query_author
    names = doc.get("author_name")
    if isinstance(names, list) and names:
        first = names[0]
        if isinstance(first, str) and first.strip():
            author_display = first.strip()
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=False)
    return DiscoveredCandidate(
        title=title.strip(),
        author=author_display,
        source=SOURCE_AUTHOR_BASED,
        catalog=CATALOG_OPEN_LIBRARY,
        external_id=key,
        publication_year=year,
        raw_json=raw,
    )
