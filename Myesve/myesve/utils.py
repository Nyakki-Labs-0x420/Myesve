"""Utility classes and functions: rate limiting, IP info, traceroute."""

import platform
import subprocess
import threading
import time
from typing import Optional

import requests  # type: ignore
from termcolor import cprint  # type: ignore


class RateLimiter:
    """Rate limiter for controlling requests per second."""

    def __init__(self, rate_per_second: float) -> None:
        """Initialize with desired rate (0 = no limit)."""
        self.rate = rate_per_second
        self.interval = 1.0 / rate_per_second if rate_per_second > 0 else 0
        self.lock = threading.Lock()
        self.last = time.monotonic()

    def wait(self) -> None:
        """Wait if necessary to maintain the requested rate."""
        if self.rate <= 0:
            return
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last = time.monotonic()


def get_ip_info(ip: Optional[str] = None) -> Optional[dict]:
    """Fetch geolocation info for current public IP (or specified IP)."""
    try:
        if ip is None:
            resp = requests.get(
                "https://api.ipify.org?format=json", timeout=10
            )
            ip = resp.json()["ip"]
        info = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
        if info["status"] == "success":
            return {
                "ip": ip,
                "country": info.get("country"),
                "region": info.get("regionName"),
                "city": info.get("city"),
                "isp": info.get("isp"),
                "lat": info.get("lat"),
                "lon": info.get("lon"),
            }
    except Exception as e:
        cprint(f"[!] Failed to get IP info: {e}", "red")
    return None


def traceroute(target: str) -> str:
    """Run system traceroute and return output."""
    try:
        if platform.system().lower() == "windows":
            cmd = ["tracert", target]
        else:
            cmd = ["traceroute", target]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=False
        )
        return result.stdout
    except Exception as e:
        return f"Traceroute failed: {e}"


def get_proxy_dict(proxy_url: Optional[str]) -> Optional[dict]:
    """Convert proxy URL (http://, socks5://) to requests proxy dict."""
    if not proxy_url:
        return None
    # requests expects 'socks5' as scheme
    if proxy_url.startswith("socks5://"):
        return {"http": proxy_url, "https": proxy_url}
    if proxy_url.startswith("http://") or proxy_url.startswith("https://"):
        return {"http": proxy_url, "https": proxy_url}
    # assume http
    return {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
