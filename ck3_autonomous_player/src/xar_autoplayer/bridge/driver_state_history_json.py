"""Exact JSON history reuse for the native driver's atomic full-state file.

The owner holds its state/history lock for every call and invalidates this
cache before the one supported in-place history-row update. A new history list
(restore, succession, or episode seed) always rebuilds the cache.
"""

from __future__ import annotations

import json


_JSON_OPTIONS = {"ensure_ascii": False, "separators": (",", ":")}
_MAX_CACHED_HISTORY_BYTES = 256 * 1024 * 1024


class DriverStateHistoryJsonCache:
    """Cache only the history array's canonical JSON, never a state envelope."""

    def __init__(self) -> None:
        self.invalidate()

    def invalidate(self) -> None:
        self._history: list[dict[str, object]] | None = None
        self._count = 0
        self._first_row: dict[str, object] | None = None
        self._last_row: dict[str, object] | None = None
        self._encoded = bytearray()

    def encode(self, history: list[dict[str, object]]) -> bytes | bytearray:
        """Return a locked, owned buffer; callers must copy it before unlock."""
        if (
            history is not self._history
            or len(history) < self._count
            or (self._count and (
                history[0] is not self._first_row
                or history[self._count - 1] is not self._last_row
            ))
        ):
            self.invalidate()
            encoded = json.dumps(history, **_JSON_OPTIONS).encode("utf-8")
            if len(encoded) > _MAX_CACHED_HISTORY_BYTES:
                return encoded
            self._history = history
            self._count = len(history)
            self._first_row = history[0] if history else None
            self._last_row = history[-1] if history else None
            self._encoded = bytearray(encoded)
            return self._encoded

        if len(history) > self._count:
            # Serialize every new row before touching the previous valid cache.
            additions = b",".join(
                json.dumps(row, **_JSON_OPTIONS).encode("utf-8")
                for row in history[self._count:]
            )
            growth = len(additions) + (1 if self._count else 0)
            if len(self._encoded) + growth > _MAX_CACHED_HISTORY_BYTES:
                self.invalidate()
                return json.dumps(history, **_JSON_OPTIONS).encode("utf-8")
            self._encoded.pop()  # array closing bracket
            if self._count:
                self._encoded.extend(b",")
            self._encoded.extend(additions)
            self._encoded.extend(b"]")
            self._count = len(history)
            self._first_row = history[0]
            self._last_row = history[-1]
        return self._encoded


def driver_state_json_parts(
    payload: dict[str, object], cache: DriverStateHistoryJsonCache,
) -> tuple[bytes, bytes | bytearray, bytes]:
    """Split only at command_history, preserving standard dumps field order."""
    keys = list(payload)
    index = keys.index("command_history")
    history = payload["command_history"]
    if not isinstance(history, list):
        raise TypeError("command_history must be a list")
    head = {key: payload[key] for key in keys[:index]}
    tail = {key: payload[key] for key in keys[index + 1:]}
    if not head or not tail:
        raise ValueError("driver state history must have surrounding fields")
    prefix = json.dumps(head, **_JSON_OPTIONS).encode("utf-8")[:-1]
    body = cache.encode(history)
    suffix = json.dumps(tail, **_JSON_OPTIONS).encode("utf-8")[1:]
    return prefix + b',"command_history":', body, b"," + suffix
