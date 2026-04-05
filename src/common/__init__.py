"""Shared utilities used across packages (no single domain owner)."""

from common.authors import (
    author_display_variants,
    author_text_matches_query,
    filter_canonical_author_names,
    format_known_strings_preview,
    unique_primary_author_names,
)

__all__ = [
    "author_display_variants",
    "author_text_matches_query",
    "filter_canonical_author_names",
    "format_known_strings_preview",
    "unique_primary_author_names",
]
