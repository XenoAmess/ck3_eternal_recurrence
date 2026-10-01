#!/usr/bin/env python3
"""Freeze/verify exact 1.20.0.2 Rite organization counts; offline file only."""
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

EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_rite_governance12002_organization.hpp"
MANIFEST = Path(__file__).with_name("religion_rite_governance12002_organization_abi.json")
CONSTANTS = {"kCountyCountRva": 0xB80410, "kCharacterFollowerCountRva": 0xEDDB90,
             "kCountyCountOffset": 0x18, "kCharacterFollowerCountOffset": 0x1C}
SPANS = [
    ("Rite.counties.leaf", 0xB80410, 0xB80414, "int32_t(Rite*)"),
    ("Rite.followers.leaf", 0xEDDB90, 0xEDDB94, "int32_t(Rite*)"),
    ("Rite.GetNumberOfCountiesOfRite.callback", 0x2444640, 0x2444678, "reflection callback"),
    ("Rite.GetNumberOfFollowers.callback", 0x24FC210, 0x24FC248, "reflection callback"),
    ("Rite.GetNumberOfCountiesOfRite.registration", 0x4EEF43, 0x4EEFDC, "registration slice"),
    ("Rite.GetNumberOfFollowers.registration", 0x4EF0D3, 0x4EF15E, "registration slice"),
    # Native scope facts only. This is not a production membership provider.
    ("CFaithCharacterList.alive_source_filter", 0x1C6113E, 0x1C61225, "native Faith collector slice"),
    ("CRiteTitleListBuilder.rite_scope", 0x1D40CD6, 0x1D40D24, "Rite 0x2A scope slice"),
    ("CRiteTitleListBuilder.ranked_title_downstream", 0x1D40E13, 0x1D40E27, "ranked Title collector call slice"),
]
SITES = [
    ("county_signed_int32", 0xB80410, "mov eax, dword ptr [rcx + 0x18]", []),
    ("followers_signed_int32", 0xEDDB90, "mov eax, dword ptr [rcx + 0x1c]", []),
    ("county_registration_name", 0x4EEF43, None, [0x4737EB0]),
    ("county_registration_callback", 0x4EEFCC, None, [0x2444640]),
    ("county_callback_leaf", 0x2444652, None, [0xB80410]),
    ("follower_registration_name", 0x4EF0D3, None, [0x472FB68]),
    ("follower_registration_callback", 0x4EF14E, None, [0x24FC210]),
    ("follower_callback_leaf", 0x24FC222, None, [0xEDDB90]),
    ("faith_source_array", 0x1C6114C, "mov rbx, qword ptr [rcx + 0x2ee60]", []),
    ("faith_source_length", 0x1C61153, "movsxd rax, dword ptr [rcx + 0x2ee6c]", []),
    ("faith_filter_not_rite_filter", 0x1C611BC, "cmp dword ptr [rcx + 0x4b8], eax", []),
    ("faith_alive_filter", 0x1C611C4, "cmp qword ptr [rdx + 0x1d0], 0", []),
    ("faith_output_character_full_ref", 0x1C611D6, "mov eax, dword ptr [rdx + 0x18]", []),
    ("title_collector_scope_rite_enum", 0x1D40CD9, "cmp word ptr [rax], 0x2a", []),
    ("ranked_title_native_collector_call", 0x1D40E22, None, [0x1D223B0]),
]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA: raise ValueError("Not the pinned 1.20.0.2 executable")
    pe = PeImage(data)
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, expected in CONSTANTS.items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9a-fA-F]+)", source)
        if not match or int(match.group(1), 0) != expected:
            raise ValueError(f"Actual source constant differs: {name}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva); return data[offset:offset + size]
    spans, dump = [], []
    for name, start, end, kind in SPANS:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": kind, "bytes": raw.hex(" "), "sha256": hashlib.sha256(raw).hexdigest()})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{ins.address:09X} {ins.bytes.hex(' '):32s} {ins.mnemonic:8s} {ins.op_str}"
                    for ins in decoder.disasm(raw, start))
    instructions = []
    for name, rva, expected_ins, expected_targets in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        instruction = f"{ins.mnemonic} {ins.op_str}"
        rip = [ins.address + ins.size + op.mem.disp for op in ins.operands
               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        direct = [op.imm for op in ins.operands
                  if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")]
        if expected_ins is not None and instruction != expected_ins:
            raise ValueError(f"Instruction mismatch: {name}: {instruction}")
        if expected_targets and rip + direct != expected_targets:
            raise ValueError(f"Target mismatch: {name}: {rip + direct}")
        instructions.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
                             "instruction": instruction, "rip_targets": list(map(hex, rip)),
                             "direct_targets": list(map(hex, direct))})
    return {"schema": "ck3_12002_rite_organization_research_v1", "game_version": "1.20.0.2",
            "executable_sha256": sha, "readiness": "static-confirmed", "local_ck3_touched": False,
            "production_scope": "current_player_rite_native_cached_counts", "live_verified": False,
            "provider_source_constants": {key: hex(value) for key, value in CONSTANTS.items()},
            "native_spans": spans, "semantic_instructions": instructions,
            "unresolved": ["Rite count refresh producer timing", "complete native Rite member collector ABI",
                           "county collector output ownership/stride", "full governance final gates"]}, "\n".join(dump) + "\n"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args()
    result, dump = extract(args.exe)
    if args.record: MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif result != json.loads(MANIFEST.read_text(encoding="utf-8")):
        raise ValueError("Frozen organization manifest differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
               "live_verified": False, "executable_sha256": EXACT_SHA,
               "source_constants": len(CONSTANTS), "native_spans": len(SPANS), "semantic_instructions": len(SITES),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
