#!/usr/bin/env python3
"""Freeze the exact-build 0xE0DBD0 pair append reached by de-jure setup.

This classifies direct stores in one bounded helper, not buffer aliasing or
indirect allocator callbacks. CK3 is not run.
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

    start, end = 0xE0DBD0, 0xE0DCBF
    raw = at(start, end - start)
    instructions = list(md.disasm(raw, start))
    if not instructions or (instructions[-1].address, instructions[-1].mnemonic,
                            instructions[-1].address + instructions[-1].size) != (0xE0DCBE, "ret", end):
        raise ValueError("0xE0DBD0 helper extent changed")
    calls = [(item.address, item.op_str) for item in instructions if item.mnemonic == "call"]
    if calls != [(0xE0DC2F, "qword ptr [rax + 8]"),
                 (0xE0DC76, "qword ptr [rax + 0x10]")]:
        raise ValueError(f"0xE0DBD0 direct calls changed: {calls}")
    writes = []
    for item in instructions:
        if not (0xE0DBE9 <= item.address <= 0xE0DC9C):
            continue  # RBX holds caller's selected change substructure here.
        for operand in item.operands:
            if (operand.type == x86_const.X86_OP_MEM
                    and operand.mem.base == x86_const.X86_REG_RBX
                    and operand.access & CS_AC_WRITE):
                writes.append((item.address, operand.mem.disp))
    expected_writes = [(0xE0DC79, 8), (0xE0DC81, 0),
                       (0xE0DC84, 0xC), (0xE0DC96, 0xC)]
    if writes != expected_writes:
        raise ValueError(f"substructure base write set changed: {writes}")

    return {
        "schema": "xar.ck3.war31.dejure_pair_append_boundary.v1",
        "status": "DIRECT_VECTOR_WRITES_ONLY_TRANSITIVE_ALIAS_UNKNOWN",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "stock_script": prior["stock_script"],
        "constructed_change_type": prior["constructed_change_type"],
        "call_chain": {
            "setup_execute": prior["setup_execute"]["rva"],
            "first_descriptor": ins(0x2E9F864, "lea", "r12, [rsi + 0x28]"),
            "second_descriptor": ins(0x2E9F868, "lea", "r13, [rsi + 0x40]"),
            "first_source_pair": [
                ins(0x2E9F880, "mov", "dword ptr [rbp + 0x2340], ebx"),
                ins(0x2E9F886, "mov", "dword ptr [rbp + 0x2344], edi"),
                ins(0x2E9F88C, "lea", "rdx, [rbp + 0x2340]"),
                ins(0x2E9F893, "mov", "rcx, r12"),
                call(0x2E9F896, 0xE0DBD0),
            ],
            "second_source_pair": [
                ins(0x2E9F89B, "mov", "dword ptr [rbp + 0x2350], ebx"),
                ins(0x2E9F8A1, "mov", "dword ptr [rbp + 0x2354], edi"),
                ins(0x2E9F8A7, "lea", "rdx, [rbp + 0x2350]"),
                ins(0x2E9F8AE, "mov", "rcx, r13"),
                call(0x2E9F8B1, 0xE0DBD0),
            ],
        },
        "append_helper": {
            "entry_rva": "0xE0DBD0", "last_ret_rva": "0xE0DCBE",
            "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "base_copy": ins(0xE0DBE9, "mov", "rbx, rcx"),
            "source_pair_copy_new_buffer": ins(0xE0DC39, "mov", "rcx, qword ptr [r14]"),
            "source_pair_store_new_buffer": ins(0xE0DC3C, "mov", "qword ptr [rax + rdx*8], rcx"),
            "source_pair_copy_existing_buffer": ins(0xE0DC8F, "mov", "rax, qword ptr [r14]"),
            "source_pair_store_existing_buffer": ins(0xE0DC92, "mov", "qword ptr [rcx + rdx*8], rax"),
            "base_write_offsets": [f"0x{offset:X}" for _, offset in writes],
            "base_write_rvas": [f"0x{rva:X}" for rva, _ in writes],
            "indirect_calls": [ins(0xE0DC2F, "call", "qword ptr [rax + 8]"),
                               ins(0xE0DC76, "call", "qword ptr [rax + 0x10]")],
            "interpretation": "The helper copies one eight-byte caller-stack record into a vector. Direct base stores touch descriptor offsets +0, +8 and +0xC; record/copy stores target vector buffers. Both allocator-vtable calls remain indirect.",
        },
        "parent_offsets_if_no_alias": {
            "first_substructure_descriptor_writes": ["0x28", "0x30", "0x34"],
            "second_substructure_descriptor_writes": ["0x40", "0x48", "0x4C"],
            "type_field": "0x268",
            "direct_descriptor_write_overlaps_type": False,
        },
        "boundary": {
            "not_proven": [
                "Whether the vector buffers or indirect allocator callbacks alias the parent change object",
                "Transitive writes in the shared prelookup helper 0x2E9FF30 and other setup calls",
                "The actual War31 change+0x268 value immediately before resolve and its taken branch",
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
