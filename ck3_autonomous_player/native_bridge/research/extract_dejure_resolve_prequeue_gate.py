#!/usr/bin/env python3
"""Freeze the exact-build WAR31 title-change resolve prequeue gate.

Reads EXE bytes only; never loads CK3 or invokes a native effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008
IMAGE_BASE = 0x140000000


def extract(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)

    def at(rva: int, size: int) -> bytes:
        raw = data[image.get_offset_from_rva(rva) : image.get_offset_from_rva(rva) + size]
        if len(raw) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return raw

    def instruction(rva: int, mnemonic: str, operands: str) -> dict[str, str]:
        decoded = list(decoder.disasm(at(rva, 16), rva, count=1))
        if len(decoded) != 1 or (decoded[0].mnemonic, decoded[0].op_str) != (mnemonic, operands):
            raise ValueError(f"instruction changed at RVA 0x{rva:X}")
        return {"rva": f"0x{rva:X}", "bytes": decoded[0].bytes.hex().upper(),
                "instruction": f"{mnemonic} {operands}"}

    def direct_call(source: int, target: int) -> dict[str, str]:
        raw = at(source, 5)
        if raw[0] != 0xE8 or source + 5 + struct.unpack_from("<i", raw, 1)[0] != target:
            raise ValueError(f"direct call changed at RVA 0x{source:X}")
        return {"call_rva": f"0x{source:X}", "target_rva": f"0x{target:X}",
                "bytes": raw.hex().upper()}

    def vtable_slot(vtable_rva: int, slot: int, target: int) -> dict[str, str]:
        raw = at(vtable_rva + slot, 8)
        pointer = struct.unpack("<Q", raw)[0]
        if pointer != IMAGE_BASE + target:
            raise ValueError(f"vtable slot changed at RVA 0x{vtable_rva + slot:X}")
        return {"vtable_rva": f"0x{vtable_rva:X}", "slot": f"0x{slot:X}",
                "target_rva": f"0x{target:X}", "bytes": raw.hex().upper()}

    main = at(0x24CC9A0, 0x24CE184 - 0x24CC9A0)
    return {
        "schema": "xar.ck3.dejure-resolve-prequeue-gate.v1",
        "status": "STATIC_PREQUEUE_GATE_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "resolve_execute": {
            "vtable_slot": vtable_slot(0x445CAD0, 0xB0, 0x2EC43F0),
            "type_compare": instruction(0x2EC4410, "cmp", "dword ptr [rax + 0x268], 0x17"),
            "type_0x17_queue_call": direct_call(0x2EC44A7, 0x27CD6A0),
            "other_type_wrapper_call": direct_call(0x2EC4567, 0x27CD510),
        },
        "wrapper_0x27CD510": {
            "non_null": instruction(0x27CD510, "test", "rdx, rdx"),
            "virtual_check": instruction(0x27CD52F, "call", "qword ptr [rax + 8]"),
            "virtual_check_failure_branch": instruction(0x27CD534, "je", "0x27cd688"),
            "type_compare": instruction(0x27CD53A, "cmp", "dword ptr [rbx + 0x268], 0x17"),
            "type_0x17_bypass_branch": instruction(0x27CD546, "je", "0x27cd678"),
            "processed_flag_compare": instruction(0x27CD54C, "cmp", "byte ptr [rbx + 0x260], 0"),
            "processed_bypass_branch": instruction(0x27CD558, "jne", "0x27cd61c"),
            "counter_load": instruction(0x27CD55E, "mov", "eax, dword ptr [rbp + 0x60]"),
            "counter_threshold": instruction(0x27CD565, "cmp", "eax, 0x32"),
            "counter_skip_branch": instruction(0x27CD568, "jl", "0x27cd5ad"),
            "counter_increment": instruction(0x27CD60E, "inc", "dword ptr [rdi]"),
            "processor_call": direct_call(0x27CD613, 0x24CC9A0),
            "counter_decrement": instruction(0x27CD618, "dec", "dword ptr [rdi]"),
            "queue_call": direct_call(0x27CD67E, 0x27CD6A0),
            "interpretation": "After non-null and virtual checks, change type 0x17 skips this wrapper's prequeue processor. Other types call 0x24CC9A0 only when byte +0x260 is zero and context dword +0x60 is below 0x32; the wrapper then calls 0x27CD6A0. The meaning of type 0x17 and the counter is not independently identified.",
        },
        "processor_0x24CC9A0": {
            "entry_rva": "0x24CC9A0", "last_ret_rva": "0x24CE183",
            "byte_count": len(main), "sha256": hashlib.sha256(main).hexdigest().upper(),
            "empty_count_checks": [
                instruction(0x24CC9D0, "cmp", "dword ptr [rcx + 0x1c], 0"),
                instruction(0x24CC9D6, "cmp", "dword ptr [rcx + 0x4c], 0"),
                instruction(0x24CC9DC, "cmp", "dword ptr [rcx + 0x7c], 0"),
                instruction(0x24CC9E2, "cmp", "dword ptr [rcx + 0x64], 0"),
                instruction(0x24CC9E8, "cmp", "dword ptr [rcx + 0x94], 0"),
            ],
            "empty_path_processed_flag": instruction(0x24CC9F1, "mov", "byte ptr [rcx + 0x260], 1"),
            "empty_path_exit_branch": instruction(0x24CC9F8, "jmp", "0x24ce161"),
            "nonempty_path_first_helper": direct_call(0x24CCA2D, 0x24BC660),
            "nonempty_path_processed_flag": instruction(0x24CE046, "mov", "byte ptr [r14 + 0x260], 1"),
            "return": instruction(0x24CE183, "ret", ""),
            "interpretation": "When five entry counts are all zero, this function marks byte +0x260 and exits; otherwise it enters a large helper chain with a later observed +0x260 write. The chain has not been reduced to holder/liege/vassal operations.",
        },
        "boundary": {
            "proven": "Exact static branch and prequeue processing conditions for this resolve-effect path only.",
            "not_proven": [
                "War31's runtime change object type, +0x260 flag, five counts, or context +0x60 counter",
                "The object-specific title holder, liege, or vassal writes inside the processor helper chain",
                "Whether a queued change was consumed and persisted after any particular surrender",
                "Any signed resource delta or evaluated truce expiry",
            ],
            "ck3_launched": False, "effect_invoked": False, "gameplay_action_submitted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.exe), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
