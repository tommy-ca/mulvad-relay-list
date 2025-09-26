#!/usr/bin/env python3
"""Convert enriched Mullvad relay JSON output into CSV format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from mullvad.output import write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the enriched JSON artifact produced by the pipeline",
    )
    parser.add_argument(
        "destination",
        type=Path,
        help="Path where the CSV artifact should be written",
    )
    return parser.parse_args()


def load_enriched_relays(path: Path) -> Iterable[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - filesystem guard
        raise SystemExit(f"Failed to read JSON from {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON at {path}: {exc}") from exc

    if not isinstance(payload, list):
        raise SystemExit(f"Expected a list of relay objects in {path}")

    coerced: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            coerced.append(item)
        else:
            raise SystemExit("Relay entries must be JSON objects")
    return coerced


def main() -> int:
    args = parse_args()
    relays = load_enriched_relays(args.source)
    try:
        args.destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:  # pragma: no cover - filesystem guard
        raise SystemExit(f"Failed to prepare output directory: {exc}") from exc

    write_csv(relays, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
