# Book Advisor — setup

First-time steps to run the CLI locally. **Architecture** and design intent: [`src/book_advisor/ARCHITECTURE.md`](src/book_advisor/ARCHITECTURE.md).

## 1. Python and install

- Use **Python 3.14.x** (see [`pyproject.toml`](pyproject.toml) and [`.python-version`](.python-version)).
- From the **repository root**:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. Goodreads library export

1. On Goodreads: **My Books → Import and export → Export library** and download the CSV.
2. Save it as **`data/goodreads_library_export.csv`** at the **repo root** (create `data/` if needed).

That path is **gitignored** (only [`data/README.md`](data/README.md) is tracked). See that file for the full artifact list.

## 3. Google Books API key (for default discovery)

`book-advisor discovery update` defaults to the **Google Books** catalog and needs an API key unless you pass **`--catalog open_library`**.

### Get a key

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select or create a **project**.
2. **APIs & Services** → **Library** → enable **[Books API](https://developers.google.com/books/docs/v1/getting_started)**.
3. **APIs & Services** → **Credentials** → **Create credentials** → **API key** and copy the key.
4. **Recommended:** edit the key → restrict **APIs** to **Books API**; set **Application restrictions** as appropriate (CLI on your machine often uses “None” or IP restrictions).

### Install the key in this repo (pick one)

| Method | What to do |
|--------|------------|
| **File** | Create **`data/google_books_api_key`** with the key on **one line** (optional `#` comment lines ignored). Same `data/` rules as above; path is explicitly gitignored. |
| **Environment** | Export **`GOOGLE_BOOKS_API_KEY`** before running commands. |
| **CLI** | Pass **`--google-api-key YOUR_KEY`** to `discovery update` (highest precedence). |

Precedence: **`--google-api-key`** → **`GOOGLE_BOOKS_API_KEY`** (via Click) → **`data/google_books_api_key`**.

### Quotas and resuming

Google Books enforces **daily quotas**. Use **`book-advisor discovery update --max-api-requests N`** to cap HTTP calls per run (each list page is one request). Progress is saved in **`data/discovery/candidates.sqlite`** (`author_catalog_refresh` + candidate upserts). **`--max-authors M`** processes at most **M** authors per run, preferring those **not completed** and with the **oldest** `last_attempt_at`. Re-run the same command later to continue.

### Optional sanity check

```bash
curl -sS "https://www.googleapis.com/books/v1/volumes?q=test&key=YOUR_KEY_HERE" | head -c 200
```

You should see JSON (not only an `error` object).

## 4. Open Library without a key

To experiment without Google:

```bash
book-advisor discovery update --catalog open_library
```

## 5. Verify

```bash
book-advisor reading_history
book-advisor discovery update
book-advisor discovery list
```

If `discovery update` fails on a missing key, re-read **§3** or use **`--catalog open_library`**.
