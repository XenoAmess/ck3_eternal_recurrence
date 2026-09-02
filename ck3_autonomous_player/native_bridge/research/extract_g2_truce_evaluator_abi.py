#!/usr/bin/env python3
"""Extract the exact-build G2 truce-evaluator ABI and direct xrefs.

The extractor is static: it reads the pinned executable, bridge source, and
one already-frozen terminal summary. It never starts or attaches to CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_INS_CALL, X86_INS_JMP, X86_OP_IMM
import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000
EVALUATOR_RVA = 0x3373000
EVALUATOR_PDATA = (0x3373000, 0x337312F, 0x4C92B1C)
CADDTRUCE_CALLS = (
    (0x2EDAF01, 0x2EDAF0F, 0x2EDAF14),
    (0x2EDB58F, 0x2EDB59E, 0x2EDB5A3),
)
WRAPPER_PDATA = (0x2EDC1B0, 0x2EDC209, 0x4C38E20)
WRAPPER_TAIL = (0x2EDC1FB, 0x2EDC209)
EXPECTED_TERMINAL_SUMMARY_SHA256 = "C4157B5E48D9634E79146A970C254914DEBB1C6B57F0A81459EAFD4DD0493574"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def instruction_row(instruction, image_base: int) -> dict[str, Any]:
    return {
        "rva": f"0x{instruction.address - image_base:X}",
        "bytes": instruction.bytes.hex().upper(),
        "mnemonic": instruction.mnemonic,
        "operands": instruction.op_str,
    }


def runtime_functions(image: pefile.PE) -> list[tuple[int, int, int]]:
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    )
    return sorted(
        (int(row.struct.BeginAddress), int(row.struct.EndAddress), int(row.struct.UnwindData))
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    )


def containing_function(functions: list[tuple[int, int, int]], rva: int):
    for begin, end, unwind in functions:
        if begin <= rva < end:
            return begin, end, unwind
    return None


def bytes_at(data: bytes, image: pefile.PE, begin: int, end: int) -> bytes:
    offset = image.get_offset_from_rva(begin)
    value = data[offset : offset + end - begin]
    if len(value) != end - begin:
        raise ValueError(f"short file-backed range 0x{begin:X}..0x{end:X}")
    return value


def decode_range(decoder: Cs, data: bytes, image: pefile.PE, begin: int, end: int):
    return list(decoder.disasm(bytes_at(data, image, begin, end), EXPECTED_IMAGE_BASE + begin))


def pdata_row(value: tuple[int, int, int]) -> dict[str, str]:
    return {
        "begin_rva": f"0x{value[0]:X}",
        "end_rva_exclusive": f"0x{value[1]:X}",
        "unwind_rva": f"0x{value[2]:X}",
    }


def scan_direct_xrefs(
    decoder: Cs,
    data: bytes,
    image: pefile.PE,
    functions: list[tuple[int, int, int]],
) -> list[dict[str, Any]]:
    """Enumerate exact E8/E9 rel32 xrefs and bind every one to PDATA."""
    result: list[dict[str, Any]] = []
    for section in image.sections:
        if not int(section.Characteristics) & 0x20000000:
            continue
        section_rva = int(section.VirtualAddress)
        section_data = section.get_data()
        for index in range(len(section_data) - 4):
            opcode = section_data[index]
            if opcode not in (0xE8, 0xE9):
                continue
            rva = section_rva + index
            displacement = struct.unpack_from("<i", section_data, index + 1)[0]
            if rva + 5 + displacement != EVALUATOR_RVA:
                continue
            decoded = list(decoder.disasm(section_data[index : index + 5], EXPECTED_IMAGE_BASE + rva))
            if len(decoded) != 1 or decoded[0].size != 5:
                continue
            instruction = decoded[0]
            if instruction.id not in (X86_INS_CALL, X86_INS_JMP):
                continue
            if (not instruction.operands or instruction.operands[0].type != X86_OP_IMM
                    or instruction.operands[0].imm != EXPECTED_IMAGE_BASE + EVALUATOR_RVA):
                continue
            owner = containing_function(functions, rva)
            if owner is None:
                raise ValueError(f"direct evaluator xref lacks PDATA at 0x{rva:X}")
            result.append({
                "kind": "call" if opcode == 0xE8 else "tail_jump",
                "rva": f"0x{rva:X}",
                "bytes": section_data[index : index + 5].hex().upper(),
                "owner_pdata": pdata_row(owner),
            })
    return sorted(result, key=lambda row: int(row["rva"], 0))


def extract(exe: Path, bridge_source: Path, terminal_summary: Path) -> dict[str, Any]:
    data = exe.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_EXE_SIZE or digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable: size={len(data)} sha256={digest}")
    image = pefile.PE(data=data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")
    functions = runtime_functions(image)
    if containing_function(functions, EVALUATOR_RVA) != EVALUATOR_PDATA:
        raise ValueError("unexpected evaluator PDATA")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    evaluator_instructions = decode_range(decoder, data, image, EVALUATOR_PDATA[0], EVALUATOR_PDATA[1])
    evaluator_rows = [instruction_row(row, EXPECTED_IMAGE_BASE) for row in evaluator_instructions]
    by_rva = {int(row["rva"], 0): row for row in evaluator_rows}
    required_bindings = {
        0x337301A: ("mov", "rbx, rcx"),
        0x3373024: ("mov", "rsi, r8"),
        0x3373027: ("mov", "rbp, rdx"),
    }
    for rva, expected in required_bindings.items():
        row = by_rva.get(rva)
        if row is None or (row["mnemonic"], row["operands"]) != expected:
            raise ValueError(f"evaluator entry binding changed at 0x{rva:X}")
    first_r9 = next((row for row in evaluator_rows if "r9" in row["operands"].lower()), None)
    if first_r9 is None or first_r9["rva"] != "0x3373046" or first_r9["mnemonic"] != "lea":
        raise ValueError("incoming R9 is consumed or its first overwrite changed")
    direct_tls_rows = [row for row in evaluator_rows
                       if "fs:" in row["operands"].lower() or "gs:" in row["operands"].lower()]
    if direct_tls_rows:
        raise ValueError("evaluator gained direct FS/GS access")

    caddtruce_rows = []
    for start, call, end in CADDTRUCE_CALLS:
        instructions = decode_range(decoder, data, image, start, end)
        rows = [instruction_row(row, EXPECTED_IMAGE_BASE) for row in instructions]
        if (len(rows) != 4 or rows[0]["rva"] != f"0x{start:X}"
                or rows[-1]["rva"] != f"0x{call:X}"):
            raise ValueError(f"unexpected CAddTruce call sequence at 0x{start:X}")
        if rows[0]["mnemonic"] != "lea" or "+ 0x108" not in rows[0]["operands"]:
            raise ValueError("CAddTruce script-value offset changed")
        if rows[1]["mnemonic"] != "mov" or "+ 0x28]" not in rows[1]["operands"]:
            raise ValueError("CAddTruce evaluation-context load changed")
        sequence = bytes_at(data, image, start, end)
        owner = containing_function(functions, call)
        if owner is None:
            raise ValueError(f"CAddTruce call lacks PDATA at 0x{call:X}")
        caddtruce_rows.append({
            "sequence_rva": f"0x{start:X}..0x{end:X}",
            "call_rva": f"0x{call:X}",
            "owner_pdata": pdata_row(owner),
            "bytes": sequence.hex().upper(),
            "sha256": sha256(sequence),
            "instructions": rows,
        })

    if containing_function(functions, WRAPPER_TAIL[0]) != WRAPPER_PDATA:
        raise ValueError("unexpected generic wrapper PDATA")
    wrapper_bytes = bytes_at(data, image, *WRAPPER_TAIL)
    wrapper_rows = [instruction_row(row, EXPECTED_IMAGE_BASE)
                    for row in decode_range(decoder, data, image, *WRAPPER_TAIL)]
    if [(row["mnemonic"], row["operands"]) for row in wrapper_rows] != [
        ("mov", "r8, qword ptr [rdx + 0x28]"),
        ("add", "rsp, 0x20"),
        ("pop", "rbx"),
        ("jmp", "0x143373000"),
    ]:
        raise ValueError("generic wrapper no longer loads [context+0x28] into R8")

    xrefs = scan_direct_xrefs(decoder, data, image, functions)
    required_xrefs = {"0x2EDAF0F", "0x2EDB59E", "0x2EDC204"}
    if not required_xrefs.issubset({row["rva"] for row in xrefs}):
        raise ValueError("required native evaluator xref missing")

    bridge_data = bridge_source.read_bytes()
    bridge_text = bridge_data.decode("utf-8")
    wrong_request = ("const RaiktorSurrenderTruceRequestV1 request{\n"
                     "      effect_context, static_cast<std::byte *>(effect_context) + 0x28};")
    if wrong_request not in bridge_text:
        raise ValueError("analyzed bridge no longer contains the live candidate request")

    terminal_data = terminal_summary.read_bytes()
    terminal_digest = sha256(terminal_data)
    if terminal_digest != EXPECTED_TERMINAL_SUMMARY_SHA256:
        raise ValueError(f"unexpected terminal summary sha256={terminal_digest}")
    terminal = json.loads(terminal_data.decode("utf-8"))
    durable = terminal["durable_jsonl"]
    effect_context = int(durable["effect_context"], 0)
    evaluation_context = int(durable["evaluation_context"], 0)
    if evaluation_context != effect_context + 0x28:
        raise ValueError("live evaluation context was not the field address")
    if durable["post_call_row_count"] != 0 or terminal["session"]["exit_reason"] != "process_exit":
        raise ValueError("terminal boundary is not first-call process_exit")

    evaluator_bytes = bytes_at(data, image, EVALUATOR_PDATA[0], EVALUATOR_PDATA[1])
    return {
        "schema": "xar.ck3.g2_truce_evaluator_abi_root_cause.v1",
        "result": "STATIC_ROOT_CAUSE_IDENTIFIED",
        "read_only": True,
        "exact_build": {"version": "1.19.0.6", "sha256": digest,
                        "file_size": len(data), "image_base": f"0x{EXPECTED_IMAGE_BASE:X}"},
        "evaluator": {
            "entry_rva": f"0x{EVALUATOR_RVA:X}", "pdata": pdata_row(EVALUATOR_PDATA),
            "bytes_sha256": sha256(evaluator_bytes),
            "entry_bindings": {"RCX": "script_value -> RBX", "RDX": "effect_context -> RBP",
                               "R8": "evaluation_context -> RSI"},
            "first_r9_reference": first_r9, "incoming_r9_consumed": False,
            "incoming_stack_parameter_consumed": False,
            "direct_fs_gs_tls_accesses": direct_tls_rows, "return": "signed int32 in EAX",
        },
        "direct_xrefs": {
            "count": len(xrefs), "call_count": sum(row["kind"] == "call" for row in xrefs),
            "tail_jump_count": sum(row["kind"] == "tail_jump" for row in xrefs), "rows": xrefs,
        },
        "native_caddtruce_calls": caddtruce_rows,
        "native_generic_wrapper": {
            "pdata": pdata_row(WRAPPER_PDATA),
            "tail_rva": f"0x{WRAPPER_TAIL[0]:X}..0x{WRAPPER_TAIL[1]:X}",
            "bytes": wrapper_bytes.hex().upper(), "sha256": sha256(wrapper_bytes),
            "instructions": wrapper_rows,
        },
        "bridge_candidate": {"source_sha256": sha256(bridge_data),
                             "request_expression": "evaluation_context = effect_context + 0x28",
                             "passes_field_address": True},
        "frozen_live_boundary": {
            "terminal_summary_sha256": terminal_digest,
            "effect_context": durable["effect_context"],
            "evaluation_context": durable["evaluation_context"],
            "evaluation_equals_effect_context_plus_0x28": True,
            "post_call_row_count": durable["post_call_row_count"],
            "terminal": terminal["session"]["exit_reason"],
        },
        "abi_diagnosis": {
            "three_parameter_msvc_x64_signature_correct": True,
            "missing_parameter": False, "thiscall_mismatch": False,
            "script_value_plus_0x108_correct": True, "effect_context_argument_correct": True,
            "evaluation_context_expected": "pointer value loaded from *(void **)(effect_context + 0x28)",
            "evaluation_context_observed": "address of field (effect_context + 0x28)",
            "root_cause": "wrong_evaluation_context_kind",
            "effect_context_lifetime": "constructed and populated before call; destroyed only after observer returns",
            "thread_tls_boundary": "no direct FS/GS access in evaluator; nested-call thread/TLS requirements remain unproven",
        },
        "next_distinct_seam": {
            "private_only_change": "load the pointer stored at effect_context+0x28 and pass that value as R8",
            "required_guards": ["loaded pointer is non-null"],
            "unchanged": ["script_value +0x108", "effect_context RDX", "evaluator RVA 0x3373000"],
        },
        "boundaries": {"ck3_started": False, "process_attached": False, "mutation_sent": False,
                       "public_abi_changed": False, "public_readiness_changed": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--bridge-source", type=Path, required=True)
    parser.add_argument("--terminal-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = extract(arguments.exe.resolve(), arguments.bridge_source.resolve(),
                     arguments.terminal_summary.resolve())
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if arguments.output is None:
        print(rendered, end="")
    else:
        arguments.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
