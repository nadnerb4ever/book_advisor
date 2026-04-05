from __future__ import annotations

import json
import re
import time
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

    def works_by_author(self, author_name: str) -> list[DiscoveredCandidate]:
        out: list[DiscoveredCandidate] = []
        seen_ids: set[str] = set()
        start_index = 0
        while len(out) < self._max_volumes:
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
                break
            for item in items:
                if len(out) >= self._max_volumes:
                    break
                cand = _item_to_candidate(item, author_name)
                if cand is None:
                    continue
                if cand.external_id in seen_ids:
                    continue
                seen_ids.add(cand.external_id)
                out.append(cand)
            # Google often returns fewer than maxResults (e.g. 20 when maxResults=40);
            # use totalItems and advance by actual page size, not requested page size.
            total_items = data.get("totalItems")
            start_index += len(items)
            if isinstance(total_items, int) and start_index >= total_items:
                break
            # No totalItems: keep requesting until a page returns zero items (see loop guard).
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
