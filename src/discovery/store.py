from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from discovery.models import DiscoveredCandidate

_SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    catalog TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publication_year INTEGER,
    source TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    raw_json TEXT,
    PRIMARY KEY (catalog, external_id)
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class CandidateStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def upsert_candidates(self, candidates: list[DiscoveredCandidate]) -> int:
        """Insert or merge rows. Returns number of rows written (insert + update)."""
        if not candidates:
            return 0
        self.init_schema()
        now = _utc_now_iso()
        n = 0
        with self._connect() as conn:
            for c in candidates:
                conn.execute(
                    """
                    INSERT INTO candidates (
                        catalog, external_id, title, author, publication_year,
                        source, first_seen_at, last_updated_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(catalog, external_id) DO UPDATE SET
                        title = excluded.title,
                        author = excluded.author,
                        publication_year = excluded.publication_year,
                        source = excluded.source,
                        last_updated_at = excluded.last_updated_at,
                        raw_json = excluded.raw_json
                    """,
                    (
                        c.catalog,
                        c.external_id,
                        c.title,
                        c.author,
                        c.publication_year,
                        c.source,
                        now,
                        now,
                        c.raw_json,
                    ),
                )
                n += 1
            conn.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                ("last_author_discovery_at", now),
            )
            conn.commit()
        return n

    def row_to_candidate(self, row: sqlite3.Row) -> DiscoveredCandidate:
        return DiscoveredCandidate(
            title=row["title"],
            author=row["author"],
            source=row["source"],
            catalog=row["catalog"],
            external_id=row["external_id"],
            publication_year=row["publication_year"],
            raw_json=row["raw_json"],
        )

    def iter_candidates(
        self,
        *,
        source: str | None = None,
        limit: int | None = None,
    ) -> Iterator[DiscoveredCandidate]:
        self.init_schema()
        sql = "SELECT * FROM candidates"
        params: list[object] = []
        if source is not None:
            sql += " WHERE source = ?"
            params.append(source)
        sql += " ORDER BY author COLLATE NOCASE, title COLLATE NOCASE"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            for row in conn.execute(sql, params):
                yield self.row_to_candidate(row)

    def count(self, *, source: str | None = None) -> int:
        self.init_schema()
        sql = "SELECT COUNT(*) FROM candidates"
        params: list[object] = []
        if source is not None:
            sql += " WHERE source = ?"
            params.append(source)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return int(row[0]) if row else 0
