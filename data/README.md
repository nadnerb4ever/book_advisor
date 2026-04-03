# Local persisted data

Files in this directory are **machine-local** and **not committed** (except this `README.md`). Document every artifact you add here: what it is, how it is produced, and what reads it.

| File | Purpose | How it is generated | Used by |
|------|---------|----------------------|---------|
| **`goodreads_library_export.csv`** | Your full Goodreads library export (shelves, ratings, reviews, dates). | You download it from Goodreads: **My Books → Import and export → Export library**, then save or copy the file here with this name. | [`GoodreadsLibraryClient`](../src/goodreads/client.py), `book-advisor reading_history`, and (planned) discovery `update`. |
| **`discovery/candidates.sqlite`** | SQLite database of discovered candidate books. | Will be created/updated by **`book-advisor discovery update`** once that command exists. | **`book-advisor discovery list`** (planned). |

Update this table when you add new persisted files under `data/`.
