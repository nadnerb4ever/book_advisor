from __future__ import annotations

import re
from datetime import datetime


def normalize_published_date_string(published_date: str | None) -> str | None:
    """Best-effort ISO calendar date (YYYY-MM-DD) from catalog ``publishedDate``-style strings.

    Returns ``None`` if the value is missing or cannot be parsed. Year-only and year-month
    values are normalized to the first day of that period.
    """
    if not published_date or not isinstance(published_date, str):
        return None
    s = published_date.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(s, fmt).date()
            return parsed.isoformat()
        except ValueError:
            continue
    # Reject strings that look like partial/invalid ISO dates (avoid mapping 2010-13-01 → 2010).
    if re.match(r"^\d{4}-\d{2}(-\d{2})?(\D|$)", s):
        return None
    m = re.match(r"^(\d{4})", s)
    if m:
        return f"{m.group(1)}-01-01"
    return None
