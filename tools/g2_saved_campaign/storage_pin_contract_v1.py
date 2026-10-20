"""Validate machine-readable SHA-256 pins before storage staging."""
from __future__ import annotations

from collections.abc import Mapping
import re

_SHA256 = re.compile(r"[0-9a-fA-F]{64}")


def require_sha256_pins(value: object, *, path: str = "$") -> None:
    """Check SHA-256 fields recursively without rewriting values or Git OIDs."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{path}: JSON key must be exact str")
            child_path = f"{path}.{key}"
            if key.lower() == "sha256" or key.lower().endswith("_sha256"):
                if type(child) is not str or _SHA256.fullmatch(child) is None:
                    raise ValueError(f"{child_path}: expected exact str with 64 hex digits")
            require_sha256_pins(child, path=child_path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            require_sha256_pins(child, path=f"{path}[{index}]")
