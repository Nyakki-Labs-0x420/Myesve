"""Mullvad VPN controller for server rotation and status."""

import random
import subprocess
import time
from typing import Optional

from termcolor import cprint  # type: ignore

from .utils import get_ip_info


class MullvadController:
    """Control Mullvad VPN CLI: connect, rotate, show status."""

    def __init__(self) -> None:
        """Check if Mullvad CLI is available."""
        self.available = self._check_mullvad()
        if not self.available:
            cprint(
                "[!] Mullvad CLI not found. VPN rotation disabled.",
                "yellow",
            )

    def _check_mullvad(self) -> bool:
        """Return True if 'mullvad version' succeeds."""
        try:
            subprocess.run(
                ["mullvad", "version"], capture_output=True, check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_current_server(self) -> Optional[str]:
        """Get current Mullvad server hostname, or None if not available."""
        if not self.available:
            return None
        try:
            result = subprocess.run(
                ["mullvad", "relay", "get"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def rotate_server(self, country: Optional[str] = None) -> bool:
        """Connect to a random Mullvad server, optionally filtered by country."""
        if not self.available:
            return False
        try:
            result = subprocess.run(
                ["mullvad", "relay", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            relays = result.stdout
            lines = relays.splitlines()
            candidates = []
            for line in lines:
                if (
                    line.strip()
                    and not line.startswith(" ")
                    and line != "Relays:"
                ):
                    parts = line.split()
                    hostname = parts[0]
                    if country and country.lower() not in hostname.lower():
                        continue
                    candidates.append(hostname)
            if not candidates:
                cprint("[!] No matching VPN servers found.", "red")
                return False
            chosen = random.choice(candidates)
            subprocess.run(
                ["mullvad", "relay", "set", "location", chosen],
                check=True,
            )
            subprocess.run(["mullvad", "connect"], check=True)
            time.sleep(5)
            cprint(f"[+] VPN rotated to {chosen}", "green")
            self.show_current_location()
            return True
        except Exception as e:
            cprint(f"[!] VPN rotation failed: {e}", "red")
            return False

    def disconnect(self) -> None:
        """Disconnect Mullvad VPN."""
        if self.available:
            subprocess.run(
                ["mullvad", "disconnect"], capture_output=True, check=False
            )

    def show_current_location(self) -> None:
        """Print current public IP and geolocation."""
        info = get_ip_info()
        if info:
            cprint(
                f"[*] Current IP: {info['ip']} | "
                f"Location: {info['city']}, {info['country']} | "
                f"ISP: {info['isp']}",
                "cyan",
            )
        else:
            cprint(
                "[*] Could not determine current IP location.",
                "yellow",
            )
