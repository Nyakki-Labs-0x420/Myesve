"""Directory scanner to find 403 endpoints with stealth and logging."""

import threading
import time
from queue import Queue
from typing import List, Optional

import requests  # type: ignore
from termcolor import cprint  # type: ignore

from .logger import setup_logger
from .stealth import AdaptiveRateLimiter, Jitter, UserAgentRotator
from .utils import get_proxy_dict


class DirectoryScanner:
    """Scan directories with stealth, proxy, and logging."""

    def __init__(
        self,
        base_url: str,
        wordlist_path: str,
        threads: int = 10,
        rate: float = 0,
        timeout: float = 5,
        adaptive_rate: bool = False,
        jitter_min: float = 0,
        jitter_max: float = 0,
        rotate_ua: bool = False,
        proxy: Optional[str] = None,
        log_file: Optional[str] = None,
        log_level: str = "INFO",
    ):
        self.base_url = base_url.rstrip("/")
        self.wordlist_path = wordlist_path
        self.threads = threads
        self.timeout = timeout
        self.results: List[str] = []
        self.lock = threading.Lock()

        # Rate limiting – explicit type annotation to avoid mypy error
        if adaptive_rate and rate > 0:
            self.rate_limiter: Optional[AdaptiveRateLimiter] = (
                AdaptiveRateLimiter(base_rate=rate)
            )
        else:
            self.rate_limiter = (
                AdaptiveRateLimiter(base_rate=rate) if rate > 0 else None
            )

        self.jitter = Jitter(jitter_min, jitter_max)
        self.ua_rotator = UserAgentRotator() if rotate_ua else None
        self.proxies = get_proxy_dict(proxy)
        self.logger = setup_logger(log_file, log_level, console=False)
        self.logger.info("Scanner initialized for %s", base_url)

    def load_wordlist(self) -> List[str]:
        try:
            with open(
                self.wordlist_path, "r", encoding="utf-8", errors="replace"
            ) as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            cprint(f"[!] Wordlist not found: {self.wordlist_path}", "red")
            self.logger.error("Wordlist not found: %s", self.wordlist_path)
            return []

    def worker(self, queue: Queue):
        session = requests.Session()
        if self.proxies:
            session.proxies.update(self.proxies)

        while True:
            try:
                directory = queue.get_nowait()
            except Exception:
                break

            url = f"{self.base_url}/{directory}/"
            if self.rate_limiter:
                self.rate_limiter.wait()
            self.jitter.sleep()

            headers = {}
            if self.ua_rotator:
                headers["User-Agent"] = self.ua_rotator.get()

            start = time.time()
            try:
                r = session.get(
                    url,
                    allow_redirects=False,
                    timeout=self.timeout,
                    headers=headers,
                )
                elapsed = time.time() - start
                if self.rate_limiter:
                    self.rate_limiter.record_response_time(elapsed)

                if r.status_code == 403:
                    with self.lock:
                        self.results.append(directory)
                        cprint(f"[+] 403 Found: {directory}", "green")
                        self.logger.info("Found 403: %s", directory)
                else:
                    self.logger.debug("%s -> %s", url, r.status_code)
            except requests.exceptions.RequestException as e:
                self.logger.debug("Request failed %s: %s", url, e)
            finally:
                queue.task_done()

    def scan(self) -> List[str]:
        directories = self.load_wordlist()
        if not directories:
            return []
        if self.rate_limiter and self.rate_limiter.enabled:
            rate_str = "adaptive"
        else:
            rate_str = (
                str(self.rate_limiter.current_rate)
                if self.rate_limiter
                else "unlimited"
            )
        cprint(
            f"\n[*] Scanning {len(directories)} directories "
            f"(threads={self.threads}, rate={rate_str}/s)...",
            "yellow",
        )
        self.logger.info("Starting scan of %d directories", len(directories))

        queue: Queue = Queue()
        for d in directories:
            queue.put(d)
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.logger.info(
            "Scan complete. Found %d directories", len(self.results)
        )
        return self.results
