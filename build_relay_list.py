#!/usr/bin/env python3
"""CLI for building Mullvad SOCKS5 relay lists."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set

from mullvad.api import MullvadAPI
from mullvad.errors import RelayBuildError
from mullvad.output import write_json, write_text, write_pac
from mullvad.transform import FilterConfig, Relay, build_relays, filter_relays


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--countries",
        nargs="*",
        help="Country names, ISO codes, or location IDs to include",
    )
    parser.add_argument(
        "--cities",
        nargs="*",
        help="City names or location IDs to include",
    )
    parser.add_argument(
        "--include-owned",
        action="store_true",
        help="Include Mullvad owned relays in the output (excluded by default)",
    )
    parser.add_argument(
        "--providers-allow",
        help="Comma-separated list of provider names to allow exclusively",
    )
    parser.add_argument(
        "--providers-block",
        help="Comma-separated list of provider names to exclude",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of relays in the output after filtering",
    )
    parser.add_argument(
        "--output-dir",
        default="build",
        help="Directory to write artifact files into (default: build)",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=300,
        help="Cache TTL for API responses in seconds (default: 300)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass on-disk cache and fetch fresh data",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def log(message: str) -> None:
        if args.verbose:
            timestamp = dt.datetime.now().isoformat(timespec="seconds")
            print(f"[{timestamp}] {message}")

    cache_dir = Path(".cache")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)

    api_client = MullvadAPI(
        cache_dir=cache_dir,
        ttl_seconds=args.cache_ttl,
        use_cache=not args.no_cache,
    )

    log("Fetching Mullvad relay data")
    payload = api_client.fetch_wireguard_relays(force_refresh=args.no_cache)

    log("Transforming relays")
    relays = build_relays(payload)

    config = FilterConfig(
        countries=_list_to_set(args.countries),
        cities=_list_to_set(args.cities),
        include_owned=args.include_owned,
        providers_allow=_csv_to_set(args.providers_allow),
        providers_block=_csv_to_set(args.providers_block),
        limit=args.limit,
    )

    filtered = filter_relays(relays, config)

    if not filtered:
        print("No relays matched the provided filters", file=sys.stderr)
        return 1

    json_path = output_dir / "mullvad_relays.json"
    text_path = output_dir / "mullvad_relays.txt"

    log(f"Writing JSON to {json_path}")
    write_json(filtered, json_path)

    log(f"Writing text list to {text_path}")
    write_text(filtered, text_path)

    pac_path = output_dir / "mullvad_relays.pac"
    log(f"Writing PAC script to {pac_path}")
    write_pac(filtered, pac_path)

    print(f"Wrote {len(filtered)} relays to {json_path}, {text_path}, and {pac_path}")
    return 0


def _list_to_set(values: Optional[Sequence[str]]) -> Optional[Set[str]]:
    if not values:
        return None
    return {value.strip().lower() for value in values if value.strip()}


def _csv_to_set(value: Optional[str]) -> Optional[Set[str]]:
    if not value:
        return None
    return {item.strip().lower() for item in value.split(",") if item.strip()}


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RelayBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
