from __future__ import annotations

from pathlib import Path

import pytest

from discovery.candidate_list import list_discovery_candidates
from discovery.models import (
    SOURCE_AUTHOR_BASED,
    CatalogBackend,
    DiscoveredCandidate,
)
from discovery.store import CandidateStore


def _one_row(
    *,
    author: str,
    title: str = "T",
    ext: str = "id1",
    cat: CatalogBackend = CatalogBackend.GOOGLE_BOOKS,
) -> DiscoveredCandidate:
    return DiscoveredCandidate(
        title=title,
        author=author,
        source=SOURCE_AUTHOR_BASED,
        catalog=cat,
        external_id=ext,
        publication_year=None,
    )


def test_list_without_author_respects_sql_limit(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates(
        [
            _one_row(author="A", ext="1"),
            _one_row(author="B", ext="2"),
        ]
    )
    out = list_discovery_candidates(
        db,
        source_filter=None,
        catalog_scope="all",
        author_query=None,
        limit=1,
    )
    assert out.summary_total == 2
    assert len(out.rows) == 1


def test_list_with_author_filter_and_limit(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates(
        [
            _one_row(author="Butcher, Jim", ext="1"),
            _one_row(author="Butcher, Jim", ext="2"),
            _one_row(author="Other", ext="3"),
        ]
    )
    out = list_discovery_candidates(
        db,
        source_filter=None,
        catalog_scope="all",
        author_query="Jim Butcher",
        limit=1,
    )
    assert out.summary_total == 2
    assert len(out.rows) == 1


def test_list_author_filter_no_match_raises(tmp_path: Path) -> None:
    db = tmp_path / "c.sqlite"
    store = CandidateStore(db)
    store.upsert_candidates([_one_row(author="Solo", ext="1")])
    with pytest.raises(ValueError, match="No candidates match"):
        list_discovery_candidates(
            db,
            source_filter=None,
            catalog_scope="all",
            author_query="Nobody",
            limit=None,
        )
