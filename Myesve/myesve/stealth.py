"""Stealth techniques: adaptive rate limiting, timing jitter, UA rotation."""

import random
import threading
import time
from typing import List, Optional

from .user_agents import USER_AGENTS


class AdaptiveRateLimiter:
    """Adjusts request rate based on response times (AIMD)."""

    def __init__(
        self,
        base_rate: float = 0,
        min_rate: float = 0.5,
        max_rate: float = 20,
        increase_factor: float = 1.1,
        decrease_factor: float = 0.7,
        sample_window: int = 10,
    ):
        self.base_rate = base_rate
        self.current_rate = base_rate if base_rate > 0 else max_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self.sample_window = sample_window
        self.response_times: List[float] = []
        self.lock = threading.Lock()
        self.last = time.monotonic()
        self.enabled = base_rate > 0

    def record_response_time(self, seconds: float):
        if not self.enabled:
            return
        with self.lock:
            self.response_times.append(seconds)
            if len(self.response_times) > self.sample_window:
                self.response_times.pop(0)
            avg_time = sum(self.response_times) / len(self.response_times)
            # If average response time > 1 second, slow down; else speed up
            if avg_time > 1.0:
                self.current_rate *= self.decrease_factor
            else:
                self.current_rate *= self.increase_factor
            # Clamp
            self.current_rate = max(
                self.min_rate, min(self.max_rate, self.current_rate)
            )

    def wait(self):
        if not self.enabled:
            return
        with self.lock:
            now = time.monotonic()
            interval = 1.0 / self.current_rate if self.current_rate > 0 else 0
            elapsed = now - self.last
            if elapsed < interval:
                time.sleep(interval - elapsed)
            self.last = time.monotonic()


class Jitter:
    """Add random delay between requests."""

    def __init__(self, min_delay: float = 0, max_delay: float = 0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enabled = min_delay > 0 or max_delay > 0

    def sleep(self):
        if self.enabled:
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)


class UserAgentRotator:
    """Pick random User-Agent from list."""

    def __init__(self, ua_list: Optional[List[str]] = None):
        self.ua_list = ua_list or USER_AGENTS
        self.enabled = len(self.ua_list) > 0

    def get(self) -> str:
        if not self.enabled:
            return "python-requests/2.28.0"
        return random.choice(self.ua_list)
