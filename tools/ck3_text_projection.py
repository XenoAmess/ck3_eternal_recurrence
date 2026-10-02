"""Pinned, reversible text projections for external CK3 mods (no game process).

Offsets refer to UTF-8-decoded text with BOM removed and LF newlines. This is
a structural brace scanner, not a CK3 grammar or scope validator.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


@dataclass(frozen=True)
class Block:
    key: str
    start: int
    opening: int
    end: int


def normalize(source: str) -> str:
    return source.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def digest(source: str) -> str:
    return hashlib.sha256(normalize(source).encode("utf-8")).hexdigest()


def masked(source: str) -> str:
    """Hide comments/quoted strings while preserving offsets and newlines."""
    output = list(source)
    quoted = comment = escaped = False
    for i, char in enumerate(source):
        if comment:
            if char == "\n":
                comment = False
            else:
                output[i] = " "
        elif quoted:
            if char != "\n":
                output[i] = " "
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == "#":
            output[i] = " "
            comment = True
        elif char == '"':
            output[i] = " "
            quoted = True
    if quoted:
        raise ValueError("unterminated quoted string")
    return "".join(output)


def blocks(source: str) -> list[Block]:
    """Locate key = { ... } at any depth, rejecting unbalanced braces."""
    clean = masked(source)
    stack: list[int] = []
    ends: dict[int, int] = {}
    for i, char in enumerate(clean):
        if char == "{":
            stack.append(i)
        elif char == "}":
            if not stack:
                raise ValueError(f"unmatched closing brace at {i}")
            ends[stack.pop()] = i + 1
    if stack:
        raise ValueError(f"unclosed brace at {stack[-1]}")
    return [Block(m.group(1), m.start(), m.end() - 1, ends[m.end() - 1])
            for m in re.finditer(r"([\w.@:-]+)\s*=\s*\{", clean)]


def named_block(source: str, key: str, name: str) -> Block:
    """Find an assignment whose first property is name = <quoted name>."""
    candidates = [b for b in blocks(source) if b.key == key and re.match(
        r'\s*name\s*=\s*"' + re.escape(name) + r'"',
        source[b.opening + 1:b.end - 1])]
    if len(candidates) != 1:
        raise ValueError(f"expected one {key} named {name}, found {len(candidates)}")
    return candidates[0]


def project(source: str, expected_sha256: str,
            replacements: list[tuple[str, str]]) -> str:
    source = normalize(source)
    if digest(source) != expected_sha256:
        raise ValueError("native source SHA-256 changed; review before regenerating")
    for before, after in replacements:
        if not before or before == after or source.count(before) != 1:
            raise ValueError("projection requires one unique, nonempty changed anchor")
        source = source.replace(before, after, 1)
    return source


def recover(projection: str, expected_sha256: str,
            replacements: list[tuple[str, str]]) -> str:
    source = normalize(projection)
    for before, after in reversed(replacements):
        if not after or source.count(after) != 1:
            raise ValueError("projection replacement is missing or ambiguous")
        source = source.replace(after, before, 1)
    if project(source, expected_sha256, replacements) != normalize(projection):
        raise ValueError("projection is not reversible")
    return source
