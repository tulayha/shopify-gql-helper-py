# Shopify GraphQL Helper

[![PyPI](https://img.shields.io/pypi/v/shopify-gql-helper)](https://pypi.org/project/shopify-gql-helper/)
[![TestPyPI](https://img.shields.io/badge/TestPyPI-shopify--gql--helper-blue)](https://test.pypi.org/project/shopify-gql-helper/)
[![Python Versions](https://img.shields.io/pypi/pyversions/shopify-gql-helper)](https://pypi.org/project/shopify-gql-helper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/tulayha/shopify-gql-helper-py/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/tulayha/shopify-gql-helper-py/actions/workflows/python-ci.yml)
[![Publish](https://github.com/tulayha/shopify-gql-helper-py/actions/workflows/upload-python-package.yml/badge.svg)](https://github.com/tulayha/shopify-gql-helper-py/actions/workflows/upload-python-package.yml)
[![GitHub Release](https://img.shields.io/github/v/release/tulayha/shopify-gql-helper-py?display_name=tag)](https://github.com/tulayha/shopify-gql-helper-py/releases)


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
for product in cursor_pages(session, query, ["data", "products"]):
    print(product["id"], product["title"])
```

``connection_path`` lists the keys from the response root to the desired
connection, so `["data", "products"]` points to `data.products` above.
Additional GraphQL variables can be supplied via the optional ``variables`` argument.

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

### Retries

Requests use a thread-local `requests.Session` with urllib3's `Retry` to handle
connect/read errors and 429/5xx responses with exponential backoff. Retry
counts can be tuned via `SHOPIFY_GQL_RETRIES` or
`RequestsTransport(retries=...)`. A small amount of random jitter is added to
backoff delays (configurable via `SHOPIFY_GQL_JITTER` or
`RequestsTransport(jitter=...)`), and `Retry-After` headers are honored. By
default, a `Connection: close` header is sent with each request; pass
`force_close=False` to `RequestsTransport` to enable persistent connections.

### Custom Transport

You can provide a custom transport that implements the `Transport` protocol:

```python
from shopify_gql_helper.transport import Transport

class CustomTransport(Transport):
    def post(self, url: str, headers: dict, json: dict, timeout: float):
        raise NotImplementedError
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*This project is not affiliated with Shopify Inc. Shopify is a registered trademark of Shopify Inc.*

MIT. Not affiliated with Shopify.
