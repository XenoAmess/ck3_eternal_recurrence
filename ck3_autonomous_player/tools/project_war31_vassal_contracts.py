#!/usr/bin/env python3
"""Read WAR31 holder personal contract edges from exact before/after CK3 saves.

The projection is a save-level relation, not a same-native-frame query.  It
cross-checks each contract against its liege's landed_data contract ID list.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from project_war31_save_material import project_pair


_CONTRACT_START = re.compile(rb"\t\t([1-9][0-9]*)=\{\r?\n$")
_CHARACTER_START = re.compile(rb"\t([1-9][0-9]*)=\{\r?\n$")


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest().upper()


def _id(raw: bytes, label: str) -> int:
    if not raw.isdigit() or raw == b"0":
        raise ValueError(f"invalid {label}")
    return int(raw)


def scan_contract_database(path: Path) -> dict[int, dict[str, int]]:
    """Parse only vassal_contracts.database, requiring unique complete edges."""
    section = "outside"
    seen_root = False
    contracts: dict[int, dict[str, int]] = {}
    current_id: int | None = None
    current: dict[str, int] = {}
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            if section == "outside":
                if line in (b"vassal_contracts={\n", b"vassal_contracts={\r\n"):
                    if seen_root:
                        raise ValueError("duplicate vassal_contracts root")
                    seen_root = True
                    section = "root"
                continue
            if section == "root":
                if line in (b"\tdatabase={\n", b"\tdatabase={\r\n"):
                    section = "database"
                elif line in (b"}\n", b"}\r\n"):
                    raise ValueError("vassal_contracts database missing")
                continue
            if section == "database":
                if line in (b"\t}\n", b"\t}\r\n"):
                    section = "after_database"
                    continue
                match = _CONTRACT_START.fullmatch(line)
                if match:
                    current_id = _id(match.group(1), "contract ID")
                    if current_id in contracts:
                        raise ValueError("duplicate contract ID")
                    current = {"line_start": line_number}
                    section = "contract"
                continue
            if section == "contract":
                if line in (b"\t\t}\n", b"\t\t}\r\n"):
                    if "vassal" not in current or "liege" not in current:
                        raise ValueError("contract missing vassal or liege")
                    current["line_end"] = line_number
                    if current_id is None:
                        raise ValueError("contract record has no ID")
                    contracts[current_id] = current
                    current_id = None
                    section = "database"
                    continue
                for field in (b"vassal", b"liege"):
                    prefix = b"\t\t\t" + field + b"="
                    if line.startswith(prefix):
                        key = field.decode("ascii")
                        if key in current:
                            raise ValueError(f"duplicate contract {key}")
                        current[key] = _id(line[len(prefix):].strip(), key)
            if section == "after_database":
                if line in (b"}\n", b"}\r\n"):
                    section = "done"
                elif line in (b"\tdatabase={\n", b"\tdatabase={\r\n"):
                    raise ValueError("duplicate vassal_contracts database")
    if section != "done" or not contracts:
        raise ValueError("vassal_contracts database missing or truncated")
    return contracts


def scan_liege_lists(path: Path, character_ids: set[int]) -> dict[int, list[int]]:
    """Read the direct contract-ID list stored in each requested living lord."""
    section = "outside"
    current_id: int | None = None
    in_landed = False
    in_refs = False
    refs: dict[int, list[int]] = {}
    landed_seen: set[int] = set()
    refs_seen: set[int] = set()
    with path.open("rb") as stream:
        for line in stream:
            if section == "outside":
                if line in (b"living={\n", b"living={\r\n"):
                    section = "living"
                continue
            if section == "living":
                if line in (b"}\n", b"}\r\n"):
                    section = "done"
                    break
                match = _CHARACTER_START.fullmatch(line)
                if match:
                    current_id = _id(match.group(1), "living character ID")
                    if current_id in character_ids:
                        if current_id in refs:
                            raise ValueError("duplicate requested living character")
                        refs[current_id] = []
                    continue
                if current_id is None:
                    continue
                if line in (b"\t}\n", b"\t}\r\n"):
                    if in_refs or in_landed:
                        raise ValueError("truncated landed_data or contract refs")
                    current_id = None
                    continue
                if current_id not in character_ids:
                    continue
                if in_refs:
                    if line in (b"\t\t\t}\n", b"\t\t\t}\r\n"):
                        in_refs = False
                    elif line.startswith(b"\t\t\t\t"):
                        refs[current_id].extend(
                            _id(token, "contract reference") for token in line.strip().split()
                        )
                    else:
                        raise ValueError("unexpected vassal_contracts reference syntax")
                    continue
                if in_landed:
                    if line in (b"\t\t}\n", b"\t\t}\r\n"):
                        in_landed = False
                    elif line in (b"\t\t\tvassal_contracts={\n",
                                  b"\t\t\tvassal_contracts={\r\n"):
                        if current_id in refs_seen:
                            raise ValueError("duplicate living vassal_contracts list")
                        refs_seen.add(current_id)
                        in_refs = True
                    continue
                if line in (b"\t\tlanded_data={\n", b"\t\tlanded_data={\r\n"):
                    if current_id in landed_seen:
                        raise ValueError("duplicate living landed_data")
                    landed_seen.add(current_id)
                    in_landed = True
    if (section != "done" or set(refs) != character_ids
            or landed_seen != character_ids or refs_seen != character_ids):
        raise ValueError("requested living lord records missing or truncated")
    return refs


def project_character_contracts(
    path: Path, character_ids: set[int]
) -> dict[int, dict[str, object]]:
    contracts = scan_contract_database(path)
    edges_by_vassal: dict[int, list[tuple[int, dict[str, int]]]] = {}
    for contract_id, row in contracts.items():
        if row["vassal"] in character_ids:
            edges_by_vassal.setdefault(row["vassal"], []).append((contract_id, row))
    needed = set(character_ids)
    for edges in edges_by_vassal.values():
        if len(edges) > 1:
            raise ValueError("holder has multiple direct liege contracts")
        needed.add(edges[0][1]["liege"])
    refs = scan_liege_lists(path, needed)
    projected: dict[int, dict[str, object]] = {}
    for holder_id in sorted(character_ids):
        holder_liege_edges = edges_by_vassal.get(holder_id, [])
        liege_id = holder_liege_edges[0][1]["liege"] if holder_liege_edges else None
        holder_refs = refs[holder_id]
        if len(holder_refs) != len(set(holder_refs)):
            raise ValueError("holder has duplicate contract references")
        expected = {
            contract_id for contract_id, row in contracts.items()
            if row["liege"] == holder_id
        }
        if set(holder_refs) != expected:
            raise ValueError("holder contract list differs from database direct liege edges")
        if holder_liege_edges and holder_liege_edges[0][0] not in refs[liege_id]:
            raise ValueError("holder's liege contract absent from liege's own list")
        direct = [
            {"contract_id": contract_id,
             "vassal_character_id": contracts[contract_id]["vassal"],
             "line_start": contracts[contract_id]["line_start"]}
            for contract_id in sorted(holder_refs)
        ]
        if len({row["vassal_character_id"] for row in direct}) != len(direct):
            raise ValueError("one direct vassal has multiple contracts")
        projected[holder_id] = {
            "holder_character_id": holder_id,
            "personal_liege": (
                {"status": "contract_observed", "character_id": liege_id,
                 "contract_id": holder_liege_edges[0][0],
                 "line_start": holder_liege_edges[0][1]["line_start"]}
                if holder_liege_edges else
                {"status": "no_contract_observed", "character_id": None}
            ),
            "direct_contract_vassals": direct,
            "contract_database_count": len(contracts),
            "cross_checked_liege_lists": sorted(needed),
        }
    return projected


def project_holder_contracts(path: Path, holder_id: int) -> dict[str, object]:
    return project_character_contracts(path, {holder_id})[holder_id]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before_save", "before_melted", "after_save", "after_melted",
                 "rakaly_exe", "exe", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    material = project_pair(args.before_save, args.before_melted,
                            args.after_save, args.after_melted,
                            rakaly=args.rakaly_exe, exe=args.exe)
    tracked = {
        stage: project_character_contracts(path, {33435, 30097})
        for stage, path in (("before", args.before_melted),
                            ("after", args.after_melted))
    }
    stages = {
        stage: tracked[stage][material[stage]["target_title"]["holder_character_id"]]
        for stage in ("before", "after")
    }
    report = {
        "schema": "xar.ck3.war31.holder-contract-edges.v1",
        "game_version": material["game_version"],
        "before": stages["before"],
        "after": stages["after"],
        "tracked_characters": {
            stage: {str(character_id): value
                    for character_id, value in tracked[stage].items()}
            for stage in ("before", "after")
        },
        "source_save_sha256": {
            stage: material["sources"][stage]["save_sha256"]
            for stage in ("before", "after")
        },
        "source_melted_sha256": {
            stage: material["sources"][stage]["melted_sha256"]
            for stage in ("before", "after")
        },
        "same_native_frame_binding": False,
        "semantic_scope": "save-level contract-defined direct liege and vassals only",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": _digest(args.output)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
