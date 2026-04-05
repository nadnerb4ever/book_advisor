from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from reading_history.goodreads_export.models import LibraryExportRow
from reading_history.goodreads_export.read_csv import parse_library_csv

_READ_SHELF = "read"


@dataclass
class GoodreadsLibraryClient:
    """Load reading history from a local Goodreads `goodreads_library_export.csv`."""

    path: Path
    _rows: list[LibraryExportRow] | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_path(cls, path: str | Path) -> Self:
        return cls(path=Path(path))

    def load(self) -> list[LibraryExportRow]:
        self._rows = parse_library_csv(self.path)
        return self._rows

    @property
    def books(self) -> list[LibraryExportRow]:
        if self._rows is None:
            self._rows = parse_library_csv(self.path)
        return self._rows

    def iter_books(self) -> Iterator[LibraryExportRow]:
        yield from self.books

    def read_books(self) -> list[LibraryExportRow]:
        return [
            b
            for b in self.books
            if (b.exclusive_shelf or "").strip().lower() == _READ_SHELF
        ]
