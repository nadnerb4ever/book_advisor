from __future__ import annotations

from pathlib import Path

import click

from book_advisor.paths import default_discovery_db, default_goodreads_csv
from reading_history import GoodreadsLibraryClient

_RATING_COLUMN_WIDTH = len("(no rating)")


def _run_reading_history(csv_path: Path) -> None:
    client = GoodreadsLibraryClient.from_path(csv_path)
    for book in client.read_books():
        if book.my_rating is not None:
            stars = f"{book.my_rating}★"
        else:
            stars = "(no rating)"
        click.echo(f"{stars:<{_RATING_COLUMN_WIDTH}}  {book.title}")


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
    """Print titles and star ratings for books on your read shelf."""
    path = csv_path if csv_path is not None else default_goodreads_csv()
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise click.Exit(1)
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
def discovery_update(csv_path: Path | None, db_path: Path | None) -> None:
    """Fetch author-based candidates from Open Library and upsert into SQLite."""
    from discovery.author_discovery import run_author_discovery_to_list
    from discovery.store import CandidateStore

    path = csv_path if csv_path is not None else default_goodreads_csv()
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise click.Exit(1)
    out_db = db_path if db_path is not None else default_discovery_db()
    try:
        candidates = run_author_discovery_to_list(
            path,
            logger=click.echo,
        )
    except Exception as exc:
        click.echo(f"Discovery failed: {exc}", err=True)
        raise click.Exit(1) from exc
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
@click.option("--limit", type=int, default=None, help="Max rows to print.")
def discovery_list(
    db_path: Path | None,
    source_filter: str | None,
    limit: int | None,
) -> None:
    """Print candidates from the discovery database."""
    from discovery.store import CandidateStore

    db = db_path if db_path is not None else default_discovery_db()
    if not db.is_file():
        click.echo(f"Database not found: {db}", err=True)
        raise click.Exit(1)
    store = CandidateStore(db)
    total = store.count(source=source_filter)
    rows = list(store.iter_candidates(source=source_filter, limit=limit))
    click.echo(f"Showing {len(rows)} of {total} candidate(s)")
    for c in rows:
        year = str(c.publication_year) if c.publication_year is not None else "—"
        click.echo(f"{c.author}\t{year}\t{c.title}\t{c.catalog}:{c.external_id}\t{c.source}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
