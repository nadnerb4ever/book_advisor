from __future__ import annotations

import sqlite3
from pathlib import Path

from discovery.models import (
    SOURCE_AUTHOR_BASED,
    CatalogBackend,
    DiscoveredCandidate,
)
from discovery.store import CandidateStore


def test_upsert_and_iter_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    c = DiscoveredCandidate(
        title="The Book",
        author="A. Writer",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/works/OL1W",
        publication_year=2001,
        release_date="2001-06-15",
        raw_json='{"k":1}',
    )
    assert store.upsert_candidates([c]) == 1
    rows = list(store.iter_candidates())
    assert len(rows) == 1
    assert rows[0].title == "The Book"
    assert rows[0].external_id == "/works/OL1W"
    assert rows[0].release_date == "2001-06-15"
    assert store.count() == 1
    assert store.count(source=SOURCE_AUTHOR_BASED) == 1


def test_upsert_conflict_preserves_first_seen(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    c1 = DiscoveredCandidate(
        title="Old Title",
        author="A",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/works/OL9W",
        publication_year=1999,
        raw_json=None,
    )
    store.upsert_candidates([c1])
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT first_seen_at, last_updated_at FROM candidates WHERE external_id = ?",
            ("/works/OL9W",),
        ).fetchone()
        assert row is not None
        first0, last0 = row
    c2 = DiscoveredCandidate(
        title="New Title",
        author="A",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/works/OL9W",
        publication_year=2000,
        raw_json=None,
    )
    store.upsert_candidates([c2])
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT first_seen_at, last_updated_at, title FROM candidates WHERE external_id = ?",
            ("/works/OL9W",),
        ).fetchone()
        assert row is not None
        first1, last1, title = row
    assert first1 == first0
    assert title == "New Title"
    assert last1 >= last0


def test_iter_catalog_filter(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates(
        [
            DiscoveredCandidate(
                title="G",
                author="A",
                source=SOURCE_AUTHOR_BASED,
                catalog=CatalogBackend.GOOGLE_BOOKS,
                external_id="gb1",
                publication_year=None,
            ),
            DiscoveredCandidate(
                title="O",
                author="B",
                source=SOURCE_AUTHOR_BASED,
                catalog=CatalogBackend.OPEN_LIBRARY,
                external_id="/ol1",
                publication_year=None,
            ),
        ]
    )
    assert store.count(catalog=CatalogBackend.GOOGLE_BOOKS) == 1
    assert store.count(catalog=CatalogBackend.OPEN_LIBRARY) == 1
    assert store.count() == 2
    gb = list(store.iter_candidates(catalog=CatalogBackend.GOOGLE_BOOKS))
    assert len(gb) == 1 and gb[0].title == "G"
    ol = list(store.iter_candidates(catalog=CatalogBackend.OPEN_LIBRARY))
    assert len(ol) == 1 and ol[0].title == "O"
    both = list(
        store.iter_candidates(
            source=SOURCE_AUTHOR_BASED,
            catalog=CatalogBackend.OPEN_LIBRARY,
        )
    )
    assert len(both) == 1


def test_iter_source_filter(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates(
        [
            DiscoveredCandidate(
                title="X",
                author="P",
                source=SOURCE_AUTHOR_BASED,
                catalog=CatalogBackend.OPEN_LIBRARY,
                external_id="/a",
                publication_year=None,
            ),
        ]
    )
    assert len(list(store.iter_candidates(source="other"))) == 0
    assert len(list(store.iter_candidates(source=SOURCE_AUTHOR_BASED))) == 1


def test_iter_limit(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates(
        [
            DiscoveredCandidate(
                title="B",
                author="Z",
                source=SOURCE_AUTHOR_BASED,
                catalog=CatalogBackend.OPEN_LIBRARY,
                external_id="/b",
                publication_year=None,
            ),
            DiscoveredCandidate(
                title="A",
                author="Z",
                source=SOURCE_AUTHOR_BASED,
                catalog=CatalogBackend.OPEN_LIBRARY,
                external_id="/a",
                publication_year=None,
            ),
        ]
    )
    limited = list(store.iter_candidates(limit=1))
    assert len(limited) == 1
    assert limited[0].title == "A"


def test_upsert_empty_returns_zero(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    assert store.upsert_candidates([]) == 0


def test_migration_adds_release_date_column(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE candidates (
                catalog TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                publication_year INTEGER,
                source TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_updated_at TEXT NOT NULL,
                raw_json TEXT,
                PRIMARY KEY (catalog, external_id)
            )
            """
        )
        conn.commit()

    store = CandidateStore(db)
    store.init_schema()
    c = DiscoveredCandidate(
        title="T",
        author="A",
        source=SOURCE_AUTHOR_BASED,
        catalog=CatalogBackend.OPEN_LIBRARY,
        external_id="/legacy",
        publication_year=2005,
        release_date="2005-05-01",
    )
    assert store.upsert_candidates([c]) == 1
    rows = list(store.iter_candidates())
    assert len(rows) == 1
    assert rows[0].release_date == "2005-05-01"
