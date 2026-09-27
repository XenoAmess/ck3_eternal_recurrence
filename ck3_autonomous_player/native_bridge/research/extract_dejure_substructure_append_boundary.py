#!/usr/bin/env python3
"""Freeze the exact-build 0x24D0270 vector append reached by de-jure setup.

Only static direct writes and immediate calls are classified; CK3 is not run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

from capstone import CS_AC_WRITE, CS_ARCH_X86, CS_MODE_64, Cs, x86_const
import pefile


ROOT = Path(__file__).resolve().parents[3]
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008


def _prior_boundary(game_dir: Path, request_path: Path) -> dict[str, object]:
    path = Path(__file__).with_name("extract_dejure_setup_change_type_write_boundary.py")
    spec = importlib.util.spec_from_file_location("dejure_setup_change_type_write_boundary", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("setup boundary extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract(game_dir, request_path)


def extract(game_dir: Path = GAME, request_path: Path = REQUEST) -> dict[str, object]:
    prior = _prior_boundary(game_dir, request_path)
    data = (game_dir / "binaries/ck3.exe").read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True

    def at(rva: int, size: int) -> bytes:
        off = image.get_offset_from_rva(rva)
        raw = data[off : off + size]
        if len(raw) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return raw

    def ins(rva: int, mnemonic: str, operands: str) -> dict[str, str]:
        items = list(md.disasm(at(rva, 16), rva, count=1))
        if len(items) != 1 or (items[0].mnemonic, items[0].op_str) != (mnemonic, operands):
            raise ValueError(f"instruction changed at RVA 0x{rva:X}")
        return {"rva": f"0x{rva:X}", "bytes": items[0].bytes.hex().upper(),
                "instruction": f"{mnemonic} {operands}"}

    def call(rva: int, target: int) -> dict[str, str]:
        raw = at(rva, 5)
        if raw[0] != 0xE8 or rva + 5 + struct.unpack_from("<i", raw, 1)[0] != target:
            raise ValueError(f"call changed at RVA 0x{rva:X}")
        return {"call_rva": f"0x{rva:X}", "target_rva": f"0x{target:X}",
                "bytes": raw.hex().upper()}

    start, end = 0x24D0270, 0x24D03AF
    raw = at(start, end - start)
    instructions = list(md.disasm(raw, start))
    if not instructions or (instructions[-1].address, instructions[-1].mnemonic,
                            instructions[-1].address + instructions[-1].size) != (0x24D03AE, "ret", end):
        raise ValueError("0x24D0270 helper extent changed")
    calls = [(i.address, i.op_str) for i in instructions if i.mnemonic == "call"]
    if calls != [(0x24D02E0, "r9"), (0x24D034E, "qword ptr [rax + 0x10]")]:
        raise ValueError(f"0x24D0270 direct call list changed: {calls}")
    writes = []
    for item in instructions:
        if not (0x24D028C <= item.address < 0x24D0388):
            continue  # RBX is the caller's substructure pointer only in this interval.
        for operand in item.operands:
            if (operand.type == x86_const.X86_OP_MEM
                    and operand.mem.base == x86_const.X86_REG_RBX
                    and operand.access & CS_AC_WRITE):
                writes.append((item.address, operand.mem.disp))
    expected_writes = [(0x24D0351, 8), (0x24D035A, 0),
                       (0x24D035D, 0xC), (0x24D037F, 0xC)]
    if writes != expected_writes:
        raise ValueError(f"substructure base write set changed: {writes}")

    return {
        "schema": "xar.ck3.war31.dejure_substructure_append_boundary.v1",
        "status": "DIRECT_VECTOR_WRITES_ONLY_TRANSITIVE_ALIAS_UNKNOWN",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "stock_script": prior["stock_script"],
        "constructed_change_type": prior["constructed_change_type"],
        "call_chain": {
            "setup_execute_whole_change_helper": prior["setup_execute"]["whole_change_helper"],
            "whole_change_helper_substructure_call": call(0x24BD8AE, 0x24D0270),
            "caller_first_selector": ins(0x24BD8A4, "lea", "rcx, [rbp + 0x58]"),
            "caller_second_selector": ins(0x24BD8AA, "lea", "rcx, [rbp + 0x70]"),
            "selected_parent_offsets": ["0x58", "0x70"],
        },
        "append_helper": {
            "entry_rva": "0x24D0270", "last_ret_rva": "0x24D03AE",
            "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "base_copy": ins(0x24D028C, "mov", "rbx, rcx"),
            "vector_count_read": ins(0x24D0288, "movsxd", "rax, dword ptr [rcx + 0xc]"),
            "vector_capacity_read": ins(0x24D028F, "mov", "ecx, dword ptr [rcx + 8]"),
            "new_buffer_store_first": ins(0x24D02F8, "mov", "dword ptr [rax + r9*4], r8d"),
            "new_buffer_store_second": ins(0x24D02FC, "mov", "dword ptr [rax + r9*4 + 4], ecx"),
            "new_buffer_store_third": ins(0x24D0301, "mov", "dword ptr [rax + r9*4 + 8], edx"),
            "existing_buffer_store_first": ins(0x24D0371, "mov", "dword ptr [r8 + r9*4], edx"),
            "existing_buffer_store_second": ins(0x24D0375, "mov", "dword ptr [r8 + r9*4 + 4], eax"),
            "existing_buffer_store_third": ins(0x24D037A, "mov", "dword ptr [r8 + r9*4 + 8], ecx"),
            "base_write_offsets": [f"0x{offset:X}" for _, offset in writes],
            "base_write_rvas": [f"0x{rva:X}" for rva, _ in writes],
            "indirect_calls": [
                ins(0x24D02E0, "call", "r9"),
                ins(0x24D034E, "call", "qword ptr [rax + 0x10]"),
            ],
            "interpretation": "The helper appends a three-dword (12-byte) record to a vector. Direct base stores touch vector descriptor offsets +0, +8, +0xC; record stores target the allocated/existing buffer pointer. Two allocator-method calls remain indirect.",
        },
        "parent_offsets_if_no_alias": {
            "first_substructure_descriptor_writes": ["0x58", "0x60", "0x64"],
            "second_substructure_descriptor_writes": ["0x70", "0x78", "0x7C"],
            "type_field": "0x268",
            "direct_descriptor_write_overlaps_type": False,
        },
        "boundary": {
            "not_proven": [
                "Exact War31 buffer pointers and whether any buffer or indirect allocator callback aliases the parent change object",
                "Transitive writes of the other setup helpers, including 0xE0DBD0 and 0x2E9FF30",
                "The actual change+0x268 value immediately before resolve and the taken resolve branch",
                "Final title/holder/liege/vassal operations or persisted surrender consequences",
            ],
            "ck3_launched": False, "native_effect_called": False,
            "gameplay_action_submitted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=GAME)
    parser.add_argument("--request", type=Path, default=REQUEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.game_dir, args.request), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
