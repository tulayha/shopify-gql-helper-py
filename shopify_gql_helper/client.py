"""Client helpers."""
from __future__ import annotations

import time
from typing import Any, Mapping

from .errors import ShopifyGQLError
from .session import ShopifySession


def execute(
    session: ShopifySession,
    query: str,
    variables: Mapping[str, Any] | None = None,
    timeout: float = 30,
    retries: int = 2,
) -> dict[str, Any]:
    """Execute a GraphQL query against the Shopify Admin API.

    Automatically retries on temporary failures, including Shopify's "Throttled"
    errors that return HTTP 200 responses.

    Args:
        session: An authenticated ShopifySession instance
        query: The GraphQL query string to execute
        variables: Optional mapping of variables for the GraphQL query
        timeout: Request timeout in seconds (default: 30)
        retries: Number of retry attempts for failed requests (default: 2)
        
    Returns:
        dict: The parsed JSON response from the Shopify API
        
    Raises:
        ShopifyGQLError: If there's an error executing the query or parsing the response
        
    Example:
        >>> session = ShopifySession(shop_url, access_token)
        >>> query = "{ shop { name } }"
        >>> result = execute(session, query)
    """

    payload = {"query": query, "variables": variables or {}}
    headers = {
        "X-Shopify-Access-Token": session.access_token,
        "Content-Type": "application/json",
    }

    for attempt in range(retries + 1):
        session.throttle.before_request(session.min_bucket, session.min_sleep)
        try:
            resp = session.transport.post(
                session.graphql_url, headers=headers, json=payload, timeout=timeout
            )
        except Exception as exc:  # pragma: no cover - transport errors
            raise ShopifyGQLError(str(exc)) from exc

        status = getattr(resp, "status_code", None)
        if status is None:
            raise ShopifyGQLError("Transport response missing status_code")
        if status >= 500 and attempt < retries:
            time.sleep(2 ** attempt)
            continue
        if status != 200:
            snippet = getattr(resp, "text", "")[:300]
            raise ShopifyGQLError(snippet, status)
        try:
            data = resp.json()
        except Exception as exc:  # pragma: no cover - malformed JSON
            snippet = getattr(resp, "text", "")[:300]
            raise ShopifyGQLError(snippet, status) from exc

        cost_info = data.get("extensions", {}).get("cost", {})
        throttle_status = cost_info.get("throttleStatus")
        cost = cost_info.get("actualQueryCost") or cost_info.get("requestedQueryCost")
        session.throttle.after_response(throttle_status, cost)

        if "errors" in data:
            errors = data["errors"]
            throttled = any(
                err.get("extensions", {}).get("code") == "THROTTLED"
                or err.get("message") == "Throttled"
                for err in errors
            )
            if throttled and attempt < retries:
                continue
            snippet = str(errors)[:300]
            raise ShopifyGQLError(snippet)

        return data
    # If loop exits without return, raise generic error
    raise ShopifyGQLError("Max retries exceeded")
