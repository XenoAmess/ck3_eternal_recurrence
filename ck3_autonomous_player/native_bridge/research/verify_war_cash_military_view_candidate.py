#!/usr/bin/env python3
"""Verify the stock MilitaryView expense getter without starting CK3.

The GUI binding is only a source candidate. This verifier deliberately does
not resolve a live MilitaryView, call game code, or claim a future cost bound.
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
NAME = b"GetAllRaisedGoldMilitaryExpenses\0"
NAME_LOAD_RVA = 0x19EDE9
REGISTRATION_CALLBACK_RVA = 0x11FCAA0
REGISTRATION_WRAPPER_RVA = 0x11FCAB0
GETTER_RVA = 0x11F7D90
VALUE_BREAKDOWN_OFFSET = 0x758
CURRENT_NAME = b"GetGoldMilitaryExpenses\0"
CURRENT_NAME_LOAD_RVA = 0x19E8A9
CURRENT_CALLBACK_RVA = 0x11FC7B0
CURRENT_GETTER_RVA = 0x11F7D00
CURRENT_GETTER_HELPER_RVA = 0x11F7370
CURRENT_BREAKDOWN_CALCULATOR_RVA = 0x290A720
VIEW_SUBJECT_HANDLE_OFFSET = 0x248


def _instruction(image: pefile.PE, binary: bytes, rva: int):
    offset = image.get_offset_from_rva(rva)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    decoded = list(decoder.disasm(
        binary[offset:offset + 16], image.OPTIONAL_HEADER.ImageBase + rva,
        count=1,
    ))
    if len(decoded) != 1:
        raise ValueError(f"instruction not decoded at {rva:#x}")
    return decoded[0]


def _relative_target(row) -> int:
    for operand in row.operands:
        if operand.type == X86_OP_IMM:
            return operand.imm
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            return row.address + row.size + operand.mem.disp
    raise ValueError(f"no relative target at {row.address:#x}")


def verify(exe: Path, game_root: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    exe_sha256 = hashlib.sha256(binary).hexdigest().upper()
    if exe_sha256 != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    image = pefile.PE(data=binary, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    name_offset = binary.find(NAME)
    if name_offset < 0 or binary.find(NAME, name_offset + 1) >= 0:
        raise ValueError("expense getter name is absent or ambiguous")
    name_rva = image.get_rva_from_offset(name_offset)

    name_load = _instruction(image, binary, NAME_LOAD_RVA)
    if (name_load.mnemonic != "movups"
            or _relative_target(name_load) != base + name_rva):
        raise ValueError("expense getter registration name link changed")
    for rva, target in ((0x19EE11, REGISTRATION_WRAPPER_RVA),
                        (0x19EE18, REGISTRATION_CALLBACK_RVA)):
        row = _instruction(image, binary, rva)
        if row.mnemonic != "lea" or _relative_target(row) != base + target:
            raise ValueError(f"expense getter registration pointer changed at {rva:#x}")
    callback = _instruction(image, binary, REGISTRATION_CALLBACK_RVA)
    if (callback.mnemonic != "jmp"
            or _relative_target(callback) != base + GETTER_RVA):
        raise ValueError("expense getter callback changed")
    getter = _instruction(image, binary, GETTER_RVA)
    getter_ret = _instruction(image, binary, GETTER_RVA + getter.size)
    if (getter.mnemonic != "lea"
            or getter.op_str != f"rax, [rcx + {VALUE_BREAKDOWN_OFFSET:#x}]"
            or getter_ret.mnemonic != "ret"):
        raise ValueError("expense getter is no longer a field reference")

    current_name_offset = binary.find(CURRENT_NAME)
    if (current_name_offset < 0
            or binary.find(CURRENT_NAME, current_name_offset + 1) >= 0):
        raise ValueError("current military expense getter name is ambiguous")
    current_name_rva = image.get_rva_from_offset(current_name_offset)
    current_name_load = _instruction(image, binary, CURRENT_NAME_LOAD_RVA)
    if (current_name_load.mnemonic != "movups"
            or _relative_target(current_name_load) != base + current_name_rva):
        raise ValueError("current expense getter registration name link changed")
    current_callback = _instruction(image, binary, CURRENT_CALLBACK_RVA)
    if (current_callback.mnemonic != "jmp"
            or _relative_target(current_callback) != base + CURRENT_GETTER_RVA):
        raise ValueError("current expense getter callback changed")
    current_getter = _instruction(image, binary, CURRENT_GETTER_RVA)
    current_jump = _instruction(image, binary, 0x11F7D0A)
    subject_handle = _instruction(image, binary, 0x11F739C)
    expense_calculation = _instruction(image, binary, 0x11F73F1)
    current_helper_write = _instruction(image, binary, 0x11F7426)
    if (current_getter.mnemonic != "lea"
            or current_getter.op_str != "rdx, [rcx + 0x268]"
            or current_jump.mnemonic != "jmp"
            or _relative_target(current_jump) != base + CURRENT_GETTER_HELPER_RVA
            or subject_handle.mnemonic != "mov"
            or subject_handle.op_str != "edx, dword ptr [rcx + 0x248]"
            or expense_calculation.mnemonic != "call"
            or _relative_target(expense_calculation)
            != base + CURRENT_BREAKDOWN_CALCULATOR_RVA
            or current_helper_write.mnemonic != "mov"
            or current_helper_write.op_str != "byte ptr [rsi + 0xb38], cl"):
        raise ValueError("current expense getter/helper control flow changed")

    gui_path = game_root / "game/gui/window_military.gui"
    gui = gui_path.read_text(encoding="utf-8-sig")
    if gui.count("[MilitaryView.GetAllRaisedGoldMilitaryExpenses]") != 2:
        raise ValueError("stock military GUI expense field changed")
    if gui.count("MONTHLY_MAX_MAINTENANCE_TT") != 2:
        raise ValueError("stock military GUI maximum-maintenance context changed")
    loc_path = game_root / "game/localization/english/gui/militaryview_l_english.yml"
    localization = loc_path.read_text(encoding="utf-8-sig")
    for required in (
        "This is the predicted military expense when you have all forces raised and at full strength.",
        "Having [armies|E] on [fleets|E] can make actual maintenance higher.",
    ):
        if required not in localization:
            raise ValueError("stock maximum-maintenance semantics changed")

    return {
        "schema": "xar.ck3.war-cash-military-view-static.v1",
        "status": "exact_build_gui_getter_candidate_only",
        "exe_sha256": exe_sha256,
        "name_rva": hex(name_rva),
        "registration_name_load_rva": hex(NAME_LOAD_RVA),
        "callback_rva": hex(REGISTRATION_CALLBACK_RVA),
        "getter_rva": hex(GETTER_RVA),
        "military_view_value_breakdown_offset": hex(VALUE_BREAKDOWN_OFFSET),
        "current_expense_getter_rva": hex(CURRENT_GETTER_RVA),
        "current_expense_helper_rva": hex(CURRENT_GETTER_HELPER_RVA),
        "current_expense_calculator_rva": hex(CURRENT_BREAKDOWN_CALCULATOR_RVA),
        "military_view_subject_handle_offset": hex(VIEW_SUBJECT_HANDLE_OFFSET),
        "current_expense_helper_writes_view": True,
        "gui_sha256": hashlib.sha256(gui_path.read_bytes()).hexdigest().upper(),
        "english_localization_sha256": hashlib.sha256(loc_path.read_bytes()).hexdigest().upper(),
        "semantics": "predicted monthly cost with all forces raised at full strength",
        "known_exclusion": "fleets can make actual maintenance higher",
        "same_frame_player_amount_observed": False,
        "complete_future_war_cost_upper_bound": False,
        "safe_to_call_from_live_bridge": False,
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
