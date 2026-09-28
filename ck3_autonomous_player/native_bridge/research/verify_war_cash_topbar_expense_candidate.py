#!/usr/bin/env python3
"""Verify exact-build InGameTopbar gold-expense cache anchors without CK3.

The getter conditionally refreshes and writes GUI state.  This is a static
read-only verifier, not a live getter or a same-frame war-cash producer.
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
EXPENSE_NAME = b"GetGoldExpensesBreakdown\0"
INCOME_NAME = b"GetGoldIncomeBreakdown\0"
EXPENSE_NAME_RVA = 0x40E5F08
INCOME_NAME_RVA = 0x40E5FD0
PLAYED_CHARACTER_ID_GLOBAL_RVA = 0x4FE7EE0


def _instruction(image: pefile.PE, binary: bytes, rva: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    offset = image.get_offset_from_rva(rva)
    rows = list(decoder.disasm(
        binary[offset:offset + 16], image.OPTIONAL_HEADER.ImageBase + rva,
        count=1,
    ))
    if len(rows) != 1:
        raise ValueError(f"topbar instruction absent at {rva:#x}")
    return rows[0]


def _relative_target(row) -> int:
    for operand in row.operands:
        if operand.type == X86_OP_IMM:
            return operand.imm
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            return row.address + row.size + operand.mem.disp
    raise ValueError(f"topbar relative target absent at {row.address:#x}")


def _expect(image: pefile.PE, binary: bytes, rva: int,
            mnemonic: str, operand: str) -> None:
    row = _instruction(image, binary, rva)
    if row.mnemonic != mnemonic or row.op_str != operand:
        raise ValueError(f"topbar ABI changed at {rva:#x}: {row.mnemonic} {row.op_str}")


def _expect_target(image: pefile.PE, binary: bytes, rva: int,
                   mnemonic: str, target_rva: int) -> None:
    row = _instruction(image, binary, rva)
    if (row.mnemonic != mnemonic
            or _relative_target(row)
            != image.OPTIONAL_HEADER.ImageBase + target_rva):
        raise ValueError(f"topbar relative link changed at {rva:#x}")


def verify(exe: Path, game_root: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("CK3 executable SHA-256 mismatch")
    image = pefile.PE(data=binary, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    for name, expected_rva in (
        (EXPENSE_NAME, EXPENSE_NAME_RVA),
        (INCOME_NAME, INCOME_NAME_RVA),
    ):
        offset = binary.find(name)
        if (offset < 0 or binary.find(name, offset + 1) >= 0
                or image.get_rva_from_offset(offset) != expected_rva):
            raise ValueError(f"topbar GUI name changed: {name!r}")

    # Registration leads to the GUI callback and then the topbar getter.
    _expect_target(image, binary, 0xB0819, "movups", EXPENSE_NAME_RVA)
    _expect_target(image, binary, 0xB0843, "lea", 0xD49920)
    _expect_target(image, binary, 0xB084A, "lea", 0xD49910)
    _expect_target(image, binary, 0xD49910, "jmp", 0xD47680)

    # Getter returns the ValueBreakdown back-pointer slot, but it can refresh
    # that cache and write the last-update frame.  Never call it as pure-read.
    _expect(image, binary, 0xD4768D, "lea", "rbx, [rcx + 0xb68]")
    _expect(image, binary, 0xD4769B, "mov", "r9, qword ptr [rax + 0x180]")
    _expect(image, binary, 0xD476A5, "sub", "r8, qword ptr [rcx + 0xf88]")
    _expect(image, binary, 0xD476AC, "cmp", "r8, rdx")
    _expect(image, binary, 0xD476B1, "mov", "qword ptr [rcx + 0xf88], r9")
    _expect_target(image, binary, 0xD476B8, "call", 0xD476D0)
    _expect(image, binary, 0xD476BD, "mov", "rax, rbx")

    # Refresh resolves the current played CharacterID, checks the resolved
    # character generation/ID, then builds the player expense breakdown.
    _expect_target(image, binary, 0xD47728, "mov", PLAYED_CHARACTER_ID_GLOBAL_RVA)
    _expect(image, binary, 0xD4774F, "cmp", "dword ptr [rdi + 0x18], eax")
    _expect(image, binary, 0xD47867, "lea", "rsi, [rbx + 0xad8]")
    _expect_target(image, binary, 0xD478BC, "call", 0x28DC5A0)
    _expect(image, binary, 0xD478C1, "mov", "rax, qword ptr [rbp + 0x130]")
    _expect(image, binary, 0xD478C8, "neg", "rax")
    _expect(image, binary, 0xD478CB, "mov", "qword ptr [rbx + 0xb50], rax")
    _expect(image, binary, 0xD47993, "lea", "rcx, [rbx + 0xb68]")
    _expect(image, binary, 0xD4799A, "mov", "qword ptr [rcx], rsi")
    if 0xAD8 + 0x78 != 0xB50 or 0xAD8 + 0x90 != 0xB68:
        raise ValueError("topbar ValueBreakdown layout arithmetic changed")

    # The expense accumulator includes the exact function previously found
    # as MilitaryView's current military-cost calculator, then other costs.
    _expect(image, binary, 0x28DC62B, "mov", "rdx, r13")
    _expect_target(image, binary, 0x28DC635, "call", 0x290A720)
    _expect(image, binary, 0x28DC63A, "mov", "rsi, qword ptr [rax]")
    _expect(image, binary, 0x28DC78C, "add", "rsi, r14")
    _expect(image, binary, 0x28DC8A4, "mov", "qword ptr [rdi], rsi")

    hud = game_root / "game/gui/hud.gui"
    breakdown = game_root / "game/gui/shared/value_breakdown.gui"
    military_loc = (
        game_root / "game/localization/english/gui/militaryview_l_english.yml"
    )
    hud_text = hud.read_text(encoding="utf-8-sig")
    breakdown_text = breakdown.read_text(encoding="utf-8-sig")
    military_text = military_loc.read_text(encoding="utf-8-sig")
    if (hud_text.count("[InGameTopbar.GetGoldIncomeBreakdown]") != 1
            or hud_text.count("[InGameTopbar.GetGoldExpensesBreakdown]") != 1
            or "[InGameTopbar.ResetLastUpdateFrame]" not in hud_text
            or breakdown_text.count("[ValueBreakdown.GetSubValues]") < 1
            or "Having [armies|E] on [fleets|E] can make actual maintenance higher."
            not in military_text):
        raise ValueError("stock topbar expense GUI semantics changed")

    return {
        "schema": "xar.ck3.war-cash-topbar-expense-static.v1",
        "status": "exact_build_topbar_expense_cache_candidate_only",
        "exe_sha256": digest,
        "image_base": hex(base),
        "expense_name_rva": hex(EXPENSE_NAME_RVA),
        "income_name_rva": hex(INCOME_NAME_RVA),
        "expense_registration_rva": hex(0xB0819),
        "expense_callback_rva": hex(0xD49910),
        "expense_getter_rva": hex(0xD47680),
        "expense_refresh_rva": hex(0xD476D0),
        "played_character_id_global_rva": hex(PLAYED_CHARACTER_ID_GLOBAL_RVA),
        "current_military_expense_calculator_rva": hex(0x290A720),
        "expense_breakdown_object_offset": hex(0xAD8),
        "expense_total_signed_raw_candidate_offset": hex(0xB50),
        "expense_total_scale_candidate_offset": hex(0xB58),
        "expense_breakdown_back_pointer_offset": hex(0xB68),
        "last_update_frame_offset": hex(0xF88),
        "hud_gui_sha256": hashlib.sha256(hud.read_bytes()).hexdigest().upper(),
        "value_breakdown_gui_sha256": hashlib.sha256(
            breakdown.read_bytes()).hexdigest().upper(),
        "getter_can_refresh_and_write_gui_cache": True,
        "safe_to_call_from_live_bridge": False,
        "unique_live_topbar_instance_proven": False,
        "same_frame_cache_freshness_proven": False,
        "same_frame_player_expense_amount_observed": False,
        "military_component_live_raw_observed": False,
        "expense_payment_cadence_proven": False,
        "future_war_cost_upper_bound_proven": False,
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
