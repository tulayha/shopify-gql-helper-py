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
        restore_rate: Number of points restored per second (leak rate, must be > 0)
        max_available: Maximum number of points the bucket can hold
        last_update: Timestamp of the last bucket update
    """

    available: float = 1000.0
    restore_rate: float = 100.0     # points per second
    max_available: float = 2000.0

    last_update: float = field(default_factory=time.monotonic)

    # Stats
    total_calls: int = field(init=False, default=0)
    total_cost: int = field(init=False, default=0)

    # Sync
    lock: threading.Lock = field(default_factory=threading.Lock)
    cond: threading.Condition = field(init=False)

    def __post_init__(self) -> None:
        self.cond = threading.Condition(self.lock)

    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        if name == "restore_rate" and float(value) <= 0:
            raise ValueError("restore_rate must be positive")
        super().__setattr__(name, value)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_update
        if elapsed > 0:
            self.available = min(self.max_available, self.available + elapsed * max(self.restore_rate, 0.0))
            self.last_update = now

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
        if min_sleep < 0:
            min_sleep = 1.0

        with self.cond:
            while True:
                self._refill()

                avg_cost = (self.total_cost / self.total_calls) if self.total_calls else 0
                # Decide how much we *really* need
                target = max(min_bucket, avg_cost if avg_cost > min_bucket else 0)

                if self.available >= target:
                    return

                sleep_time = max(min_sleep, (target - self.available) / self.restore_rate)

                # Wait releases the lock and reacquires it after timeout/notify
                self.cond.wait(timeout=sleep_time)

    def after_response(self, throttle_status: dict[str, Any] | None, cost: int | None = None) -> None:
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
        with self.cond:
            if throttle_status:
                # Trust server authoritative numbers
                ca = throttle_status.get("currentlyAvailable")
                rr = throttle_status.get("restoreRate")
                ma = throttle_status.get("maximumAvailable")

                if ca is not None:
                    self.available = float(ca)
                if rr is not None:
                    rr_val = float(rr)
                    if rr_val > 0:
                        self.restore_rate = rr_val
                if ma is not None:
                    self.max_available = float(ma)

                self.last_update = time.monotonic()

            if cost is not None:
                self.total_calls += 1
                self.total_cost += int(cost)

            self.cond.notify_all()
