# Shopify GraphQL Helper

Tiny, production‑minded helpers for the Shopify Admin GraphQL API.
Shopify's official Python SDK exposes `GraphQL().execute` only; this
package adds sessions, automatic cursor pagination, and per‑shop
throttling.

**Features**:
- 🚀 Simple, focused API for Shopify GraphQL Admin API
- 🔄 Automatic cursor-based pagination
- ⚡ Built-in request throttling
- 🔒 Thread-safe implementation
- 🧩 Transport layer abstraction

> **Note**: This is not an official Shopify package.

## Installation

```bash
pip install shopify-gql-helper
```

## Quickstart

```python
query = """
query ($first:Int!, $after:String) {
  products(first:$first, after:$after, query:"status:ACTIVE") {
    pageInfo { hasNextPage endCursor }
    nodes { id legacyResourceId title handle }
  }
}
"""

from shopify_gql_helper import ShopifySession, execute, cursor_pages

session = ShopifySession("https://example.myshopify.com", "shpca_123")

# One-off request
data = execute(session, query, {"first": 1})

# Stream all products
for product in cursor_pages(session, query, {}, ["data", "products"]):
    print(product["id"], product["title"])
```

``connection_path`` lists the keys from the response root to the desired
connection, so `["data", "products"]` points to `data.products` above.

## Throttling

Shopify uses a [leaky bucket](https://shopify.dev/docs/api/usage/rate-limits) policy.
`ShopifySession` coordinates requests per shop through a shared
`ThrottleController`. Adjust `min_bucket` (default 50) and `min_sleep`
(default 1.0s) to tune how aggressively you consume the bucket. **Reuse a
single `ShopifySession` per shop** to avoid fighting the throttling
limits.

## Configuration

### ShopifySession

```python
from shopify_gql_helper import ShopifySession

# Required parameters
session = ShopifySession(
    shop_url="https://your-store.myshopify.com",
    access_token="shpca_your_access_token"
)

# Optional parameters
session = ShopifySession(
    shop_url="https://your-store.myshopify.com",
    access_token="shpca_your_access_token",
    api_version="2025-01",  # default
    min_bucket=50,          # minimum available requests before throttling
    min_sleep=1.0,          # minimum sleep time between requests (seconds)
)
```

### Throttling

Shopify uses a [leaky bucket](https://shopify.dev/docs/api/usage/rate-limits) policy.
`ShopifySession` coordinates requests per shop through a shared
`ThrottleController`. 

**Important**: Reuse a single `ShopifySession` per shop to properly respect rate limits.

### Custom Transport

You can provide a custom transport that implements the `Transport` protocol:

```python
from shopify_gql_helper.transport import Transport

class CustomTransport(Transport):
    def post(self, url: str, headers: dict, json: dict, timeout: float):
        # Your custom implementation
        pass
```

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=shopify_gql_helper
```

## Limitations / Roadmap

- [ ] Bulk operations
- [ ] Nested pagination (e.g., products → variants)
- [ ] ShopifyQL Analytics table pagination

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*This project is not affiliated with Shopify Inc. Shopify is a registered trademark of Shopify Inc.*

MIT. Not affiliated with Shopify.
