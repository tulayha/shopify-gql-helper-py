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
    """Transport using the requests library with retry support.

    Args:
        retries: Total retry attempts for failed requests. Defaults to the
            ``SHOPIFY_GQL_RETRIES`` env var or ``3``.
        backoff: Exponential backoff factor between retries. Defaults to the
            ``SHOPIFY_GQL_BACKOFF`` env var or ``0.5`` seconds.
        jitter: Random jitter added to retry backoff. Defaults to the
            ``SHOPIFY_GQL_JITTER`` env var or ``0.1`` seconds.
        force_close: If True, send ``Connection: close`` with each request to
            disable keep-alives. Set to False to allow persistent connections.
    """

    def __init__(
        self,
        *,
        retries: int | None = None,
        backoff: float | None = None,
        jitter: float | None = None,
        force_close: bool = True,
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
        backoff_jitter = jitter if jitter is not None else float(
            os.getenv("SHOPIFY_GQL_JITTER", "0.1")
        )
        retry = Retry(
            total=retry_total,
            connect=retry_total,
            read=retry_total,
            backoff_factor=backoff_factor,
            backoff_jitter=backoff_jitter,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        if force_close:
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
