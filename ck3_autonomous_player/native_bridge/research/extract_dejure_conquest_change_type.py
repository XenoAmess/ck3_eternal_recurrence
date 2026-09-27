#!/usr/bin/env python3
"""Pin stock de-jure conquest's native change-type construction boundary.

This reads the exact installed EXE and stock script; it never invokes CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008
IMAGE_BASE = 0x140000000
ROOT = Path(__file__).resolve().parents[3]
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def _script_sequence(game_dir: Path, request_path: Path) -> dict[str, object]:
    path = Path(__file__).with_name("extract_dejure_war31_title_effect_sequence.py")
    spec = importlib.util.spec_from_file_location("dejure_war31_title_effect_sequence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("stock script sequence extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract(game_dir, request_path)


def extract(game_dir: Path = GAME, request_path: Path = REQUEST) -> dict[str, object]:
    script = _script_sequence(game_dir, request_path)
    if script["scripted_sequence"][0]["type"] != "conquest":
        raise ValueError("stock de-jure victory type differs from conquest")
    data = (game_dir / "binaries/ck3.exe").read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("unexpected PE image base")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        raw = data[offset : offset + size]
        if len(raw) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return raw

    def ins(rva: int, mnemonic: str, operands: str) -> dict[str, str]:
        items = list(decoder.disasm(at(rva, 16), rva, count=1))
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

    def token_record(record_rva: int, expected_id: int, string_rva: int, value: str) -> dict[str, str]:
        raw = at(record_rva, 16)
        token_id, padding, pointer = struct.unpack("<IIQ", raw)
        if (token_id, padding, pointer) != (expected_id, 0, IMAGE_BASE + string_rva):
            raise ValueError(f"interned token record changed at RVA 0x{record_rva:X}")
        if at(string_rva, len(value) + 1) != value.encode() + b"\0":
            raise ValueError(f"interned token string changed at RVA 0x{string_rva:X}")
        return {"name": value, "id": f"0x{token_id:X}",
                "record_rva": f"0x{record_rva:X}", "string_rva": f"0x{string_rva:X}",
                "record_bytes": raw.hex().upper()}

    name = ".?AVCCreateTitleAndVassalChangeEffect@@"
    if at(0x55D6F28 + 16, len(name) + 1) != name.encode() + b"\0":
        raise ValueError("create-change RTTI name changed")
    col = struct.unpack("<6I", at(0x4ABE710, 24))
    if (col[0], col[1], col[2], col[3], col[5]) != (1, 0, 0, 0x55D6F28, 0x4ABE710):
        raise ValueError("create-change RTTI locator changed")
    if struct.unpack("<Q", at(0x445C5C0 - 8, 8))[0] != IMAGE_BASE + 0x4ABE710:
        raise ValueError("create-change vtable locator changed")
    slots = {"parse": (0x10, 0x2EC37A0), "execute": (0xB0, 0x2EC3CF0)}
    for slot, target in slots.values():
        if struct.unpack("<Q", at(0x445C5C0 + slot, 8))[0] != IMAGE_BASE + target:
            raise ValueError(f"create-change vtable slot 0x{slot:X} changed")

    table = struct.unpack("<23I", at(0x431F2A0, 23 * 4))
    if table[:4] != (0x2CD7, 0x324C, 0x324D, 0x324E) or table.count(0x2CD7) != 1:
        raise ValueError("native change-type lookup table changed")
    if 0x431F2A0 + len(table) * 4 != 0x431F2FC:
        raise ValueError("native change-type table extent changed")
    argument_span = at(0x2EC3D90, 0x2EC3DDB - 0x2EC3D90)
    argument_instructions = list(decoder.disasm(argument_span, 0x2EC3D90))
    if not argument_instructions or argument_instructions[-1].address + argument_instructions[-1].size != 0x2EC3DDB:
        raise ValueError("native constructor argument span changed")
    for item in argument_instructions:
        if item.mnemonic in ("call", "jmp"):
            raise ValueError("unexpected call or jump before native change constructor")
        _, writes = item.regs_access()
        if any(decoder.reg_name(reg) in ("rdx", "edx", "dx", "dl", "dh") for reg in writes):
            raise ValueError("native constructor type argument is overwritten")

    return {
        "schema": "xar.ck3.war31.dejure_conquest_change_type.v1",
        "status": "STATIC_CONSTRUCTED_TYPE_ZERO_RESOLVE_VALUE_UNOBSERVED",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "stock_script": {"request_id": script["request_id"], "request_sha256": script["request_sha256"],
                         "script_path": script["script_path"], "script_sha256": script["script_sha256"],
                         "create_type": "conquest", "setup_between_create_and_resolve": True},
        "interned_tokens": {
            "type_key": token_record(0x42B91A0, 0xE1, 0x40A743C, "type"),
            "conquest": token_record(0x42C0530, 0x2CD7, 0x4095878, "conquest"),
            "conquest_holy_war": token_record(0x42C4CA0, 0x324C, 0x4095860, "conquest_holy_war"),
            "conquest_claim": token_record(0x42C4CB0, 0x324D, 0x4095850, "conquest_claim"),
            "conquest_populist": token_record(0x42C4CC0, 0x324E, 0x4095838, "conquest_populist"),
        },
        "create_effect": {
            "rtti_type_rva": "0x55D6F28", "rtti_col_rva": "0x4ABE710",
            "vtable_rva": "0x445C5C0", "parse_rva": "0x2EC37A0", "execute_rva": "0x2EC3CF0",
            "parse_type_key_compare": ins(0x2EC37BB, "cmp", "r8d, 0xe1"),
            "parse_type_branch": ins(0x2EC37C2, "je", "0x2ec3a0a"),
            "special_token_compare": ins(0x2EC3A10, "cmp", "eax, 0x2cd5"),
            "table_base": ins(0x2EC3AAD, "lea", "rdi, [rip + 0x145b7ec]"),
            "table_end": ins(0x2EC3AA0, "lea", "rbx, [rip + 0x145b855]"),
            "table_rva": "0x431F2A0", "table_end_rva": "0x431F2FC",
            "table_sha256": hashlib.sha256(at(0x431F2A0, 23 * 4)).hexdigest().upper(),
            "conquest_token_index": table.index(0x2CD7),
            "table_lookup": call(0x2EC3AC1, 0x8155C0),
            "lookup_equal_compare": ins(0x815674, "cmp", "dword ptr [rbx], esi"),
            "index_byte_difference": ins(0x2EC3ACB, "sub", "rax, rdi"),
            "index_divide_by_four": ins(0x2EC3ACE, "sar", "rax, 2"),
            "compiled_type_store": ins(0x2EC3AD2, "mov", "dword ptr [r13 + 0x64], eax"),
            "execute_type_load": ins(0x2EC3D03, "mov", "edx, dword ptr [rcx + 0x64]"),
            "execute_invalid_compare": ins(0x2EC3D06, "cmp", "edx, 0x17"),
            "execute_valid_branch": ins(0x2EC3D09, "jne", "0x2ec3d90"),
            "argument_unchanged_span_sha256": hashlib.sha256(argument_span).hexdigest().upper(),
            "native_constructor_call": call(0x2EC3DDB, 0x27CD320),
        },
        "native_change_constructor": {
            "entry_rva": "0x27CD320",
            "type_argument_copy": ins(0x27CD339, "mov", "ebp, edx"),
            "default_type_store": ins(0x27CD414, "mov", "dword ptr [rbx + 0x268], 0x17"),
            "argument_type_store": ins(0x27CD45B, "mov", "dword ptr [rbx + 0x268], ebp"),
            "constructed_type": 0,
        },
        "resolve_boundary": {
            "type_compare": ins(0x2EC4410, "cmp", "dword ptr [rax + 0x268], 0x17"),
            "non_0x17_branch": ins(0x2EC4417, "jne", "0x2ec44bd"),
            "non_0x17_wrapper_call": call(0x2EC4567, 0x27CD510),
            "conclusion": "Stock type=conquest compiles to index 0 and create-effect execution initializes change+0x268 to 0, not 0x17. The intervening setup_de_jure_cb may mutate the change; the actual value at resolve is not proven without tracing or observing that step.",
        },
        "boundary": {"runtime_change_type_at_resolve": None,
                     "final_title_holder_liege_vassal": None,
                     "ck3_launched": False, "native_effect_called": False,
                     "gameplay_action_submitted": False},
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
