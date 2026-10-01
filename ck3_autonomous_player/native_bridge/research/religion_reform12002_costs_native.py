#!/usr/bin/env python3
"""Verify actual Rite draft price bindings against the frozen 1.20.0.2 PE."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
MANIFEST = HERE / "religion_reform12002_costs_abi.json"
EXACT = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
CONSTANTS = {
    "kRiteCreationPietyCostRva": 0x14F57C0,
    "kRiteCreationPietyMissingRva": 0x14F58E0,
    "kRiteCreationEditOwnedRiteRva": 0x14F4400,
    "kRiteCreationActorOffset": 0xCC,
    "kRiteCreationSourceRiteOffset": 0xC8,
    "kRiteCreationPriceDraftOffset": 0xB28,
}
SPANS = [
    ("RiteCreationWindow.CalcPietyCost.registration", 0x22A460, 0x22A5CC, "registration_function"),
    ("RiteCreationWindow.CalcPietyMissing.registration", 0x22A5D0, 0x22A744, "registration_function"),
    ("RiteCreationWindow.CalcPietyCost.callback", 0x14FB120, 0x14FB157, "complete_function"),
    ("RiteCreationWindow.CalcPietyMissing.callback", 0x14FB160, 0x14FB197, "complete_function"),
    ("RiteCreationWindow.CalcPietyCost.core", 0x14F57C0, 0x14F58DD, "complete_function"),
    ("RiteCreationWindow.CalcPietyMissing.core", 0x14F58E0, 0x14F5965, "complete_function"),
    ("RiteCreationWindow.EditingOwnedCurrentRite", 0x14F4400, 0x14F449B, "complete_leaf_function"),
    ("native_total_piety_evaluator", 0x2C64BD0, 0x2C64D8F, "complete_function"),
    ("native_creation_base_price", 0x2C64200, 0x2C64730, "complete_function"),
    ("native_owned_edit_base_price", 0x2C64730, 0x2C64BC3, "complete_function"),
    ("native_final_price_factor", 0x2C62CE0, 0x2C62E49, "complete_function"),
    ("native_script_price_factor", 0x2C628C0, 0x2C62CDE, "complete_function"),
    ("native_script_value_enum_registration", 0x1D61DF0, 0x1D62477, "registration_function"),
    ("GetCostTooltip_mutates_UI_breakdown_not_called", 0x14F1710, 0x14F1948, "complete_function"),
]
SITES = [
    ("cost_registration_callback", 0x22A541),
    ("missing_registration_callback", 0x22A6B9),
    ("cost_callback_to_core", 0x14FB137),
    ("missing_callback_to_core", 0x14FB177),
    ("cost_actor_full_ref", 0x14F57ED),
    ("cost_actor_rite_full_ref", 0x14F5827),
    ("cost_price_subdraft", 0x14F5897),
    ("cost_native_edit_predicate", 0x14F589E),
    ("cost_price_subdraft_stack_argument", 0x14F58BB),
    ("cost_native_evaluator", 0x14F58C0),
    ("missing_native_cost", 0x14F58F5),
    ("missing_actor_extension", 0x14F593B),
    ("missing_actor_piety", 0x14F5947),
    ("missing_signed_subtraction", 0x14F5951),
    ("editing_window_current_rite_compare", 0x14F4481),
    ("editing_rite_head_compare", 0x14F448D),
    ("edit_branch_comparison", 0x2C64C18),
    ("edit_branch_native_price", 0x2C64C24),
    ("create_branch_native_price", 0x2C64C33),
    ("new_tenet_membership_in_current_rite", 0x2C64874),
    ("new_tenet_price", 0x2C64887),
    ("create_tenet_price", 0x2C64329),
    ("character_additive_modifier", 0x2C64D2A),
    ("native_final_factor_call", 0x2C64D66),
    ("character_multiplicative_modifier", 0x2C62D64),
    ("script_and_character_factor_sum", 0x2C62D7E),
    ("native_final_cost_zero_floor", 0x2C62E38),
    ("script_value_enum_slot_22", 0x1D62033),
    ("script_value_name_rite_creation_cost_mult", 0x1D62038),
    ("price_script_value_slot_22_times_8", 0x2C62900),
    ("tooltip_object_pointer", 0x14F172C),
    ("tooltip_object_mutation", 0x14F1736),
]

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    a = p.parse_args()
    raw = a.exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    if sha != EXACT or len(raw) != 101039736:
        raise ValueError("Not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(raw)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, length: int) -> bytes:
        off = pe.rva_to_offset(rva)
        return raw[off:off + length]
    header = NATIVE / "include/xar_bridge/religion_reform12002_costs.hpp"
    text = header.read_text(encoding="utf-8-sig")
    for key, value in CONSTANTS.items():
        m = re.search(rf"\b{key}\s*=\s*(0x[0-9A-Fa-f]+)", text)
        if not m or int(m.group(1), 16) != value:
            raise ValueError("Actual provider constant differs: " + key)
    spans = []; dump = []
    for name, start, end, kind in SPANS:
        code = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": kind, "sha256": hashlib.sha256(code).hexdigest(), "bytes": code.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:08X} {i.bytes.hex(' '):32s} {i.mnemonic} {i.op_str}"
                    for i in decoder.disasm(code, start))
    sites = []
    for name, rva in SITES:
        i = next(decoder.disasm(read(rva, 15), rva))
        sites.append({"name": name, "rva": hex(rva), "bytes": i.bytes.hex(" "),
                      "instruction": i.mnemonic + " " + i.op_str,
                      "direct_targets": [hex(o.imm) for o in i.operands if
                                         o.type == X86_OP_IMM and i.mnemonic in ("call", "jmp")],
                      "rip_targets": [hex(i.address + i.size + o.mem.disp) for o in i.operands if
                                      o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]})
    root = HERE.parents[2]
    stock = a.exe.parent.parent / "game"
    inputs = [stock / "gui/window_rite_creation.gui", stock / "common/defines/00_defines.txt",
              stock / "common/script_values/02_religion_values.txt"]
    result = {"schema": "xar.ck3_12002_rite_creation_cost_abi.v1", "game_version": "1.20.0.2",
              "executable_sha256": sha, "executable_size": len(raw),
              "readiness": "static-confirmed", "local_ck3_touched": False, "live_verified": False,
              "provider_constants": {k: hex(v) for k, v in CONSTANTS.items()},
              "native_spans": spans, "semantic_instructions": sites,
              "stock_input_sha256": {str(f.relative_to(stock)): hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs},
              "provider_header_sha256": hashlib.sha256(header.read_bytes()).hexdigest(),
              "unknown": ["full other-resource command debit semantics", "current-window discovery and paused caller hookup", "production paused comparison"]}
    if a.record: MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif result != json.loads(MANIFEST.read_text(encoding="utf-8")):
        raise ValueError("Native extraction differs from recorded reviewed ABI")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    disassembly = "\n".join(dump) + "\n"
    (a.output_dir / "native-disassembly.txt").write_text(disassembly, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
               "live_verified": False, "executable_sha256": sha, "native_spans": len(spans),
               "semantic_instructions": len(sites), "source_constants": len(CONSTANTS),
               "abi_manifest": str(MANIFEST.relative_to(root)),
               "abi_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "native_disassembly_sha256": hashlib.sha256(disassembly.encode()).hexdigest()}
    (a.output_dir / "native-result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__": raise SystemExit(main())
