#!/usr/bin/env python3
"""Read-only disassembly of exact CK3 1.19.0.6 active advantage helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
FUNCTIONS = {
    "resolve": (0x2308D50, 0x2308DE5),
    "side_total": (0x2307CB0, 0x2307EE0),
    "commander": (0x2307680, 0x2307A2D),
    "side_modifier": (0x2307230, 0x2307679),
    "main_tick": (0x2309E80, 0x230A010),
    "damage_advantage": (0x23053B0, 0x2305580),
    "side_primary_refresh": (0x23CBC20, 0x23CBCE0),
    "manager_refresh_pass_a": (0x27FB280, 0x27FB4C9),
    "phase_event_schedule_head": (0x27FB4D0, 0x27FB53B),
    "phase_event_schedule_loop": (0x27FB53B, 0x27FB5BA),
    "daily_dispatch": (0x27FB5D0, 0x27FB780),
    # Counter helper safety audit: the original side caller, damage wrapper,
    # class resolver, and per-entry current-chunk reader.
    "counter_side_caller": (0x23CB1D0, 0x23CB435),
    "counter_damage_wrapper": (0x23CAE70, 0x23CB1D0),
    "counter_class_resolver": (0x23CF1B0, 0x23CF96D),
    "counter_current_chunk": (0x23D2B90, 0x23D2CDE),
}


# Exact-build instruction sites for the current CCombat+0x710 cache path.
# These do not prove cross-manager timing or future input values.
CACHE_ANCHORS = {
    "base_from_combat": ("resolve", 0x2308D9A, "mov", "rbx, qword ptr [rsi + 0x6c8]"),
    "side0_target_context_null": ("resolve", 0x2308DA6, "xor", "r9d, r9d"),
    "side0_total_call": ("resolve", 0x2308DAF, "call", "0x2307cb0"),
    "side1_target_context_null": ("resolve", 0x2308DB4, "xor", "r9d, r9d"),
    "side1_total_call": ("resolve", 0x2308DC6, "call", "0x2307cb0"),
    "resolved_cache_write": ("resolve", 0x2308DCE, "mov", "qword ptr [rsi + 0x710], rbx"),
    "side_roll_read": ("side_total", 0x2307CD8, "movsxd", "rcx, dword ptr [rcx + r14*4 + 0x6d0]"),
    "roll_scale_q100000": ("side_total", 0x2307CE0, "imul", "rbx, rcx, 0x186a0"),
    "target_context_gate": ("side_total", 0x2307CEA, "test", "r9, r9"),
    "null_target_skips_conditions": ("side_total", 0x2307CED, "je", "0x2307e19"),
    "commander_selection_read": ("side_total", 0x2307E2C, "mov", "r8d, dword ptr [r15 + rdi + 0x94]"),
    "commander_component_call": ("side_total", 0x2307E88, "call", "0x2307680"),
    "side_aggregator_call": ("side_total", 0x2307EB5, "call", "0x2307230"),
    "main_tick_updates_roll0": ("main_tick", 0x2309F29, "mov", "dword ptr [rdi + 0x6d0], eax"),
    "main_tick_updates_roll1": ("main_tick", 0x2309F37, "mov", "dword ptr [rdi + 0x6d4], eax"),
    "main_tick_damage_multiplier_call": ("main_tick", 0x2309F55, "call", "0x23053b0"),
    "main_tick_cached_advantage_sign": ("main_tick", 0x2309F5A, "cmp", "qword ptr [rdi + 0x710], 0"),
    "multiplier_reads_cached_advantage": ("damage_advantage", 0x23053B4, "mov", "rax, qword ptr [rcx + 0x710]"),
}


# The current-cache commander and side-aggregator operands, with exact .pdata
# function spans. These are dependency sites, not a reconstruction of values.
COMPONENT_ANCHORS = {
    "side_total_output_initialized_from_roll": ("side_total", 0x2307CE7, "mov", "qword ptr [rdx], rbx"),
    "side_total_commander_call": ("side_total", 0x2307E88, "call", "0x2307680"),
    "side_total_commander_return_value": ("side_total", 0x2307E8D, "mov", "rcx, qword ptr [rax]"),
    "side_total_commander_add": ("side_total", 0x2307E90, "add", "qword ptr [r12], rcx"),
    "side_total_aggregator_call": ("side_total", 0x2307EB5, "call", "0x2307230"),
    "side_total_aggregator_return_value": ("side_total", 0x2307EBA, "mov", "rcx, qword ptr [rax]"),
    "side_total_aggregator_add": ("side_total", 0x2307EBD, "add", "qword ptr [r12], rcx"),
    "commander_side_index": ("commander", 0x23076AC, "movsxd", "r12, r9d"),
    "commander_character_stat": ("commander", 0x23076B8, "movsxd", "rdx, dword ptr [r8 + 0xd8]"),
    "commander_stat_scale": ("commander", 0x23076BF, "imul", "rdi, rdx, 0x186a0"),
    "commander_null_context_branch": ("commander", 0x23076D2, "test", "r14, r14"),
    "commander_side_specific_operand": ("commander", 0x2307799, "mov", "r8d, dword ptr [rax + r13]"),
    "commander_first_helper": ("commander", 0x23077A7, "call", "0x2306940"),
    "commander_second_helper": ("commander", 0x23077D4, "call", "0x2306c70"),
    "commander_modifier_set": ("commander", 0x23077E2, "call", "0x26172c0"),
    "commander_regiment_backlink": ("commander", 0x2307868, "mov", "rax, qword ptr [r15 + 0x1b0]"),
    "commander_late_identity_compare": ("commander", 0x230790A, "cmp", "eax, dword ptr [r15 + 0x18]"),
    "side_aggregator_context": ("side_modifier", 0x230724C, "mov", "rdi, qword ptr [rsp + 0x88]"),
    "side_aggregator_first_modifier": ("side_modifier", 0x2307280, "call", "0x2940d50"),
    "side_aggregator_null_context_branch": ("side_modifier", 0x2307294, "test", "rdi, rdi"),
    "side_aggregator_modifier_set": ("side_modifier", 0x23072BC, "lea", "rcx, [rsi + 0x68]"),
    "side_aggregator_set_lookup": ("side_modifier", 0x23072C0, "call", "0x20ab950"),
    "side_aggregator_location_context": ("side_modifier", 0x2307365, "mov", "rax, qword ptr [r15 + 0x6b8]"),
    "side_aggregator_context_chain_operand": ("side_modifier", 0x230738D, "movzx", "r8d, word ptr [rax + 0x76c]"),
    "side_aggregator_combat_flag": ("side_modifier", 0x23074C9, "cmp", "byte ptr [r15 + 0x6fd], 0"),
}
COMPONENT_FUNCTION_BOUNDS = {
    "side_total": (0x2307CB0, 0x2307EE0),
    "commander": (0x2307680, 0x2307A2D),
    "side_modifier": (0x2307230, 0x2307679),
}


def read_image(exe: Path) -> pefile.PE:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    if sha != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {sha}")
    return pefile.PE(data=data, fast_load=True)


def decode(image: pefile.PE, name: str) -> list:
    start, end = FUNCTIONS[name]
    code = image.get_data(start, end - start)
    if len(code) != end - start:
        raise ValueError("short executable read")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return list(decoder.disasm(code, start))


def verify_cache_chain(image: pefile.PE) -> dict:
    decoded = {name: {instruction.address: instruction for instruction in decode(image, name)}
               for name in {row[0] for row in CACHE_ANCHORS.values()}}
    anchors = {}
    for claim, (name, address, mnemonic, operands) in CACHE_ANCHORS.items():
        instruction = decoded[name].get(address)
        if instruction is None or (instruction.mnemonic, instruction.op_str) != (mnemonic, operands):
            actual = None if instruction is None else f"{instruction.mnemonic} {instruction.op_str}"
            raise ValueError(f"{claim} at 0x{address:X}: expected {mnemonic} {operands}, got {actual}")
        anchors[claim] = {"rva": f"0x{address:X}", "bytes_hex": instruction.bytes.hex().upper(),
                          "instruction": f"{mnemonic} {operands}"}
    return {
        "schema": "ck3.native_active_advantage_cache_source_chain.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "proof_layer": "exact-build-instruction-sites",
        "anchors": anchors,
        "path_result": {
            "cached_total_formula": "base + side0_total - side1_total",
            "both_total_calls_pass_null_target_context": True,
            "target_context_condition_branch_executed_for_cache": False,
            "commander_and_side_aggregator_calls_remain_on_cache_path": True,
            "main_tick_may_update_roll_before_reading_cached_advantage": True,
        },
        "not_proven": ["same-generation roll and cached advantage in paused reads",
                       "future side modifier and commander values", "cross-manager global order",
                       "native next-day or whole-battle probability"],
    }


def verify_component_sources(image: pefile.PE) -> dict:
    # The two component helpers are only relevant here through the pinned
    # current-cache call path; verify its null-context callsites as well.
    verify_cache_chain(image)
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    spans = {}
    for name, expected in COMPONENT_FUNCTION_BOUNDS.items():
        matches = [(int(row.struct.BeginAddress), int(row.struct.EndAddress))
                   for row in image.DIRECTORY_ENTRY_EXCEPTION
                   if int(row.struct.BeginAddress) <= expected[0] < int(row.struct.EndAddress)]
        if matches != [expected]:
            raise ValueError(f"{name} .pdata span changed: {matches}")
        spans[name] = {"begin_rva": f"0x{expected[0]:X}", "end_rva_exclusive": f"0x{expected[1]:X}"}
    decoded = {name: {instruction.address: instruction for instruction in decode(image, name)}
               for name in COMPONENT_FUNCTION_BOUNDS}
    anchors = {}
    for claim, (name, address, mnemonic, operands) in COMPONENT_ANCHORS.items():
        instruction = decoded[name].get(address)
        if instruction is None or (instruction.mnemonic, instruction.op_str) != (mnemonic, operands):
            actual = None if instruction is None else f"{instruction.mnemonic} {instruction.op_str}"
            raise ValueError(f"{claim} at 0x{address:X}: expected {mnemonic} {operands}, got {actual}")
        anchors[claim] = {"rva": f"0x{address:X}", "bytes_hex": instruction.bytes.hex().upper(),
                          "instruction": f"{mnemonic} {operands}"}
    return {
        "schema": "ck3.native_active_advantage_component_sources.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "proof_layer": "exact-build-instruction-sites-and-pdata-bounds",
        "cache_chain_verified_on_same_image": True,
        "function_spans": spans,
        "anchors": anchors,
        "confirmed_boundary": "current-cache side_total calls both components with null target context",
        "not_proven": ["exact contribution values at current pause or next day",
                       "semantic names of every modifier enum and operand",
                       "cross-manager event/join ordering", "safe paused replay of either helper"],
    }


def disassemble(exe: Path, name: str, calls_to: list[int] | None = None) -> list[str]:
    image = read_image(exe)
    if name == "callers":
        image.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
        )
        if not calls_to:
            raise ValueError("--calls-to required for callers")
        targets = set(calls_to)
        callers = []
        for section in image.sections:
            if not section.Characteristics & 0x20000000:
                continue
            section_rva = int(section.VirtualAddress)
            code = section.get_data()
            for i in range(len(code) - 4):
                if code[i] != 0xE8:
                    continue
                destination = section_rva + i + 5 + struct.unpack_from("<i", code, i + 1)[0]
                if destination in targets:
                    caller = section_rva + i
                    owner = next(
                        (
                            (int(row.struct.BeginAddress), int(row.struct.EndAddress))
                            for row in image.DIRECTORY_ENTRY_EXCEPTION
                            if int(row.struct.BeginAddress) <= caller < int(row.struct.EndAddress)
                        ),
                        None,
                    )
                    callers.append(f"{caller:08X} -> {destination:08X}; owner={owner}")
        return callers
    return [
        f"{instruction.address:08X}  {instruction.mnemonic:<8} {instruction.op_str}"
        for instruction in decode(image, name)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--function", choices=sorted(FUNCTIONS) + ["callers"])
    parser.add_argument("--calls-to", action="append", type=lambda value: int(value, 0))
    parser.add_argument("--verify-cache", action="store_true", help="verify the current cache source path")
    parser.add_argument("--verify-components", action="store_true", help="verify commander/side source sites and .pdata spans")
    parser.add_argument("--output", type=Path, help="exclusively create a new verification artifact")
    parser.add_argument("--expected", type=Path, help="compare verification bytes to a frozen artifact")
    args = parser.parse_args()
    if sum((args.verify_cache, args.verify_components, bool(args.function))) != 1:
        parser.error("provide exactly one of --verify-cache, --verify-components or --function")
    if args.verify_cache or args.verify_components:
        image = read_image(args.exe)
        result = verify_cache_chain(image) if args.verify_cache else verify_component_sources(image)
        body = json.dumps(result, indent=2) + "\n"
        if args.expected is not None and args.expected.read_bytes() != body.encode("utf-8"):
            raise ValueError(f"frozen verification artifact differs: {args.expected}")
        if args.output is None:
            print(body, end="")
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(body)
    else:
        if args.output is not None or args.expected is not None:
            parser.error("--output/--expected are only valid with verification")
        print("\n".join(disassemble(args.exe, args.function, args.calls_to)))


if __name__ == "__main__":
    main()
