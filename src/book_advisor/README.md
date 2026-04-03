# `book_advisor`

**System overview:** [ARCHITECTURE.md](ARCHITECTURE.md) describes how Book Advisor is intended to work end-to-end (reading library, parallel discovery paths, ranking, recommendation, and future researcher / interactive layers).

This package holds the **runnable application**: entrypoints, wiring, and glue that turn the rest of the codebase into something you can actually run. It **binds** domain logic, adapters, and infrastructure into a single coherent program.

Put supporting libraries and isolated concerns in sibling packages under `src/`; keep orchestration and app-specific composition here.

## CLI

After `pip install -e .`, run **`book-advisor`** (or `python -m book_advisor.run`):

- **`reading_history`** — print each **read** book’s title and your star rating (from [`goodreads`](../goodreads/) CSV). Defaults to `src/goodreads/data/goodreads_library_export.csv`; override with `--csv PATH`.
