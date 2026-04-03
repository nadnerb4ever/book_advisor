# `goodreads`

Goodreads **no longer offers a public API** (shutdown for new consumers around 2020). Mature PyPI clients such as [betterreads](https://pypi.org/project/betterreads/) wrapped that XML/REST API and are **retired or unmaintained**, so they are not a dependable base for new work. Community **HTML scrapers** tend to break with site changes and sit in a gray area with respect to terms of service.

This package is **first-party**: it reads the **official desktop CSV export** (`goodreads_library_export.csv`), which includes shelves, **star ratings**, **review text**, and dates—the same source serious migration tools use, without chasing live HTML.

## Getting an export

On the Goodreads website (desktop): **My Books → Import and export → Export library**. Save the file locally.

## Usage

```python
from pathlib import Path
from goodreads import GoodreadsLibraryClient

client = GoodreadsLibraryClient.from_path(Path("~/Downloads/goodreads_library_export.csv"))
for book in client.read_books():
    print(book.title, book.my_rating, book.my_review)
```

Lower-level parsing without the client wrapper:

```python
from goodreads import parse_library_csv

rows = parse_library_csv("goodreads_library_export.csv")
```

## Tests

Automated tests for this package live under [`tests/`](tests/) (i.e. `src/goodreads/tests/`). From the repository root, run `python3.14 -m pytest` after `pip install -e ".[dev]"` (see the root [`README.md`](../../README.md) and [`pyproject.toml`](../../pyproject.toml)).

## Relationship to `book_advisor`

[`book_advisor`](../book_advisor/README.md) is the runnable application package. Import `goodreads` as a **sibling** library for recommendation signals (read books, ratings, reviews) without nesting this adapter inside the app package.
