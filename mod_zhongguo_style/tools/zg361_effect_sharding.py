#!/usr/bin/env python3
"""Deterministic purpose sharding for generated CK3 scripted effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


MAX_EFFECTS_PER_SHARD = 10


@dataclass(frozen=True)
class EffectEntry:
    name: str
    segment: str
    block: str


@dataclass(frozen=True)
class EffectShard:
    purpose: str
    part: int
    names: tuple[str, ...]
    body: str


def _block_end(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unterminated top-level scripted effect")


def top_level_effect_entries(source: bytes | str, *, generated_header: str = "") -> tuple[EffectEntry, ...]:
    if isinstance(source, bytes):
        text = source.decode("utf-8-sig")
    else:
        text = source.removeprefix("\ufeff")
    if generated_header and text.startswith(generated_header):
        text = text[len(generated_header) :]

    entries: list[EffectEntry] = []
    cursor = 0
    search = 0
    while search < len(text):
        line_end = text.find("\n", search)
        if line_end < 0:
            line_end = len(text)
        line = text[search:line_end]
        stripped = line.lstrip()
        # Generated top-level definitions are flush-left.  Nested calls may be
        # flush-left inside a block, so skip directly to the matching close.
        if line == stripped and "=" in line and stripped.endswith("{"):
            name, separator, suffix = stripped.partition("=")
            name = name.strip()
            if (
                separator
                and suffix.strip() == "{"
                and name
                and all(char.isalnum() or char == "_" for char in name)
            ):
                opening = text.find("{", search, line_end + 1)
                end = _block_end(text, opening)
                entries.append(
                    EffectEntry(
                        name=name,
                        segment=text[cursor:end],
                        block=text[search:end],
                    )
                )
                cursor = end
                search = end
                continue
        search = line_end + 1

    if not entries:
        raise ValueError("generated source contains no top-level scripted effects")
    tail = text[cursor:]
    if tail:
        last = entries[-1]
        entries[-1] = EffectEntry(last.name, last.segment + tail, last.block)
    return tuple(entries)


def top_level_effect_blocks(source: bytes | str, *, generated_header: str = "") -> tuple[tuple[str, str], ...]:
    return tuple(
        (entry.name, entry.block)
        for entry in top_level_effect_entries(source, generated_header=generated_header)
    )


def plan_effect_shards(
    source: bytes | str,
    *,
    generated_header: str,
    classify: Callable[[str], str],
    max_effects: int = MAX_EFFECTS_PER_SHARD,
) -> tuple[EffectShard, ...]:
    if not 1 <= max_effects <= MAX_EFFECTS_PER_SHARD:
        raise ValueError(f"effect shard limit must be in 1..{MAX_EFFECTS_PER_SHARD}")
    entries = top_level_effect_entries(source, generated_header=generated_header)
    grouped: list[tuple[str, list[EffectEntry]]] = []
    for entry in entries:
        purpose = classify(entry.name)
        if not purpose:
            raise ValueError(f"empty purpose for scripted effect {entry.name}")
        if not grouped or grouped[-1][0] != purpose:
            grouped.append((purpose, []))
        grouped[-1][1].append(entry)

    shards: list[EffectShard] = []
    for purpose, group in grouped:
        for offset in range(0, len(group), max_effects):
            chunk = group[offset : offset + max_effects]
            shards.append(
                EffectShard(
                    purpose=purpose,
                    part=offset // max_effects + 1,
                    names=tuple(entry.name for entry in chunk),
                    body="".join(entry.segment for entry in chunk),
                )
            )
    return tuple(shards)
