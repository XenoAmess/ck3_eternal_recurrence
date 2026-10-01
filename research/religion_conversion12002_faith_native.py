#!/usr/bin/env python3
"""Verify the exact Faith candidate registry and native conversion-rule ABI.

Only reads the supplied PE file. No process, UI, Steam, or command submission.
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage
EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_conversion12002_faith_abi.json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_conversion_faith.hpp"
CONSTANTS = {
    "kFaithStorageSlotRva": 0x5D1E300, "kCharacterFaithRva": 0x289E750,
    "kFaithMainRiteRva": 0x2444360, "kRiteFaithRva": 0x24FC560,
    "kFaithTagRva": 0xB801A0, "kFaithConversionRuleRva": 0x1D635E0,
    "kWorldDataOffset": 0xA0, "kWorldFaithsOffset": 0xD598,
    "kWorldFaithCountOffset": 0xD5A4, "kIdentityOffset": 0x08,
    "kFaithMainRiteIdOffset": 0x98,
}
SPANS = [
    ("faith_conversion_rule", 0x1D635E0, 0x1D636F6, "bool(Character*,uint32_t FaithID,reasons* nullable)"),
    ("faith_same_identity_precondition", 0x1D632A0, 0x1D633A8, "bool(Character*,uint32_t FaithID,reasons* nullable)"),
    ("same_faith_lambda", 0x1D66C10, 0x1D66C65, "bool(capture{Character*,FaithID}*)"),
    ("same_faith_localization_thunk", 0x1D66BD0, 0x1D66BDC, "tail jump reason formatting"),
    ("same_faith_localization", 0x1D633B0, 0x1D635D0, "FAITH_CONVERSION_SAME_FAITH"),
    ("negative_requirement_evaluate", 0x37C5600, 0x37C57DE, "native predicate is negated; null-reasons path"),
    ("world_faith_registry_to_window", 0x14C3650, 0x14C373A, "complete chained body; includes filter copy and all-world path"),
    ("faith_id_vector_copy", 0xC858C0, 0xC8593B, "uint32_t row copy, stride 4"),
    ("faith_list_datamodel_wrapper_a", 0x14C7310, 0x14C7363, "window+0x20 datamodel"),
    ("faith_list_datamodel_wrapper_b", 0x14C76E0, 0x14C7733, "window+0x20 datamodel"),
    ("convert_rite_command_final_validator", 0x29A34C0, 0x29A38CB, "context only: sibling owns overall gate and cost"),
]
SITES = [
    ("faith_precondition_call", 0x1D635FC),
    ("scope_new_faith_tag", 0x1D6361E),
    ("scope_full_faith_id", 0x1D63626),
    ("rules_owner_getter", 0x1D63640),
    ("rules_table", 0x1D63645),
    ("faith_rule_offset", 0x1D6364C),
    ("faith_rule_no_reasons", 0x1D63667),
    ("same_faith_source_rite", 0x1D66C23),
    ("same_faith_target_full_id", 0x1D66C57),
    ("same_faith_compare", 0x1D66C5B),
    ("same_faith_localization_key", 0x1D63414),
    ("game_state_slot", 0x14C3656),
    ("world_data_pointer", 0x14C3664),
    ("religion_filtered_faith_vector", 0x14C36A9),
    ("world_faith_array", 0x14C36C7),
    ("world_faith_count", 0x14C36CE),
    ("world_faith_pointer_stride", 0x14C36DA),
    ("candidate_faith_full_identity", 0x14C36F8),
    ("world_faith_next_pointer", 0x14C3708),
    ("faith_vector_copy_count", 0xC858D3),
    ("faith_vector_copy_stride", 0xC8590A),
    ("command_different_faith_rule_call", 0x29A365E),
]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes(); sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA: raise ValueError("Not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data); decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    source = HEADER.read_text(encoding="utf-8-sig")
    for name, expected in CONSTANTS.items():
        found = re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+)", source)
        if not found or int(found.group(1), 0) != expected: raise ValueError("Provider differs: " + name)
    def read(rva: int, count: int) -> bytes:
        offset = pe.rva_to_offset(rva); return data[offset:offset + count]
    spans, dump = [], []
    for name, start, end, abi in SPANS:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
            "kind": "complete_function", "abi": abi, "bytes": raw.hex(" "),
            "sha256": hashlib.sha256(raw).hexdigest()})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}" for i in decoder.disasm(raw, start))
    sites = []
    for name, rva in SITES:
        i = next(decoder.disasm(read(rva, 15), rva))
        sites.append({"name": name, "rva": hex(rva), "bytes": i.bytes.hex(" "),
            "instruction": f"{i.mnemonic} {i.op_str}",
            "rip_targets": [hex(i.address + i.size + op.mem.disp) for op in i.operands
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
            "direct_targets": [hex(op.imm) for op in i.operands if op.type == X86_OP_IMM and i.mnemonic in ("call", "jmp")]})
    # The final same-Faith condition uses std::function captures with exact vtables.
    tables = []
    for name, rva, entries in [("same_faith_reason_functor", 0x4669D00, 6),
                               ("same_faith_predicate_functor", 0x4669D38, 6),
                               ("negative_requirement", 0x493ACF0, 4)]:
        raw = read(rva, entries * 8)
        tables.append({"name": name, "rva": hex(rva), "bytes": raw.hex(" "),
            "targets": [hex(struct.unpack_from("<Q", raw, index * 8)[0] - pe.image_base) for index in range(entries)],
            "sha256": hashlib.sha256(raw).hexdigest()})
    literals = []
    for name, rva in [("same_faith_reason_key", 0x4669CD8)]:
        raw = read(rva, 64).split(b"\0", 1)[0]
        literals.append({"name": name, "rva": hex(rva), "value": raw.decode("ascii")})
    return {"schema": "ck3_12002_nonwar_faith_conversion_abi_v1", "game_version": "1.20.0.2",
        "executable_sha256": sha, "executable_size": len(data), "readiness": "static-confirmed",
        "local_ck3_touched": False, "live_verified": False, "provider_implemented": True,
        "provider_source_constants": {name: hex(value) for name, value in CONSTANTS.items()},
        "native_spans": spans, "semantic_instructions": sites, "functor_vtables": tables,
        "literals": literals, "candidate_source": "native world Faith registry, not GUI sorted/filtered model",
        "native_rule_boundary": "same-Faith rejection and native scripted Faith conversion rules only",
        "other_package_dependencies": ["full target-Rite final command validator", "actual piety conversion cost"],
        "unresolved": ["Faith GUI sorting and user filter semantics", "native reason-description string extraction",
            "complete per-Faith Rite enumeration", "production paused artifact"]}, "\n".join(dump) + "\n"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True); p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args(); result, dump = extract(args.exe)
    if args.record: MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result: raise ValueError("Recorded ABI differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "live_verified": False,
        "local_ck3_touched": False, "exact_executable_sha256": EXACT_SHA,
        "complete_functions": len(SPANS), "semantic_instructions": len(SITES), "functor_vtables": 3,
        "provider_source_constants": len(CONSTANTS), "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir / "native-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
