## Cursor Cloud specific instructions

### Python version

This project requires **Python 3.14.3** (strict bounds in `pyproject.toml`). The VM uses **pyenv** (installed to `~/.pyenv`, initialized in `~/.bashrc`) with `3.14.3` set as the local version via `.python-version`.

### Virtual environment and dependencies

The virtualenv lives at `/workspace/.venv`. Activate it before any Python/CLI work:

```bash
source .venv/bin/activate
```

Install (or refresh) the project in editable mode with dev extras:

```bash
pip install -e ".[dev]"
```

### Running tests

All tests are self-contained (mocked HTTP, in-memory SQLite, local fixture CSV). No API keys, network, or external services needed:

```bash
pytest          # 60 tests, runs in <1s
```

Test paths are configured in `pyproject.toml` under `[tool.pytest.ini_options]`.

### CLI commands

See `SETUP.md` for full details. Quick reference:

| Command | Requires |
|---------|----------|
| `book-advisor reading_history` | Goodreads CSV at `data/goodreads_library_export.csv` |
| `book-advisor discovery update` | CSV + Google Books API key (env `GOOGLE_BOOKS_API_KEY` or file `data/google_books_api_key`) |
| `book-advisor discovery list` | Prior `discovery update` run (SQLite DB at `data/discovery/candidates.sqlite`) |

For quick smoke-testing without a real Goodreads export, copy the test fixture:

```bash
mkdir -p data
cp src/reading_history/goodreads_export/tests/fixtures/goodreads_library_export.csv data/
```

### Gotchas

- The `discovery update` command makes live HTTP calls to the Google Books API and requires a valid API key. Tests mock this entirely, so **tests never need the key**.
- The `data/` directory is gitignored (except `data/README.md`). Don't commit user data or API keys.
- There is no linter configured in the project (no ruff, flake8, mypy, or pyright config). Lint checks are limited to `pytest` passing.
