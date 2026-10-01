#!/usr/bin/env python3
"""Freeze/verify the 1.20.0.2 general-religion hostility getter, from a PE file."""
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage

EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_doctrine12002_hostility_abi.json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_hostility.hpp"
SOURCE_CONSTANTS = {
    "kHostilityRiteStorageSlotRva": 0x5D1E2F8,
    "kHostilityRiteFinalRva": 0x2591CE0,
    "kHostilityFaithFinalRva": 0x243E950,
    "kHostilityRiteComponentOffset": 0x750,
    "kHostilityRiteTypeTag": 0x52697465,
}
SPANS = [
    ("Rite.final_hostility", 0x2591CE0, 0x2591F71, "uint8_t(source_component, source_Rite, target_Rite)"),
    ("Rite.component_overrides.chained", 0x2591F80, 0x259218B, "uint8_t(source_component, relation_byte, target_component)"),
    ("Faith.final_hostility", 0x243E950, 0x243EA23, "uint8_t(source_Faith,target_Faith,bool_offset)"),
    ("Faith.GetHostilityLevelTowards.reflection", 0x2443580, 0x24435BB, "reflection wrapper"),
    ("Rite.actual_divergence", 0x2BDF930, 0x2BDFB9A, "int64_t*(int64_t*out,source_Rite,target_Rite)"),
    ("CRiteHostilityLevelTrigger.value_virtual", 0x2AEAA50, 0x2AEABA8, "script scoped Rite -> target Rite"),
    ("CFaithHostilityLevelTrigger.value_virtual", 0x2B28090, 0x2B281CB, "script scoped Faith -> target Faith; offset=false"),
]
SLICES = [
    ("Faith.GetHostilityLevelTowards.registration", 0x4D3513, 0x4D35A2),
    ("Faith.reflection_abi_call_and_byte_return", 0x2446303, 0x2446348),
]
SITES = [
    ("Rite.full_generation_storage_slot", 0x243E956),
    ("Faith.source_main_Rite_ref", 0x243E975),
    ("Faith.target_main_Rite_ref", 0x243E9AD),
    ("Faith.source_Rite_type", 0x243E9EF),
    ("Faith.owning_Rite_component", 0x243E9FE),
    ("Faith.final_Rite_call", 0x243EA05),
    ("Faith.offset_enabled", 0x243EA0A),
    ("Faith.offset_evil_bound", 0x243EA0F),
    ("Faith.offset_increment", 0x243EA13),
    ("Faith.invalid_sentinel", 0x243EA1B),
    ("Rite.source_Faith_full_ref", 0x2591D16),
    ("Rite.target_Faith_full_ref", 0x2591D4F),
    ("Rite.same_Faith_relation", 0x2591E4E),
    ("Rite.same_Religion_relation", 0x2591E79),
    ("Rite.religion_family_relation", 0x2591EFF),
    ("Rite.component_override_call", 0x2591F1A),
    ("Rite.actual_divergence_call", 0x2591F2D),
    ("Rite.divergence_define", 0x2591F32),
    ("Rite.divergence_compare", 0x2591F39),
    ("Rite.divergence_strict_greater_branch", 0x2591F3E),
    ("Rite.divergence_nonzero_decrement", 0x2591F44),
    ("Rite.same_head_override_minimum", 0x2591F5B),
    ("Rite.script_value_call", 0x2AEAAF7),
    ("Faith.script_value_offset_false", 0x2B2811B),
    ("Faith.script_value_call", 0x2B28124),
    ("Faith.registration_callback", 0x4D3592),
    ("Faith.wrapper_core_pointer", 0x244358C),
    ("Faith.reflection_bool_input", 0x2446307),
    ("Faith.reflection_byte_output", 0x2446325),
]
RTTI = [
    ("CRiteHostilityLevelTrigger", 0x5A356E0, 0x4E4B530, 0x4784678, 0x2AEAA50),
    ("CFaithHostilityLevelTrigger", 0x5A49D38, 0x4E72D70, 0x47BE370, 0x2B28090),
]
STOCK = [
    ("common/religion/doctrine_types/_doctrine_types.info", 170, 194,
     ["same_religion = astray", "same_family = hostile", "unrelated = evil", "same_hof_hostility_override = righteous"]),
    ("common/religion/doctrine_types/_doctrine_types.info", 260, 275,
     ["righteous (0)", "astray\t(1)", "hostile\t(2)", "evil\t\t(3)"]),
    ("common/defines/00_defines.txt", 834, 834, ["RITE_DIVERGENCE_HOSTILITY_THRESHOLD = 1"]),
    ("common/defines/00_defines.txt", 870, 875,
     ["FAITH_HOSTILITY_RIGHTEOUS", "FAITH_HOSTILITY_ASTRAY", "FAITH_HOSTILITY_HOSTILE", "FAITH_HOSTILITY_EVIL"]),
    ("common/scripted_modifiers/00_marriage_scripted_modifiers.txt", 1127, 1265,
     ["scope:recipient.rite = {", "target = scope:puppet_or_actor.rite", "subtract = 975", "#Divergence"]),
]

