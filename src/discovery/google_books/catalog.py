from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

from discovery.models import (
    SOURCE_AUTHOR_BASED,
    CatalogBackend,
    DiscoveredCandidate,
)

_VOLUMES_URL = "https://www.googleapis.com/books/v1/volumes"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_PAGE_SIZE = 40
_DEFAULT_MAX_VOLUMES_PER_AUTHOR = 400
_DEFAULT_PAUSE_SEC = 0.25
_YEAR_RE = re.compile(r"^(\d{4})")


@dataclass(frozen=True, slots=True)
class AuthorPageResult:
    """One Google Books volumes list response for an author query."""

    candidates: list[DiscoveredCandidate]
    next_start_index: int
    exhausted: bool


def _google_books_http_error_message(response: requests.Response) -> str:
    """Best-effort parse of Books API JSON error for clearer CLI messages."""
    try:
        payload: Any = response.json()
        err = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(err, dict):
            msg = err.get("message")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
    except (ValueError, OSError):
        pass
    text = (response.text or "").strip()
    return text[:500] if text else ""


class GoogleBooksCatalog:
    """Google Books Volumes API — author query (`q=inauthor:"...\"`)."""

    def __init__(
        self,
        api_key: str,
        *,
        session: requests.Session | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        page_size: int = _DEFAULT_PAGE_SIZE,
        max_volumes_per_author: int = _DEFAULT_MAX_VOLUMES_PER_AUTHOR,
        pause_between_pages_sec: float = _DEFAULT_PAUSE_SEC,
    ) -> None:
        if not (api_key and api_key.strip()):
            msg = "Google Books API key is required"
            raise ValueError(msg)
        self._api_key = api_key.strip()
        self._session = session or requests.Session()
        self._timeout = timeout
        self._page_size = min(page_size, 40)
        self._max_volumes = max_volumes_per_author
        self._pause = pause_between_pages_sec

    @property
    def max_volumes_per_author(self) -> int:
        return self._max_volumes

    @property
    def pause_between_pages_sec(self) -> float:
        return self._pause

    def fetch_author_page(
        self,
        author_name: str,
        *,
        start_index: int,
    ) -> AuthorPageResult:
        """Perform a single list request; used for resumable / incremental updates."""
        resp = self._session.get(
            _VOLUMES_URL,
            params={
                "q": f'inauthor:"{author_name}"',
                "key": self._api_key,
                "maxResults": self._page_size,
                "startIndex": start_index,
            },
            timeout=self._timeout,
        )
        if not resp.ok:
            detail = _google_books_http_error_message(resp)
            base = f"Google Books API HTTP {resp.status_code}"
            raise RuntimeError(f"{base}: {detail}" if detail else base)
        data: dict[str, Any] = resp.json()
        items = data.get("items") or []
        if not items:
            return AuthorPageResult([], start_index, True)

        candidates: list[DiscoveredCandidate] = []
        seen_ids: set[str] = set()
        for item in items:
            cand = _item_to_candidate(item, author_name)
            if cand is None:
                continue
            if cand.external_id in seen_ids:
                continue
            seen_ids.add(cand.external_id)
            candidates.append(cand)

        total_items = data.get("totalItems")
        next_start = start_index + len(items)
        exhausted = isinstance(total_items, int) and next_start >= total_items
        return AuthorPageResult(candidates, next_start, exhausted)

    def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
        out: list[DiscoveredCandidate] = []
        seen_ids: set[str] = set()
        start_index = 0
        while len(out) < self._max_volumes:
            page = self.fetch_author_page(author_name, start_index=start_index)
            if not page.candidates and page.exhausted:
                break
            for cand in page.candidates:
                if len(out) >= self._max_volumes:
                    break
                if cand.external_id in seen_ids:
                    continue
                seen_ids.add(cand.external_id)
                out.append(cand)
            start_index = page.next_start_index
            if page.exhausted:
                break
            if self._pause > 0:
                time.sleep(self._pause)
        return out


def _published_year(published_date: str | None) -> int | None:
    if not published_date or not isinstance(published_date, str):
        return None
    m = _YEAR_RE.match(published_date.strip())
    if not m:
        return None
    return int(m.group(1))


def _item_to_candidate(item: dict[str, Any], query_author: str) -> DiscoveredCandidate | None:
    vid = item.get("id")
    if not isinstance(vid, str) or not vid:
        return None
    info = item.get("volumeInfo")
    if not isinstance(info, dict):
        return None
    title = info.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    author_display = query_author
    authors = info.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, str) and first.strip():
            author_display = first.strip()
    pd_raw = info.get("publishedDate")
    pd_str = pd_raw if isinstance(pd_raw, str) else None
    raw = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
    return DiscoveredCandidate(
        title=title.strip(),
        author=author_display,
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.GOOGLE_BOOKS,
        external_id=vid,
        publication_year=_published_year(pd_str),
        raw_json=raw,
    )
