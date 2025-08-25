"""Per-shop throttle controller."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThrottleController:
    """Thread-safe controller for Shopify API rate limiting and throttling.
    
    This class implements the leaky bucket algorithm to respect Shopify's rate limits.
    It's thread-safe and can be shared across multiple threads making API requests.
    
    Attributes:
        available: Current number of available request points in the bucket
        restore_rate: Number of points restored per second (leak rate)
        max_available: Maximum number of points the bucket can hold
        last_update: Timestamp of the last bucket update
    """

    lock: threading.Lock = field(default_factory=threading.Lock)
    cond: threading.Condition = field(init=False)
    available: int = 1000
    restore_rate: int = 50
    max_available: int = 1000
    last_update: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.cond = threading.Condition(self.lock)

    def before_request(self, min_bucket: int, min_sleep: float) -> None:
        """Check if we can make a request, or sleep until we can.
        
        This should be called before making an API request. It will block if necessary
        to respect rate limits.
        
        Args:
            min_bucket: Minimum number of points that should be available before
                allowing a request to proceed
            min_sleep: Minimum time to sleep when rate limited (in seconds)
                
        Note:
            This method is thread-safe and will block the calling thread if the rate
            limit would be exceeded.
        """
        with self.cond:
            now = time.monotonic()
            elapsed = now - self.last_update
            new_available = min(
                self.max_available, self.available + elapsed * self.restore_rate
            )
            self.available = int(new_available)
            self.last_update = now
            if self.available < min_bucket:
                if self.restore_rate <= 0:
                    sleep_time = min_sleep
                else:
                    sleep_time = max(
                        min_sleep,
                        (min_bucket - self.available) / self.restore_rate,
                    )
                self.cond.wait(timeout=sleep_time)
                now = time.monotonic()
                elapsed = now - self.last_update
                new_available = min(
                    self.max_available, self.available + elapsed * self.restore_rate
                )
                self.available = int(new_available)
                self.last_update = now

    def after_response(self, throttle_status: dict[str, Any] | None) -> None:
        """Update rate limiting information after a request completes.
        
        This should be called after receiving a response from the Shopify API to
        update our rate limiting information based on the server's response.
        
        Args:
            throttle_status: The throttle status from the Shopify API response,
                typically found in `extensions.cost.throttleStatus`
                
        Note:
            This method is thread-safe and will notify any waiting threads when the
            rate limit status changes.
        """
        if not throttle_status:
            return
        with self.cond:
            self.available = int(
                throttle_status.get("currentlyAvailable", self.available)
            )
            self.restore_rate = int(
                throttle_status.get("restoreRate", self.restore_rate)
            )
            self.max_available = int(
                throttle_status.get("maximumAvailable", self.max_available)
            )
            self.last_update = time.monotonic()
            self.cond.notify_all()
