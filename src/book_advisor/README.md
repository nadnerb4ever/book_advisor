# `book_advisor`

**System overview:** [ARCHITECTURE.md](ARCHITECTURE.md) describes how Book Advisor is intended to work end-to-end (reading library, parallel discovery paths, ranking, recommendation, and future researcher / interactive layers).

This package holds the **runnable application**: entrypoints, wiring, and glue that turn the rest of the codebase into something you can actually run. It **binds** domain logic, adapters, and infrastructure into a single coherent program.

Put supporting libraries and isolated concerns in sibling packages under `src/`; keep orchestration and app-specific composition here.

## CLI

After `pip install -e .`, run **`book-advisor`** (or `python -m book_advisor.run`). Paths below are relative to the **repo root** unless you override them.

| Command | Purpose |
|--------|---------|
| `book-advisor reading_history` | Print each **read**-shelf book’s **author**, title, and your star rating from the Goodreads export CSV. |
| `book-advisor discovery update` | Load authors from the read shelf, query **Google Books**, and **upsert** candidates into SQLite (resumable paging and per-author state in the same DB). |
| `book-advisor discovery list` | Print stored discovery candidates (author, year, title, catalog id, source). |

**Common options**

- **`reading_history --csv PATH`** — Goodreads export file (default: `data/goodreads_library_export.csv`).
- **`discovery update --csv PATH`** — same CSV default as above.
- **Google Books API key** — set **`GOOGLE_BOOKS_API_KEY`** or **`data/google_books_api_key`** (not a CLI flag); see [SETUP.md](../../SETUP.md).
- **`discovery update --author NAME`** — only query one primary author from the read shelf (case-insensitive exact match); for manual testing.
- **`discovery update --max-authors N`** — process at most **N** authors per run (incomplete / stale first).
- **`discovery update --max-api-requests N`** — stop after **N** catalog HTTP requests (e.g. Google Books list pages); re-run to resume.
- **`discovery update --db PATH`** — SQLite database (default: `data/discovery/candidates.sqlite`).
- **`discovery list --db PATH`** — same database default as above.
- **`discovery list --source TAG`** — filter rows (e.g. `author_based`).
- **`discovery list --limit N`** — cap how many rows are printed.
- **`discovery list --catalog google_books|open_library|all`** — filter by catalog (`open_library` only useful for **legacy** rows from older DBs).

Use **`book-advisor --help`** or **`book-advisor COMMAND --help`** for full option text.
