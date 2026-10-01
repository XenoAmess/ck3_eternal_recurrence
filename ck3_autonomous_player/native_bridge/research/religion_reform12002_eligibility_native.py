#!/usr/bin/env python3
"""Verify real Rite draft final gates in the frozen 1.20.0.2 PE, without a process."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = HERE / "religion_reform12002_eligibility_abi.json"
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_reform12002_eligibility.hpp"
CONSTANTS = {"kCanCreateRiteCoreRva": 0x14F56D0,
             "kCanEditRiteCoreRva": 0x14F5050,
             "kCreationWindowActorIdOffset": 0xCC}
SPANS = [
    ("RiteCreationWindow.CanCreateRite.core", 0x14F56D0, 0x14F5777),
    ("RiteCreationWindow.CanCreateRite.reflection", 0x14FB0E0, 0x14FB11A),
    ("RiteCreationWindow.CanEditRite.core", 0x14F5050, 0x14F5101),
    ("RiteCreationWindow.CanEditRite.reflection", 0x14FAF50, 0x14FAF8A),
    ("RiteCreationWindow.name_conflict_check", 0x14F8930, 0x14F8C18),
    ("CCreateRiteCommand.final_validator", 0x29A2F60, 0x29A3132),
    ("CEditRiteCommand.final_validator", 0x29A2640, 0x29A2AD7),
    ("Faith.proposed_draft_split_or_unreformed_predicate", 0x2BDCA90, 0x2BDCB01),
    ("new_faith_or_reformation_final_requirements", 0x29D1820, 0x29D2477),
    ("new_rite_final_requirements", 0x29C9760, 0x29CA1F2),
    ("scripted_rule_for_character.evaluate", 0x1D65B00, 0x1D65BE5),
]
REGISTRATION_SLICES = [
    ("RiteCreationWindow.CanCreateRite.registration", 0x22A3CB, 0x22A417),
    ("RiteCreationWindow.CanEditRite.registration", 0x229FEB, 0x22A039),
]
EDGES = [
    ("create_reflection_to_final", 0x14FB0F4, 0x14F56D0),
    ("edit_reflection_to_final", 0x14FAF64, 0x14F5050),
    ("create_draft_copy", 0x14F5726, 0x29A1F10),
    ("create_command_validity", 0x14F5734, 0x29A2F60),
    ("create_name_conflict", 0x14F5742, 0x14F8930),
    ("edit_draft_copy", 0x14F50B0, 0x29A1F10),
    ("edit_command_validity", 0x14F50BE, 0x29A2640),
    ("edit_name_conflict", 0x14F50CC, 0x14F8930),
    ("draft_predicate", 0x29A30B7, 0x2BDCA90),
    ("new_faith_or_reformation_branch", 0x29A30D1, 0x29D1820),
    ("new_rite_branch", 0x29A30D8, 0x29C9760),
    ("new_faith_or_reformation_rule", 0x29D18D6, 0x1D65B00),
    ("new_rite_rule", 0x29C980B, 0x1D65B00),
    ("new_faith_or_reformation_resource_gate", 0x29D1A6A, 0x310E710),
    ("new_rite_resource_gate", 0x29C9997, 0x310E710),
]
SITES = [
    ("draft_actor_for_creation", 0x14F5710),
    ("real_inline_draft_for_creation", 0x14F571A),
    ("draft_actor_for_editing", 0x14F509A),
    ("real_inline_draft_for_editing", 0x14F50A4),
    ("creation_result_AND_name_gate", 0x14F5747),
    ("editing_result_AND_name_gate", 0x14F50D1),
    ("create_method_name", 0x22A3DB),
    ("create_method_callback", 0x22A407),
    ("edit_method_name", 0x229FFB),
    ("edit_method_callback", 0x22A029),
    ("command_actor_full_ref", 0x29A2F89),
    ("new_faith_rule_selector", 0x29D18D1),
    ("new_rite_rule_selector", 0x29C9806),
    ("script_rule_array_stride", 0x1D65B37),
    ("script_rule_array", 0x1D65B3E),
]
STOCK_WINDOWS = [
    ("gui/window_rite_creation.gui", 593, 629),
    ("common/scripted_rules/00_rules.txt", 22, 33),
    ("common/scripted_triggers/00_religious_triggers.txt", 3140, 3253),
]


def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXACT_SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    header = HEADER.read_text(encoding="utf-8-sig")
    for name, value in CONSTANTS.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if not match or int(match.group(1), 0) != value:
            raise ValueError("Actual source constant differs: " + name)
    cs = Cs(CS_ARCH_X86, CS_MODE_64)
    cs.detail = True

    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]

    spans, dump = [], []
    for name, start, end in SPANS + REGISTRATION_SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function" if (name, start, end) in SPANS else "registration_slice",
                      "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):35s} {i.mnemonic:8s} {i.op_str}"
                    for i in cs.disasm(raw, start))
    edges = []
    for name, site, target in EDGES:
        instruction = next(cs.disasm(read(site, 15), site))
        if instruction.mnemonic != "call" or instruction.operands[0].type != X86_OP_IMM or instruction.operands[0].imm != target:
            raise ValueError("Native call edge differs: " + name)
        edges.append({"name": name, "site_rva": hex(site), "target_rva": hex(target),
                      "bytes": instruction.bytes.hex(" ")})
    sites = []
    for name, site in SITES:
        instruction = next(cs.disasm(read(site, 15), site))
        sites.append({"name": name, "rva": hex(site), "bytes": instruction.bytes.hex(" "),
                      "instruction": f"{instruction.mnemonic} {instruction.op_str}",
                      "rip_targets": [hex(instruction.address + instruction.size + o.mem.disp)
                                      for o in instruction.operands if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]})
    vt = 0x4770550
    entries = [struct.unpack_from("<Q", read(vt + offset, 8))[0] - pe.image_base
               for offset in (0, 0x30)]
    if entries != [0x29A1EC0, 0x29A2F60]:
        raise ValueError("CCreateRiteCommand vtable differs")
    stock = []
    game = exe.resolve().parents[1] / "game"
    for relative, first, last in STOCK_WINDOWS:
        raw = (game / relative).read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        if last > len(lines):
            raise ValueError("Stock evidence window absent: " + relative)
        stock.append({"path": relative, "file_sha256": hashlib.sha256(raw).hexdigest(),
                      "first_line": first, "last_line": last,
                      "text": "\n".join(lines[first-1:last])})
    result = {"schema": "ck3_12002_rite_draft_eligibility_native_v1",
              "game_version": "1.20.0.2", "executable_sha256": sha,
              "executable_size": len(data), "readiness": "static-confirmed",
              "scope": "actual_current_rite_creation_window_draft", "local_ck3_touched": False,
              "live_verified": False, "source_constants": {k: hex(v) for k, v in CONSTANTS.items()},
              "native_spans": spans, "native_call_edges": edges, "semantic_instructions": sites,
              "stock_evidence_windows": stock,
              "create_command_vtable": {"rva": hex(vt), "destructor_rva": hex(entries[0]),
                                         "validator_offset": "0x30", "validator_rva": hex(entries[1])},
              "unknown": ["headless arbitrary proposed draft construction is not implemented",
                          "full native reason strings are not copied by this boolean provider",
                          "native registration and paused live query pending parent integration"]}
    return result, "\n".join(dump) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args()
    result, disassembly = extract(args.exe)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result:
        raise ValueError("Frozen eligibility ABI differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(disassembly, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed", "local_ck3_touched": False,
               "live_verified": False, "complete_functions": len(SPANS),
               "registration_slices": len(REGISTRATION_SLICES), "call_edges": len(EDGES),
               "semantic_instructions": len(SITES), "vtable_prefixes": 1,
               "stock_evidence_windows": len(STOCK_WINDOWS),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "disassembly_sha256": hashlib.sha256(disassembly.encode()).hexdigest()}
    (args.output_dir / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
