#!/usr/bin/env python3
"""Inspect selected CK3 character variables and persistent lists offline.

The caller chooses one root CharacterID or a variable used to discover roots,
plus root variables, lists, and variables to read from Character references
followed through those lists.  The report is path-neutral, hash-bound
prelaunch evidence; exact-build live MCP remains the authority for current
game state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Iterator, Sequence

from inspect_ck3_save_player_topology import _numeric_records, _sha256


SCHEMA_VERSION = 1
KIND = "ck3_character_scope_offline_v1"
DISCOVERY_KIND = "ck3_character_scope_discovery_offline_v1"


def _anonymous_records(text: str) -> Iterator[str]:
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        if lines[index].strip() != "{" or index + 1 >= len(lines):
            index += 1
            continue
        discriminator = lines[index + 1].strip()
        if not (discriminator.startswith('flag="') or discriminator.startswith('name="')):
            index += 1
            continue
        depth = 0
        record: list[str] = []
        while index < len(lines):
            line = lines[index]
            record.append(line)
            depth += line.count("{") - line.count("}")
            index += 1
            if depth == 0:
                yield "".join(record)
                break


def _variable_record(record: str) -> tuple[str, dict[str, object]] | None:
    name = re.search(r'(?m)^\s*flag="([^"]+)"$', record)
    if name is None:
        return None
    value_type = re.search(r"(?m)^\s*type=([^\s]+)$", record)
    identity = re.search(r"(?m)^\s*identity=(-?\d+)$", record)
    kind = value_type.group(1) if value_type is not None else None
    raw_identity = int(identity.group(1)) if identity is not None else None
    result: dict[str, object] = {
        "present": True,
        "type": kind,
        "identity": raw_identity,
    }
    if kind == "value":
        result["number"] = (raw_identity or 0) / 100000
    elif kind == "char":
        result["character_id"] = raw_identity
    return name.group(1), result


def _list_record(record: str) -> tuple[str, dict[str, object]] | None:
    name = re.search(r'(?m)^\s*name="([^"]+)"$', record)
    if name is None:
        return None
    items = []
    pattern = re.compile(
        r"item=\{\s*type=([^\s]+)(?:\s+identity=(-?\d+))?\s*\}",
        re.DOTALL,
    )
    for match in pattern.finditer(record):
        item: dict[str, object] = {
            "type": match.group(1),
            "identity": int(match.group(2)) if match.group(2) is not None else None,
        }
        items.append(item)
    duration = re.search(r"duration=\{\s*(-?\d+)\s*\}", record, re.DOTALL)
    return name.group(1), {
        "present": True,
        "item_count": len(items),
        "duration": int(duration.group(1)) if duration is not None else None,
        "items": items,
    }


def _selected_scope(
    block: str | None,
    *,
    variable_names: Sequence[str],
    list_names: Sequence[str],
) -> dict[str, object]:
    variables = {
        name: {"present": False, "type": None, "identity": None}
        for name in variable_names
    }
    lists = {
        name: {"present": False, "item_count": 0, "duration": None, "items": []}
        for name in list_names
    }
    if block is None:
        return {"found": False, "alive": False, "variables": variables, "lists": lists}
    for record in _anonymous_records(block):
        variable = _variable_record(record)
        if variable is not None and variable[0] in variables:
            variables[variable[0]] = variable[1]
        listed = _list_record(record)
        if listed is not None and listed[0] in lists:
            lists[listed[0]] = listed[1]
    return {
        "found": True,
        "alive": "\n\t\talive_data={" in block,
        "variables": variables,
        "lists": lists,
    }


def _character_blocks(path: Path, wanted: set[int]) -> dict[int, str]:
    found: dict[int, str] = {}
    for level, record_id, block in _numeric_records(path):
        if level == 1 and record_id in wanted:
            found[record_id] = block
            if len(found) == len(wanted):
                break
    return found


def _game_version(path: Path) -> str | None:
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = re.fullmatch(r'version="([^"]+)"', line.strip())
            if match is not None:
                return match.group(1)
    return None


def _referenced_scopes(
    path: Path,
    roots: Sequence[dict[str, object]],
    referenced_variables: Sequence[str],
) -> tuple[int, list[dict[str, object]]]:
    references: set[int] = set()
    for root in roots:
        for listed in root["lists"].values():
            for item in listed["items"]:
                if item.get("type") == "char" and isinstance(item.get("identity"), int):
                    references.add(int(item["identity"]))
    referenced_blocks = _character_blocks(path, references) if references else {}
    referenced = []
    for character_id in sorted(references):
        scope = _selected_scope(
            referenced_blocks.get(character_id),
            variable_names=referenced_variables,
            list_names=(),
        )
        referenced.append({"character_id": character_id, **scope})
    return len(references), referenced


def inspect_melted(
    path: Path,
    *,
    root_character_id: int,
    root_variables: Sequence[str] = (),
    list_names: Sequence[str] = (),
    referenced_variables: Sequence[str] = (),
) -> dict[str, object]:
    root_blocks = _character_blocks(path, {root_character_id})
    root_scope = _selected_scope(
        root_blocks.get(root_character_id),
        variable_names=root_variables,
        list_names=list_names,
    )
    reference_count, referenced = _referenced_scopes(
        path, [root_scope], referenced_variables
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "result": "GREEN",
        "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
        "game_version": _game_version(path),
        "root_character_id": root_character_id,
        "requested_root_variables": list(root_variables),
        "requested_lists": list(list_names),
        "requested_referenced_variables": list(referenced_variables),
        "root": root_scope,
        "unique_referenced_character_count": reference_count,
        "referenced_characters": referenced,
    }


def inspect_discovery_melted(
    path: Path,
    *,
    discovery_variable: str,
    root_variables: Sequence[str] = (),
    list_names: Sequence[str] = (),
    referenced_variables: Sequence[str] = (),
) -> dict[str, object]:
    requested_root_variables = list(
        dict.fromkeys([discovery_variable, *root_variables])
    )
    roots: list[dict[str, object]] = []
    variable_marker = f'flag="{discovery_variable}"'
    for level, character_id, block in _numeric_records(path):
        if level != 1 or variable_marker not in block:
            continue
        scope = _selected_scope(
            block,
            variable_names=requested_root_variables,
            list_names=list_names,
        )
        if not scope["variables"][discovery_variable]["present"]:
            continue
        roots.append({"root_character_id": character_id, **scope})
    roots.sort(key=lambda row: int(row["root_character_id"]))
    reference_count, referenced = _referenced_scopes(
        path, roots, referenced_variables
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": DISCOVERY_KIND,
        "result": "GREEN",
        "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
        "game_version": _game_version(path),
        "discovery_variable": discovery_variable,
        "requested_root_variables": requested_root_variables,
        "requested_lists": list(list_names),
        "requested_referenced_variables": list(referenced_variables),
        "root_character_count": len(roots),
        "roots": roots,
        "unique_referenced_character_count": reference_count,
        "referenced_characters": referenced,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--save", type=Path)
    source.add_argument("--melted", type=Path)
    parser.add_argument("--rakaly", type=Path)
    root = parser.add_mutually_exclusive_group(required=True)
    root.add_argument("--root-character-id", type=int)
    root.add_argument("--discover-root-variable")
    parser.add_argument("--root-variable", action="append", default=[])
    parser.add_argument("--list", dest="list_names", action="append", default=[])
    parser.add_argument("--referenced-variable", action="append", default=[])
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.melted is not None:
            melted = args.melted.resolve()
            if not melted.is_file():
                raise ValueError("melted input does not exist")
            source_record = None
            rakaly_record = None
        else:
            save = args.save.resolve()
            rakaly = args.rakaly.resolve() if args.rakaly is not None else None
            if not save.is_file() or rakaly is None or not rakaly.is_file():
                raise ValueError("--save requires an existing --rakaly executable")
            temporary = tempfile.TemporaryDirectory(prefix="ck3-character-scope-")
            melted = Path(temporary.name) / "source-melted.ck3"
            completed = subprocess.run(
                [str(rakaly), "melt", str(save), "-o", str(melted)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0 or not melted.is_file():
                raise RuntimeError(
                    f"Rakaly melt failed ({completed.returncode}): {completed.stderr.strip()}"
                )
            source_record = {
                "path": str(save),
                "bytes": save.stat().st_size,
                "sha256": _sha256(save),
                "container_header": save.read_bytes()[:7].decode("ascii", errors="replace"),
            }
            rakaly_record = {
                "path": str(rakaly),
                "bytes": rakaly.stat().st_size,
                "sha256": _sha256(rakaly),
            }
        if args.discover_root_variable is not None:
            report = inspect_discovery_melted(
                melted,
                discovery_variable=args.discover_root_variable,
                root_variables=args.root_variable,
                list_names=args.list_names,
                referenced_variables=args.referenced_variable,
            )
        else:
            report = inspect_melted(
                melted,
                root_character_id=args.root_character_id,
                root_variables=args.root_variable,
                list_names=args.list_names,
                referenced_variables=args.referenced_variable,
            )
        report["source"] = source_record
        report["rakaly"] = rakaly_record
        report["melted_sha256"] = _sha256(melted)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
