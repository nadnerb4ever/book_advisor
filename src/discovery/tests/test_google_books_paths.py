from __future__ import annotations

from discovery.google_books.paths import (
    default_google_books_api_key_path,
    workspace_root,
)


def test_workspace_root_contains_src() -> None:
    assert (workspace_root() / "src" / "discovery").is_dir()


def test_default_api_key_path_is_data_file() -> None:
    p = default_google_books_api_key_path()
    assert p.name == "google_books_api_key"
    assert p.parent.name == "data"
