"""Exact bodies projected from the sealed lossless save parser; no date decoder."""
from __future__ import annotations
import re

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}=]+')


def parse_block(body: str) -> list[dict]:
    tokens = TOKEN.findall(body)
    position = 0

    def value() -> str | list[dict]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError('truncated block value')
        token = tokens[position]
        position += 1
        if token != '{':
            if token in ('}', '='):
                raise ValueError('unexpected block token')
            return token
        entries = []
        while position < len(tokens) and tokens[position] != '}':
            key = None
            if position + 1 < len(tokens) and tokens[position + 1] == '=':
                key = tokens[position]
                position += 2
            entries.append({'key': key, 'value': value()})
        if position == len(tokens):
            raise ValueError('unterminated block')
        position += 1
        return entries

    parsed = value()
    if position != len(tokens) or not isinstance(parsed, list):
        raise ValueError('block was not consumed exactly')
    return parsed


def extract_exact_indented_block(text: str, key: str, depth: int) -> str:
    prefix = '\t' * depth
    pattern = rf'^{prefix}{re.escape(key)}=\{{\n(.*?)^{prefix}\}}'
    matches = list(re.finditer(pattern, text, re.M | re.S))
    if len(matches) != 1:
        raise ValueError(f'expected one block {key} at indentation {depth}; got {len(matches)}')
    return matches[0].group(0)


def block_body(raw: str) -> str:
    return raw[raw.index('{'):]


def one(entries: list[dict], key: str, *, required: bool = False):
    values = [entry['value'] for entry in entries if entry['key'] == key]
    if len(values) > 1 or (required and len(values) != 1):
        raise ValueError(f'nonunique or missing field {key}')
    return values[0] if values else None
