from __future__ import annotations

from pathlib import Path

import click

from goodreads import GoodreadsLibraryClient

_RATING_COLUMN_WIDTH = len("(no rating)")


def _default_export_csv() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "goodreads"
        / "data"
        / "goodreads_library_export.csv"
    )


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
        f"(default: {_default_export_csv()})"
    ),
)
def reading_history(csv_path: Path | None) -> None:
    """Print titles and star ratings for books on your read shelf."""
    path = csv_path if csv_path is not None else _default_export_csv()
    if not path.is_file():
        click.echo(f"CSV not found: {path}", err=True)
        raise click.Exit(1)
    _run_reading_history(path)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
