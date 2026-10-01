"""Verify native outbound marriage pending fields from a frozen CK3 PE file.

This verifier reads disk evidence only. It does not start or attach to CK3,
open a pipe, inspect the desktop, or touch profiles, saves, or workshop data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, verify

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures/ck3_12002_family_outbound_fields_abi.json"


def verify_outbound_fields(exe: Path, fixture: Path = FIXTURE) -> dict:
    contract = json.loads(fixture.read_text(encoding="utf-8"))
    failures = verify(exe, fixture)
    if failures:
        raise ValueError("; ".join(failures))
    data = exe.read_bytes()
    image = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = {}
    for row in contract["semantic_checks"]:
        rva = int(row["rva"], 0)
        offset = image.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        rip = [hex(instruction.address + instruction.size + op.mem.disp)
               for op in instruction.operands
               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        direct = [hex(op.imm) for op in instruction.operands
                  if op.type == X86_OP_IMM and instruction.mnemonic in
                  ("call", "jmp", "je", "jne")]
        actual = (instruction.bytes.hex(" ").upper(),
                  f"{instruction.mnemonic} {instruction.op_str}", rip, direct)
        expected = (row["bytes"], row["instruction"], row["rip_targets"],
                    row["direct_targets"])
        if actual != expected:
            raise ValueError(f"Changed {row['purpose']} at {row['rva']}")
        if row["purpose"] in instructions:
            raise ValueError(f"Duplicate purpose {row['purpose']}")
        instructions[row["purpose"]] = row

    for span in contract["exact_byte_spans"]:
        start, end = int(span["start_rva"], 0), int(span["end_rva"], 0)
        offset = image.rva_to_offset(start)
        digest = hashlib.sha256(data[offset:offset + end - start]).hexdigest()
        if digest != span["sha256"]:
            raise ValueError(f"Changed native span {span['name']}")

    for row in contract["rtti"]:
        col_rva = int(row["col_rva"], 0)
        col = struct.unpack_from("<6I", data, image.rva_to_offset(col_rva))
        type_rva = int(row["type_rva"], 0)
        if (col[0], col[1], col[3], col[5]) != (
                1, row["subobject_offset"], type_rva, col_rva):
            raise ValueError(f"Changed RTTI locator for {row['name']}")
        name_offset = image.rva_to_offset(type_rva) + 16
        name = data[name_offset:data.index(0, name_offset)].decode("ascii")
        if name != row["name"]:
            raise ValueError(f"Changed native type identity for {row['name']}")
        vt = image.rva_to_offset(int(row["vtable_rva"], 0))
        locator = struct.unpack_from("<Q", data, vt - 8)[0] - image.image_base
        if locator != col_rva:
            raise ValueError(f"Changed vtable/RTTI binding for {row['name']}")

    bindings = contract["runtime_bindings"]
    for purpose, binding in (
            ("constructor_pending_primary_vtable", "pending_object_vtable"),
            ("constructor_pending_secondary_vtable", "pending_component_vtable"),
            ("daily_pending_storage_global", "pending_storage_slot"),
            ("daily_expiration_global", "expiration_days_slot"),
            ("marriage_offer_factory_vtable", "marriage_special_vtable"),
            ("arrange_interaction_database_global", "interaction_database_slot")):
        actual = [int(value, 0) for value in instructions[purpose]["rip_targets"]]
        if actual != [int(bindings[binding], 0)]:
            raise ValueError(f"Changed native binding {binding}")
    for purpose in ("response_remove_pending", "expiry_remove_pending"):
        actual = [int(value, 0) for value in instructions[purpose]["direct_targets"]]
        if actual != [int(bindings["pending_remove"], 0)]:
            raise ValueError("Response/expiry no longer removes the pending entry")
    layout = contract["layouts"]
    for role in ("actor", "recipient", "subject_secondary_actor",
                 "candidate_secondary_recipient", "intermediary"):
        if layout[f"pending_{role}"] != layout["pending_context"] + layout[f"context_{role}"]:
            raise ValueError(f"Embedded context role differs: {role}")

    source = HERE.parent / contract["source_binding_file"]
    header = source.read_text(encoding="utf-8")
    for name, value in contract["source_bindings"].items():
        found = re.search(r"\b" + re.escape(name) + r"\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if found is None or int(found.group(1), 0) != int(value, 0):
            raise ValueError(f"Changed production source binding {name}")
    scanner = (HERE.parent / contract["source_scanner_file"]).read_text(encoding="utf-8")
    for name, pattern in contract["source_scanner_patterns"].items():
        if re.search(pattern, scanner) is None:
            raise ValueError(f"Changed production storage reader {name}")

    return {
        "schema_version": 1,
        "status": "GREEN",
        "readiness": "static-ready",
        "game_version": "1.20.0.2",
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "unique_signature_count": len(contract["signature_anchors"]),
        "vtable_prefix_count": len(contract["vtable_prefixes"]),
        "semantic_instruction_count": len(instructions),
        "native_span_count": len(contract["exact_byte_spans"]),
        "rtti_type_binding_count": len(contract["rtti"]),
        "source_constant_binding_count": len(contract["source_bindings"]),
        "source_scanner_binding_count": len(contract["source_scanner_patterns"]),
        "runtime_bindings": bindings,
        "layouts": layout,
        "local_ck3_touched": False,
        "live_verified": False,
        "unverified": contract["known_gaps"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_outbound_fields(args.exe, args.fixture)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {result['unique_signature_count']} signatures, "
          f"{result['vtable_prefix_count']} vtables, "
          f"{result['semantic_instruction_count']} instructions, "
          f"{result['native_span_count']} native spans, "
          f"{result['rtti_type_binding_count']} RTTI bindings, "
          f"{result['source_constant_binding_count']} source constants and "
          f"{result['source_scanner_binding_count']} typed storage reads; offline only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
