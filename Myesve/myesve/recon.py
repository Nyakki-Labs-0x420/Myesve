"""Optional Shodan and Censys integration for target discovery."""

from typing import Dict, List

# Optional imports – users must install the respective packages.
try:
    import shodan

    HAS_SHODAN = True
except ImportError:
    HAS_SHODAN = False

try:
    from censys.hosts import CensysHosts

    HAS_CENSYS = True
except ImportError:
    HAS_CENSYS = False


def shodan_search(api_key: str, query: str, limit: int = 10) -> List[Dict]:
    """Search Shodan for hosts matching query."""
    if not HAS_SHODAN:
        raise ImportError(
            "Shodan library not installed. Run: pip install shodan"
        )
    api = shodan.Shodan(api_key)
    results = api.search(query, limit=limit)
    return results.get("matches", [])


def censys_search(
    api_id: str, api_secret: str, query: str, limit: int = 10
) -> List[Dict]:
    """Search Censys for hosts matching query."""
    if not HAS_CENSYS:
        raise ImportError(
            "Censys library not installed. Run: pip install censys"
        )
    c = CensysHosts(api_id, api_secret)
    results = c.search(query, per_page=limit)
    return list(results)
