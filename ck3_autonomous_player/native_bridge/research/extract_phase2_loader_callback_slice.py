#!/usr/bin/env python3
"""Extract a bounded, read-only callback slice from the pinned CK3 binary.

The extractor deliberately inspects one exact-build function and the two
nearby MSVC callable vtables that are statically referenced by its database
registration helpers.  It never attaches to or starts CK3 and never writes to
the executable.  The output is a small JSON evidence record suitable for an
offline review artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import pefile


EXPECTED_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SIZE = 95_206_008
EXPECTED_TIMESTAMP = 0x6A1EEE6D
EXPECTED_IMAGE_BASE = 0x140000000
EXPECTED_IMAGE_SIZE = 0x5C2D000

FUNCTION_RVA = 0x3B9AB00
FUNCTION_END_RVA = 0x3B9ACED
PROLOGUE_END_RVA = 0x3B9AB23
CALLBACK_CALL_RVA = 0x3B9AB90
UNWIND_RVA = 0x4F0FE28
UNWIND_HANDLER_RVA = 0x3E27DD0

PROLOGUE_BYTES = bytes.fromhex(
    "48 89 5C 24 10 48 89 74 24 18 48 89 7C 24 20 55 41 56 41 57 "
    "48 8D AC 24 10 FE FF FF 48 81 EC F0 02 00 00"
)

CALLSITE_RVAS = (
    0x0821E45,
    0x088B5DC,
    0x1B3984D,
    0x1E18C56,
    0x1E21CD3,
    0x203FF96,
    0x2041D8C,
    0x3B9AEF4,
)

CALLBACK_BYTES = {
    0x3B9AB7D: bytes.fromhex("48 8B 8E 88 00 00 00"),
    0x3B9AB84: bytes.fromhex("48 85 C9"),
    0x3B9AB8D: bytes.fromhex("48 8B 01"),
    0x3B9AB90: bytes.fromhex("FF 50 10"),
}

# Direct branch boundaries in the one function under review.  Keeping the
# opcode bytes beside the expected target/fall-through makes the CFG check
# independent of a disassembler version while still proving the rel8/rel32
# target arithmetic against the exact image.
CFG_BRANCHES = (
    {
        "rva": 0x3B9AB36,
        "bytes": bytes.fromhex("0F 84 88 01 00 00"),
        "target_rva": 0x3B9ACC4,
        "fallthrough_rva": 0x3B9AB3C,
        "condition": "node_range_empty",
    },
    {
        "rva": 0x3B9AB5B,
        "bytes": bytes.fromhex("74 36"),
        "target_rva": 0x3B9AB93,
        "fallthrough_rva": 0x3B9AB5D,
        "condition": "initial_callback_field_is_null",
    },
    {
        "rva": 0x3B9AB87,
        "bytes": bytes.fromhex("0F 84 54 01 00 00"),
        "target_rva": 0x3B9ACE1,
        "fallthrough_rva": 0x3B9AB8D,
        "condition": "reloaded_callback_field_is_null",
    },
    {
        "rva": 0x3B9ABAE,
        "bytes": bytes.fromhex("74 17"),
        "target_rva": 0x3B9ABC7,
        "fallthrough_rva": 0x3B9ABB0,
        "condition": "dependency_chain_is_sentinel",
    },
    {
        "rva": 0x3B9ABC5,
        "bytes": bytes.fromhex("75 E9"),
        "target_rva": 0x3B9ABB0,
        "fallthrough_rva": 0x3B9ABC7,
        "condition": "dependency_chain_not_sentinel",
    },
    {
        "rva": 0x3B9AC3E,
        "bytes": bytes.fromhex("7D 40"),
        "target_rva": 0x3B9AC80,
        "fallthrough_rva": 0x3B9AC40,
        "condition": "counter_at_or_above_threshold",
    },
    {
        "rva": 0x3B9AC4D,
        "bytes": bytes.fromhex("74 31"),
        "target_rva": 0x3B9AC80,
        "fallthrough_rva": 0x3B9AC4F,
        "condition": "optional_helper_return_is_null",
    },
    {
        "rva": 0x3B9AC88,
        "bytes": bytes.fromhex("72 2D"),
        "target_rva": 0x3B9ACB7,
        "fallthrough_rva": 0x3B9AC8A,
        "condition": "allocation_size_below_small_threshold",
    },
    {
        "rva": 0x3B9AC9B,
        "bytes": bytes.fromhex("72 15"),
        "target_rva": 0x3B9ACB2,
        "fallthrough_rva": 0x3B9AC9D,
        "condition": "allocation_size_below_page_threshold",
    },
    {
        "rva": 0x3B9ACB0,
        "bytes": bytes.fromhex("77 35"),
        "target_rva": 0x3B9ACE7,
        "fallthrough_rva": 0x3B9ACB2,
        "condition": "allocation_header_distance_too_large",
    },
    {
        "rva": 0x3B9ACBE,
        "bytes": bytes.fromhex("0F 85 8C FE FF FF"),
        "target_rva": 0x3B9AB50,
        "fallthrough_rva": 0x3B9ACC4,
        "condition": "next_node_exists",
    },
)

CFG_TERMINAL_BYTES = {
    0x3B9ACE0: bytes.fromhex("C3"),
    0x3B9ACE1: bytes.fromhex("E8 A2 7D 28 00"),
    0x3B9ACE7: bytes.fromhex("E8 04 A1 29 00"),
}

VTABLES = (
    {
        "type_descriptor_rva": 0x56F1390,
        "type_name":
        ".?AV?$_Func_impl_no_alloc@V<lambda_8128e40481c938ef2e798c8b366f7112>@@X$$V@std@@",
        "complete_object_locator_rva": 0x4BFA738,
        "vtable_rva": 0x4558700,
        "construction_reference_rva": 0x3B9A8A4,
    },
    {
        "type_descriptor_rva": 0x56F1210,
        "type_name":
        ".?AV?$_Func_impl_no_alloc@V<lambda_f64d2a3595213b63f4c97f202457024f>@@X$$V@std@@",
        "complete_object_locator_rva": 0x4BFA710,
        "vtable_rva": 0x4558770,
        "construction_reference_rva": 0x3B9A3C3,
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def rva_offset(image: pefile.PE, rva: int) -> int:
    try:
        return image.get_offset_from_rva(rva)
    except pefile.PEFormatError as exc:
        raise ValueError(f"RVA 0x{rva:X} is outside the image") from exc


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = rva_offset(image, rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}: {len(value)} != {size}")
    return value


def verify_rel_branch(
    data: bytes, image: pefile.PE, branch: dict[str, Any]
) -> dict[str, Any]:
    """Verify one exact short/near conditional branch and return its edge."""

    rva = int(branch["rva"])
    expected = bytes(branch["bytes"])
    actual = bytes_at(data, image, rva, len(expected))
    if actual != expected:
        raise ValueError(
            f"CFG branch bytes changed at 0x{rva:X}: "
            f"{actual.hex().upper()} != {expected.hex().upper()}"
        )
    if len(expected) == 2:
        displacement = struct.unpack("<b", expected[1:2])[0]
    elif len(expected) == 6 and expected[0] == 0x0F:
        displacement = struct.unpack("<i", expected[2:6])[0]
    else:
        raise ValueError(f"unsupported conditional branch encoding at 0x{rva:X}")
    target = rva + len(expected) + displacement
    fallthrough = rva + len(expected)
    if target != int(branch["target_rva"]):
        raise ValueError(
            f"CFG target changed at 0x{rva:X}: 0x{target:X} != "
            f"0x{int(branch['target_rva']):X}"
        )
    if fallthrough != int(branch["fallthrough_rva"]):
        raise ValueError(
            f"CFG fallthrough changed at 0x{rva:X}: 0x{fallthrough:X} != "
            f"0x{int(branch['fallthrough_rva']):X}"
        )
    return {
        "rva": f"0x{rva:X}",
        "bytes_hex": actual.hex().upper(),
        "target_rva": f"0x{target:X}",
        "fallthrough_rva": f"0x{fallthrough:X}",
        "condition": branch["condition"],
    }


def extract_cfg(data: bytes, image: pefile.PE) -> dict[str, Any]:
    """Return the bounded function CFG and explicitly marked null edges."""

    branches = [verify_rel_branch(data, image, branch) for branch in CFG_BRANCHES]
    terminal_bytes: dict[str, str] = {}
    for rva, expected in CFG_TERMINAL_BYTES.items():
        actual = bytes_at(data, image, rva, len(expected))
        if actual != expected:
            raise ValueError(
                f"terminal bytes changed at 0x{rva:X}: "
                f"{actual.hex().upper()} != {expected.hex().upper()}"
            )
        terminal_bytes[f"0x{rva:X}"] = actual.hex().upper()

    error_call_targets = {
        0x3B9ACE1: 0x3E22A88,
        0x3B9ACE7: 0x3E34DF0,
    }
    error_edges: list[dict[str, str]] = []
    for rva, expected_target in error_call_targets.items():
        raw = bytes.fromhex(terminal_bytes[f"0x{rva:X}"])
        if raw[0] != 0xE8 or len(raw) != 5:
            raise ValueError(f"expected a direct error call at 0x{rva:X}")
        target = rva + 5 + struct.unpack("<i", raw[1:])[0]
        if target != expected_target:
            raise ValueError(
                f"error call target changed at 0x{rva:X}: "
                f"0x{target:X} != 0x{expected_target:X}"
            )
        error_edges.append(
            {"from_rva": f"0x{rva:X}", "target_rva": f"0x{target:X}"}
        )

    return {
        "branch_edges": branches,
        "terminal_instruction_bytes": terminal_bytes,
        "normal_return_rva": "0x3B9ACE0",
        "opaque_error_call_edges": error_edges,
        "null_edges": [
            {
                "field": "node+0x88",
                "initial_check_rva": "0x3B9AB53",
                "initial_branch_rva": "0x3B9AB5B",
                "initial_null_target_rva": "0x3B9AB93",
                "reload_rva": "0x3B9AB7D",
                "reload_test_rva": "0x3B9AB84",
                "reload_null_target_rva": "0x3B9ACE1",
                "initial_null_effect": "skip callback and continue timing aggregation",
                "reload_null_effect": "enter opaque error call",
                "path_condition": "initial check non-null, then reload reads null",
                "race_or_lifetime_cause": "unknown",
            },
            {
                "field": "optional helper return in RAX",
                "test_rva": "0x3B9AC4A",
                "null_target_rva": "0x3B9AC80",
                "effect": "skip optional post-log construction",
            },
        ],
        "loop_edges": [
            {
                "from_rva": "0x3B9ABC5",
                "target_rva": "0x3B9ABB0",
                "condition": "dependency_chain_not_sentinel",
            },
            {
                "from_rva": "0x3B9ACBE",
                "target_rva": "0x3B9AB50",
                "condition": "next_node_exists",
            },
        ],
        "padding_after_function_body": {
            "normal_return_rva": "0x3B9ACE0",
            "error_call_rvas": ["0x3B9ACE1", "0x3B9ACE7"],
            "function_end_rva_exclusive": "0x3B9ACED",
            "int3_padding_rvas": ["0x3B9ACE6", "0x3B9ACEC"],
        },
    }


def rva_from_va(image_base: int, value: int) -> int | None:
    if image_base <= value < image_base + EXPECTED_IMAGE_SIZE:
        return value - image_base
    return None


def decode_pdata(image: pefile.PE) -> dict[str, Any]:
    rows = getattr(image, "DIRECTORY_ENTRY_EXCEPTION", ())
    for entry in rows:
        begin = int(entry.struct.BeginAddress)
        end = int(entry.struct.EndAddress)
        if begin == FUNCTION_RVA and end == FUNCTION_END_RVA:
            unwind = int(entry.struct.UnwindData)
            return {
                "begin_rva": f"0x{begin:X}",
                "end_rva_exclusive": f"0x{end:X}",
                "unwind_info_rva": f"0x{unwind:X}",
            }
    raise ValueError("the exact callback function has no matching pdata row")


def decode_unwind(data: bytes, image: pefile.PE) -> dict[str, Any]:
    raw = bytes_at(data, image, UNWIND_RVA, 4)
    version = raw[0] & 0x07
    flags = raw[0] >> 3
    prolog_size = raw[1]
    code_count = raw[2]
    frame = raw[3]
    # UNWIND_CODE is an array of two-byte slots.  The array is rounded to an
    # even slot count before the optional handler RVA.  This exact row has a
    # non-zero flags field, so retaining the handler address is important: a
    # zero/"no EH" interpretation would lose part of the evidence.
    handler: int | None = None
    handler_bytes_hex: str | None = None
    if flags:
        handler_offset = 4 + ((code_count + 1) & ~1) * 2
        handler_bytes = bytes_at(data, image, UNWIND_RVA + handler_offset, 4)
        handler = struct.unpack("<I", handler_bytes)[0]
        handler_bytes_hex = handler_bytes.hex().upper()
    return {
        "raw_header_hex": raw.hex().upper(),
        "version": version,
        "flags": flags,
        "prolog_size_bytes": prolog_size,
        "unwind_code_count": code_count,
        "frame_register": frame & 0x0F,
        "frame_offset_units": frame >> 4,
        "handler_rva": f"0x{handler:X}" if handler is not None else None,
        "handler_bytes_hex": handler_bytes_hex,
    }


def decode_vtable(
    data: bytes, image: pefile.PE, descriptor: dict[str, Any]
) -> dict[str, Any]:
    vtable_rva = int(descriptor["vtable_rva"])
    values = struct.unpack(
        "<16Q", bytes_at(data, image, vtable_rva, 16 * 8)
    )
    image_base = int(image.OPTIONAL_HEADER.ImageBase)
    slots: list[str] = []
    for value in values:
        target = rva_from_va(image_base, value)
        slots.append(f"0x{target:X}" if target is not None else f"0x{value:X}")

    col_rva = int(descriptor["complete_object_locator_rva"])
    col = struct.unpack("<6I", bytes_at(data, image, col_rva, 24))
    type_rva = col[3]
    name = bytes_at(data, image, type_rva + 16, len(descriptor["type_name"]) + 1)
    expected_name = (descriptor["type_name"] + "\x00").encode("ascii")
    if name != expected_name:
        raise ValueError(
            f"RTTI type name mismatch at 0x{type_rva:X}: {name!r} != {expected_name!r}"
        )

    construction_rva = int(descriptor["construction_reference_rva"])
    construction = bytes_at(data, image, construction_rva, 7)
    if construction[:3] not in (b"L\x8d-", b"L\x8d="):
        raise ValueError(f"unexpected vtable construction instruction at 0x{construction_rva:X}")
    rel = struct.unpack_from("<i", construction, 3)[0]
    referenced = construction_rva + 7 + rel
    if referenced != vtable_rva:
        raise ValueError(
            f"construction reference 0x{construction_rva:X} targets 0x{referenced:X}, "
            f"expected 0x{vtable_rva:X}"
        )

    return {
        "type_descriptor_rva": f"0x{type_rva:X}",
        "type_name": descriptor["type_name"],
        "complete_object_locator_rva": f"0x{col_rva:X}",
        "vtable_rva": f"0x{vtable_rva:X}",
        "slot_target_rvas": slots,
        "invoke_slot": {
            "slot_index": 2,
            "byte_offset": "0x10",
            "target_rva": slots[2],
        },
        "construction_reference_rva": f"0x{construction_rva:X}",
        "construction_reference_bytes_hex": construction.hex().upper(),
    }


def find_direct_calls(image: pefile.PE, data: bytes, target_rva: int) -> list[int]:
    """Return direct ``E8 rel32`` callsite RVAs in the executable .text."""

    text_section = next(
        (
            section
            for section in image.sections
            if section.Name.rstrip(b"\x00") == b".text"
        ),
        None,
    )
    if text_section is None:
        raise ValueError("the exact executable has no .text section")
    raw = text_section.get_data()
    start_rva = int(text_section.VirtualAddress)
    hits: list[int] = []
    for offset in range(max(0, len(raw) - 4)):
        if raw[offset] != 0xE8:
            continue
        relative = struct.unpack_from("<i", raw, offset + 1)[0]
        call_rva = start_rva + offset + 5 + relative
        if call_rva == target_rva:
            hits.append(start_rva + offset)
    return hits


def extract(exe: Path, fixture: Path | None = None) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError(
            "source executable is not the pinned CK3 1.19.0.6 build: "
            f"size={len(data)} sha256={digest}"
        )

    image = pefile.PE(str(source), fast_load=False)
    if int(image.FILE_HEADER.TimeDateStamp) != EXPECTED_TIMESTAMP:
        raise ValueError("unexpected PE timestamp")
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected PE image base")
    if int(image.OPTIONAL_HEADER.SizeOfImage) != EXPECTED_IMAGE_SIZE:
        raise ValueError("unexpected PE image size")

    prologue = bytes_at(data, image, FUNCTION_RVA, len(PROLOGUE_BYTES))
    if prologue != PROLOGUE_BYTES:
        raise ValueError("exact callback prologue bytes do not match")

    callback_bytes = {
        f"0x{rva:X}": bytes_at(data, image, rva, len(expected)).hex().upper()
        for rva, expected in CALLBACK_BYTES.items()
    }
    for rva, expected in CALLBACK_BYTES.items():
        if bytes.fromhex(callback_bytes[f"0x{rva:X}"]) != expected:
            raise ValueError(f"callback instruction mismatch at 0x{rva:X}")

    pdata = decode_pdata(image)
    unwind = decode_unwind(data, image)
    if pdata["unwind_info_rva"] != f"0x{UNWIND_RVA:X}":
        raise ValueError("unexpected unwind RVA")
    if unwind["prolog_size_bytes"] != len(PROLOGUE_BYTES):
        raise ValueError("pdata prologue size does not match exact bytes")
    if unwind["handler_rva"] != f"0x{UNWIND_HANDLER_RVA:X}":
        raise ValueError("unexpected exact-build unwind handler RVA")

    vtables = [decode_vtable(data, image, item) for item in VTABLES]
    cfg = extract_cfg(data, image)
    direct_calls = find_direct_calls(image, data, FUNCTION_RVA)
    if direct_calls != list(CALLSITE_RVAS):
        raise ValueError(
            "direct callback-loop callsites changed: "
            f"{[f'0x{x:X}' for x in direct_calls]}"
        )
    fixture_info: dict[str, Any] | None = None
    if fixture is not None:
        fixture_path = fixture.resolve()
        fixture_data = fixture_path.read_bytes()
        fixture_info = {
            "path": str(fixture_path),
            "sha256": sha256(fixture_data),
            "size_bytes": len(fixture_data),
        }

    return {
        "contract": "phase2-loader-callback-static-slice-v1",
        "status": "static-ready",
        "read_only": True,
        "production_installed": False,
        "production_abi_changed": False,
        "source": {
            "path": str(source),
            "sha256": digest,
            "size_bytes": len(data),
            "pe_timestamp": f"0x{EXPECTED_TIMESTAMP:X}",
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
            "size_of_image": f"0x{EXPECTED_IMAGE_SIZE:X}",
        },
        "fixture": fixture_info,
        "function": {
            "rva": f"0x{FUNCTION_RVA:X}",
            "end_rva_exclusive": f"0x{FUNCTION_END_RVA:X}",
            "prologue": {
                "rva": f"0x{FUNCTION_RVA:X}",
                "end_rva_exclusive": f"0x{PROLOGUE_END_RVA:X}",
                "bytes_hex": prologue.hex().upper(),
                "length_bytes": len(prologue),
                "pdata": pdata,
                "unwind": unwind,
            },
            "callback_instruction_bytes": callback_bytes,
            "cfg": cfg,
        },
        "win64_parameter_flow": {
            "calling_convention": "MSVC x64",
            "entry_argument_register": "RCX",
            "entry_owner_load": "[RCX+0x08]",
            "node_vector_begin_load": "[owner+0x70]",
            "node_count_load": "[owner+0x7C]",
            "callback_receiver_load": "RCX=[node+0x88]",
            "vptr_load": "RAX=[RCX]",
            "indirect_call": "[RAX+0x10]",
            "explicitly_initialized_call_registers": ["RCX"],
            "additional_argument_registers": "not_established",
            "return_value_consumed_by_loop": False,
        },
        "callback_vtable": {
            "slot_index": 2,
            "byte_offset": "0x10",
            "slot_target_rva": "0x3B9BA70",
            "candidate_callable_vtables": vtables,
            "runtime_node_vptr_identity": "unknown",
            "runtime_callback_return_semantics": "unknown",
            "static_candidate_return_kind": "void_callable_wrapper",
        },
        "callers": {
            "direct_relative_callsite_rvas": [f"0x{rva:X}" for rva in direct_calls],
            "count": len(direct_calls),
            "argument_setup_observed": "local 16-byte pair address passed in RCX at each listed callsite",
        },
        "thread_lifecycle": {
            "bounded_dispatch": "direct_synchronous_call",
            "continuation_rva": "0x3B9AB93",
            "same_function_continuation": True,
            "thread_handoff_observed_in_bounded_range": False,
            "thread_identity": "unknown",
            "callback_object_lifetime": "unknown",
            "lock_or_quiescence": "not_observed",
            "unwind_metadata_present": True,
            "production_detour": False,
        },
        "evidence_limits": [
            "candidate callable vtables are static construction evidence; runtime node+0x88 vptr is not observed",
            "void kind applies to the candidate _Func_impl_no_alloc wrappers; runtime callback return remains unknown",
            "a synchronous direct call does not identify the operating-system thread",
            "no production callback hook, bridge field, or loader-readiness claim follows",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = extract(args.exe, args.fixture)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
