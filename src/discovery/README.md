# Discovery (`src/discovery`)

**Books of interest discovery** — this package implements the **author-based** path: authors from your Goodreads **read** shelf are queried against a **catalog adapter** to produce normalized **candidate** records.

## Design

- **Catalog protocol** — [`catalog.py`](catalog.py) defines `AuthorWorksCatalog` so you can swap Open Library for Google Books, fixtures in tests, etc.
- **Default v1 backend** — [`open_library/catalog.py`](open_library/catalog.py) uses the [Open Library Search API](https://openlibrary.org/dev/docs/api/search) (`/search.json?author=...`). It requires **no API key** and is easy to call from automation. Data quality and latency vary; treat results as **candidates** to be ranked later, not guaranteed matches. Source-specific adapters live under **`discovery/<source>/`** (e.g. `open_library/`); shared types and orchestration stay at the `discovery/` package root.
- **Author extraction** — [`authors.py`](authors.py) uses the export’s primary **`author`** field only for v1 (not `additional_authors`).

## Persistence

Candidate SQLite lives under **repo-root [`data/discovery/candidates.sqlite`](../../data/README.md)** (gitignored). See [`data/README.md`](../../data/README.md) for how it is produced and consumed.

## CLI

- `book-advisor discovery update` — refresh candidates from your export and upsert into SQLite.
- `book-advisor discovery list` — print stored candidates (optional `--source`, `--limit`).
