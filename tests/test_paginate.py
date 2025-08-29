import json
import pathlib
import sys
from dataclasses import dataclass

import pytest
import requests

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
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


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
            connection_path=["data", "products"],
            variables={},
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
                connection_path=["data", "missing"],
                variables={},
                page_size=2,
            )
        )


def test_cursor_pages_recovers_from_transient_error():
    resp1 = json.load(open("tests/fixtures/products_page1.json"))
    resp2 = json.load(open("tests/fixtures/products_page2.json"))
    transport = ListTransport(
        [
            DummyResponse(200, resp1),
            requests.exceptions.ConnectionError("boom"),
            DummyResponse(200, resp2),
        ]
    )
    session = ShopifySession("https://test.myshopify.com", "token", transport=transport)
    query = "query"
    items = list(
        cursor_pages(
            session,
            query,
            connection_path=["data", "products"],
            variables={},
            page_size=2,
        )
    )
    ids = [item["id"] for item in items]
    assert ids == [
        "gid://shopify/Product/1",
        "gid://shopify/Product/2",
        "gid://shopify/Product/3",
    ]
    assert len(ids) == len(set(ids))
    # second call failed and retried with same cursor
    assert transport.calls[1]["variables"]["after"] == "cursor1"
    assert transport.calls[2]["variables"]["after"] == "cursor1"
