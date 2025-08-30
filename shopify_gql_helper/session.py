"""Session object for Shopify GraphQL API."""
from __future__ import annotations

from dataclasses import dataclass, field

from .throttle import ThrottleController
from .transport import RequestsTransport, Transport


@dataclass
class ShopifySession:
    """Represents a session for interacting with a specific Shopify store's GraphQL API.
    
    This class holds configuration and state for making authenticated requests to a Shopify store's
    Admin API. It manages authentication, API versioning, and request throttling.
    
    Attributes:
        shop_url: The base URL of the Shopify store (e.g., 'https://your-store.myshopify.com')
        access_token: The API access token for authentication
        api_version: The Shopify API version to use (default: '2025-01')
        throttle: ThrottleController instance for rate limiting (auto-created if not provided)
        transport: Transport implementation for making HTTP requests (defaults to RequestsTransport)
        min_bucket: Minimum available request points before throttling (default: 50)
        min_sleep: Minimum sleep time when rate limited, in seconds (default: 1.0)
    """

    shop_url: str
    access_token: str
    api_version: str = "2025-01"
    throttle: ThrottleController = field(default_factory=ThrottleController)
    transport: Transport = field(default_factory=RequestsTransport)
    min_bucket: int = 100
    min_sleep: float = 1.0
    graphql_url: str = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the session by normalizing the shop URL and setting up the GraphQL endpoint.
        
        This is automatically called after the dataclass is initialized.
        It ensures the shop URL is properly formatted and constructs the full GraphQL API URL.
        """
        self.shop_url = self.shop_url.strip().rstrip("/")
        self.graphql_url = f"{self.shop_url}/admin/api/{self.api_version}/graphql.json"
