#!/usr/bin/env python3
"""Verify the CK3 1.19.0.6 found-kingdom native submit ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000
EXPECTED_DECISION_FILE_SHA256 = (
    "4E406B77DCEE8E98DB4875973030AAF0FDB18A9CD6505EAC374B75D481718471"
)
EXPECTED_DECISION_BLOCK_SHA256 = (
    "4AA72233FD9266CD36C18DF10E9DBFC21B967003201F61B575C687FAA380C7DF"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _fail(errors: list[str], condition: bool, message: str) -> bool:
    if not condition:
        errors.append(message)
        return False
    return True


def _pe_layout(
    image: bytes, errors: list[str]
) -> tuple[int, list[tuple[int, int, int, int]]] | None:
    if len(image) < 0x40 or image[:2] != b"MZ":
        errors.append("exact executable is missing its DOS header")
        return None
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if pe + 24 > len(image) or image[pe : pe + 4] != b"PE\0\0":
        errors.append("exact executable is missing its PE signature")
        return None
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    if optional + optional_size > len(image):
        errors.append("PE optional header is truncated")
        return None
    if struct.unpack_from("<H", image, optional)[0] != 0x20B:
        errors.append("exact executable is not PE32+")
        return None
    image_base = struct.unpack_from("<Q", image, optional + 24)[0]
    cursor = optional + optional_size
    sections: list[tuple[int, int, int, int]] = []
    for _ in range(section_count):
        if cursor + 40 > len(image):
            errors.append("PE section table is truncated")
            return None
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", image, cursor + 8
        )
        sections.append((virtual_address, virtual_size, raw_offset, raw_size))
        cursor += 40
    return image_base, sections


def _at(
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    rva: int,
    size: int,
) -> bytes | None:
    if size < 0:
        return None
    for virtual_address, virtual_size, raw_offset, raw_size in sections:
        span = max(virtual_size, raw_size)
        if virtual_address <= rva and rva + size <= virtual_address + span:
            offset = raw_offset + rva - virtual_address
            if offset + size <= len(image):
                return image[offset : offset + size]
    return None


def _integer(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise ValueError(f"not an integer: {value!r}")


def _direct_call_target(instruction_rva: int, instruction: bytes) -> int | None:
    if len(instruction) != 5 or instruction[0] != 0xE8:
        return None
    return instruction_rva + 5 + struct.unpack_from("<i", instruction, 1)[0]


def _extract_top_level_block(text: str, key: str) -> str | None:
    prefix = f"{key} = {{"
    start = 0
    for line in text.splitlines(keepends=True):
        if line.rstrip("\r\n") == prefix:
            break
        start += len(line)
    else:
        return None

    depth = 0
    in_string = False
    escaped = False
    in_comment = False
    opened = False
    for index in range(start, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            opened = True
            depth += 1
        elif character == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start : index + 1]
    return None


def _verify_source(
    game_root: Path, contract: dict[str, Any], errors: list[str]
) -> None:
    source = game_root / "game/common/decisions/80_major_decisions.txt"
    if not source.is_file():
        errors.append(f"missing exact decision source: {source}")
        return
    raw = source.read_bytes()
    _fail(
        errors,
        _sha256(raw) == EXPECTED_DECISION_FILE_SHA256,
        "80_major_decisions.txt SHA-256 drifted",
    )
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    block = _extract_top_level_block(text, "found_kingdom_decision")
    if block is None:
        errors.append("found_kingdom_decision block is missing")
        return
    _fail(
        errors,
        _sha256(block.encode("utf-8")) == EXPECTED_DECISION_BLOCK_SHA256,
        "found_kingdom_decision block hash drifted",
    )
    _fail(
        errors,
        contract.get("build", {}).get("decision_source_block_sha256")
        == EXPECTED_DECISION_BLOCK_SHA256,
        "ABI contract decision block binding drifted",
    )
    _fail(
        errors,
        "option =" not in block and "widget" not in block,
        "found_kingdom_decision gained an authored option/widget context",
    )


def _verify_spans(
    contract: dict[str, Any],
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    errors: list[str],
) -> None:
    spans = contract.get("instruction_spans", [])
    _fail(errors, len(spans) == 11, "instruction span inventory drifted")
    names: set[str] = set()
    for span in spans:
        name = str(span.get("name", "<unnamed>"))
        if name in names:
            errors.append(f"duplicate instruction span: {name}")
        names.add(name)
        try:
            start = _integer(span.get("rva_start"))
            end = _integer(span.get("rva_end_exclusive"))
            length = int(span.get("length"))
        except (TypeError, ValueError) as exc:
            errors.append(f"{name} has invalid span metadata: {exc}")
            continue
        if end <= start or length != end - start:
            errors.append(f"{name} span length is inconsistent")
            continue
        body = _at(image, sections, start, length)
        if body is None:
            errors.append(f"{name} span is not file-backed")
            continue
        _fail(
            errors,
            _sha256(body) == span.get("sha256"),
            f"{name} full instruction span hash drifted",
        )
        try:
            prefix = bytes.fromhex(str(span.get("prefix16", "")))
        except ValueError:
            prefix = b""
        _fail(
            errors,
            len(prefix) == 16 and body.startswith(prefix),
            f"{name} runtime prefix drifted",
        )


def _verify_rtti_and_slots(
    contract: dict[str, Any],
    image: bytes,
    image_base: int,
    sections: list[tuple[int, int, int, int]],
    errors: list[str],
) -> None:
    rtti = contract.get("command_rtti", {})
    try:
        type_descriptor = _integer(rtti.get("type_descriptor_rva"))
        primary_col_rva = _integer(rtti.get("primary_complete_object_locator_rva"))
        secondary_col_rva = _integer(
            rtti.get("secondary_complete_object_locator_rva")
        )
        primary_vtable = _integer(rtti.get("primary_vtable_rva"))
        secondary_vtable = _integer(rtti.get("secondary_vtable_rva"))
    except ValueError as exc:
        errors.append(f"RTTI metadata is invalid: {exc}")
        return
    rtti_name = (str(rtti.get("name", "")) + "\0").encode("ascii", "replace")
    _fail(
        errors,
        _at(image, sections, type_descriptor + 0x10, len(rtti_name)) == rtti_name,
        "CExecuteDecisionCommand RTTI name drifted",
    )
    for label, col_rva, vtable_rva, expected_offset in (
        ("primary", primary_col_rva, primary_vtable, 0),
        ("secondary", secondary_col_rva, secondary_vtable, 0x18),
    ):
        raw_col = _at(image, sections, col_rva, 24)
        if raw_col is None:
            errors.append(f"{label} complete-object locator is not file-backed")
            continue
        col = struct.unpack("<6I", raw_col)
        recorded_key = f"{label}_complete_object_locator"
        try:
            recorded = tuple(_integer(value) for value in rtti.get(recorded_key, []))
        except ValueError as exc:
            recorded = ()
            errors.append(f"{label} recorded complete-object locator is invalid: {exc}")
        _fail(
            errors,
            recorded == col,
            f"{label} recorded complete-object locator drifted",
        )
        _fail(
            errors,
            col[0] == 1
            and col[1] == expected_offset
            and col[2] == 0
            and col[3] == type_descriptor
            and col[5] == col_rva,
            f"{label} complete-object locator drifted",
        )
        raw_owner = _at(image, sections, vtable_rva - 8, 8)
        _fail(
            errors,
            raw_owner is not None
            and struct.unpack("<Q", raw_owner)[0] == image_base + col_rva,
            f"{label} vtable/COL link drifted",
        )

    slots = contract.get("vtable_slots", [])
    _fail(errors, len(slots) == 4, "command vtable slot inventory drifted")
    for slot in slots:
        try:
            slot_rva = _integer(slot.get("slot_rva"))
            target_rva = _integer(slot.get("target_rva"))
        except ValueError as exc:
            errors.append(f"vtable slot metadata is invalid: {exc}")
            continue
        raw = _at(image, sections, slot_rva, 8)
        _fail(
            errors,
            raw is not None
            and struct.unpack("<Q", raw)[0] == image_base + target_rva,
            f"vtable slot {slot.get('role')} drifted",
        )


def _verify_edges(
    contract: dict[str, Any],
    image: bytes,
    sections: list[tuple[int, int, int, int]],
    errors: list[str],
) -> None:
    edges = contract.get("validated_edges", [])
    _fail(errors, len(edges) >= 16, "validated instruction-edge inventory drifted")
    for edge in edges:
        role = str(edge.get("role", "<unnamed edge>"))
        try:
            rva = _integer(edge.get("instruction_rva"))
        except ValueError as exc:
            errors.append(f"{role} has invalid instruction RVA: {exc}")
            continue
        kind = edge.get("kind")
        if kind == "direct_call":
            instruction = _at(image, sections, rva, 5)
            target = (
                _direct_call_target(rva, instruction)
                if instruction is not None
                else None
            )
            try:
                expected = _integer(edge.get("target_rva"))
            except ValueError as exc:
                errors.append(f"{role} has invalid target RVA: {exc}")
                continue
            _fail(errors, target == expected, f"{role} direct call target drifted")
        elif kind == "bytes":
            try:
                expected_bytes = bytes.fromhex(str(edge.get("bytes", "")))
            except ValueError:
                expected_bytes = b""
            _fail(
                errors,
                bool(expected_bytes)
                and _at(image, sections, rva, len(expected_bytes))
                == expected_bytes,
                f"{role} instruction bytes drifted",
            )
        elif kind == "rip_lea":
            try:
                expected_bytes = bytes.fromhex(str(edge.get("bytes", "")))
                expected_target = _integer(edge.get("target_rva"))
            except ValueError as exc:
                errors.append(f"{role} has invalid RIP-relative metadata: {exc}")
                continue
            target = None
            if (
                len(expected_bytes) == 7
                and expected_bytes[:3] == bytes.fromhex("488D0D")
            ):
                target = rva + 7 + struct.unpack_from("<i", expected_bytes, 3)[0]
            _fail(
                errors,
                target == expected_target
                and _at(image, sections, rva, 7) == expected_bytes,
                f"{role} RIP-relative target drifted",
            )
        else:
            errors.append(f"{role} has an unsupported edge kind: {kind}")

    fixed_bytes = {
        0x188270E: "41B807000000",
        0x341DA2F: "48C70700000000",
        0x25E201C: "BA38000000",
        0x25E2074: "895120",
        0x25E2077: "4C894128",
        0x25E207B: "498B01",
        0x25E207E: "498931",
        0x25E2081: "48894130",
    }
    for rva, encoded in fixed_bytes.items():
        expected = bytes.fromhex(encoded)
        _fail(
            errors,
            _at(image, sections, rva, len(expected)) == expected,
            f"ownership/layout instruction at RVA 0x{rva:X} drifted",
        )


def _verify_contract_and_sources(
    root: Path, contract: dict[str, Any], errors: list[str]
) -> None:
    _fail(errors, contract.get("schema_version") == 1, "ABI schema drifted")
    _fail(
        errors,
        contract.get("artifact_id")
        == "major_decision_found_kingdom_native_submit_abi_v1",
        "ABI artifact identity drifted",
    )
    build = contract.get("build", {})
    _fail(errors, build.get("game_version") == "1.19.0.6", "game version drifted")
    _fail(
        errors,
        build.get("exe_sha256") == EXPECTED_EXE_SHA256,
        "contract executable hash drifted",
    )
    queue = contract.get("queue_contract", {})
    _fail(errors, queue.get("flags") == 7, "queue flags drifted")
    _fail(
        errors,
        queue.get("receiver_rva") == "0x341D990"
        and queue.get("receiver_context_rva") == "0x57621F0",
        "queue receiver binding drifted",
    )
    context = contract.get("context_contract", {})
    _fail(
        errors,
        context.get("found_kingdom_adapter_context") == "null"
        and context.get("effect_preview") == "not provided",
        "found-kingdom nullable context/effect boundary drifted",
    )
    adapter = contract.get("adapter_contract", {})
    _fail(
        errors,
        adapter.get("inherited_decision4_read_signature_gates") == 11
        and adapter.get("inherited_decision4_read_vtable_slot_gates") == 6
        and adapter.get("command_submit_signature_gates") == 11
        and adapter.get("command_submit_vtable_slot_gates") == 4
        and
        adapter.get("production_operation_overrides_forbidden") is True
        and adapter.get("offline_fixture_does_not_certify_production_abi") is True,
        "production/fixture admission boundary drifted",
    )
    boundary = contract.get("boundary", {})
    for key in (
        "cmake_changed",
        "shared_bridge_changed",
        "public_schema_changed",
        "mcp_changed",
        "ck3_launched",
        "desktop_used",
        "master_updated",
        "effect_preview_provided",
        "exact_benefit_claimed",
        "live_submission_performed",
    ):
        _fail(errors, boundary.get(key) is False, f"boundary {key} was overclaimed")

    native = root / "ck3_autonomous_player/native_bridge"
    header_path = (
        native
        / "include/xar_bridge/major_decision_found_kingdom_native_submit_v1.hpp"
    )
    source_path = native / "src/major_decision_found_kingdom_native_submit_v1.cpp"
    docs_path = root / "docs/ck3-native-ai/major-decision-found-kingdom-native-submit-abi.md"
    for path in (header_path, source_path, docs_path):
        if not path.is_file():
            errors.append(f"missing ABI artifact: {path}")
    if not header_path.is_file() or not source_path.is_file():
        return
    implementation = header_path.read_text(encoding="utf-8") + "\n" + source_path.read_text(
        encoding="utf-8"
    )
    for token in (
        "kMajorDecisionFoundKingdomExecuteCommandConstructorRvaV1",
        "kMajorDecisionFoundKingdomExecuteCommandValidatorRvaV1",
        "kMajorDecisionFoundKingdomExecuteCommandCloneRvaV1",
        "kMajorDecisionFoundKingdomExecuteCommandDestructorRvaV1",
        "kMajorDecisionFoundKingdomCommandQueueReceiverRvaV1",
        "kMajorDecisionFoundKingdomCommandQueueContextRvaV1",
        "AnyOverride(environment.operations)",
        "owned_decision_context != nullptr",
        "accepted && consumed",
    ):
        _fail(errors, token in implementation, f"native adapter token missing: {token}")


def verify(root: Path, game_root: Path, contract_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read ABI contract: {exc}"]
    _verify_contract_and_sources(root, contract, errors)
    _verify_source(game_root, contract, errors)

    executable = game_root / "binaries/ck3.exe"
    if not executable.is_file():
        errors.append(f"missing exact executable: {executable}")
        return errors
    image = executable.read_bytes()
    _fail(errors, len(image) == EXPECTED_EXE_SIZE, "exact executable size drifted")
    _fail(errors, _sha256(image) == EXPECTED_EXE_SHA256, "exact executable hash drifted")
    layout = _pe_layout(image, errors)
    if layout is None:
        return errors
    image_base, sections = layout
    _fail(errors, image_base == EXPECTED_IMAGE_BASE, "PE image base drifted")
    _verify_spans(contract, image, sections, errors)
    _verify_rtti_and_slots(contract, image, image_base, sections, errors)
    _verify_edges(contract, image, sections, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root",
        type=Path,
        required=True,
        help="Exact CK3 root containing binaries/ck3.exe and game/",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root; defaults from this verifier location",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).with_name(
            "major_decision_found_kingdom_native_submit_abi_v1.json"
        ),
    )
    arguments = parser.parse_args()
    errors = verify(
        arguments.repo_root.resolve(),
        arguments.game_root.resolve(),
        arguments.contract.resolve(),
    )
    if errors:
        for error in errors:
            print(f"RED: {error}", file=sys.stderr)
        return 1
    print(
        "GREEN: CK3 1.19.0.6 CExecuteDecisionCommand/context/validator/"
        "clone/queue/lifecycle spans and private found-kingdom submit adapter match"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
