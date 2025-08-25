import json
from dataclasses import dataclass
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from shopify_gql_helper.paginate import cursor_pages
from shopify_gql_helper.session import ShopifySession
from shopify_gql_helper.transport import Transport


@dataclass
class DummyResponse:
    status_code: int
    _json: dict
    text: str = ""

    def json(self):
        return self._json


class ListTransport(Transport):
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def post(self, url, headers, json, timeout):
        self.calls.append({"query": json["query"], "variables": dict(json["variables"])})
        return self.responses.pop(0)


def test_cursor_pages_streams_all_items():
    resp1 = json.load(open("tests/fixtures/products_page1.json"))
    resp2 = json.load(open("tests/fixtures/products_page2.json"))
    transport = ListTransport([
        DummyResponse(200, resp1),
        DummyResponse(200, resp2),
    ])
    session = ShopifySession("https://test.myshopify.com", "token", transport=transport)
    query = "query"
    items = list(
        cursor_pages(
            session,
            query,
            variables={},
            connection_path=["data", "products"],
            page_size=2,
        )
    )
    assert [item["id"] for item in items] == [
        "gid://shopify/Product/1",
        "gid://shopify/Product/2",
        "gid://shopify/Product/3",
    ]
    assert transport.calls[0]["variables"]["after"] is None
    assert transport.calls[1]["variables"]["after"] == "cursor1"


def test_cursor_pages_bad_path():
    resp1 = json.load(open("tests/fixtures/products_page1.json"))
    transport = ListTransport([DummyResponse(200, resp1)])
    session = ShopifySession("https://test.myshopify.com", "token", transport=transport)
    with pytest.raises(ValueError):
        list(
            cursor_pages(
                session,
                "query",
                variables={},
                connection_path=["data", "missing"],
                page_size=2,
            )
        )
