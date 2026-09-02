#!/usr/bin/env python3
"""Verify the exact-build spawn_army execute observation point offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "raiktor_spawn_army_execute_v1_abi.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, got {value!r}")


def span(data: bytes, image: PeImage, start: int, end: int) -> bytes:
    if end <= start:
        raise ValueError(f"invalid span 0x{start:X}..0x{end:X}")
    offset = image.rva_to_offset(start)
    value = data[offset : offset + end - start]
    if len(value) != end - start:
        raise ValueError(f"short file-backed span at 0x{start:X}")
    return value


def qword_rva(data: bytes, image: PeImage, rva: int) -> int:
    value = struct.unpack("<Q", span(data, image, rva, rva + 8))[0]
    return value - image.image_base


def direct_call_target(data: bytes, image: PeImage, call_rva: int) -> int:
    instruction = span(data, image, call_rva, call_rva + 5)
    if instruction[0] != 0xE8:
        raise ValueError(f"direct CALL opcode missing at 0x{call_rva:X}")
    return call_rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def verify(executable: Path, contract_path: Path) -> list[str]:
    data = executable.read_bytes()
    image = PeImage(data)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    build = contract["build"]
    checks = (
        ("sha256", hashlib.sha256(data).hexdigest().upper(), build["executable_sha256"]),
        ("file_size", len(data), integer(build["file_size"])),
        ("pe_timestamp", image.timestamp, integer(build["pe_timestamp"])),
        ("image_base", image.image_base, integer(build["image_base"])),
        ("size_of_image", image.size_of_image, integer(build["size_of_image"])),
    )
    for name, actual, expected in checks:
        if actual != expected:
            failures.append(f"build {name}: expected {expected!r}, found {actual!r}")

    registration = contract["registration"]
    keyword = bytes.fromhex(registration["keyword_bytes_hex"])
    if span(
        data,
        image,
        integer(registration["keyword_rva"]),
        integer(registration["keyword_rva"]) + len(keyword),
    ) != keyword:
        failures.append("spawn_army keyword bytes differ")
    registration_bytes = span(
        data,
        image,
        integer(registration["registration_rva"]),
        integer(registration["registration_end_rva_exclusive"]),
    )
    if hashlib.sha256(registration_bytes).hexdigest().upper() != registration["registration_sha256"]:
        failures.append("spawn_army registration span differs")

    constructor_call = integer(registration["factory_method_rva"])
    constructor_window = span(data, image, constructor_call, constructor_call + 0x44)
    if struct.pack("<I", integer(registration["runtime_object_size"])) not in constructor_window:
        failures.append("spawn_army runtime object size is not constructed")
    vptr_lea = span(data, image, constructor_call + 0x2F, constructor_call + 0x36)
    if vptr_lea[:3] != b"\x48\x8D\x05":
        failures.append("runtime vtable LEA is missing")
    else:
        displacement = struct.unpack_from("<i", vptr_lea, 3)[0]
        actual_vtable = constructor_call + 0x36 + displacement
        if actual_vtable != integer(registration["runtime_vtable_rva"]):
            failures.append("runtime vtable target differs")

    vtable = contract["runtime_vtable"]
    vtable_rva = integer(registration["runtime_vtable_rva"])
    if qword_rva(data, image, vtable_rva - 8) != integer(vtable["complete_object_locator_rva"]):
        failures.append("runtime complete-object locator differs")
    for slot_name, target_name in (("execute_slot_index", "execute_rva"), ("preview_slot_index", "preview_rva")):
        slot = integer(vtable[slot_name])
        if qword_rva(data, image, vtable_rva + slot * 8) != integer(vtable[target_name]):
            failures.append(f"runtime {slot_name} target differs")

    execute = contract["execute"]
    execute_bytes = span(
        data,
        image,
        integer(execute["rva"]),
        integer(execute["end_rva_exclusive"]),
    )
    if len(execute_bytes) != integer(execute["length_bytes"]):
        failures.append("execute length differs")
    if hashlib.sha256(execute_bytes).hexdigest().upper() != execute["sha256"]:
        failures.append("execute function digest differs")

    for row in contract["pinned_spans"]:
        actual = span(
            data,
            image,
            integer(row["start_rva"]),
            integer(row["end_rva_exclusive"]),
        )
        if "bytes_hex" in row and actual.hex().upper() != row["bytes_hex"]:
            failures.append(f"{row['name']} bytes differ")
        if hashlib.sha256(actual).hexdigest().upper() != row["sha256"]:
            failures.append(f"{row['name']} digest differs")

    flow = contract["source_and_creation_flow"]
    calls = [flow["evaluated_name_call"], flow["persistent_regiment_create"], flow["army_create"]]
    calls.extend(flow["attach_and_finalize_calls"])
    for row in calls:
        call_rva = integer(row["call_instruction_rva"])
        expected = integer(row["target_rva"])
        if direct_call_target(data, image, call_rva) != expected:
            failures.append(f"direct call target differs at 0x{call_rva:X}")

    observation = contract["next_native_observation"]
    if integer(observation["stop_rva"]) != integer(contract["pinned_spans"][4]["start_rva"]):
        failures.append("observation stop is not the pinned post-finalize window")
    if integer(observation["window_end_rva_exclusive"]) != integer(contract["pinned_spans"][5]["start_rva"]):
        failures.append("observation window does not end at local vector cleanup")
    audit = contract["current_wiring_audit"]
    if (
        audit["direct_loss_wiring_supported"] is not False
        or audit["public_readiness_remains"] is not False
        or contract["production_installed"] is not False
        or contract["production_abi_changed"] is not False
    ):
        failures.append("contract overclaims production loss readiness")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    arguments = parser.parse_args()
    try:
        failures = verify(arguments.exe.resolve(), arguments.contract.resolve())
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: exact_build=1 spawn_army_execute=1 observation_window=1 production_abi=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
