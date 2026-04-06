from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from discovery.models import AuthorRefreshState, CatalogBackend, DiscoveredCandidate

_SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    catalog TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publication_year INTEGER,
    release_date TEXT,
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
CREATE TABLE IF NOT EXISTS author_catalog_refresh (
    catalog TEXT NOT NULL,
    author TEXT NOT NULL,
    resume_cursor INTEGER NOT NULL DEFAULT 0,
    complete INTEGER NOT NULL DEFAULT 0,
    last_completed_at TEXT,
    last_attempt_at TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (catalog, author)
);
"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_candidates_release_date(conn: sqlite3.Connection) -> None:
    cols = {
        row[1] for row in conn.execute("PRAGMA table_info(candidates)").fetchall()
    }
    if "release_date" not in cols:
        conn.execute("ALTER TABLE candidates ADD COLUMN release_date TEXT")


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
            _ensure_candidates_release_date(conn)
            conn.commit()

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
                        release_date, source, first_seen_at, last_updated_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(catalog, external_id) DO UPDATE SET
                        title = excluded.title,
                        author = excluded.author,
                        publication_year = excluded.publication_year,
                        release_date = excluded.release_date,
                        source = excluded.source,
                        last_updated_at = excluded.last_updated_at,
                        raw_json = excluded.raw_json
                    """,
                    (
                        c.catalog.value,
                        c.external_id,
                        c.title,
                        c.author,
                        c.publication_year,
                        c.release_date,
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
            catalog=CatalogBackend(row["catalog"]),
            external_id=row["external_id"],
            publication_year=row["publication_year"],
            release_date=row["release_date"],
            raw_json=row["raw_json"],
        )

    def iter_candidates(
        self,
        *,
        source: str | None = None,
        catalog: CatalogBackend | None = None,
        limit: int | None = None,
    ) -> Iterator[DiscoveredCandidate]:
        self.init_schema()
        sql = "SELECT * FROM candidates"
        params: list[object] = []
        clauses: list[str] = []
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if catalog is not None:
            clauses.append("catalog = ?")
            params.append(catalog.value)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY author COLLATE NOCASE, title COLLATE NOCASE"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            for row in conn.execute(sql, params):
                yield self.row_to_candidate(row)

    def count(
        self,
        *,
        source: str | None = None,
        catalog: CatalogBackend | None = None,
    ) -> int:
        self.init_schema()
        sql = "SELECT COUNT(*) FROM candidates"
        params: list[object] = []
        clauses: list[str] = []
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if catalog is not None:
            clauses.append("catalog = ?")
            params.append(catalog.value)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def _row_to_author_refresh(self, row: sqlite3.Row) -> AuthorRefreshState:
        return AuthorRefreshState(
            catalog=CatalogBackend(row["catalog"]),
            author=row["author"],
            resume_cursor=int(row["resume_cursor"]),
            complete=bool(row["complete"]),
            last_completed_at=row["last_completed_at"],
            last_attempt_at=row["last_attempt_at"],
            updated_at=row["updated_at"],
        )

    def get_author_refresh_state(
        self,
        catalog: CatalogBackend,
        author: str,
    ) -> AuthorRefreshState | None:
        self.init_schema()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM author_catalog_refresh "
                "WHERE catalog = ? AND author = ?",
                (catalog.value, author),
            ).fetchone()
            return self._row_to_author_refresh(row) if row else None

    def put_author_refresh_state(self, state: AuthorRefreshState) -> None:
        self.init_schema()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO author_catalog_refresh (
                    catalog, author, resume_cursor, complete,
                    last_completed_at, last_attempt_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(catalog, author) DO UPDATE SET
                    resume_cursor = excluded.resume_cursor,
                    complete = excluded.complete,
                    last_completed_at = excluded.last_completed_at,
                    last_attempt_at = excluded.last_attempt_at,
                    updated_at = excluded.updated_at
                """,
                (
                    state.catalog.value,
                    state.author,
                    state.resume_cursor,
                    1 if state.complete else 0,
                    state.last_completed_at,
                    state.last_attempt_at,
                    state.updated_at,
                ),
            )
            conn.commit()

    def load_author_refresh_map(
        self,
        catalog: CatalogBackend,
        authors: list[str],
    ) -> dict[str, AuthorRefreshState]:
        """Load refresh rows for the given authors in one query."""
        if not authors:
            return {}
        self.init_schema()
        placeholders = ",".join("?" * len(authors))
        sql = (
            f"SELECT * FROM author_catalog_refresh WHERE catalog = ? "
            f"AND author IN ({placeholders})"
        )
        params: list[object] = [catalog.value, *authors]
        out: dict[str, AuthorRefreshState] = {}
        with self._connect() as conn:
            for row in conn.execute(sql, params):
                st = self._row_to_author_refresh(row)
                out[st.author] = st
        return out

    def select_authors_for_run(
        self,
        catalog: CatalogBackend,
        shelf_authors: list[str],
        *,
        limit: int | None,
    ) -> list[str]:
        """Incomplete authors first, then oldest ``last_attempt_at``, then name.

        Authors with ``complete=1`` are omitted. Missing table rows are treated
        as incomplete (never refreshed).
        """
        by_name = self.load_author_refresh_map(catalog, shelf_authors)

        def sort_key(name: str) -> tuple[int, str, str]:
            st = by_name.get(name)
            if st is None or st.last_attempt_at is None:
                return (0, "", name)
            return (1, st.last_attempt_at, name)

        incomplete = []
        for a in shelf_authors:
            st = by_name.get(a)
            if st is not None and st.complete:
                continue
            incomplete.append(a)
        incomplete.sort(key=sort_key)
        if limit is not None:
            return incomplete[:limit]
        return incomplete
