#!/usr/bin/env python3
"""Exact-file ABI proof for conversion inputs; no process or game access."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage
EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = ROOT / "research/religion_conversion12002_ai_abi.json"
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"
SPANS = [
    ("expected_rite_fulfillment_change.registration", 0x57E300, 0x57E398),
    ("expected_rite_fulfillment_change.factory", 0x2AEBCF0, 0x2AEBD39),
    ("expected_rite_fulfillment_change.evaluate", 0x2AEC800, 0x2AEC992),
    ("Character.RiteBaseFulfillment.evaluate", 0x2BFC270, 0x2BFC457),
    ("NAI.MIN_YEARS_BETWEEN_RITE_CHANGE.register", 0x1A62780, 0x1A629D7),
    ("NAI.MIN_YEARS_BETWEEN_RITE_CHANGE.bound_check", 0x1A629E0, 0x1A62A11),
]
SITES = [
    ("script_name_registration", 0x57E311, "lea", 0x4783130),
    ("script_factory_registration", 0x57E379, "lea", 0x4786168),
    ("actual_trigger_factory_vtable", 0x2AEBD17, "lea", 0x4784E78),
    ("target_base_call", 0x2AEC89A, "call", 0x2BFC270),
    ("current_character_full_rite_id", 0x2AEC8AB, "mov", None),
    ("current_rite_storage", 0x2AEC89F, "mov", 0x5D1E2F8),
    ("current_base_call", 0x2AEC8EA, "call", 0x2BFC270),
    ("delta_target_minus_current", 0x2AEC8F7, "sub", None),
    ("native_trait_collection_input", 0x2BFC2D3, "lea", None),
    ("native_rite_trait_evaluator_call", 0x2BFC2E0, "call", 0x2BFAC30),
    ("native_modifier_collection_call", 0x2BFC2E8, "call", 0x28C3AE0),
    ("native_base_modifier_key", 0x2BFC302, "mov", None),
    ("native_modifier_sum", 0x2BFC390, "add", None),
    ("native_upper_bound", 0x2BFC3A3, "mov", 0x5C68DF8),
    ("native_lower_bound", 0x2BFC3AA, "mov", 0x5C68E00),
    ("min_reevaluation_define_name", 0x1A62798, "lea", 0x45AE990),
    ("min_reevaluation_define_value_binding", 0x1A628B8, "lea", 0x5C68824),
]

def extract(exe: Path, game: Path) -> tuple[dict, str]:
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXACT_SHA:
        raise ValueError("Not the frozen 1.20.0.2 executable")
    image = PeImage(raw)
    def read(rva: int, size: int) -> bytes:
        at = image.rva_to_offset(rva); return raw[at:at + size]
    md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
    source = HEADER.read_text(encoding="utf-8-sig")
    constants = {"kRiteStorageSlotRva": 0x5D1E2F8, "kRiteBaseFulfillmentRva": 0x2BFC270,
                 "kCharacterRiteOffset": 0xB4, "kRiteIdentityOffset": 8}
    for name, value in constants.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+)", source)
        if not match or int(match[1], 0) != value: raise ValueError("Provider binding differs: " + name)
    spans, dump = [], []
    for name, start, end in SPANS:
        body = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_exception_body", "bytes": body.hex(" "),
                      "sha256": hashlib.sha256(body).hexdigest()})
        dump.append(name + f" [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):35s} {i.mnemonic:8s} {i.op_str}"
                    for i in md.disasm(body, start))
    instructions = []
    for name, rva, mnemonic, target in SITES:
        ins = next(md.disasm(read(rva, 15), rva))
        rip = [ins.address + ins.size + o.mem.disp for o in ins.operands
               if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]
        direct = [o.imm for o in ins.operands if o.type == X86_OP_IMM and ins.mnemonic == "call"]
        if ins.mnemonic != mnemonic or (target is not None and target not in rip + direct):
            raise ValueError("Semantic anchor differs: " + name)
        instructions.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
                             "instruction": ins.mnemonic + " " + ins.op_str,
                             "rip_targets": [hex(t) for t in rip], "call_targets": [hex(t) for t in direct]})
    # +0x100 is the actual numeric evaluator; +0x60 is a scope declaration.
    entries = {"factory": (0x4786168, 8, 0x2AEBCF0),
               "numeric_evaluator": (0x4784E78, 0x100, 0x2AEC800)}
    vtables = []
    for name, (table, slot, expected) in entries.items():
        actual = struct.unpack("<Q", read(table + slot, 8))[0] - image.image_base
        if actual != expected: raise ValueError("Wrong actual evaluator vtable slot")
        vtables.append({"name": name, "vtable_rva": hex(table), "slot_offset": hex(slot),
                        "function_rva": hex(actual)})
    literal = b".?AVCDefineRegistryHelper_NAIMIN_YEARS_BETWEEN_RITE_CHANGE@NDefines@@\0"
    pos = raw.find(literal)
    if pos < 0 or raw.find(literal, pos + 1) >= 0: raise ValueError("Define helper RTTI not unique")
    if image.offset_to_rva(pos) != 0x581BBA0: raise ValueError("Define helper RTTI moved")
    definitions = []
    for rel, first, last in [("common/defines/ai/00_ai.txt", 1839, 1842),
                             ("common/defines/00_defines.txt", 888, 900)]:
        p = game / rel; lines = p.read_text(encoding="utf-8-sig").splitlines()
        definitions.append({"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                            "first_line": first, "last_line": last,
                            "text": "\n".join(lines[first-1:last])})
    # A direct E8 census is evidence about this body, not a proof that no AI
    # caller exists: indirect calls, inlining, and callers of inner helpers remain.
    callers = []
    for va, _, offset, length in image.sections[:1]:
        code = raw[offset:offset+length]; cursor = 0
        while (at := code.find(b"\xe8", cursor)) >= 0:
            cursor = at + 1
            if at + 5 > len(code): continue
            destination = va + at + 5 + struct.unpack_from("<i", code, at+1)[0]
            if destination == 0x2BFC270:
                callers.append(hex(va + at))
    expected_callers = ["0xedfdf8", "0x1933ade", "0x1cfc82c", "0x2aec89a", "0x2aec8ea", "0x2aeca3e", "0x2d08ad7"]
    if callers != expected_callers: raise ValueError("Candidate base direct caller map differs")
    return {"schema": "ck3_12002_religion_conversion_ai_inputs_abi_v1",
            "game_version": "1.20.0.2", "executable_sha256": EXACT_SHA,
            "executable_size": len(raw), "readiness": "static-confirmed",
            "live_verified": False, "local_ck3_touched": False,
            "provider_constants": {k: hex(v) for k, v in constants.items()},
            "complete_bodies": spans, "semantic_instructions": instructions,
            "vtables": vtables, "define_rtti_name_rva": "0x581bba0",
            "stock_definitions": definitions, "base_direct_e8_call_sites": callers,
            "final_ai_desire_verified": False, "ai_scheduler_verified": False,
            "unknown": ["actual landed AI rite reevaluation scheduler",
                        "complete conversion AI candidate enumeration and final scoring",
                        "MIN_YEARS_BETWEEN_RITE_CHANGE actual AI consumption",
                        "conversion AI command submission and observed outcome"]}, "\n".join(dump) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    result, dump = extract(args.exe, args.game)
    if args.record: MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result: raise ValueError("Reviewed ABI map differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    disasm = args.output_dir / "native-disassembly.txt"; disasm.write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "live_verified": False,
               "local_ck3_touched": False, "complete_bodies": len(SPANS),
               "semantic_instructions": len(SITES), "vtable_slots": 2,
               "direct_base_call_sites": len(result["base_direct_e8_call_sites"]),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(disasm.read_bytes()).hexdigest()}
    (args.output_dir / "native-result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
