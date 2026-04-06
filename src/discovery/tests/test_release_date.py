from __future__ import annotations

import pytest

from discovery.release_date import normalize_published_date_string


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("2010", "2010-01-01"),
        ("2010-03", "2010-03-01"),
        ("2010-03-15", "2010-03-15"),
        ("1999-12-31", "1999-12-31"),
        ("2001-01", "2001-01-01"),
        ("1980 junk", "1980-01-01"),
    ],
)
def test_normalize_published_date_string(raw: str | None, expected: str | None) -> None:
    assert normalize_published_date_string(raw) == expected


def test_normalize_rejects_bad_month() -> None:
    assert normalize_published_date_string("2010-13-01") is None
