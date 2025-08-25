"""Per-shop throttle controller."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ThrottleController:
    """Thread-safe controller for Shopify API throttling."""

    lock: threading.Lock = field(default_factory=threading.Lock)
    cond: threading.Condition = field(init=False)
    available: int = 1000
    restore_rate: int = 50
    max_available: int = 1000
    last_update: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.cond = threading.Condition(self.lock)

    def before_request(self, min_bucket: int, min_sleep: float) -> None:
        with self.cond:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.available = min(
                self.max_available, self.available + elapsed * self.restore_rate
            )
            self.available = int(self.available)
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
                self.available = min(
                    self.max_available, self.available + elapsed * self.restore_rate
                )
                self.available = int(self.available)
                self.last_update = now

    def after_response(self, throttle_status: Optional[dict]) -> None:
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
