# `book_advisor`

**System overview:** [ARCHITECTURE.md](ARCHITECTURE.md) describes how Book Advisor is intended to work end-to-end (reading library, parallel discovery paths, ranking, recommendation, and future researcher / interactive layers).

This package holds the **runnable application**: entrypoints, wiring, and glue that turn the rest of the codebase into something you can actually run. It **binds** domain logic, adapters, and infrastructure into a single coherent program.

Put supporting libraries and isolated concerns in sibling packages under `src/`; keep orchestration and app-specific composition here.

## CLI

After `pip install -e .`, run **`book-advisor`** (or `python -m book_advisor.run`). Paths below are relative to the **repo root** unless you override them.

| Command | Purpose |
|--------|---------|
| `book-advisor reading_history` | Print each **read**-shelf book’s title and your star rating from the Goodreads export CSV. |
| `book-advisor discovery update` | Load authors from the read shelf, query Open Library for works, and **upsert** candidates into the discovery SQLite database. |
| `book-advisor discovery list` | Print stored discovery candidates (author, year, title, catalog id, source). |

**Common options**

- **`reading_history --csv PATH`** — Goodreads export file (default: `data/goodreads_library_export.csv`).
- **`discovery update --csv PATH`** — same CSV default as above.
- **`discovery update --db PATH`** — SQLite database (default: `data/discovery/candidates.sqlite`).
- **`discovery list --db PATH`** — same database default as above.
- **`discovery list --source TAG`** — filter rows (e.g. `author_based`).
- **`discovery list --limit N`** — cap how many rows are printed.

Use **`book-advisor --help`** or **`book-advisor COMMAND --help`** for full option text.
