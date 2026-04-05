from __future__ import annotations

import re

import requests
import responses

from discovery.google_books.catalog import GoogleBooksCatalog
from discovery.models import SOURCE_AUTHOR_BASED, CatalogBackend


@responses.activate
def test_works_by_author_maps_volumes() -> None:
    responses.add(
        responses.GET,
        re.compile(r"https://www\.googleapis\.com/books/v1/volumes\?.*"),
        json={
            "totalItems": 2,
            "items": [
                {
                    "id": "vol1",
                    "volumeInfo": {
                        "title": "Sample Title",
                        "authors": ["Jane Q. Author"],
                        "publishedDate": "2019-03-15",
                    },
                },
                {
                    "id": "vol2",
                    "volumeInfo": {
                        "title": "Second",
                        "authors": ["Other"],
                    },
                },
            ],
        },
        status=200,
    )
    sess = requests.Session()
    cat = GoogleBooksCatalog("fake-key", session=sess)  # noqa: S106
    out = cat.works_by_author("Jane Doe")
    assert len(out) == 2
    assert out[0].external_id == "vol1"
    assert out[0].title == "Sample Title"
    assert out[0].author == "Jane Q. Author"
    assert out[0].catalog is CatalogBackend.GOOGLE_BOOKS
    assert out[0].source == SOURCE_AUTHOR_BASED
    assert out[0].publication_year == 2019
    assert out[1].publication_year is None


@responses.activate
def test_works_by_author_stops_on_empty_page_when_total_items_omitted() -> None:
    base = "https://www.googleapis.com/books/v1/volumes"
    q = 'inauthor:"Pat Author"'
    responses.add(
        responses.GET,
        base,
        match=[
            responses.matchers.query_param_matcher(
                {"q": q, "key": "fake-key", "maxResults": "40", "startIndex": "0"},
            ),
        ],
        json={
            "items": [
                {
                    "id": f"p{i}",
                    "volumeInfo": {"title": f"T{i}", "authors": ["Pat Author"]},
                }
                for i in range(10)
            ],
        },
        status=200,
    )
    responses.add(
        responses.GET,
        base,
        match=[
            responses.matchers.query_param_matcher(
                {"q": q, "key": "fake-key", "maxResults": "40", "startIndex": "10"},
            ),
        ],
        json={"items": []},
        status=200,
    )
    cat = GoogleBooksCatalog(
        "fake-key",  # noqa: S106
        session=requests.Session(),
        pause_between_pages_sec=0,
    )
    out = cat.works_by_author("Pat Author")
    assert len(out) == 10


@responses.activate
def test_works_by_author_paginates_when_first_page_short_of_max_results() -> None:
    """API may return e.g. 20 volumes when maxResults=40; follow totalItems + startIndex."""
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
            "totalItems": 25,
            "items": [
                {
                    "id": f"id{i}",
                    "volumeInfo": {"title": f"Book {i}", "authors": ["A"]},
                }
                for i in range(20)
            ],
        },
        status=200,
    )
    responses.add(
        responses.GET,
        base,
        match=[
            responses.matchers.query_param_matcher(
                {"q": q, "key": "fake-key", "maxResults": "40", "startIndex": "20"},
            ),
        ],
        json={
            "totalItems": 25,
            "items": [
                {
                    "id": f"id{i}",
                    "volumeInfo": {"title": f"Book {i}", "authors": ["A"]},
                }
                for i in range(20, 25)
            ],
        },
        status=200,
    )
    cat = GoogleBooksCatalog(
        "fake-key",  # noqa: S106
        session=requests.Session(),
        pause_between_pages_sec=0,
    )
    out = cat.works_by_author("Jane Doe")
    assert len(out) == 25
    assert out[0].external_id == "id0"
    assert out[-1].external_id == "id24"


def test_google_books_catalog_rejects_blank_key() -> None:
    try:
        GoogleBooksCatalog("   ")  # noqa: S106
    except ValueError as e:
        assert "key" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")


@responses.activate
def test_works_by_author_surfaces_api_error_message() -> None:
    responses.add(
        responses.GET,
        re.compile(r"https://www\.googleapis\.com/books/v1/volumes\?.*"),
        json={"error": {"code": 400, "message": "API key expired. Please renew the API key."}},
        status=400,
    )
    cat = GoogleBooksCatalog("fake-key", session=requests.Session())  # noqa: S106
    try:
        cat.works_by_author("Anyone")
    except RuntimeError as e:
        assert "400" in str(e)
        assert "API key expired" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
