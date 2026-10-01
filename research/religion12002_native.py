#!/usr/bin/env python3
"""Extract/verify CK3 1.20.0.2 nonwar religion context from a frozen PE file.

This is a research verifier, not a bridge provider. It does not access a process.
"""
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
MANIFEST = HERE / "religion12002_native_abi.json"
HEADER = HERE.parent / "ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_context.hpp"
SOURCE_RVAS = {
    "kCharacterRiteRva": 0x28D2F90, "kCharacterFaithRva": 0x289E750,
    "kRiteFaithRva": 0x24FC560, "kFaithReligionRva": 0x2443D40,
    "kFaithMainRiteRva": 0x2444360, "kFaithFervorRva": 0x243EA90,
    "kCharacterSpiritualFulfillmentRva": 0x28BCE40,
    "kFaithTagRva": 0xB801A0, "kReligionTagRva": 0x247CA20,
    "kCharacterRiteIdOffset": 0xB4, "kRiteFaithIdOffset": 0x4B8,
    "kFaithReligionIdOffset": 0x8C, "kFaithMainRiteIdOffset": 0x98,
    "kReferenceIdentityOffset": 0x08,
}

# Every end is after the final instruction in the complete function body,
# except named registration slices, which are deliberately labelled as slices.
SPANS = [
    ("Character.GetFaith.core", 0x289E750, 0x289E7CD, "Faith*(Character*)"),
    ("Character.GetFaith.thunk", 0x28D2F40, 0x28D2F45, "Faith*(Character*)"),
    ("Character.GetRite.core", 0x28D2F90, 0x28D2FCD, "Rite*(Character*)"),
    ("Rite.GetFaith.core", 0x24FC560, 0x24FC59D, "Faith*(Rite*)"),
    ("Faith.GetReligion.core", 0x2443D40, 0x2443D7D, "Religion*(Faith*)"),
    ("Faith.GetMainRite.core", 0x2444360, 0x244439D, "Rite*(Faith*)"),
    ("Faith.GetFervor.core", 0x243EA90, 0x243EA9E, "int64_t*(Faith*,int64_t* out)"),
    ("Faith.GetFervor.thunk", 0x2444490, 0x24444C7, "reflection wrapper"),
    ("Character.GetSpiritualFulfillment.core", 0x28BCE40, 0x28BCE7C, "int64_t*(Character*,int64_t* out)"),
    ("Character.GetSpiritualFulfillment.thunk", 0x28CFC20, 0x28CFC57, "reflection wrapper"),
    ("Character.spiritual_fulfillment.default", 0x2BFB4C0, 0x2BFB6E7, "int64_t*(int64_t* out,Character*)"),
    ("Faith.GetTag.core", 0xB801A0, 0xB801A8, "CString*(Faith*)"),
    ("Faith.GetTag.thunk", 0x2443240, 0x2443283, "reflection wrapper; complete chained spans"),
    ("Religion.GetTag.core", 0x247CA20, 0x247CA29, "CString*(Religion*)"),
    ("Religion.GetTag.thunk", 0x24819E0, 0x2481A23, "reflection wrapper; complete chained spans"),
    ("Religion.GetID.thunk", 0x2481A30, 0x2481A63, "reflection integer from +0x10; not full ref"),
    ("Rite.GetTenets.collection_address", 0x1CF98A0, 0x1CF98A8, "opaque collection*(Rite*); row layout unresolved"),
    ("Rite.GetTenets.thunk", 0x24FC1B0, 0x24FC207, "reflection collection wrapper"),
    ("Rite.GetName.core", 0x24F6E40, 0x24F6F01, "CString*(Rite*,CString* out); rendered name, not stable key"),
]
REGISTRATION_SLICES = [
    ("Character.GetFaith.registration", 0x568AA2, 0x568B31),
    ("Character.GetRite.registration", 0x568C87, 0x568D29),
    ("Rite.GetFaith.registration", 0x4EF972, 0x4EFA01),
    ("Faith.GetReligion.registration", 0x4D49D2, 0x4D4A65),
    ("Faith.GetMainRite.registration", 0x4D51A2, 0x4D5235),
    ("Faith.GetFervor.registration", 0x4D55D9, 0x4D5664),
    ("Character.GetSpiritualFulfillment.registration", 0x55D2B3, 0x55D357),
    ("Faith.GetTag.registration", 0x4D201D, 0x4D20A8),
    ("Religion.GetTag.registration", 0x4DE53D, 0x4DE5C8),
    ("Rite.GetTenets.registration", 0x4EEDC9, 0x4EEE54),
]
SITES = [
    ("character_rite_full_ref", 0x28D2F9C),
    ("character_faith_rite_full_ref", 0x289E75C),
    ("rite_faith_full_ref", 0x289E798),
    ("rite_faith_direct_full_ref", 0x24FC56C),
    ("faith_religion_full_ref", 0x2443D4C),
    ("faith_main_rite_full_ref", 0x244436C),
    ("faith_fervor_signed_fixed_point", 0x243EA90),
    ("faith_fervor_core_call", 0x24444A7),
    ("character_spiritual_extension", 0x28BCE46),
    ("character_spiritual_cached_fixed_point", 0x28BCE55),
    ("character_spiritual_native_default_call", 0x28BCE6E),
    ("character_spiritual_core_call", 0x28CFC37),
    ("faith_tag_address", 0xB801A0),
    ("religion_tag_definition_pointer", 0x247CA20),
    ("religion_tag_definition_string_address", 0x247CA24),
    ("religion_reflection_integer_identity", 0x2481A41),
    ("rite_tenets_collection_address", 0x1CF98A0),
    ("rite_tenets_collection_core_call", 0x24FC1BE),
    ("character_faith_registration_callback", 0x568B20),
    ("character_rite_registration_callback", 0x568D18),
    ("rite_faith_registration_callback", 0x4EF9E0),
    ("faith_religion_registration_callback", 0x4D4A54),
    ("faith_main_rite_registration_callback", 0x4D5224),
    ("faith_fervor_registration_callback", 0x4D5654),
    ("spiritual_fulfillment_registration_callback", 0x55D347),
]


