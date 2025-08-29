"""Pagination helpers."""
from __future__ import annotations

import os
import time
from typing import Any, Iterable, Mapping

import requests

from .client import execute
from .errors import ShopifyGQLError
from .session import ShopifySession


def cursor_pages(
    session: ShopifySession,
    query: str,
    connection_path: list[str],
    variables: Mapping[str, Any] | None = None,
    page_size: int = 50,
) -> Iterable[dict[str, Any]]:
    """
    Yield items from a cursor-based GraphQL connection, requesting additional
    pages until `pageInfo.hasNextPage` is false.

    The supplied `query` must accept `$first:Int!` and `$after:String` variables
    for pagination. `connection_path` is a list of keys from the root of the
    response to the desired connection object (e.g. `["data", "products"]`).

    Args:
        session: Authenticated `ShopifySession`.
        query: GraphQL document containing a connection field.
        connection_path: Keys navigating from the root response to the connection.
        variables: Initial query variables (updated with pagination params). May be None.
            For example, if your query returns data like {"data": {"products": {"edges": [...]}}},
            the connection_path would be ["data", "products"]
        page_size: Items per page (default 250, Shopify max).

    Yields:
        dict: Each node from the connection, one at a time.

    Raises:
        ValueError: If `connection_path` is invalid or connection lacks
            `nodes`/`edges`.

    Example:
        >>> query = '''
        ...   query($first:Int!, $after:String) {
        ...     products(first:$first, after:$after) {
        ...       pageInfo { hasNextPage endCursor }
        ...       nodes { id title }
        ...     }
        ...   }
        ... '''
        >>> for product in cursor_pages(session, query, ["data", "products"]):
        ...     print(product["title"])
    """


    vars_copy: dict[str, Any] = dict(variables or {})
    cursor: str | None = None
    first = vars_copy.get("first")
    vars_copy["first"] = first if (isinstance(first, int) and first > 0) else page_size
    page_retries = int(
        os.getenv("SHOPIFY_GQL_PAGE_RETRIES", os.getenv("SHOPIFY_GQL_RETRIES", "3"))
    )
    while True:
        vars_copy["after"] = cursor
        for attempt in range(page_retries + 1):
            try:
                data = execute(session, query, vars_copy)
                break
            except ShopifyGQLError as exc:
                cause = exc.__cause__
                if isinstance(
                    cause,
                    (
                        requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                    ),
                ) and attempt < page_retries:
                    time.sleep(2**attempt)
                    continue
                raise
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
