# Discovery (`src/discovery`)

**Books of interest discovery** — this package implements the **author-based** path: authors from your reading library **read** shelf are queried against the **Google Books** catalog adapter to produce normalized **candidate** records.

## Design

- **Catalog protocol** — [`catalog.py`](catalog.py) defines `AuthorWorksCatalog` so you can swap backends or use fakes in tests.
- **Catalog identity** — [`models.py`](models.py) defines **`CatalogBackend`** (`StrEnum`): `google_books`, and **`open_library`** only for **legacy rows** already in SQLite. Each `DiscoveredCandidate` stores which backend produced the row (persisted as text in SQLite).
- **Google Books** — [`google_books/catalog.py`](google_books/catalog.py) uses the [Volumes API](https://developers.google.com/books/docs/v1/using) with `q=inauthor:"..."`. Default key file path: [`GOOGLE_BOOKS_API_KEY_PATH`](../path_constants.py). Key resolution (`GOOGLE_BOOKS_API_KEY`, then that file) lives in [`google_books/paths.py`](google_books/paths.py); see [SETUP.md](../../SETUP.md).

Source-specific adapters live under **`discovery/<source>/`**. Service-style orchestration: [`author_discovery.py`](author_discovery.py), [`catalog_factory.py`](catalog_factory.py), [`candidate_list.py`](candidate_list.py), [`discovery_update.py`](discovery_update.py). See CSR layering in [`../book_advisor/ARCHITECTURE.md`](../book_advisor/ARCHITECTURE.md). **Author filter semantics** use [`../common/authors.py`](../common/authors.py).

## Persistence

Candidate SQLite lives under **repo-root [`data/discovery/candidates.sqlite`](../../data/README.md)** (gitignored). The DB also stores **`author_catalog_refresh`** (per-catalog author cursors and last-attempt times) so **`discovery update`** can resume after quota limits. See [`data/README.md`](../../data/README.md).

## CLI

Wired from [`book_advisor/run.py`](../book_advisor/run.py): `book-advisor discovery update` and `discovery list`. Full flags: **`book-advisor discovery update --help`**.
