#!/usr/bin/env python3
"""Freeze exact nonwar Faith-main-Rite doctrine and definition-key evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage
SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_doctrine12002_intrinsic_abi.json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_intrinsic.hpp"
CONSTANTS = {
    "kMainRiteDoctrineArrayOffset": 0x7A0, "kMainRiteDoctrineCountOffset": 0x7AC,
    "kDoctrineStableKeyOffset": 0x18, "kDoctrineGroupPointerOffset": 0xB08,
    "kDoctrineGroupStableKeyOffset": 0x18, "kDoctrineDatabaseGetterRva": 0x8FC740,
    "kDoctrineDatabasePointerRva": 0x5C67198,
    "kDoctrineDatabaseArrayOffset": 0x50, "kDoctrineDatabaseCountOffset": 0x5C,
}
SPANS = [
    ("Faith.HasDoctrine.wrapper", 0x2443A40, 0x2443AE5),
    ("Faith.HasDoctrine.core", 0x2439C20, 0x2439CAF),
    ("Faith.current_main_rite_container", 0x243EA30, 0x243EA85),
    ("Faith.UI.GetDoctrines", 0xC59360, 0xC593F1),
    ("Rite.initialize_effective_doctrines", 0x24FA130, 0x24FA716),
    ("DoctrineGroup.postload", 0x31E0FA0, 0x31E12BB),
    ("DoctrineDatabase.getter", 0x8FC740, 0x8FC797),
]
SLICES = [
    ("Faith.HasDoctrine.registration", 0x4D4620, 0x4D4718),
    ("Faith.UI.GetDoctrines.registration", 0x71279, 0x71314),
    ("Rite.inherited_main_rite_source.caller", 0x24F816F, 0x24F818A),
]
SITES = {
    "faith_has_doctrine_callback": 0x4D4707,
    "faith_has_doctrine_core_call": 0x2443AB4,
    "faith_main_rite_full_id": 0x2439C35,
    "faith_main_rite_generation_check": 0x2439C5B,
    "main_rite_doctrine_array": 0x2439C67,
    "main_rite_doctrine_count": 0x2439C73,
    "main_rite_doctrine_stride8": 0x2439C7F,
    "ui_doctrine_callback": 0x71303,
    "ui_main_rite_doctrine_array_address": 0xC593A8,
    "faith_main_rite_container_address": 0x243EA7D,
    "inherited_container_getter": 0x24F8176,
    "inherited_doctrine_array": 0x24F8181,
    "native_initializer_call": 0x24F8185,
    "definition_group_pointer_first": 0x24FA2AA,
    "definition_group_pointer_second": 0x24FA371,
    "definition_stable_key": 0x24FA541,
    "group_stable_key_address": 0x31E0FD2,
    "group_stable_key_length": 0x31E1003,
    "group_stable_key_capacity": 0x31E100A,
    "group_key_log_argument": 0x31E11E8,
    "group_native_definition_lookup": 0x31E1183,
    "definition_database_getter_call": 0x31E1161,
    "definition_database_array": 0x31E1166,
    "definition_database_count": 0x31E116A,
    "definition_database_pointer": 0x8FC744,
}

def extract(exe: Path):
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError("Expected the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, value in CONSTANTS.items():
        found = re.search(rf"\b{name}\s*=\s*(0x[\da-fA-F]+)", source)
        if not found or int(found.group(1), 0) != value:
            raise ValueError("Actual producer constant differs: " + name)
    def read(rva, size):
        at = pe.rva_to_offset(rva); return data[at:at + size]
    spans, text = [], []
    for name, begin, end in SPANS + SLICES:
        raw = read(begin, end - begin)
        spans.append({"name": name, "begin_rva": hex(begin), "end_exclusive_rva": hex(end),
            "kind": "complete_function" if (name, begin, end) in SPANS else "registration_or_caller_slice",
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        text.append(f"\n{name} [{begin:#x},{end:#x})")
        text.extend(f"{i.address:08X} {i.bytes.hex(' '):30} {i.mnemonic} {i.op_str}"
                    for i in decoder.disasm(raw, begin))
    sites = []
    for name, at in SITES.items():
        i = next(decoder.disasm(read(at, 15), at))
        sites.append({"name": name, "rva": hex(at), "bytes": i.bytes.hex(" "),
            "instruction": i.mnemonic + " " + i.op_str,
            "rip_targets": [hex(i.address + i.size + o.mem.disp) for o in i.operands
                            if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP],
            "direct_targets": [hex(o.imm) for o in i.operands
                               if o.type == X86_OP_IMM and i.mnemonic in ("call", "jmp")]})
    rtti = []
    for name in (".?AUSDoctrineType@@", ".?AUSDoctrineGroupType@@", ".?AVCDoctrineTypeDatabase@@"):
        needle = name.encode() + b"\0"; offset = data.find(needle)
        if offset < 0 or data.find(needle, offset + 1) >= 0:
            raise ValueError("Exact definition RTTI not unique: " + name)
        rtti.append({"name": name, "type_descriptor_rva": hex(pe.offset_to_rva(offset) - 16)})
    info = exe.resolve().parent.parent / "game/common/religion/faith_types/_faith_types.info"
    result = {"schema": "ck3_12002_faith_main_rite_doctrine_native_v1", "game_version": "1.20.0.2",
        "executable_sha256": SHA, "executable_size": len(data), "readiness": "static-confirmed",
        "local_ck3_touched": False, "live_verified": False,
        "source_constants": {k: hex(v) for k, v in CONSTANTS.items()},
        "complete_functions_and_slices": spans, "semantic_instructions": sites, "exact_rtti": rtti,
        "stock_seed_source": {"relative_path": "common/religion/faith_types/_faith_types.info",
            "sha256": hashlib.sha256(info.read_bytes()).hexdigest(), "lines": [[35,43],[60,64]]},
        "current_output_source": "faith_main_rite",
        "unresolved": ["independent current Faith intrinsic runtime collection not established",
            "per-row historic origin is not derivable from current effective collection",
            "paused live validation remains with root"]}
    return result, "\n".join(text) + "\n"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--record", action="store_true")
    a = p.parse_args(); result, disassembly = extract(a.exe)
    if a.record:
        MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif result != json.loads(MANIFEST.read_text(encoding="utf-8")):
        raise ValueError("Frozen native ABI manifest differs")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    dump = a.output_dir / "native-disassembly.txt"; dump.write_text(disassembly, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
        "live_verified": False, "complete_functions": len(SPANS), "explicit_slices": len(SLICES),
        "semantic_instructions": len(SITES), "exact_rtti": len(result["exact_rtti"]),
        "source_constants": len(CONSTANTS), "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "disassembly_sha256": hashlib.sha256(dump.read_bytes()).hexdigest()}
    (a.output_dir / "native-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
