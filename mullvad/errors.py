"""Custom exceptions for the Mullvad relay tooling."""


class RelayBuildError(RuntimeError):
    """Raised when building the relay list fails in a recoverable way."""


__all__ = ["RelayBuildError"]
