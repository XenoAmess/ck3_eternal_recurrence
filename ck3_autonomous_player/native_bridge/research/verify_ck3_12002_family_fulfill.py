"""Verify CK3 1.20 existing-betrothal fulfillment using the frozen EXE only.

This reads a PE file and the reviewed ABI fixture. It never opens a CK3 process,
pipe, desktop, user profile, save, or workshop directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, verify


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures/ck3_12002_family_fulfill_abi.json"


def verify_fulfillment(exe: Path, fixture: Path = FIXTURE) -> dict:
    manifest = json.loads(fixture.read_text(encoding="utf-8-sig"))
    failures = verify(exe, fixture)
    if failures:
        raise ValueError("; ".join(failures))
    data = exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows = {}
    for row in manifest["semantic_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(decoder.disasm(data[offset:offset + 15], rva))
        rip_targets = [hex(instruction.address + instruction.size + op.mem.disp)
                       for op in instruction.operands
                       if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        direct_targets = [hex(op.imm) for op in instruction.operands
                          if op.type == X86_OP_IMM and instruction.mnemonic in
                          ("call", "jmp", "je", "jne")]
        actual = (instruction.bytes.hex(" ").upper(),
                  f"{instruction.mnemonic} {instruction.op_str}",
                  rip_targets, direct_targets)
        expected = (row["bytes"], row["instruction"], row["rip_targets"],
                    row["direct_targets"])
        if actual != expected:
            raise ValueError(f"Changed {row['purpose']} at {row['rva']}")
        if row["purpose"] in rows:
            raise ValueError(f"Duplicate semantic purpose {row['purpose']}")
        rows[row["purpose"]] = row

    for literal in manifest["literals"]:
        expected = bytes.fromhex(literal["hex"])
        offset = pe.rva_to_offset(int(literal["rva"], 0))
        if data[offset:offset + len(expected)] != expected:
            raise ValueError(f"Changed matrilineal literal at {literal['rva']}")

    # The relationship producer, the native existing-pair call chain and the
    # runtime binding ledger must agree. This checks a useful ABI distinction:
    # CanSend's final result is reused; a raw 1.19 queue call is not carried over.
    binding_calls = {
        "fulfillment_construct_context": "construct_all_roles",
        "fulfillment_complete_can_send": "complete_can_send",
        "fulfillment_clone_embedded_context": "copy_context",
        "fulfillment_intermediary_acceptance": "intermediary_acceptance",
        "fulfillment_recipient_acceptance": "recipient_acceptance",
        "fulfillment_destroy_caller_embedded_context": "destroy_context",
        "can_execute_complete_can_send": "complete_can_send",
        "complete_can_send_outer_answer": "outer_answer",
        "send_context_copy": "copy_context",
        "opposite_sex_read_matrilineal": "read_boolean_option",
        "ordinary_marriage_caller_destroy_embedded_context": "destroy_context",
        "ordinary_marriage_caller_destroy_source_context": "destroy_context",
    }
    for purpose, binding in binding_calls.items():
        wanted = int(manifest["runtime_bindings"][binding], 0)
        if [int(item, 0) for item in rows[purpose]["direct_targets"]] != [wanted]:
            raise ValueError(f"Native call disagrees with binding {binding}")
    for purpose in ("matrilineal_string_id_slot_initialize",
                    "matrilineal_string_id_slot_register",
                    "opposite_sex_matrilineal_slot"):
        wanted = int(manifest["runtime_bindings"]["matrilineal_option_id_slot"], 0)
        if [int(item, 0) for item in rows[purpose]["rip_targets"]] != [wanted]:
            raise ValueError(f"Matrilineal StringID producer/consumer differs: {purpose}")
    for purpose, binding in (
            ("fulfillment_primary_command_vtable", "send_command_primary_vtable"),
            ("fulfillment_secondary_command_vtable", "send_command_secondary_vtable"),
            ("send_primary_command_vtable", "send_command_primary_vtable"),
            ("send_secondary_command_vtable", "send_command_secondary_vtable")):
        wanted = int(manifest["runtime_bindings"][binding], 0)
        if [int(item, 0) for item in rows[purpose]["rip_targets"]] != [wanted]:
            raise ValueError(f"Existing-pair command differs from generic send {binding}")

    return {
        "schema_version": 1,
        "status": "GREEN",
        "readiness": "static-ready",
        "game_version": "1.20.0.2",
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "unique_signature_count": len(manifest["signature_anchors"]),
        "vtable_prefix_count": len(manifest["vtable_prefixes"]),
        "semantic_instruction_count": len(rows),
        "call_binding_count": len(binding_calls),
        "global_and_vtable_binding_count": 7,
        "local_ck3_touched": False,
        "live_verified": False,
        "runtime_bindings": manifest["runtime_bindings"],
        "unverified": manifest["known_gaps"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_fulfillment(args.exe, args.fixture)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {result['unique_signature_count']} unique signatures, "
          f"{result['vtable_prefix_count']} vtables, "
          f"{result['semantic_instruction_count']} instructions, "
          f"{result['call_binding_count'] + result['global_and_vtable_binding_count']} "
          "native binding relations; offline only, no live validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
