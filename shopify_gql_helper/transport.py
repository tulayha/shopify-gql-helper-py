"""Transport abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
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
    """Transport using the requests library."""

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        json: Mapping[str, Any],
        timeout: float,
    ) -> "requests.Response":
        import requests

        return requests.post(url, headers=headers, json=json, timeout=timeout)
