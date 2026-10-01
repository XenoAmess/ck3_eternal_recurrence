#!/usr/bin/env python3
"""Freeze the exact 1.20.0.2 GUI conversion-cost chain; never accesses a process."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage
EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = HERE / "religion_conversion12002_cost_abi.json"
HEADER = HERE.parent / "ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_conversion_cost.hpp"
SOURCE_RVAS = {
    "kFinalPietyCostRva": 0x29A3DE0,
    "kConversionCommandVtableRva": 0x4770340,
    "kConversionCommandSecondaryVtableRva": 0x47703D8,
    "kRiteDatabaseGlobalRva": 0x5D1E2F8,
    "kResourceExtensionOffset": 0x1B0,
    "kPietyBalanceOffset": 0x110,
}
SPANS = [
    ("FaithConversionWindow.CalcPietyCost.thunk", 0x1516CD0, 0x1516D08, "reflection wrapper int32"),
    ("FaithConversionWindow.CalcPietyCost", 0x15169B0, 0x1516A07, "int32_t(const Window*)"),
    ("FaithConversionWindow.CalcPietyMissing", 0x1516A10, 0x1516A9D, "int32_t(const Window*)"),
    ("FaithConversionWindow.GetPietyCostDesc", 0x1516AA0, 0x1516B1E, "CString*(const Window*,CString* out)"),
    ("CConvertFaithAndRiteCommand.final_piety_cost", 0x29A3DE0, 0x29A4247, "int32_t(const Command*,tooltip_or_null)"),
    ("faith_conversion_cost_mult.evaluate", 0x29A3A20, 0x29A3DD4, "int64_t*(int64_t* out,Faith*,Character*,tooltip_or_null)"),
]
SLICES = [
    ("CalcPietyCost.registration", 0x22EE69, 0x22EEFD),
    ("CalcPietyMissing.registration", 0x22EFF3, 0x22F075),
    ("GetPietyCostDesc.registration", 0x22F163, 0x22F1E5),
    ("script_value.faith_conversion_cost_mult.registration", 0x1D62022, 0x1D62033),
    ("validator.final_piety_requirement", 0x29A36DE, 0x29A379C),
]
SITES = [
    ("reflection_cost_callback", 0x22EEED), ("reflection_cost_core", 0x1516CE2),
    ("window_primary_vtable", 0x15169C4), ("window_secondary_vtable", 0x15169D0),
    ("window_played_actor_full_id", 0x15169DC), ("window_target_rite_full_id", 0x15169E6),
    ("window_pay_flag", 0x15169F0), ("window_final_cost_call", 0x15169FC),
    ("cost_charge_flag", 0x29A3E0B), ("cost_actor_full_ref", 0x29A3E24),
    ("cost_rite_database", 0x29A3E55), ("cost_target_rite_full_ref", 0x29A3E61),
    ("cost_rite_faith_full_ref", 0x29A3E92), ("cost_target_rite_compiled_value", 0x29A3ED2),
    ("cost_compiled_value_evaluation", 0x29A3EEB), ("cost_actor_additive_modifier", 0x29A3EF8),
    ("cost_actor_modifier_evaluation", 0x29A3F14), ("cost_dynamic_faith_actor_multiplier", 0x29A3F33),
    ("cost_actor_multiplicative_modifier", 0x29A3F4A),
    ("fixedpoint_one", 0x29A3F3B), ("fixedpoint_scale_division", 0x29A3F9B),
    ("native_round_negative", 0x29A40AB), ("native_round_positive", 0x29A40B4),
    ("native_minimum_define", 0x29A40CC),
    ("script_registry_root", 0x29A3A59), ("script_registry_slot_0x21", 0x29A3A60),
    ("script_actor_kind", 0x29A3AA6), ("script_actor_full_id", 0x29A3AAE),
    ("script_target_faith_kind", 0x29A3ACB), ("script_target_faith_full_id", 0x29A3AD3),
    ("script_native_evaluation", 0x29A3CD6), ("script_value_registered_ordinal", 0x1D62022),
    ("script_value_registered_name", 0x1D62027),
    ("wallet_character_resources", 0x1516A58), ("wallet_piety_fixedpoint", 0x1516A64),
    ("wallet_native_whole_point_division", 0x1516A76),
    ("validator_cost_call", 0x29A36EE), ("validator_piety_raw_requirement", 0x29A3741),
]

def extract(exe: Path, game: Path):
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, value in SOURCE_RVAS.items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if not match or int(match.group(1), 0) != value:
            raise ValueError(f"Actual provider source binding differs: {name}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    def read(rva, size):
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]
    spans, dump = [], []
    for name, start, end, *abi in SPANS + SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
            "kind": "complete_function" if abi else "registration_or_semantic_slice",
            "abi": abi[0] if abi else None, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}" for i in decoder.disasm(raw, start))
    instructions = []
    for name, rva in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        instructions.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
            "instruction": f"{ins.mnemonic} {ins.op_str}",
            "rip_targets": [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
            "direct_targets": [hex(op.imm) for op in ins.operands
                if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")]})
    type_name = b".?AVCConvertFaithAndRiteCommand@@\0"
    if read(0x5A16778, len(type_name)) != type_name:
        raise ValueError("Conversion command RTTI differs")
    vtables = []
    for rva, expected_locator, offset in [(0x4770340, 0x4E263F0, 0), (0x47703D8, 0x4E263C8, 0x18)]:
        locator = struct.unpack("<Q", read(rva - 8, 8))[0] - pe.image_base
        values = struct.unpack("<6I", read(locator, 24))
        if locator != expected_locator or values[1] != offset or values[3] != 0x5A16768:
            raise ValueError("Conversion command complete-object locator differs")
        vtables.append({"rva": hex(rva), "locator_rva": hex(locator), "this_offset": offset,
            "type_descriptor_rva": hex(values[3]), "locator_bytes": read(locator, 24).hex(" ")})
    stock = []
    for rel, ranges in [("gui/window_faith_conversion.gui", [(64, 88)]),
                        ("common/defines/00_defines.txt", [(876, 880)]),
                        ("common/script_values/02_religion_values.txt", [(3355, 3439)])]:
        path = game / rel
        raw = path.read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        excerpts = [{"first": a, "last": b, "text": "\n".join(lines[a-1:b])} for a, b in ranges]
        stock.append({"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "excerpts": excerpts})
    manifest = {"schema": "ck3_12002_religion_conversion_cost_native_v1", "game_version": "1.20.0.2",
        "executable_sha256": sha, "executable_size": len(data), "readiness": "static-confirmed",
        "local_ck3_touched": False, "live_verified": False,
        "source_constants": {k: hex(v) for k, v in SOURCE_RVAS.items()}, "native_spans": spans,
        "semantic_instructions": instructions, "vtables": vtables,
        "command_rtti": {"type_descriptor_rva": "0x5a16768", "name": type_name[:-1].decode()},
        "stock": stock,
        "cost_semantics": {"return_type": "int32 whole piety points", "intermediate_raw_scale": 100000,
            "paid_flag_offset": "0x28", "target_identity": "full RiteID; Faith resolved from Rite+0x4b8",
            "script_value_ordinal": "0x21", "script_value_key": "faith_conversion_cost_mult",
            "modifier_add_ordinal": "0x221", "modifier_mult_ordinal": "0x222",
            "native_minimum_runtime_define_rva": "0x5c696ac", "stock_minimum_piety_points": 250},
        "unresolved": ["native modifier-name mapping for numeric ordinals 0x221/0x222",
            "live positive/negative paused cost snapshots", "payment/outcome semantics owned by the outcome work package"]}
    return manifest, "\n".join(dump) + "\n"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args()
    manifest, dump = extract(args.exe, args.game)
    if args.record:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text()) != manifest:
        raise ValueError("Recorded cost ABI differs from exact frozen PE")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
        "live_verified": False, "complete_functions": len(SPANS), "slices": len(SLICES),
        "semantic_instructions": len(SITES), "source_constants": len(SOURCE_RVAS),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
