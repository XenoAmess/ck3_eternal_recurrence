#!/usr/bin/env python3
"""Pin direct effect-base access in setup's shared 0x2E9FF30 helper.

This establishes register provenance only. Calls, global aliases and runtime
change referents are outside the direct-effect-base conclusion. CK3 is not run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs, x86_const
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

    start, end = 0x2E9FF30, 0x2EA0B1A
    raw = at(start, end - start)
    instructions = list(md.disasm(raw, start))
    if not instructions or (instructions[-1].address, instructions[-1].mnemonic,
                            instructions[-1].address + instructions[-1].size) != (0x2EA0B19, "ret", end):
        raise ValueError("shared helper extent changed")

    # The incoming RCX is the effect pointer. RBX retains that value from
    # 0x2E9FF67 until a branch-specific first overwrite at 0x2EA00E4 or
    # 0x2EA01FA; the +0x258==0 branch goes straight to cleanup.
    rb_uses = []
    for item in instructions:
        if not (0x2E9FF67 <= item.address < 0x2EA01FA):
            continue
        if any(
            (operand.type == x86_const.X86_OP_REG
             and operand.reg in (x86_const.X86_REG_RBX, x86_const.X86_REG_EBX))
            or (operand.type == x86_const.X86_OP_MEM
                and operand.mem.base in (x86_const.X86_REG_RBX, x86_const.X86_REG_EBX))
            for operand in item.operands
        ):
            rb_uses.append((item.address, item.mnemonic, item.op_str))
    expected = [
        (0x2E9FF67, "mov", "rbx, rcx"),
        (0x2E9FFF0, "lea", "rcx, [rbx + 0x260]"),
        (0x2EA0030, "cmp", "byte ptr [rbx + 0x258], 0"),
        (0x2EA00E4, "mov", "ebx, esi"),
        (0x2EA00E8, "cmovl", "ebx, eax"),
        (0x2EA00F5, "mov", "edx, ebx"),
        (0x2EA015A, "mov", "dword ptr [rbp + 0xa8], ebx"),
    ]
    if rb_uses != expected:
        raise ValueError(f"early RBX provenance changed: {rb_uses}")

    # A later [rbx+0x1B8] looks tempting, but RBX is replaced with a
    # table-resolved entity (or fallback) before that instruction.
    later_rebinds = [
        ins(0x2EA028B, "lea", "rbx, [rip + 0x214a1d6]"),
        ins(0x2EA0394, "mov", "rbx, qword ptr [rcx + rdx*8 + 8]"),
        ins(0x2EA03A3, "mov", "rbx, qword ptr [rip + 0x286bd8e]"),
        ins(0x2EA03AA, "mov", "rcx, qword ptr [rbx + 0x1b8]"),
    ]

    return {
        "schema": "xar.ck3.war31.dejure_shared_prelookup_effect_base.v1",
        "status": "DIRECT_EFFECT_BASE_ACCESSES_BOUNDED_TRANSITIVE_UNKNOWN",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "stock_script": prior["stock_script"],
        "constructed_change_type": prior["constructed_change_type"],
        "call_site": {
            "effect_argument": ins(0x2E9F708, "mov", "rcx, rsi"),
            "call": prior["setup_execute"]["prelookup_shared_helper"],
        },
        "helper": {
            "entry_rva": "0x2E9FF30", "end_exclusive_rva": "0x2EA0B1A",
            "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "effect_pointer_copy": ins(0x2E9FF67, "mov", "rbx, rcx"),
            "effect_base_direct_accesses": [
                ins(0x2E9FFF0, "lea", "rcx, [rbx + 0x260]"),
                ins(0x2EA0030, "cmp", "byte ptr [rbx + 0x258], 0"),
            ],
            "early_rbx_uses": [f"0x{rva:X}: {mnemonic} {operands}"
                               for rva, mnemonic, operands in rb_uses],
            "early_first_overwrites": [
                ins(0x2EA00E4, "mov", "ebx, esi"),
                ins(0x2EA01FA, "mov", "ebx, dword ptr [rbp + 0x28]"),
            ],
            "zero_flag_cleanup_branch": ins(0x2EA0037, "je", "0x2ea0ada"),
            "capacity_branch": ins(0x2EA00C8, "jne", "0x2ea0162"),
            "later_rbx_rebinds_before_plus_1b8": later_rebinds,
            "direct_effect_base_change_scope_access": False,
            "direct_effect_base_change_type_write": False,
            "interpretation": "Before the incoming effect pointer in RBX is overwritten or cleanup starts, this helper directly addresses only effect+0x260 (title scope) and reads effect+0x258. The later [rbx+0x1B8] reads a table-resolved/fallback entity after RBX was repurposed; it is not direct effect+0x1B8 evidence.",
        },
        "boundary": {
            "not_proven": [
                "Transitive or global-alias accesses by calls from this helper, including title-scope virtual dispatch and downstream table helpers",
                "Any pointed-buffer or allocator alias to the parent change object in setup",
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
