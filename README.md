# myesve

**CVE-2024-38475 Exploitation Framework – Version 1.0**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPLv3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

> **Disclaimer:** This tool is intended for authorized security testing, educational research, and legitimate bug bounty programs only. Do not use it against systems you do not own or lack explicit permission to test. The authors assume no liability for any misuse.

`myesve` is a modular tool that detects and exploits CVE-2024-38475, a source code disclosure vulnerability in Apache HTTP Server. It combines directory scanning, multi‑threaded exploitation, file downloading, and optional Mullvad VPN rotation.

Original discovery by [Orange Tsai](https://blog.orange.tw/).

## Features

- 403 directory discovery – multi‑threaded scanning for forbidden paths.
- Source code disclosure – exploits CVE-2024-38475 to retrieve PHP, configuration, and other files.
- Automatic file download – saves retrieved source code to a local directory.
- Mullvad VPN integration – rotate public IP before or during exploitation.
- Rate limiting – control requests per second to avoid detection or overloading the target.
- IP geolocation and traceroute – show VPN exit node location and network path to target.
- Colored console output – readable and informative terminal feedback.
- Bundled wordlists – includes SecLists’ `raft-medium` directories and files (no extra downloads).

## Installation

### Requirements

- Python 3.9 or newer.
- pip (usually included with Python).
- Mullvad VPN CLI – only needed if you use the `--vpn` or `vpn` subcommands. Install from [Mullvad](https://mullvad.net/download/).

### Install from Source

```bash
git clone https://github.com/yourname/myesve.git
cd myesve
pip install .
```

The `myesve` command becomes available system‑wide. Wordlists are bundled inside the package.

### Development / Editable Install

```bash
pip install -e .
```

Changes to the source code take effect immediately.

## Usage

### Subcommands

| Command | Description                                 |
|---------|---------------------------------------------|
| `scan`  | Find directories that return HTTP 403.      |
| `exploit` | Attempt source disclosure using 403 directories. |
| `vpn`   | Control Mullvad VPN (status, rotate, geolocation, traceroute). |
| `full`  | Run scan + exploit together, optionally with VPN rotation. |

### Examples

Scan for 403 directories:
```bash
myesve scan -t http://target.com -o dirs.txt
```

Exploit using the found directories:
```bash
myesve exploit -t http://target.com --directories-file dirs.txt --download
```

Rotate VPN and show location:
```bash
myesve vpn --rotate --country se
myesve vpn --info
```

Full automated scan + exploit with VPN rotation:
```bash
myesve full -t http://target.com --vpn --vpn-rotate-before --download
```

For all options, refer to the built-in help:
```bash
myesve --help
myesve scan --help
myesve exploit --help
myesve vpn --help
myesve full --help
```

## Project Structure

```
myesve/
├── myesve/
│   ├── __init__.py
│   ├── banner.py
│   ├── cli.py
│   ├── scanner.py
│   ├── exploiter.py
│   ├── vpn.py
│   ├── utils.py
│   ├── user_agents.py
│   ├── stealth.py
│   ├── output.py
│   ├── logger.py (may be deprecated)
│   ├── recon.py
│   └── wordlists/
│       ├── raft-medium-directories.txt
│       └── raft-medium-files.txt
├── pyproject.toml
├── README.md
├── DOCUMENTATION.md
└── LICENSE
```

## License

GNU Affero General Public License v3.0 (AGPLv3). See [LICENSE](LICENSE).

## Credits

- Orange Tsai – original discovery of CVE-2024-38475.
- Daniel Miessler – SecLists project for wordlists.
- Mullvad VPN – CLI tool for anonymity.

## Contributing

Issues and pull requests are welcome. Please open an issue first to discuss any significant changes.
```
