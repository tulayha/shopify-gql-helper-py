"""Transport abstractions."""
from __future__ import annotations

from typing import Any, Dict


class Transport:
    """Abstract transport interface."""

    def post(self, url: str, headers: Dict[str, str], json: Dict[str, Any], timeout: float):  # noqa: D401
        """Send a POST request."""
        raise NotImplementedError


class RequestsTransport(Transport):
    """Transport using the requests library."""

    def post(self, url: str, headers: Dict[str, str], json: Dict[str, Any], timeout: float):
        import requests

        return requests.post(url, headers=headers, json=json, timeout=timeout)
