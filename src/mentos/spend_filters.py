from __future__ import annotations

from typing import Any

from .storage import get_rule


def build_spend_filter_clause(conn) -> tuple[str, list[Any]]:
    """Build SQL clause + params for excluding configured spend rows.

    Supported rules:
    - exclude_categories: JSON array of categories to exclude.
    - exclude_description_keywords: JSON array of case-insensitive substrings.
    """
    clauses: list[str] = []
    params: list[Any] = []

    categories = get_rule(conn, "exclude_categories") or []
    if isinstance(categories, list):
        categories = [c for c in categories if isinstance(c, str) and c]
        if categories:
            placeholders = ",".join("?" for _ in categories)
            clauses.append(f"COALESCE(category, '') NOT IN ({placeholders})")
            params.extend(categories)

    keywords = get_rule(conn, "exclude_description_keywords") or []
    if isinstance(keywords, list):
        keywords = [k.lower() for k in keywords if isinstance(k, str) and k]
        for keyword in keywords:
            clauses.append("lower(COALESCE(description, '')) NOT LIKE ?")
            params.append(f"%{keyword}%")

    if not clauses:
        return "", []
    return " AND " + " AND ".join(clauses), params

