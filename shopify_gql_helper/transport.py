"""Transport abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
import os
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class Transport(ABC):
    """Abstract transport interface."""

    @abstractmethod
    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        json: Mapping[str, Any],
        timeout: float,
    ) -> "requests.Response":  # noqa: D401
        """Send a POST request."""
        raise NotImplementedError


class RequestsTransport(Transport):
    """Transport using the requests library with retry support."""

    def __init__(
        self,
        *,
        retries: int | None = None,
        backoff: float | None = None,
    ) -> None:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util import Retry

        retry_total = retries if retries is not None else int(
            os.getenv("SHOPIFY_GQL_RETRIES", "3")
        )
        backoff_factor = backoff if backoff is not None else float(
            os.getenv("SHOPIFY_GQL_BACKOFF", "0.5")
        )
        retry = Retry(
            total=retry_total,
            connect=retry_total,
            read=retry_total,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.setdefault("Connection", "close")
        self._session = session

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        json: Mapping[str, Any],
        timeout: float,
    ) -> "requests.Response":
        return self._session.post(url, headers=headers, json=json, timeout=timeout)
