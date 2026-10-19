"""Use bounded C-encoder leaves while retaining compact JSON streaming.

Only exact built-in scalar containers with a conservative encoded-size bound
use JSONEncoder.encode. Large/nested containers remain streamed; unfamiliar
types retain the original encoder path. No whole result is materialized here.
"""
from __future__ import annotations

import json
import math

MAX_FAST_CHUNK_BYTES = 256 * 1024
MAX_FAST_ITEMS = 4096


def _scalar_upper_bytes(value: object, *, allow_nan: bool) -> int | None:
    kind = type(value)
    if kind is str:
        # UTF-8 needs at most four bytes/code point; JSON control escaping at
        # most six. This also bounds ensure_ascii=True surrogate escaping.
        return 12 * len(value) + 2
    if kind is int:
        return 21 if value.bit_length() <= 64 else None
    if kind is float:
        if not allow_nan and not math.isfinite(value):
            return None  # Keep the original encoder's rejection and message.
        return 32
    if kind is bool:
        return 5
    if value is None:
        return 4
    return None


def _flat_dict_fits(value: dict, encoder: json.JSONEncoder) -> bool:
    if len(value) > MAX_FAST_ITEMS:
        return False
    size = 2
    for key, item in value.items():
        if type(key) is not str:
            return False
        item_size = _scalar_upper_bytes(item, allow_nan=encoder.allow_nan)
        if item_size is None:
            return False
        size += 12 * len(key) + 2 + len(encoder.key_separator) + item_size
        if size > MAX_FAST_CHUNK_BYTES:
            return False
    size += max(0, len(value) - 1) * len(encoder.item_separator)
    return size <= MAX_FAST_CHUNK_BYTES


def iter_bounded_json_chunks_v1(value: object, encoder: json.JSONEncoder):
    """Yield the same compact JSON text, with bounded scalar-container batches.

    The bound applies to newly grouped fast leaves. An individual oversized
    string retains JSONEncoder's existing per-string allocation behavior.
    """
    if (type(encoder) is not json.JSONEncoder or encoder.indent is not None
            or (encoder.item_separator, encoder.key_separator) != (",", ":")):
        yield from encoder.iterencode(value)
        return
    markers: set[int] = set()

    def enter(container):
        if encoder.check_circular:
            identity = id(container)
            if identity in markers:
                raise ValueError("Circular reference detected")
            markers.add(identity)

    def leave(container):
        if encoder.check_circular:
            markers.remove(id(container))

    def walk(item):
        if type(item) is dict and all(type(key) is str for key in item):
            if _flat_dict_fits(item, encoder):
                yield encoder.encode(item)
                return
            enter(item)
            try:
                yield "{"
                entries = sorted(item.items()) if encoder.sort_keys else item.items()
                first = True
                for key, child in entries:
                    if not first:
                        yield encoder.item_separator
                    first = False
                    yield encoder.encode(key)
                    yield encoder.key_separator
                    yield from walk(child)
                yield "}"
            finally:
                leave(item)
        elif type(item) in (list, tuple):
            enter(item)
            try:
                yield "["
                position = 0
                first = True
                while position < len(item):
                    if not first:
                        yield encoder.item_separator
                    first = False
                    batch = []
                    size = 2
                    while position < len(item) and len(batch) < MAX_FAST_ITEMS:
                        child = item[position]
                        child_size = _scalar_upper_bytes(child, allow_nan=encoder.allow_nan)
                        if child_size is None:
                            break
                        added = child_size + (len(encoder.item_separator) if batch else 0)
                        if size + added > MAX_FAST_CHUNK_BYTES:
                            break
                        batch.append(child)
                        size += added
                        position += 1
                    if batch:
                        # The small temporary list owns references only, never
                        # copied result subtrees. Strip its two outer brackets.
                        yield encoder.encode(batch)[1:-1]
                    else:
                        yield from walk(item[position])
                        position += 1
                yield "]"
            finally:
                leave(item)
        else:
            yield from encoder.iterencode(item)

    yield from walk(value)
