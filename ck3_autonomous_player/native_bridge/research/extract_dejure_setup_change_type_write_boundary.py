#!/usr/bin/env python3
"""Pin setup_de_jure_cb direct writes and change-pointer escapes on exact CK3.

Static bytes only. This is not a transitive write-set or a runtime observation.
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
IMAGE_BASE = 0x140000000


def _constructed_type(game_dir: Path, request_path: Path) -> dict[str, object]:
    path = Path(__file__).with_name("extract_dejure_conquest_change_type.py")
    spec = importlib.util.spec_from_file_location("dejure_conquest_change_type", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("conquest type extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract(game_dir, request_path)


def extract(game_dir: Path = GAME, request_path: Path = REQUEST) -> dict[str, object]:
    prior = _constructed_type(game_dir, request_path)
    if prior["native_change_constructor"]["constructed_type"] != 0:
        raise ValueError("frozen conquest construction type changed")
    data = (game_dir / "binaries/ck3.exe").read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        raw = data[offset : offset + size]
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
            raise ValueError(f"direct call changed at RVA 0x{rva:X}")
        return {"call_rva": f"0x{rva:X}", "target_rva": f"0x{target:X}",
                "bytes": raw.hex().upper()}

    def no_direct_base_writes(start: int, end: int, base: int) -> dict[str, object]:
        raw = at(start, end - start)
        instructions = list(md.disasm(raw, start))
        if not instructions or instructions[-1].address + instructions[-1].size != end:
            raise ValueError(f"disassembly extent changed at RVA 0x{start:X}")
        offenders = []
        for item in instructions:
            for operand in item.operands:
                if (operand.type == x86_const.X86_OP_MEM and operand.mem.base == base
                        and operand.access & CS_AC_WRITE):
                    offenders.append(f"0x{item.address:X}: {item.mnemonic} {item.op_str}")
        if offenders:
            raise ValueError(f"direct base writes appeared: {offenders}")
        return {"start_rva": f"0x{start:X}", "end_exclusive_rva": f"0x{end:X}",
                "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper(),
                "direct_memory_writes_through_base": 0}

    if struct.unpack("<Q", at(0x444AFA0 + 0xB0, 8))[0] != IMAGE_BASE + 0x2E9F420:
        raise ValueError("setup-de-jure execute vtable slot changed")
    if struct.unpack("<Q", at(0x445CAD0 + 0xB0, 8))[0] != IMAGE_BASE + 0x2EC43F0:
        raise ValueError("resolve execute vtable slot changed")

    return {
        "schema": "xar.ck3.war31.dejure_setup_change_type_write_boundary.v1",
        "status": "DIRECT_NO_TYPE_WRITE_TRANSITIVE_UNKNOWN",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "stock_script": prior["stock_script"],
        "constructed_change_type": 0,
        "setup_execute": {
            "rva": "0x2E9F420", "vtable_rva": "0x444AFA0", "execute_slot": "0xB0",
            "prelookup_shared_helper": call(0x2E9F70B, 0x2E9FF30),
            "change_scope_address": ins(0x2E9F734, "lea", "rcx, [rsi + 0x1b0]"),
            "change_lookup": call(0x2E9F741, 0x2EA1D30),
            "resolved_change_pointer": ins(0x2E9F746, "mov", "rsi, rax"),
            "change_virtual_check": ins(0x2E9F74F, "call", "qword ptr [rdx + 8]"),
            "direct_writes_while_rsi_is_change": no_direct_base_writes(
                0x2E9F746, 0x2E9F86C, x86_const.X86_REG_RSI),
            "whole_change_argument": ins(0x2E9F7F4, "mov", "rcx, rsi"),
            "whole_change_helper": call(0x2E9F7F7, 0x24BD610),
            "first_substructure_address": ins(0x2E9F864, "lea", "r12, [rsi + 0x28]"),
            "second_substructure_address": ins(0x2E9F868, "lea", "r13, [rsi + 0x40]"),
            "first_substructure_call": call(0x2E9F896, 0xE0DBD0),
            "second_substructure_call": call(0x2E9F8B1, 0xE0DBD0),
            "interpretation": "The resolved change pointer is checked and passed whole to 0x24BD610. Bounded direct instructions do not store through RSI before it is repurposed, but callees and global alias paths are not covered.",
        },
        "whole_change_helper": {
            "rva": "0x24BD610",
            "change_pointer_copy": ins(0x24BD630, "mov", "rbp, rcx"),
            "change_flag_read": ins(0x24BD743, "cmp", "byte ptr [rbp + 0x265], 0"),
            "direct_writes_through_change_base": no_direct_base_writes(
                0x24BD610, 0x24BD8CA, x86_const.X86_REG_RBP),
            "substructure_selector": call(0x24BD8AE, 0x24D0270),
            "interpretation": "This helper directly reads the change and delegates with addresses of +0x58 or +0x70 substructures; its own bounded instructions do not store through RBP. Callee writes and aliasing are not excluded.",
        },
        "resolve": {
            "rva": "0x2EC43F0",
            "type_read": ins(0x2EC4410, "cmp", "dword ptr [rax + 0x268], 0x17"),
            "actual_type_for_war31": None,
            "branch_determined_from_static_setup_analysis": False,
        },
        "boundary": {
            "known": "Creation initializes change+0x268 to 0; setup entry and 0x24BD610 show no direct write to that field in bounded disassembly.",
            "remaining_bridge": [
                "Transitive writes of 0x24BD610 -> 0x24D0270 and the +0x28/+0x40 substructure helper 0xE0DBD0",
                "Shared prelookup helper 0x2E9FF30 and other called helpers may access the change by scope or global alias",
                "No exact War31 runtime value of change+0x268 immediately before resolve has been read",
            ],
            "final_title_holder_liege_vassal": None,
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
