from __future__ import annotations

import re
from pathlib import Path

import requests
import responses

from discovery.discovery_update import run_discovery_update
from discovery.models import CatalogBackend


def _minimal_read_csv(author: str = "Jane Doe") -> str:
    return (
        "Book Id,Title,Author,Author l-f,Additional Authors,ISBN,ISBN13,My Rating,"
        "Average Rating,Publisher,Binding,Number of Pages,Year Published,"
        "Original Publication Year,Date Read,Date Added,Bookshelves,Bookshelves with positions,"
        "Exclusive Shelf,My Review,Spoiler,Private Notes,Read Count,Owned Copies\n"
        f'1,"Hello","{author}",,,,,,,,,,,,,,,,read,,,,,\n'
    )


@responses.activate
def test_max_api_requests_saves_resume_cursor(tmp_path: Path) -> None:
    csv_path = tmp_path / "lib.csv"
    csv_path.write_text(_minimal_read_csv(), encoding="utf-8")
    db_path = tmp_path / "c.sqlite"
    base = "https://www.googleapis.com/books/v1/volumes"
    q = 'inauthor:"Jane Doe"'
    responses.add(
        responses.GET,
        base,
        match=[
            responses.matchers.query_param_matcher(
                {"q": q, "key": "fake-key", "maxResults": "40", "startIndex": "0"},
            ),
        ],
        json={
            "totalItems": 50,
            "items": [
                {
                    "id": f"id{i}",
                    "volumeInfo": {"title": f"T{i}", "authors": ["Jane Doe"]},
                }
                for i in range(2)
            ],
        },
        status=200,
    )
    responses.add(
        responses.GET,
        base,
        match=[
            responses.matchers.query_param_matcher(
                {"q": q, "key": "fake-key", "maxResults": "40", "startIndex": "2"},
            ),
        ],
        json={"totalItems": 50, "items": [{"id": "last", "volumeInfo": {"title": "Z", "authors": ["Jane Doe"]}}]},
        status=200,
    )

    result = run_discovery_update(
        csv_path=csv_path,
        out_db=db_path,
        catalog_name=CatalogBackend.GOOGLE_BOOKS.value,
        google_api_key="fake-key",  # noqa: S106
        only_author=None,
        logger=None,
        max_authors=None,
        max_api_requests=1,
        pause_between_authors_sec=0.0,
    )

    assert result.upserted_rows == 2
    assert result.resume_message is not None
    assert "max-api-requests" in result.resume_message.lower() or "API request" in result.resume_message

    from discovery.store import CandidateStore

    store = CandidateStore(db_path)
    st = store.get_author_refresh_state(CatalogBackend.GOOGLE_BOOKS, "Jane Doe")
    assert st is not None
    assert st.resume_cursor == 2
    assert st.complete is False


@responses.activate
def test_incremental_completes_author_and_marks_complete(tmp_path: Path) -> None:
    csv_path = tmp_path / "lib.csv"
    csv_path.write_text(_minimal_read_csv(), encoding="utf-8")
    db_path = tmp_path / "c.sqlite"
    responses.add(
        responses.GET,
        re.compile(r"https://www\.googleapis\.com/books/v1/volumes\?.*"),
        json={
            "totalItems": 1,
            "items": [
                {
                    "id": "only",
                    "volumeInfo": {"title": "One", "authors": ["Jane Doe"]},
                },
            ],
        },
        status=200,
    )

    result = run_discovery_update(
        csv_path=csv_path,
        out_db=db_path,
        catalog_name=CatalogBackend.GOOGLE_BOOKS.value,
        google_api_key="fake-key",  # noqa: S106
        only_author=None,
        logger=None,
        max_authors=None,
        max_api_requests=None,
        pause_between_authors_sec=0.0,
    )

    assert result.upserted_rows == 1
    from discovery.store import CandidateStore

    store = CandidateStore(db_path)
    st = store.get_author_refresh_state(CatalogBackend.GOOGLE_BOOKS, "Jane Doe")
    assert st is not None
    assert st.complete is True
    assert st.resume_cursor == 0
