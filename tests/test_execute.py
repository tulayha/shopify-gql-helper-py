import json
import time
from dataclasses import dataclass
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from shopify_gql_helper.client import execute
from shopify_gql_helper.errors import ShopifyGQLError
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
        self.calls.append(json)
        return self.responses.pop(0)


def make_session(transport):
    return ShopifySession("https://test.myshopify.com", "token", transport=transport)


def test_execute_success_updates_throttle():
    resp_data = json.load(open("tests/fixtures/products_page1.json"))
    transport = ListTransport([DummyResponse(200, resp_data)])
    session = make_session(transport)
    data = execute(session, "query")
    assert data["data"]["products"]["nodes"][0]["id"] == "gid://shopify/Product/1"
    assert session.throttle.available == 900


def test_execute_retries_on_5xx(monkeypatch):
    resp_data = json.load(open("tests/fixtures/products_page1.json"))
    transport = ListTransport([DummyResponse(500, {}, text="err"), DummyResponse(200, resp_data)])
    session = make_session(transport)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    data = execute(session, "query")
    assert len(transport.calls) == 2
    assert slept == [1]
    assert data["data"]["products"]


def test_execute_raises_on_non_200():
    transport = ListTransport([DummyResponse(404, {}, text="missing")])
    session = make_session(transport)
    with pytest.raises(ShopifyGQLError) as exc:
        execute(session, "query")
    assert "HTTP 404" in str(exc.value)


def test_execute_raises_on_graphql_errors():
    transport = ListTransport([DummyResponse(200, {"errors": [{"message": "bad"}]})])
    session = make_session(transport)
    with pytest.raises(ShopifyGQLError) as exc:
        execute(session, "query")
    assert "bad" in str(exc.value)


def test_execute_raises_on_invalid_json():
    class BadJsonResponse(DummyResponse):
        def json(self):  # type: ignore[override]
            raise ValueError("no json")

    transport = ListTransport([BadJsonResponse(200, {}, text="oops")])
    session = make_session(transport)
    with pytest.raises(ShopifyGQLError) as exc:
        execute(session, "query")
    assert "oops" in str(exc.value)
