# `reading_history`

**Purpose:** Load and represent **your personal reading history** (finished books, shelves, ratings, reviews, dates) for downstream stages such as discovery and ranking.

**Layout:** Implementation-specific adapters live in **subpackages** (e.g. [`goodreads_export/`](goodreads_export/) for the Goodreads desktop CSV). The package root re-exports the current default adapter entrypoints for convenience; prefer `reading_history.goodreads_export` imports when referencing a specific source.

See [`src/book_advisor/ARCHITECTURE.md`](../book_advisor/ARCHITECTURE.md) for how this concern fits the pipeline and how directory naming maps to architecture stages.
