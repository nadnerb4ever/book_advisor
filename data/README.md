# Local persisted data

Files in this directory are **machine-local** and **not committed** (except this `README.md`). Document every artifact you add here: what it is, how it is produced, and what reads it.

| File | Purpose | How it is generated | Used by |
|------|---------|----------------------|---------|
| **`goodreads_library_export.csv`** | Your full Goodreads library export (shelves, ratings, reviews, dates). | You download it from Goodreads: **My Books → Import and export → Export library**, then save or copy the file here with this name. | [`GoodreadsLibraryClient`](../src/reading_history/goodreads_export/client.py), `book-advisor reading_history`, and `book-advisor discovery update`. |
| **`google_books_api_key`** | Your [Google Books API](https://developers.google.com/books) key (optional if you set **`GOOGLE_BOOKS_API_KEY`**). | You create it in Google Cloud (see [SETUP.md](../SETUP.md)). Put the key on a **single line**; lines starting with `#` are ignored. | `book-advisor discovery update` (path: [`GOOGLE_BOOKS_API_KEY_PATH`](../src/path_constants.py); read by [`google_books/paths.py`](../src/discovery/google_books/paths.py) if env var is unset). |
| **`discovery/candidates.sqlite`** | SQLite database of discovered candidate books plus **`author_catalog_refresh`** (per-author catalog cursors / completion / timestamps for resumable updates). | Created/updated by **`book-advisor discovery update`** (Google Books). | **`book-advisor discovery list`**; **`discovery update`** resume state. |

Update this table when you add new persisted files under `data/`.
