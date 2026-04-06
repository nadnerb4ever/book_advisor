from __future__ import annotations

from path_constants import GOOGLE_BOOKS_API_KEY_PATH, WORKSPACE_ROOT


def test_workspace_root_contains_src() -> None:
    assert (WORKSPACE_ROOT / "src" / "discovery").is_dir()


def test_google_books_api_key_path_is_data_file() -> None:
    p = GOOGLE_BOOKS_API_KEY_PATH
    assert p.name == "google_books_api_key"
    assert p.parent.name == "data"
