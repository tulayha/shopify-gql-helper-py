"""Error classes for Shopify GraphQL helper."""
from __future__ import annotations

from typing import Optional


class ShopifyGQLError(Exception):
    """Raised for HTTP or GraphQL errors from Shopify."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        snippet = message if len(message) <= 300 else message[:300]
        if status_code is not None:
            msg = f"HTTP {status_code}: {snippet}"
        else:
            msg = snippet
        super().__init__(msg)
        self.status_code = status_code