def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA:
        raise ValueError("The file is not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, rva in SOURCE_RVAS.items():
        definition = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if not definition or int(definition.group(1), 0) != rva:
            raise ValueError(f"Actual provider source binding differs: {name}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]
    spans, dump = [], []
    for name, start, end, *abi in SPANS + REGISTRATION_SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function" if abi else "registration_slice",
                      "abi": abi[0] if abi else None,
                      "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{ins.address:09X} {ins.bytes.hex(' '):32s} {ins.mnemonic:8s} {ins.op_str}"
                    for ins in decoder.disasm(raw, start))
    instructions = []
    for name, rva in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        instructions.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
                             "instruction": f"{ins.mnemonic} {ins.op_str}",
                             "rip_targets": [hex(ins.address + ins.size + op.mem.disp)
                                             for op in ins.operands if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
                             "direct_targets": [hex(op.imm) for op in ins.operands
                                                if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")]})
    # Obtain actual class descriptors without matching template visitors.
    rtti = []
    for cls in ["CFaith", "CRite", "CReligion"]:
        encoded = f".?AV{cls}@@".encode() + b"\0"
        offset = data.find(encoded)
        if offset < 0 or data.find(encoded, offset + 1) >= 0:
            raise ValueError(f"Exact class RTTI not unique: {cls}")
        type_rva = pe.offset_to_rva(offset) - 16
        rtti.append({"class": cls, "type_descriptor_rva": hex(type_rva), "name": encoded[:-1].decode()})
    return {"schema": "ck3_12002_nonwar_religion_native_research_v1", "game_version": "1.20.0.2",
            "executable_sha256": sha, "executable_size": len(data), "readiness": "static-confirmed",
            "local_ck3_touched": False, "provider_implemented": True, "mcp_registered": False, "live_verified": False,
            "provider_source_constants": {k: hex(v) for k, v in SOURCE_RVAS.items()},
            "native_spans": spans, "semantic_instructions": instructions, "exact_class_rtti": rtti,
            "unresolved": ["effective doctrine collection and merging ABI", "personal tenet collection row ABI",
                           "faith knowledge native getter", "conversion final gates/cost ABI",
                           "Rite stable authored key getter", "native AI selection branches"]}, "\n".join(dump) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--record", action="store_true", help="Record the reviewed research map beside this script")
    args = p.parse_args()
    result, dump = extract(args.exe)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        recorded = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if recorded != result:
            raise ValueError("The recorded native research map differs from the exact PE extraction")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
               "live_verified": False, "provider_implemented": True, "mcp_registered": False, "executable_sha256": EXACT_SHA,
               "provider_source_constants": len(SOURCE_RVAS),
               "complete_functions": len(SPANS), "registration_slices": len(REGISTRATION_SLICES),
               "semantic_instructions": len(SITES), "exact_class_rtti": len(result["exact_class_rtti"]),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "native-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
