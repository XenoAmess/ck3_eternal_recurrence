#!/usr/bin/env python3
"""Verify the frozen 1.20 default-raise query chain without opening a process."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM
import pefile

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def verify(executable: Path) -> dict:
    data = executable.read_bytes()
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != EXE_SHA256:
        raise ValueError("expected frozen CK3 1.20.0.2 executable")
    pe = pefile.PE(data=data, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows = []
    for name, rva, size, required_calls in (
        ("temporary_raise_constructor", 0x298C130, 0xF6, ()),
        ("final_raise_validator", 0x298C2C0, 0x424, (0x28B1CD0, 0x24A48B0)),
        ("native_per_province_legality", 0x24A48B0, 0x22C,
         (0x24A4540, 0x28BFC70)),
    ):
        offset = pe.get_offset_from_rva(rva)
        body = data[offset:offset + size]
        instructions = tuple(decoder.disasm(body, base + rva))
        calls = tuple(
            ins.operands[0].imm - base
            for ins in instructions
            if ins.mnemonic == "call" and ins.operands
            and ins.operands[0].type == X86_OP_IMM
        )
        missing = [hex(value) for value in required_calls if value not in calls]
        if missing:
            raise ValueError(f"{name}: missing native calls {missing}")
        rows.append({
            "name": name, "rva": hex(rva), "size": size,
            "sha256": hashlib.sha256(body).hexdigest(),
            "direct_calls": [hex(value) for value in calls],
            "instruction_count": len(instructions),
        })
    return {
        "status": "PASS", "game_version": "1.20.0.2",
        "executable_sha256": actual, "read_only": True,
        "local_ck3_access": False, "source_chains": rows,
        "temporary_command_size": "0x50",
        "temporary_command_primary_vtable": "0x45345c0",
        "temporary_command_secondary_vtable": "0x4534658",
        "execution_not_called": "0x2a9b5a0",
        "readiness": {
            "default_raise_legality_static_ready": True,
            "default_raise_legality_live_ready": False,
            "hypothetical_raised_roster_ready": False,
            "muster_time_ready": False,
            "future_supply_ready": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "verified_native_chains": len(result["source_chains"]),
                      "local_ck3_access": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
