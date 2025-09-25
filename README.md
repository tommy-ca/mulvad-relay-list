# Mullvad Relay List Builder

A small Python utility that fetches Mullvad's public WireGuard relay inventory, derives the corresponding SOCKS5 endpoints, and writes consumable relay lists for automation or browser PAC scripts. See [docs/spec.md](docs/spec.md) for detailed requirements and design notes.

## Quick Start

```bash
uv sync
uv run python build_relay_list.py --limit 20 --verbose
```

Artifacts are written to `build/mullvad_relays.json`, `build/mullvad_relays.txt`, and `build/mullvad_relays.pac` by default.

### Filtering examples

- Include Mullvad-owned relays in Sweden alongside rented servers: `uv run python build_relay_list.py --countries sw --include-owned --providers-allow mullvad`
- United States & Canada relays from specific providers: `uv run python build_relay_list.py --countries us ca --providers-allow "m247,datacamp"`

Country filters accept full names, two-letter ISO prefixes, or location IDs (e.g. `us-chi`). Provider filters are case-insensitive.

### Proxy verification

Use the verifier to confirm SOCKS5 endpoints against custom targets (e.g., Binance public API):

```bash
uv run python scripts/verify_proxies.py --json build/mullvad_relays.json --limit 3 --http-url https://api.binance.com/api/v3/ping
```

Set `--ws-url` when you need to exercise an alternate WebSocket endpoint.

## Tests

```bash
uv run pytest
```

## References

- [Using a Random Mullvad SOCKS5 Proxy for Each Browser Request](https://k4yt3x.com/using-a-random-mullvad-socks5-proxy-for-each-browser-request/) — baseline workflow that inspired this automation.
