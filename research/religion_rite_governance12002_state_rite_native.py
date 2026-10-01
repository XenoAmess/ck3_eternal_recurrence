#!/usr/bin/env python3
"""Freeze/verify actual stateRite identities from the 1.20.0.2 PE, disk only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage

SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_rite_governance12002_state_rite_abi.json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_rite_governance12002_state_rite.hpp"
CONSTANTS = {
    "kCharacterTopLiegeRva": 0x28BFDA0,
    "kCharacterPrimaryTitleRva": 0x289DA30,
    "kTitleStateRiteRva": 0x2315030,
    "kCharacterIdentityOffset": 0x18,
    "kCharacterLandedDataOffset": 0x1C0,
    "kLandedTitlesOffset": 0x1E0,
    "kLandedTitlesCountOffset": 0x1EC,
    "kDeathTitlesOffset": 0x68,
    "kDeathTitlesCountOffset": 0x74,
    "kTitleIdentityOffset": 0x10,
    "kTitleStateRiteIdOffset": 0x308,
}
FUNCTIONS = [
    ("Character.GetTopLiege.core", 0x28BFDA0, 0x28BFE38, "Character*(Character*)"),
    ("Character.GetTopLiege.thunk", 0x28CE5B0, 0x28CE5B5, "Character*(Character*)"),
    ("Character.GetPrimaryTitle.core", 0x289DA30, 0x289DAA6, "Title*(Character*)"),
    ("Character.GetPrimaryTitle.thunk", 0x28CE510, 0x28CE515, "Title*(Character*)"),
    ("Title.GetStateRite.core", 0x2315030, 0x2315092, "Rite*(Title*)"),
    ("Title.GetStateRite.reference", 0x11F8130, 0x11F813C, "uint32_t*(Title*,uint32_t* out)"),
]
SLICES = [
    ("Title.GetStateRite.registration", 0x456972, 0x4569F9),
    ("Character.GetPrimaryTitle.registration", 0x557CAB, 0x557CFE),
    ("Character.GetTopLiege.registration", 0x557F92, 0x558028),
]
SITES = [
    ("top_liege_landed_data", 0x28BFDC0),
    ("top_liege_landed_scope", 0x28BFDCF),
    ("top_liege_landed_character_type", 0x28BFDDA),
    ("top_liege_full_character_ref", 0x28BFDE3),
    ("top_liege_unlanded_data", 0x28BFDEB),
    ("top_liege_unlanded_liege_ref", 0x28BFDFC),
    ("top_liege_unlanded_full_generation_match", 0x28BFE22),
    ("primary_title_landed_data", 0x289DA30),
    ("primary_title_landed_count", 0x289DA3C),
    ("primary_title_landed_array", 0x289DA45),
    ("primary_title_death_data", 0x289DA50),
    ("primary_title_death_count", 0x289DA5C),
    ("primary_title_death_array", 0x289DA62),
    ("primary_title_no_title_sentinel", 0x289DA6A),
    ("primary_title_full_generation_match", 0x289DA99),
    ("title_state_rite_full_ref_field", 0x11F8130),
    ("title_state_rite_full_ref_call", 0x231503E),
    ("title_state_rite_storage_slot", 0x2315043),
    ("title_state_rite_native_default_slot", 0x231504A),
    ("title_state_rite_full_generation_match", 0x231507B),
    ("title_state_rite_callback_registration", 0x4569E8),
    ("primary_title_callback_registration", 0x557CE7),
    ("top_liege_callback_registration", 0x558017),
]
STOCK_WINDOWS = {
    "common/scripted_rules/00_rules.txt": [(65, 72), (108, 115)],
    "gui/window_government_administration.gui": [(1086, 1090)],
}

def extract(exe: Path, game: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 PE")
    pe = PeImage(data)
    source = HEADER.read_text(encoding="utf-8-sig")
    for key, value in CONSTANTS.items():
        match = re.search(rf"\b{key}\s*=\s*(0x[\da-fA-F]+)", source)
        if not match or int(match.group(1), 0) != value:
            raise ValueError(f"Actual provider constant differs: {key}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]
    spans, dump = [], []
    for name, start, end, *abi in FUNCTIONS + SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function" if abi else "registration_slice",
                      "abi": abi[0] if abi else None, "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}"
                    for i in decoder.disasm(raw, start))
    sites = []
    for name, rva in SITES:
        i = next(decoder.disasm(read(rva, 15), rva))
        sites.append({"name": name, "rva": hex(rva), "bytes": i.bytes.hex(" "),
                      "instruction": f"{i.mnemonic} {i.op_str}",
                      "rip_targets": [hex(i.address + i.size + o.mem.disp)
                                      for o in i.operands if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP],
                      "direct_targets": [hex(o.imm) for o in i.operands
                                         if o.type == X86_OP_IMM and i.mnemonic in ["call", "jmp"]]})
    stock = []
    for relative, windows in STOCK_WINDOWS.items():
        path = game / relative
        raw = path.read_bytes(); lines = raw.decode("utf-8-sig").splitlines()
        stock.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                      "windows": [{"first_line": a, "last_line": b, "text": "\n".join(lines[a - 1:b])}
                                  for a, b in windows]})
    return {"schema": "ck3_12002_religion_state_rite_abi_v1", "game_version": "1.20.0.2",
            "executable_sha256": SHA, "executable_size": len(data),
            "source_constants": {k: hex(v) for k, v in CONSTANTS.items()},
            "native_spans": spans, "semantic_instructions": sites, "stock": stock,
            "reused_context_contract": "research/religion12002_native_abi.json",
            "local_ck3_touched": False, "live_verified": False,
            "unresolved": ["MCP integration", "paused native artifact",
                           "final conversion gates/cost and native AI choice (outside this readonly package)"]}, "\n".join(dump) + "\n"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args(); result, dump = extract(args.exe, args.game)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result:
        raise ValueError("Exact source/PE/stock manifest differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "local_ck3_touched": False, "live_verified": False,
               "complete_functions": len(FUNCTIONS), "registration_slices": len(SLICES),
               "semantic_instructions": len(SITES), "source_constants": len(CONSTANTS),
               "stock_files": len(result["stock"]), "executable_sha256": SHA,
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "native-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
