#!/usr/bin/env python3
"""Verify the reviewed nonmilitary Rite-head/faith-title chain against frozen PE."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from religion12002_native import PeImage, Cs, CS_ARCH_X86, CS_MODE_64, EXACT_SHA
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).with_suffix(".json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_rite_governance12002_head.hpp"
CONSTANTS = {
    "kRiteHeadIdGetterRva": 0xD55CF0, "kRiteHeadObjectGetterRva": 0x24FC610,
    "kFaithReligiousHeadGetterRva": 0x2439E10, "kFaithReligiousHeadTitleGetterRva": 0x2443FA0,
    "kRiteHeadCharacterIdOffset": 0x4C0, "kFaithReligiousHeadTitleIdOffset": 0x300,
    "kTitleReferenceIdOffset": 0x10, "kTitleHolderCharacterIdOffset": 0x128,
}
SPANS = [
    ("Rite.head.full_character_reference", 0xD55CF0, 0xD55CFC, "uint32_t*(Rite*,uint32_t*out)"),
    ("Rite.GetHeadOfRite", 0x24FC610, 0x24FC672, "Character*(Rite*)"),
    ("Faith.GetReligiousHead.core", 0x2439E10, 0x2439E8D, "Character*(Faith*) via religious title holder"),
    ("Faith.GetReligiousHead.thunk", 0x2443DF0, 0x2443DF5, "Character*(Faith*)"),
    ("Faith.GetReligiousHeadTitle.core", 0x2443FA0, 0x2443FDD, "Title*(Faith*)"),
    ("Faith.GetReligiousHeadTitle.reflection", 0x2443FE0, 0x244404D, "reflection wrapper"),
]
REGISTRATION = [
    ("Faith.GetReligiousHead.registration", 0x4D4BC8, 0x4D4BFE),
    ("Faith.GetReligiousHeadTitle.registration", 0x4D4CB8, 0x4D4D01),
    ("Rite.GetHeadOfRite.registration", 0x4EFB52, 0x4EFC57),
]
SITES = [
    ("rite_head_full_reference", 0xD55CF0),
    ("rite_head_id_getter_call", 0x24FC61E),
    ("rite_head_character_storage", 0x24FC623),
    ("rite_head_character_full_generation", 0x24FC65B),
    ("faith_head_title_reference", 0x2439E1C),
    ("faith_title_full_generation", 0x2439E40),
    ("faith_title_holder_reference", 0x2439E58),
    ("faith_holder_full_generation", 0x2439E7F),
    ("faith_head_thunk_to_core", 0x2443DF0),
    ("faith_title_getter_reference", 0x2443FAC),
    ("faith_title_getter_generation", 0x2443FD0),
    ("faith_head_registration_getter", 0x4D4BED),
    ("faith_title_registration_getter", 0x4D4CF0),
    ("rite_head_registration_getter", 0x4EFBD2),
]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXACT_SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, value in CONSTANTS.items():
        found = re.search(rf"\b{name}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if not found or int(found.group(1), 0) != value:
            raise ValueError(f"Actual provider constant differs: {name}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]
    dump, spans = [], []
    for name, start, end, *abi in SPANS + REGISTRATION:
        raw = read(start, end - start)
        decoded = list(decoder.disasm(raw, start))
        if not decoded or sum(i.size for i in decoded) != len(raw):
            raise ValueError(f"Incomplete instruction span: {name}")
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function" if abi else "registration_slice",
                      "abi": abi[0] if abi else None, "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}" for i in decoded)
    sites = []
    for name, rva in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        sites.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
                      "instruction": f"{ins.mnemonic} {ins.op_str}",
                      "rip_targets": [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                                      if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
                      "direct_targets": [hex(op.imm) for op in ins.operands
                                         if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")]})
    stock = []
    for relative, windows in [
        ("common/religion/doctrine_types/20_doctrines.txt", [(1170, 1221), (1224, 1256)]),
        ("common/scripted_triggers/pam_scripted_triggers.txt", [(1485, 1512)]),
        ("gui/window_faith.gui", [(5429, 5429), (5698, 5698)]),
    ]:
        path = exe.parent.parent / "game" / relative
        raw = path.read_bytes(); lines = raw.decode("utf-8-sig").splitlines()
        stock.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                      "selected_nonmilitary_windows": [
                          {"first_line": first, "last_line": last, "text": "\n".join(lines[first-1:last])}
                          for first, last in windows]})
    return {"schema": "ck3_12002_religion_rite_heads_native_v1", "executable_sha256": EXACT_SHA,
            "game_version": "1.20.0.2", "provider_constants": {k: hex(v) for k, v in CONSTANTS.items()},
            "native_spans": spans, "semantic_instructions": sites, "stock_evidence": stock,
            "scope": "nonmilitary identity relations only", "local_ck3_touched": False,
            "live_verified": False, "unresolved": ["effective doctrine head institution classification dependency",
            "religious_head_or_challenger final authority", "Rite head distinct own title mapping",
            "native AI head selection/appointment tree"]}, "\n".join(dump) + "\n"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args(); result, dump = extract(args.exe)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result:
        raise ValueError("Reviewed exact-PE manifest differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "executable_sha256": EXACT_SHA,
               "provider_constants": len(CONSTANTS), "complete_functions": len(SPANS),
               "registration_slices": len(REGISTRATION), "semantic_instructions": len(SITES),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest(),
               "local_ck3_touched": False, "live_verified": False}
    (args.output_dir / "native-verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt)); return 0
if __name__ == "__main__": raise SystemExit(main())
