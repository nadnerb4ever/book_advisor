# Goodreads export (`reading_history/goodreads_export`)

This subpackage reads the **official Goodreads desktop CSV export** (`goodreads_library_export.csv`): shelves, **star ratings**, **review text**, and dates—the same source many migration tools use, without scraping live HTML.

## Usage

Keep your personal file at **`data/goodreads_library_export.csv`** (repo root). See [`data/README.md`](../../../data/README.md).

```python
from pathlib import Path

from reading_history.goodreads_export import GoodreadsLibraryClient

client = GoodreadsLibraryClient.from_path(Path("~/Downloads/goodreads_library_export.csv"))
for book in client.read_books():
    print(book.title, book.my_rating)
```

Lower-level parsing:

```python
from reading_history.goodreads_export import parse_library_csv

rows = parse_library_csv("goodreads_library_export.csv")
```

## Tests

Tests and fixtures live under [`tests/`](tests/). From the repository root, run `pytest` (see root [`README.md`](../../../README.md) and [`pyproject.toml`](../../../pyproject.toml)).

[`book_advisor`](../../book_advisor/README.md) is the runnable app; import **`reading_history`** (or this subpackage) as a **sibling** library, not nested inside the app package.
