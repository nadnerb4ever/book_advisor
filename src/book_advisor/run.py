from __future__ import annotations

from pathlib import Path

import click
from click.exceptions import Exit

from path_constants import DISCOVERY_CANDIDATES_SQLITE, GOODREADS_LIBRARY_EXPORT_CSV
from discovery.catalog_factory import MissingGoogleBooksApiKeyError
from discovery.candidate_list import list_discovery_candidates
from discovery.discovery_update import run_discovery_update
from reading_history.goodreads_export.models import LibraryExportRow
from reading_history.read_shelf import load_read_shelf_books

_RATING_COLUMN_WIDTH = len("(no rating)")

_AUTHOR_OPTION_HELP = (
    "Restrict to this author: natural order or 'Last, First', case-insensitive."
)


def _parsed_author_cli_value(author_filter: str | None) -> str | None:
    """Return stripped query, None if unset, or raise ValueError if set but blank."""
    if author_filter is None:
        return None
    q = author_filter.strip()
    if not q:
        raise ValueError("--author must be non-empty")
    return q


_AUTHOR_COL_MAX = 48


def _print_reading_history_table(books: list[LibraryExportRow]) -> None:
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
        f"(default: {GOODREADS_LIBRARY_EXPORT_CSV})"
    ),
)
@click.option(
    "--author",
    "author_filter",
    default=None,
    help=_AUTHOR_OPTION_HELP + " Filters by export `Author` on the read shelf.",
)
def reading_history(csv_path: Path | None, author_filter: str | None) -> None:
    """Print author, title, and star rating for books on your read shelf."""
    path = csv_path if csv_path is not None else GOODREADS_LIBRARY_EXPORT_CSV
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise Exit(1)
    try:
        author_query = _parsed_author_cli_value(author_filter)
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise Exit(1) from exc
    try:
        books = load_read_shelf_books(path, author_query=author_query)
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise Exit(1) from exc
    _print_reading_history_table(books)


@cli.group("discovery")
def discovery_cli() -> None:
    """Discover candidate books from your reading history."""


@discovery_cli.command("update")
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Goodreads export CSV (default: {GOODREADS_LIBRARY_EXPORT_CSV})",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Discovery SQLite path (default: {DISCOVERY_CANDIDATES_SQLITE})",
)
@click.option(
    "--author",
    "only_author",
    default=None,
    help=_AUTHOR_OPTION_HELP + " Must match a read-shelf primary `Author` value.",
)
@click.option(
    "--max-authors",
    "max_authors",
    type=int,
    default=None,
    help=(
        "Process at most this many authors this run (incomplete / stale first). "
        "Omit to process all incomplete authors."
    ),
)
@click.option(
    "--max-api-requests",
    "max_api_requests",
    type=int,
    default=None,
    help=(
        "Stop after this many catalog HTTP requests (Google Books: one per page). "
        "Progress and cursors are saved; re-run to continue."
    ),
)
def discovery_update(
    csv_path: Path | None,
    db_path: Path | None,
    only_author: str | None,
    max_authors: int | None,
    max_api_requests: int | None,
) -> None:
    """Fetch author-based candidates from Google Books and upsert into SQLite."""
    path = csv_path if csv_path is not None else GOODREADS_LIBRARY_EXPORT_CSV
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise Exit(1)
    out_db = db_path if db_path is not None else DISCOVERY_CANDIDATES_SQLITE
    if max_authors is not None and max_authors < 1:
        click.echo("--max-authors must be at least 1.", err=True)
        raise Exit(1)
    if max_api_requests is not None and max_api_requests < 1:
        click.echo("--max-api-requests must be at least 1.", err=True)
        raise Exit(1)
    try:
        result = run_discovery_update(
            csv_path=path,
            out_db=out_db,
            only_author=only_author,
            logger=click.echo,
            max_authors=max_authors,
            max_api_requests=max_api_requests,
        )
    except MissingGoogleBooksApiKeyError as exc:
        click.echo(exc.message, err=True)
        raise Exit(1) from exc
    except Exception as exc:
        click.echo(f"Discovery failed: {exc}", err=True)
        raise Exit(1) from exc
    click.echo(
        f"Upserted {result.upserted_rows} candidate row(s) into {out_db} "
        f"({result.authors_targeted} author(s) scheduled this run)."
    )
    if result.resume_message:
        click.echo(result.resume_message)


@discovery_cli.command("list")
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path, exists=False, dir_okay=False),
    default=None,
    help=f"Discovery SQLite path (default: {DISCOVERY_CANDIDATES_SQLITE})",
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
@click.option(
    "--author",
    "author_filter",
    default=None,
    help=_AUTHOR_OPTION_HELP + " Filters rows by stored candidate author text.",
)
@click.option("--limit", type=int, default=None, help="Max rows to print.")
def discovery_list(
    db_path: Path | None,
    source_filter: str | None,
    catalog_scope: str,
    author_filter: str | None,
    limit: int | None,
) -> None:
    """Print candidates from the discovery database."""
    try:
        author_query = _parsed_author_cli_value(author_filter)
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise Exit(1) from exc

    db = db_path if db_path is not None else DISCOVERY_CANDIDATES_SQLITE
    if not db.is_file():
        click.echo(f"Database not found: {db}", err=True)
        raise Exit(1)
    try:
        listed = list_discovery_candidates(
            db,
            source_filter=source_filter,
            catalog_scope=catalog_scope,
            author_query=author_query,
            limit=limit,
        )
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise Exit(1) from exc
    click.echo(f"Showing {len(listed.rows)} of {listed.summary_total} candidate(s)")
    for c in listed.rows:
        year = str(c.publication_year) if c.publication_year is not None else "—"
        cat_s = c.catalog.value
        click.echo(f"{c.author}\t{year}\t{c.title}\t{cat_s}:{c.external_id}\t{c.source}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
