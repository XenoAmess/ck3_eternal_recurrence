"""Load repository and artifact JSON with a strict UTF-8 BOM-safe contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonInputContractError(ValueError):
    """A JSON input could not satisfy the UTF-8 document contract."""


def load_json_document(path: Path) -> Any:
    """Load BOM-free UTF-8 or UTF-8 with one leading BOM.

    ``utf-8-sig`` consumes the optional UTF-8 BOM while retaining strict UTF-8
    decoding.  Malformed JSON and non-UTF-8 inputs are reported through one
    stable exception type so artifact runners fail before using partial data.
    """

    resolved = path.expanduser().resolve()
    try:
        text = resolved.read_text(encoding="utf-8-sig", errors="strict")
        return json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise JsonInputContractError(
            f"invalid UTF-8 JSON input {resolved}: {type(error).__name__}: {error}"
        ) from error


def load_json_object(path: Path, *, expected_schema: str | None = None) -> dict[str, Any]:
    """Load a top-level JSON object and optionally bind its schema identity."""

    value = load_json_document(path)
    if not isinstance(value, dict):
        raise JsonInputContractError(f"JSON input is not an object: {path}")
    if expected_schema is not None and value.get("schema") != expected_schema:
        raise JsonInputContractError(
            f"JSON input schema differs for {path}: {value.get('schema')!r}"
        )
    return value
