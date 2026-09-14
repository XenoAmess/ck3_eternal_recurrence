#!/usr/bin/env python3
"""Verify the exact-build core diplomatic proposal research contract.

This verifier is offline. It reads the pinned CK3 executable and stock script
tree, but it never starts or attaches to CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[2]
DEFAULT_CONTRACT = HERE / "core_diplomatic_proposals_v1_contract.json"
DEFAULT_GAME_ROOT = REPOSITORY_ROOT / "Crusader Kings III"
DEFAULT_ANCHORS = HERE / "ck3_1_19_0_6_anchors.json"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def runtime_function_ranges(data: bytes, image: PeImage) -> set[tuple[int, int]]:
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        raise ValueError("expected PE32+ optional header")
    exception_rva, exception_size = struct.unpack_from(
        "<II", data, optional + 112 + 3 * 8
    )
    if exception_size % 12:
        raise ValueError("malformed AMD64 exception directory")
    offset = image.rva_to_offset(exception_rva)
    return {
        struct.unpack_from("<II", data, offset + delta)
        for delta in range(0, exception_size, 12)
    }


def strip_comments(line: str) -> str:
    return line.split("#", maxsplit=1)[0]


def interaction_block(lines: list[str], key: str) -> tuple[int, int, str]:
    start = None
    depth = 0
    opened = False
    for index, raw_line in enumerate(lines, start=1):
        line = strip_comments(raw_line)
        if start is None:
            if line.strip().startswith(f"{key} = {{"):
                start = index
            else:
                continue
        for character in line:
            if character == "{":
                depth += 1
                opened = True
            elif character == "}":
                depth -= 1
                if opened and depth == 0:
                    return start, index, "\n".join(lines[start - 1 : index])
        if depth < 0:
            raise ValueError(f"{key}: brace depth became negative at line {index}")
    raise ValueError(f"{key}: complete top-level definition not found")


def verify_source_definitions(
    game_root: Path, contract: dict[str, object], failures: list[str]
) -> None:
    source_cache: dict[str, list[str]] = {}
    rows: list[dict[str, object]] = []
    rows.extend(contract.get("interactions", []))
    for group in contract.get("regional_followups", []):
        rows.extend(group.get("interactions", []))
        inbound_only = group.get("inbound_only")
        if inbound_only:
            rows.append(inbound_only)

    seen: set[str] = set()
    for row in rows:
        key = row["key"]
        if key in seen:
            failures.append(f"interaction {key}: duplicate contract row")
            continue
        seen.add(key)
        relative = row["source"]
        if relative not in source_cache:
            source_path = game_root / Path(relative)
            source_cache[relative] = source_path.read_text(
                encoding="utf-8-sig"
            ).splitlines()
        try:
            start, end, block = interaction_block(source_cache[relative], key)
        except ValueError as error:
            failures.append(str(error))
            continue
        wanted_lines = tuple(row["definition_lines"])
        if (start, end) != wanted_lines:
            failures.append(
                f"{key}: expected lines {wanted_lines[0]}..{wanted_lines[1]}, "
                f"found {start}..{end}"
            )
        for token in row.get("required_tokens", []):
            if token not in block:
                failures.append(f"{key}: missing source token {token!r}")


def verify(contract_path: Path, game_root: Path, exe: Path, anchors_path: Path) -> list[str]:
    failures: list[str] = []
    contract_text = contract_path.read_text(encoding="utf-8")
    contract = json.loads(contract_text)
    anchors = json.loads(anchors_path.read_text(encoding="utf-8"))

    build = contract["game_build"]
    executable_data = exe.read_bytes()
    executable_sha = hashlib.sha256(executable_data).hexdigest().upper()
    if len(executable_data) != integer(build["executable_size"]):
        failures.append("executable size does not match the contract")
    if executable_sha != build["executable_sha256"].upper():
        failures.append(
            "executable SHA mismatch: "
            f"expected {build['executable_sha256']}, found {executable_sha}"
        )

    image = PeImage(executable_data)
    pdata_ranges = runtime_function_ranges(executable_data, image)
    anchor_rvas = anchors.get("rvas", {})
    spans = contract["native_pipeline"]["spans"]
    for span in spans:
        start = integer(span["rva_start"])
        end = integer(span["rva_end_exclusive"])
        length = end - start
        if length != integer(span["length"]):
            failures.append(f"{span['name']}: declared byte length drifted")
            continue
        regions = span.get("runtime_function_regions")
        if regions:
            expected_regions = []
            for region in regions:
                begin_text, finish_text = region.split("..", maxsplit=1)
                expected_regions.append((integer(begin_text), integer(finish_text)))
        else:
            expected_regions = [(start, end)]
        for region in expected_regions:
            if region not in pdata_ranges:
                failures.append(
                    f"{span['name']}: 0x{region[0]:X}..0x{region[1]:X} "
                    "is not an exact .pdata runtime-function extent"
                )
        offset = image.rva_to_offset(start)
        blob = executable_data[offset : offset + length]
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        if len(blob) != length:
            failures.append(f"{span['name']}: span is not fully file-backed")
        elif actual_sha != span["sha256"].upper():
            failures.append(
                f"{span['name']}: expected {span['sha256']}, found {actual_sha}"
            )
        anchor_key = span.get("anchor_key")
        if anchor_key and integer(anchor_rvas.get(anchor_key, -1)) != start:
            failures.append(f"{span['name']}: shared anchor RVA drifted")

    for source in contract["stock_sources"]:
        relative = source["relative_path"]
        data = (game_root / Path(relative)).read_bytes()
        if len(data) != integer(source["size"]):
            failures.append(f"{relative}: source size drifted")
        actual_sha = hashlib.sha256(data).hexdigest().upper()
        if actual_sha != source["sha256"].upper():
            failures.append(f"{relative}: source SHA drifted")

    verify_source_definitions(game_root, contract, failures)

    primary_keys = [row["key"] for row in contract["interactions"]]
    expected_primary = [
        "gift_interaction",
        "recruit_guest_interaction",
        "invite_to_court_interaction",
        "offer_vassalization_interaction",
        "demand_payment_interaction",
        "educate_child_interaction",
        "offer_ward_interaction",
        "offer_guardianship_interaction",
        "grant_titles_interaction",
        "grant_vassal_interaction",
        "ransom_interaction",
    ]
    if primary_keys != expected_primary:
        failures.append("primary interaction value order drifted")

    allowlist = contract["next_contracts"]["P1_generic_action"]["first_allowlist"]
    if allowlist != [
        "gift_interaction",
        "recruit_guest_interaction",
        "invite_to_court_interaction",
        "offer_vassalization_interaction ordinary feudal/clan subset",
        "demand_payment_interaction",
    ]:
        failures.append("first mutating allowlist drifted")

    readiness = contract["readiness_at_research_close"]
    if readiness.get("source_tree_ready") is not True:
        failures.append("source tree must be research-ready")
    if readiness.get("exact_build_native_pipeline_ready") is not True:
        failures.append("exact-build pipeline must be research-ready")
    for key, value in readiness.items():
        if (
            key not in {"source_tree_ready", "exact_build_native_pipeline_ready"}
            and value is not False
        ):
            failures.append(f"readiness {key}: static work cannot claim live capability")

    forbidden_scope = ("marriage", "betrothal", "holy_order")
    if any(term in key for key in primary_keys for term in forbidden_scope):
        failures.append("owner-excluded domain entered the primary interaction set")
    if "Crusader Kings III" in contract_text or "Z:\\" in contract_text:
        failures.append("contract contains a machine-specific absolute path")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--anchors", type=Path, default=DEFAULT_ANCHORS)
    arguments = parser.parse_args()
    game_root = arguments.game_root.resolve()
    exe = (
        arguments.exe.resolve()
        if arguments.exe
        else game_root / "binaries" / "ck3.exe"
    )
    try:
        failures = verify(
            arguments.contract.resolve(), game_root, exe, arguments.anchors.resolve()
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    contract = json.loads(arguments.contract.resolve().read_text(encoding="utf-8"))
    regional_count = sum(
        len(group.get("interactions", [])) + int(bool(group.get("inbound_only")))
        for group in contract.get("regional_followups", [])
    )
    print(
        "PASS exact_build=1 "
        f"spans={len(contract['native_pipeline']['spans'])} "
        f"primary_interactions={len(contract['interactions'])} "
        f"regional_followups={regional_count} live=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
