# Book Advisor

This project uses **personal reading history** and **reviews** to produce **personalized book recommendations**. The goal is to learn from what you have read and how you rated or described those books, then suggest titles that fit your tastes.

**Status:** Early planning—repository initialized for future development.

**Python:** Target **3.14.x** (see `requires-python` in [`pyproject.toml`](pyproject.toml) and [`.python-version`](.python-version)). Application code lives under [`src/`](src/).

**Local data:** Persisted files (exports, databases) live under [`data/`](data/); see [`data/README.md`](data/README.md). Only that README is tracked; other paths are gitignored.

**Architecture:** See the intent-level overview in [`src/book_advisor/ARCHITECTURE.md`](src/book_advisor/ARCHITECTURE.md).
