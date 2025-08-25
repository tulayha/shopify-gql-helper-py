"""Session object for Shopify GraphQL API."""
from __future__ import annotations

from dataclasses import dataclass, field

from .throttle import ThrottleController
from .transport import RequestsTransport, Transport


@dataclass
class ShopifySession:
    """Represents per-shop session configuration."""

    shop_url: str
    access_token: str
    api_version: str = "2025-01"
    throttle: ThrottleController = field(default_factory=ThrottleController)
    transport: Transport = field(default_factory=RequestsTransport)
    min_bucket: int = 50
    min_sleep: float = 1.0
    graphql_url: str = field(init=False)

    def __post_init__(self) -> None:
        self.shop_url = self.shop_url.strip().rstrip("/")
        self.graphql_url = f"{self.shop_url}/admin/api/{self.api_version}/graphql.json"