def extract(exe: Path, game: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 PE")
    pe = PeImage(data)
    header = HEADER.read_text(encoding="utf-8-sig")
    for name, expected in SOURCE_CONSTANTS.items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)", header)
        if not match or int(match.group(1), 0) != expected:
            raise ValueError(f"Actual provider binding differs: {name}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva); return data[offset:offset + size]
    spans, dump = [], []
    for name, start, end, *abi in SPANS + SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
            "kind": "complete_function_including_chained_spans" if abi else "labelled_slice",
            "abi": abi[0] if abi else None, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{ins.address:09X} {ins.bytes.hex(' '):32s} {ins.mnemonic:8s} {ins.op_str}"
                    for ins in decoder.disasm(raw, start))
    instructions = []
    for name, address in SITES:
        ins = next(decoder.disasm(read(address, 15), address))
        instructions.append({"name": name, "rva": hex(address), "bytes": ins.bytes.hex(" "),
            "instruction": f"{ins.mnemonic} {ins.op_str}",
            "rip_targets": [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
            "direct_targets": [hex(op.imm) for op in ins.operands if op.type == X86_OP_IMM
                               and ins.mnemonic in ("call", "jmp")]})
    rtti = []
    for name, type_rva, col_rva, vtable_rva, value_rva in RTTI:
        if read(type_rva + 16, len(name) + 7) != (".?AV" + name + "@@").encode() + b"\0":
            raise ValueError("RTTI class differs: " + name)
        fields = struct.unpack("<6I", read(col_rva, 24))
        if fields[0] != 1 or fields[3] != type_rva or fields[5] != col_rva:
            raise ValueError("COL differs: " + name)
        if struct.unpack("<Q", read(vtable_rva - 8, 8))[0] != pe.image_base + col_rva:
            raise ValueError("Vtable COL pointer differs: " + name)
        if struct.unpack("<Q", read(vtable_rva + 0x100, 8))[0] != pe.image_base + value_rva:
            raise ValueError("Actual script value virtual differs: " + name)
        rtti.append({"class": name, "type_descriptor_rva": hex(type_rva),
            "col_rva": hex(col_rva), "vtable_rva": hex(vtable_rva),
            "value_virtual_offset": "0x100", "value_virtual_rva": hex(value_rva)})
    stock = []
    for relative, start, end, expected in STOCK:
        path = game / relative; raw = path.read_bytes()
        lines = raw.decode("utf-8-sig").splitlines(); window = "\n".join(lines[start - 1:end])
        if not all(value in window for value in expected):
            raise ValueError("Frozen stock evidence differs: " + relative)
        stock.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
            "start_line": start, "end_line": end, "window": window})
    return {"schema": "ck3_12002_nonwar_hostility_abi_v1", "game_version": "1.20.0.2",
        "executable_sha256": sha, "executable_size": len(data), "readiness": "static-confirmed",
        "local_ck3_touched": False, "live_verified": False, "war_research": False,
        "source_constants": {k: hex(v) for k, v in SOURCE_CONSTANTS.items()},
        "enum_levels": {"righteous": 0, "astray": 1, "hostile": 2, "evil": 3},
        "native_invalid_sentinel": 4, "faith_offset_used": False,
        "native_spans": spans, "semantic_instructions": instructions, "script_trigger_rtti": rtti,
        "stock_evidence": stock, "unresolved": ["paused live values", "central mailbox/MCP query",
            "detailed reason enumeration for a final native level; final getter already resolves effective overrides"]}, "\n".join(dump) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(); result, dump = extract(args.exe, args.game)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result:
        raise ValueError("Recorded exact ABI differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
        "live_verified": False, "war_research": False, "exact_executable_sha256": EXACT_SHA,
        "complete_functions": len(SPANS), "labelled_slices": len(SLICES),
        "semantic_instructions": len(SITES), "script_trigger_rtti": len(RTTI),
        "stock_windows": len(STOCK), "source_constants": len(SOURCE_CONSTANTS),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
