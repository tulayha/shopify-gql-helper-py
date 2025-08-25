"""Pagination helpers."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .client import execute
from .session import ShopifySession


def cursor_pages(
    session: ShopifySession,
    query: str,
    variables: Dict[str, Any],
    connection_path: List[str],
    page_size: int = 250,
) -> Iterable[Dict[str, Any]]:
    """Yield items from a cursor-based connection.

    ``connection_path`` is a list of keys from the root of the response to
    the connection object, e.g. ``["data", "products"]``.
    """

    vars_copy: Dict[str, Any] = dict(variables or {})
    cursor: str | None = None
    while True:
        vars_copy["first"] = page_size
        vars_copy["after"] = cursor
        data = execute(session, query, vars_copy)
        conn: Any = data
        for key in connection_path:
            if not isinstance(conn, dict) or key not in conn:
                raise ValueError(f"connection_path missing key '{key}'")
            conn = conn[key]
        if "nodes" in conn:
            items = conn["nodes"]
        elif "edges" in conn:
            items = [edge["node"] for edge in conn["edges"]]
        else:
            raise ValueError("Connection missing 'nodes' or 'edges'")
        for item in items:
            yield item
        page_info = conn.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
