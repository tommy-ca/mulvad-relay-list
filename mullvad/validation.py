"""Relay validation helpers to guard against schema drift and missing data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .errors import RelayBuildError
from .transform import Relay


@dataclass(slots=True)
class ValidationIssue:
    """Represents a relay that was rejected during validation."""

    relay: Relay
    reason: str


@dataclass(slots=True)
class ValidationResult:
    """Outcome of validating a batch of relays."""

    valid_relays: List[Relay]
    issues: List[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


class ValidationError(RelayBuildError):
    """Raised when validation cannot proceed due to schema regressions."""


REQUIRED_FIELDS = (
    "hostname",
    "socks5_endpoint",
    "provider",
    "location_id",
    "ipv4",
)


def validate_relays(relays: Iterable[Relay]) -> ValidationResult:
    """Validate relays, returning accepted entries and any issues."""

    valid: List[Relay] = []
    issues: List[ValidationIssue] = []

    for relay in relays:
        missing = [field for field in REQUIRED_FIELDS if not getattr(relay, field)]
        if missing:
            issues.append(
                ValidationIssue(
                    relay=relay,
                    reason=f"missing fields: {', '.join(missing)}",
                )
            )
            continue
        valid.append(relay)

    return ValidationResult(valid_relays=valid, issues=issues)


__all__ = [
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "validate_relays",
]
