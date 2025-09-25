# Mullvad Relay List Builder

A small Python utility that fetches Mullvad's public WireGuard relay inventory, derives the corresponding SOCKS5 endpoints, and writes consumable relay lists for automation or browser PAC scripts. See [docs/spec.md](docs/spec.md) for detailed requirements and design notes.

## Quick Start

```bash
uv sync
uv run python build_relay_list.py --limit 20 --verbose
```

Artifacts are written to `build/mullvad_relays.json`, `build/mullvad_relays.txt`, and `build/mullvad_relays.pac` by default. Add `--emit-canonical-json` when you also want `build/mullvad_relays_canonical.json`, a validated-but-unenriched Mullvad payload that downstream tooling can reshape into other formats.

The text artifact is a newline-delimited list of bare `host:port` SOCKS5 endpoints that can be fed directly into tools such as [Mubeng](https://github.com/mubeng/mubeng):

```bash
mubeng run --proxy-file build/mullvad_relays.txt --address https://api.binance.com/api/v3/ping
```

The PAC artifact embeds the same endpoint list for browser automation.

### Filtering examples

- Include Mullvad-owned relays in Sweden alongside rented servers: `uv run python build_relay_list.py --countries sw --include-owned --providers-allow mullvad`
- United States & Canada relays from specific providers: `uv run python build_relay_list.py --countries us ca --providers-allow "m247,datacamp"`

Country filters accept full names, two-letter ISO prefixes, or location IDs (e.g. `us-chi`). Provider filters are case-insensitive.

### Proxy verification

Use the verifier to confirm SOCKS5 endpoints against custom targets (e.g., Binance public API):

```bash
uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 3 --http-url https://api.binance.com/api/v3/ping
```

Set `--ws-url` when you need to exercise an alternate WebSocket endpoint. Binance's WebSocket API expects JSON subscription payloads, so stick with the default echo server or implement a custom checker message before relying on WebSocket success ratios for Binance targets.

### Proxy Scraper Checker Integration

The pipeline supports enrichment via [Proxy Scraper Checker](https://github.com/monosans/proxy-scraper-checker) to validate and augment relay metadata with latency and availability information.

#### Installation

Install the proxy-scraper-checker binary using mise:

```bash
mise install --from git+https://github.com/monosans/proxy-scraper-checker.git --language=rust proxy-scraper-checker
```

#### Usage

After installation, the enricher can process JSON exports from proxy-scraper-checker to enhance relay metadata:

```python
from mullvad.proxy_checker import ProxyScraperChecker
from mullvad.enrich import enrich_relays

# Load proxy-scraper-checker results
checker = ProxyScraperChecker(Path("proxy_checker_results.json"))
result = enrich_relays(relays, proxy_checker=checker)
```

#### Expected JSON Schema

The ProxyScraperChecker supports various JSON output formats from proxy-scraper-checker:

**Direct format** (array of proxy objects):
```json
[
  {
    "socks5_endpoint": "relay.example.com:1080",
    "availability": "up",
    "latency_ms": 45,
    "country": "Sweden",
    "city": "Stockholm",
    "source": "proxy-scraper-checker",
    "protocol": "socks5"
  }
]
```

**Wrapped format** (proxies under key):
```json
{
  "proxies": [
    {
      "endpoint": "relay.example.com:1080",
      "status": "up",
      "latency": 89,
      "country": "Netherlands",
      "protocol": "socks5"
    }
  ]
}
```

**Alternative field mappings**:
- Endpoint: `socks5_endpoint`, `endpoint`, `proxy`, or `host`+`port`
- Availability: `availability`, `status`, or `alive`
- Latency: `latency_ms`, `latency`, or `ping`
- Protocol detection: `protocol` or `type` (must be "socks5")

The enricher automatically maps these field variations to a consistent internal format.

## Tests

```bash
uv run pytest
```

## References

- [Using a Random Mullvad SOCKS5 Proxy for Each Browser Request](https://k4yt3x.com/using-a-random-mullvad-socks5-proxy-for-each-browser-request/) — baseline workflow that inspired this automation.
