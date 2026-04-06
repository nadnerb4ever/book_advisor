from __future__ import annotations

from pathlib import Path

from discovery.models import AuthorRefreshState, CatalogBackend
from discovery.store import CandidateStore


def test_select_authors_never_attempted_before_attempted(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.init_schema()
    now = "2026-01-15T12:00:00+00:00"
    store.put_author_refresh_state(
        AuthorRefreshState(
            catalog=CatalogBackend.GOOGLE_BOOKS,
            author="Amy",
            resume_cursor=0,
            complete=False,
            last_completed_at=None,
            last_attempt_at=now,
            updated_at=now,
        )
    )
    shelf = ["Zed", "Amy"]
    out = store.select_authors_for_run(CatalogBackend.GOOGLE_BOOKS, shelf, limit=None)
    assert out == ["Zed", "Amy"]


def test_select_authors_oldest_attempt_first(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    for name, ts in [("Bob", "2026-01-10T00:00:00+00:00"), ("Amy", "2026-01-01T00:00:00+00:00")]:
        store.put_author_refresh_state(
            AuthorRefreshState(
                catalog=CatalogBackend.GOOGLE_BOOKS,
                author=name,
                resume_cursor=0,
                complete=False,
                last_completed_at=None,
                last_attempt_at=ts,
                updated_at=ts,
            )
        )
    shelf = ["Bob", "Amy"]
    out = store.select_authors_for_run(CatalogBackend.GOOGLE_BOOKS, shelf, limit=None)
    assert out == ["Amy", "Bob"]


def test_select_authors_skips_complete(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    now = "2026-01-15T12:00:00+00:00"
    store.put_author_refresh_state(
        AuthorRefreshState(
            catalog=CatalogBackend.GOOGLE_BOOKS,
            author="Done",
            resume_cursor=0,
            complete=True,
            last_completed_at=now,
            last_attempt_at=now,
            updated_at=now,
        )
    )
    shelf = ["Done", "Todo"]
    out = store.select_authors_for_run(CatalogBackend.GOOGLE_BOOKS, shelf, limit=None)
    assert out == ["Todo"]


def test_select_authors_respects_limit(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    shelf = ["C", "A", "B"]
    out = store.select_authors_for_run(CatalogBackend.GOOGLE_BOOKS, shelf, limit=2)
    assert out == ["A", "B"]
