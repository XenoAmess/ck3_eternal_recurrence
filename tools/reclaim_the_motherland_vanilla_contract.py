"""Exact CK3 1.21.0 source contract; no runtime or semantic compatibility claim."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get("RMTM_CK3_GAME_ROOT", str(ROOT / "Crusader Kings III/game")))
CONTRACT_PATH = ROOT / "tools/reclaim_the_motherland_vanilla_1_21_0.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
if (CONTRACT["game_version"], CONTRACT["steam_build_id"], CONTRACT["exe_sha256"]) != (
    "1.21.0", "26622941", "2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc"
):
    raise ValueError("RMTM vanilla contract targets a different exact build")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def extract_definition(source: str, name: str = "offer_vassalization_interaction") -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(re.finditer(rf"^{re.escape(name)}\s*=\s*\{{", source, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"definition count for {name}: {len(matches)}, expected 1")
    start = matches[0].start()
    brace = source.find("{", start)
    depth = 0
    quoted = escaped = in_comment = False
    for index in range(brace, len(source)):
        char = source[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and char == "#":
            in_comment = True
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1] + "\n"
    raise ValueError(f"unterminated definition: {name}")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label} anchor count is {count}, expected exactly 1")
    return source.replace(old, new, 1)


def assert_source_files(game: Path = GAME) -> None:
    for relative, expected in CONTRACT["files"].items():
        actual = sha256_bytes((game / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"vanilla file changed: {relative}: {actual}; expected {expected}")


def definition(name: str, game: Path = GAME) -> str:
    item = CONTRACT["definitions"][name]
    raw = (game / item["file"]).read_bytes()
    expected_file = CONTRACT["files"][item["file"]]
    if sha256_bytes(raw) != expected_file:
        raise ValueError(f"vanilla source file changed: {item['file']}")
    body = extract_definition(raw.decode("utf-8-sig"), name)
    assert_definition(body, name)
    return body


def assert_definition(body: str, name: str) -> None:
    expected = CONTRACT["definitions"][name]["normalized_text_sha256"]
    actual = sha256_bytes(body.encode("utf-8"))
    if actual != expected:
        raise ValueError(f"vanilla {name} body changed: {actual}; expected {expected}")


def header(names: tuple[str, ...], note: str) -> str:
    rows = ["# GENERATED FILE. DO NOT EDIT.", "# CK3 1.21.0 / Steam build 26622941 source projection."]
    for name in names:
        item = CONTRACT["definitions"][name]
        rows.append(f"# Vanilla {item['file']} SHA-256: {CONTRACT['files'][item['file']]}")
        rows.append(f"# Vanilla {name} SHA-256: {item['normalized_text_sha256']}")
    return "\n".join(rows) + f"\n# {note}\n\n"
