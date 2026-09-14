#!/usr/bin/env python3
"""Verify FACTION2-CORE's exact targeting-span and identity evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008
EXPECTED_GUI_SHA256 = "798F177B1DB914B34CCE177D8CD29F336E182BC6BB24294BD46ECE7B27392770"
PATCH_RVA = 0x1395F0E
PATCH_ANCHOR = bytes.fromhex("E87D98BDFF4889442420488D542430")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sections(image: bytes) -> list[tuple[int, int, int, int]]:
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    _require(image[pe : pe + 4] == b"PE\0\0", "PE signature drifted")
    count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    cursor = pe + 24 + optional_size
    result: list[tuple[int, int, int, int]] = []
    for _ in range(count):
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        result.append((virtual_address, virtual_size, raw_offset, raw_size))
        cursor += 40
    return result


def _at(
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    rva: int,
    size: int,
) -> bytes:
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            return image[offset : offset + size]
    raise AssertionError(f"RVA 0x{rva:X} is not file-backed")


def _direct_target(rva: int, instruction: bytes) -> int:
    _require(
        len(instruction) == 5 and instruction[0] == 0xE8,
        f"RVA 0x{rva:X} is not a direct CALL",
    )
    return rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def _rip_target(rva: int, instruction: bytes, displacement_offset: int) -> int:
    return rva + len(instruction) + struct.unpack_from(
        "<i", instruction, displacement_offset
    )[0]


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def check(root: Path, *, ck3_root: Path | None = None) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    header = (
        native / "include/xar_bridge/faction_targeting_row_observer_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (
        native / "src/faction_targeting_row_observer_v1.cpp"
    ).read_text(encoding="utf-8")
    serializer = (
        native / "src/faction_targeting_row_observer_v1_serializer.cpp"
    ).read_text(encoding="utf-8")
    abi = json.loads(
        (native / "research/faction_targeting_row_observer_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (
            native
            / "research/fixtures/faction_targeting_row_observer_v1_source_contract.json"
        ).read_text(encoding="utf-8")
    )
    capture = json.loads(
        (
            native
            / "research/fixtures/faction_targeting_row_observer_v1_capture_fixture.json"
        ).read_text(encoding="utf-8")
    )

    _require(abi["schema_version"] == 1, "ABI schema drifted")
    _require(contract["schema_version"] == 1, "source contract schema drifted")
    for token in contract["required_header_tokens"]:
        _require(token in header, f"missing header token: {token}")
    for token in contract["required_implementation_tokens"]:
        _require(token in source, f"missing implementation token: {token}")
    for token in contract["required_serializer_tokens"]:
        _require(token in serializer, f"missing serializer token: {token}")
    _require(
        abi["capture_seam"]["installed_by_default"] is False
        and contract["public_impact"]["public_targeting_rows_ready"] is False,
        "private/default-off boundary drifted",
    )
    _require(
        abi["readiness"]["campaign_root_count_equivalence_ready"] is False
        and abi["readiness"]["target_character_identity_ready"] is False,
        "unresolved public join was promoted without evidence",
    )
    _require(
        abi["targeting_span"]["row_stride"] == 0x18
        and abi["adapter_evidence"]["producer_writer_ready"] is False
        and "producer" not in abi,
        "inline FactionItem row/evidence boundary drifted",
    )
    _require(
        contract["unique_next_reverse_engineering_entry"]
        == abi["unique_next_reverse_engineering_entry"],
        "next reverse-engineering seam drifted",
    )
    _require(
        capture["status"] == "fixture-captured-private-stable-identities"
        and capture["offline_fixture"] is True,
        "offline fixture status drifted",
    )
    _require(
        capture["capture"]["faction_ids"] == [7, 42]
        and capture["readiness"]["public_targeting_rows"] is False,
        "fixture identity/public boundary drifted",
    )
    _require(
        capture["raw_pointer_fields_persisted"] is False
        and capture["raw_row_bytes_persisted"] is False,
        "pointer persistence boundary drifted",
    )
    prohibited_capture_keys = {
        "module_base",
        "owner_pointer",
        "data_pointer",
        "row_pointer",
        "pointer_hash",
        "raw_row_bytes",
    }
    _require(
        prohibited_capture_keys.isdisjoint(set(_walk(capture))),
        "capture fixture leaked a process-local pointer field",
    )

    install = (ck3_root or root / "Crusader Kings III").resolve()
    executable = install / "binaries/ck3.exe"
    gui_path = install / "game/gui/window_factions.gui"
    image = executable.read_bytes()
    gui = gui_path.read_bytes()
    _require(len(image) == EXPECTED_SIZE, "executable size drifted")
    _require(
        hashlib.sha256(image).hexdigest().upper() == EXPECTED_SHA256,
        "executable SHA-256 drifted",
    )
    _require(
        hashlib.sha256(gui).hexdigest().upper() == EXPECTED_GUI_SHA256,
        "window_factions.gui SHA-256 drifted",
    )
    gui_text = gui.decode("utf-8-sig")
    for token in (
        "datamodel = \"[FactionsWindow.GetTargetingFactions]\"",
        "visible = \"[FactionsWindow.HasTargetingFactions]\"",
        "datacontext = \"[FactionItem.GetFaction]\"",
    ):
        _require(token in gui_text, f"stock GUI anchor missing: {token}")

    sections = _sections(image)
    _require(
        _at(image, sections, PATCH_RVA, len(PATCH_ANCHOR)) == PATCH_ANCHOR,
        "post-getter patch anchor drifted",
    )
    _require(
        _direct_target(PATCH_RVA, _at(image, sections, PATCH_RVA, 5))
        == 0xF6F790,
        "GetTargetingFactions leaf target drifted",
    )
    registration_callback = _at(image, sections, 0x201478, 7)
    _require(
        registration_callback[:3] == bytes.fromhex("4C8D0D")
        and _rip_target(0x201478, registration_callback, 3) == 0x1395F00,
        "GetTargetingFactions registered callback drifted",
    )
    identity_registration = _at(image, sections, 0x1FCFAD, 7)
    _require(
        identity_registration[:3] == bytes.fromhex("488D15")
        and _rip_target(0x1FCFAD, identity_registration, 3) == 0xE6F440,
        "FactionItem.GetFaction resolver registration drifted",
    )
    _require(
        _at(image, sections, 0xF6F790, 8)
        == bytes.fromhex("488D8138010000C3"),
        "targeting container getter layout drifted",
    )
    _require(
        _at(image, sections, 0x1393C40, 11)
        == bytes.fromhex("83B944010000000F95C0C3"),
        "targeting count predicate layout drifted",
    )
    _require(
        _at(image, sections, 0x96DB7A, 3) == bytes.fromhex("8B400C"),
        "targeting collection count adapter drifted",
    )
    _require(
        _at(image, sections, 0x13A32E2, 6) == bytes.fromhex("8B480C4C8B00")
        and _at(image, sections, 0x13A32F3, 8)
        == bytes.fromhex("488D0C5B488B5C24")
        and _at(image, sections, 0x13A32FC, 4)
        == bytes.fromhex("498D04C8"),
        "targeting collection slice/0x18 stride adapter drifted",
    )
    _require(
        _at(image, sections, 0x13A3161, 3) == bytes.fromhex("8B700C")
        and _at(image, sections, 0x13A31A5, 7)
        == bytes.fromhex("488D0C7F498B06")
        and _at(image, sections, 0x13A31AC, 4)
        == bytes.fromhex("488D0CC8"),
        "targeting collection item/0x18 stride adapter drifted",
    )
    _require(
        _at(image, sections, 0xE6F44C, 2) == bytes.fromhex("8B11")
        and _at(image, sections, 0xE6F46C, 3) == bytes.fromhex("395010"),
        "FactionItem full-generation identity round-trip drifted",
    )

    for span in contract["native_spans"]:
        start = int(span["rva_start"], 0)
        end = int(span["rva_end_exclusive"], 0)
        body = _at(image, sections, start, end - start)
        _require(len(body) == span["length"], f"{span['name']} length drifted")
        _require(
            hashlib.sha256(body).hexdigest().upper() == span["sha256"],
            f"{span['name']} body hash drifted",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-root", type=Path)
    arguments = parser.parse_args()
    check(
        arguments.root.resolve(),
        ck3_root=arguments.ck3_root.resolve() if arguments.ck3_root else None,
    )
    print("faction-targeting-row-observer-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
