"""Weighted random selection utilities for relay lists."""

from __future__ import annotations

import random
from typing import Iterable, Optional, Sequence

from .transform import Relay


def pick_random(
    relays: Sequence[Relay],
    *,
    weighted: bool = True,
    rng: Optional[random.Random] = None,
) -> Relay:
    """Pick a random relay, optionally applying weight-based selection."""

    if not relays:
        raise ValueError("Relay sequence is empty")

    rng = rng or random
    if weighted:
        weights = [max(relay.weight, 1) for relay in relays]
        try:
            return rng.choices(relays, weights=weights, k=1)[0]
        except AttributeError:  # pragma: no cover - ancient Python fallback
            # Fallback: manual roulette-wheel selection
            total = sum(weights)
            pick = (rng.random() if callable(getattr(rng, "random", None)) else random.random()) * total
            cumulative = 0
            for relay, weight in zip(relays, weights):
                cumulative += weight
                if pick <= cumulative:
                    return relay
            return relays[-1]
    else:
        idx = rng.randrange(len(relays))  # type: ignore[arg-type]
        return relays[idx]


__all__ = ["pick_random"]
