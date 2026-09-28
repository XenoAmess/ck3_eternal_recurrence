#!/usr/bin/env python3
"""Verify the stock topbar mouse-enter cache reset without launching CK3.

This only fixes exact-build static instructions and GUI bindings. It does not
observe a rendered tooltip, finished expense refresh, or wartime cash amount.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
RESET_NAME = b"ResetLastUpdateFrame\0"
RESET_NAME_RVA = 0x40E5F28


def _instruction(image: pefile.PE, binary: bytes, rva: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    offset = image.get_offset_from_rva(rva)
    rows = list(decoder.disasm(
        binary[offset:offset + 16], image.OPTIONAL_HEADER.ImageBase + rva,
        count=1,
    ))
    if len(rows) != 1:
        raise ValueError(f"topbar reset instruction absent at {rva:#x}")
    return rows[0]


def _relative_target(row) -> int:
    for operand in row.operands:
        if operand.type == X86_OP_IMM:
            return operand.imm
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            return row.address + row.size + operand.mem.disp
    raise ValueError(f"topbar reset relative target absent at {row.address:#x}")


def _expect_target(image: pefile.PE, binary: bytes, rva: int,
                   mnemonic: str, target_rva: int) -> None:
    row = _instruction(image, binary, rva)
    if (row.mnemonic != mnemonic
            or _relative_target(row)
            != image.OPTIONAL_HEADER.ImageBase + target_rva):
        raise ValueError(f"topbar reset edge changed at {rva:#x}")


def _expect(image: pefile.PE, binary: bytes, rva: int,
            mnemonic: str, operand: str) -> None:
    row = _instruction(image, binary, rva)
    if row.mnemonic != mnemonic or row.op_str != operand:
        raise ValueError(f"topbar reset instruction changed at {rva:#x}")


def verify(exe: Path, game_root: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    image = pefile.PE(data=binary, fast_load=True)
    name_offset = binary.find(RESET_NAME)
    if (name_offset < 0 or binary.find(RESET_NAME, name_offset + 1) >= 0
            or image.get_rva_from_offset(name_offset) != RESET_NAME_RVA):
        raise ValueError("topbar reset GUI name is absent or ambiguous")

    # Registration -> GUI callback -> the one-slot reset. This is a GUI write,
    # so the passive process sampler must never call any of these functions.
    _expect_target(image, binary, 0xB1063, "movups", RESET_NAME_RVA)
    _expect_target(image, binary, 0xB10DB, "lea", 0xD49B20)
    _expect_target(image, binary, 0xD49B29, "call", 0xD462B0)
    _expect(image, binary, 0xD462B0, "mov", "qword ptr [rcx + 0xf88], 0")

    # The expense getter can still write the tick before its rebuild returns.
    _expect(image, binary, 0xD476A5, "sub", "r8, qword ptr [rcx + 0xf88]")
    _expect(image, binary, 0xD476AC, "cmp", "r8, rdx")
    _expect_target(image, binary, 0xD476AF, "jb", 0xD476BD)
    _expect(image, binary, 0xD476B1, "mov", "qword ptr [rcx + 0xf88], r9")
    _expect_target(image, binary, 0xD476B8, "call", 0xD476D0)

    hud = game_root / "game/gui/hud.gui"
    gui = hud.read_text(encoding="utf-8-sig")
    reset = 'on_start = "[InGameTopbar.ResetLastUpdateFrame]"'
    expense = 'datacontext = "[InGameTopbar.GetGoldExpensesBreakdown]"'
    if gui.count(expense) != 1:
        raise ValueError("stock topbar expense tooltip binding changed")
    expense_position = gui.index(expense)
    gold_position = gui.rfind('name = "gold"', 0, expense_position)
    reset_position = gui.rfind(reset, 0, expense_position)
    if (gold_position < 0 or reset_position < 0
            or not 0 < reset_position - gold_position < 250
            or not 0 < expense_position - reset_position < 1500):
        raise ValueError("stock topbar mouse-enter/tooltip binding changed")
    return {
        "schema": "xar.ck3.war-cash-topbar-mouse-enter-refresh-static.v1",
        "status": "exact_build_gui_reset_edge_only",
        "exe_sha256": digest,
        "hud_gui_sha256": hashlib.sha256(hud.read_bytes()).hexdigest().upper(),
        "reset_name_rva": hex(RESET_NAME_RVA),
        "reset_callback_rva": hex(0xD49B20),
        "reset_method_rva": hex(0xD462B0),
        "last_update_tick_offset": hex(0xF88),
        "mouse_enter_sets_last_update_tick_zero": True,
        "getter_stores_tick_before_refresh_call": True,
        "natural_tooltip_render_observed": False,
        "cache_refresh_completed_proven": False,
        "same_native_frame_proven": False,
        "formal_cash_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.exe, args.game_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
