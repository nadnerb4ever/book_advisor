from __future__ import annotations

from pathlib import Path

import click
from click.exceptions import Exit

from book_advisor.paths import (
    default_discovery_db,
    default_goodreads_csv,
    default_google_books_api_key_file,
)
from discovery.models import CatalogBackend
from reading_history import GoodreadsLibraryClient

_RATING_COLUMN_WIDTH = len("(no rating)")


def _read_google_books_key_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return None


def _resolve_google_books_api_key(
    cli_or_env_key: str | None,
    *,
    key_file: Path,
) -> str | None:
    if cli_or_env_key is not None and cli_or_env_key.strip():
        return cli_or_env_key.strip()
    return _read_google_books_key_file(key_file)


def _build_discovery_catalog(
    catalog_name: str,
    *,
    google_api_key: str | None,
    key_file: Path,
):
    backend = CatalogBackend(catalog_name)
    if backend is CatalogBackend.OPEN_LIBRARY:
        from discovery.open_library import OpenLibraryCatalog

        return OpenLibraryCatalog()
    if backend is CatalogBackend.GOOGLE_BOOKS:
        key = _resolve_google_books_api_key(
            google_api_key,
            key_file=key_file,
        )
        if not key:
            click.echo(
                "Google Books catalog requires an API key. Set GOOGLE_BOOKS_API_KEY, "
                f"put the key in {key_file} (first non-comment line), pass "
                "--google-api-key, or use --catalog open_library.",
                err=True,
            )
            raise Exit(1)
        from discovery.google_books import GoogleBooksCatalog

        return GoogleBooksCatalog(key)
    raise AssertionError(f"Unhandled catalog {backend!r}")


_AUTHOR_COL_MAX = 48


def _run_reading_history(csv_path: Path) -> None:
    client = GoodreadsLibraryClient.from_path(csv_path)
    books = client.read_books()
    if not books:
        return
    author_w = min(
        max(len(b.author) for b in books),
        _AUTHOR_COL_MAX,
    )
    author_w = max(author_w, len("Author"))
    for book in books:
        if book.my_rating is not None:
            stars = f"{book.my_rating}★"
        else:
            stars = "(no rating)"
        author_display = book.author
        if len(author_display) > _AUTHOR_COL_MAX:
            author_display = author_display[: _AUTHOR_COL_MAX - 1] + "…"
        click.echo(
            f"{stars:<{_RATING_COLUMN_WIDTH}}  "
            f"{author_display:<{author_w}}  "
            f"{book.title}"
        )


@click.group()
def cli() -> None:
    """Personalized book recommendations from reading history."""


@cli.command("reading_history")
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=(
        "Path to goodreads_library_export.csv "
        f"(default: {default_goodreads_csv()})"
    ),
)
def reading_history(csv_path: Path | None) -> None:
    """Print author, title, and star rating for books on your read shelf."""
    path = csv_path if csv_path is not None else default_goodreads_csv()
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise Exit(1)
    _run_reading_history(path)


@cli.group("discovery")
def discovery_cli() -> None:
    """Discover candidate books from your reading history."""


@discovery_cli.command("update")
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Goodreads export CSV (default: {default_goodreads_csv()})",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Discovery SQLite path (default: {default_discovery_db()})",
)
@click.option(
    "--catalog",
    "catalog_name",
    type=click.Choice([e.value for e in CatalogBackend]),
    default=CatalogBackend.GOOGLE_BOOKS.value,
    show_default=True,
    help="Discovery catalog backend.",
)
@click.option(
    "--google-api-key",
    "google_api_key",
    default=None,
    envvar="GOOGLE_BOOKS_API_KEY",
    show_envvar=True,
    help="Google Books API key (CLI wins over env; then key file).",
)
@click.option(
    "--author",
    "only_author",
    default=None,
    help=(
        "Only query this primary author: matches the export `Author` value, including "
        "natural order vs 'Last, First' (case-insensitive). Useful for manual testing."
    ),
)
def discovery_update(
    csv_path: Path | None,
    db_path: Path | None,
    catalog_name: str,
    google_api_key: str | None,
    only_author: str | None,
) -> None:
    """Fetch author-based candidates and upsert into SQLite (default: Google Books)."""
    from discovery.author_discovery import run_author_discovery_to_list
    from discovery.store import CandidateStore

    path = csv_path if csv_path is not None else default_goodreads_csv()
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise Exit(1)
    out_db = db_path if db_path is not None else default_discovery_db()
    key_file = default_google_books_api_key_file()
    try:
        cat = _build_discovery_catalog(
            catalog_name,
            google_api_key=google_api_key,
            key_file=key_file,
        )
        candidates = run_author_discovery_to_list(
            path,
            catalog=cat,
            logger=click.echo,
            only_author=only_author,
        )
    except Exit:
        raise
    except Exception as exc:
        click.echo(f"Discovery failed: {exc}", err=True)
        raise Exit(1) from exc
    click.echo(f"Writing {len(candidates)} candidate(s) to {out_db} …")
    store = CandidateStore(out_db)
    n = store.upsert_candidates(candidates)
    click.echo(f"Upserted {n} candidate row(s) into {out_db}")


@discovery_cli.command("list")
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Discovery SQLite path (default: {default_discovery_db()})",
)
@click.option(
    "--source",
    "source_filter",
    default=None,
    help="Filter by source tag (e.g. author_based).",
)
@click.option(
    "--catalog",
    "catalog_scope",
    type=click.Choice(["google_books", "open_library", "all"], case_sensitive=False),
    default="google_books",
    show_default=True,
    help="List rows from this catalog only, or all backends.",
)
@click.option("--limit", type=int, default=None, help="Max rows to print.")
def discovery_list(
    db_path: Path | None,
    source_filter: str | None,
    catalog_scope: str,
    limit: int | None,
) -> None:
    """Print candidates from the discovery database."""
    from discovery.store import CandidateStore

    db = db_path if db_path is not None else default_discovery_db()
    if not db.is_file():
        click.echo(f"Database not found: {db}", err=True)
        raise Exit(1)
    catalog_filter: CatalogBackend | None
    if catalog_scope == "all":
        catalog_filter = None
    else:
        catalog_filter = CatalogBackend(catalog_scope)
    store = CandidateStore(db)
    total = store.count(source=source_filter, catalog=catalog_filter)
    rows = list(
        store.iter_candidates(
            source=source_filter,
            catalog=catalog_filter,
            limit=limit,
        )
    )
    click.echo(f"Showing {len(rows)} of {total} candidate(s)")
    for c in rows:
        year = str(c.publication_year) if c.publication_year is not None else "—"
        cat_s = c.catalog.value
        click.echo(f"{c.author}\t{year}\t{c.title}\t{cat_s}:{c.external_id}\t{c.source}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
