#!/usr/bin/env python3
"""Freeze nonmilitary CK3 1.20.0.2 conversion result sources; never execute them."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage

EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = HERE / "religion_conversion12002_outcome_abi.json"
SPANS = [
    ("CConvertRiteCommand.secondary_execute", 0x29A4F90, 0x29A5017, "leaf function; Character*, Rite* -> native setter"),
    ("CConvertFaithAndRiteCommand.secondary_execute", 0x29A3370, 0x29A34B2, "command secondary subobject; calls shared conversion result wrapper"),
    ("conversion.result_wrapper", 0x29A8040, 0x29A85D7, "Character*, result branch indices, command owner pointer; attribution only"),
    ("Character.set_rite", 0x28B01A0, 0x28B0902, "void(Character*, Rite*, bool, bool); does not return a conversion receipt"),
    ("Character.update_default_spiritual_baseline", 0x28BD170, 0x28BD1EA, "void(Character*, signed fixed value); complete chained unwind body"),
    ("Character.set_spiritual_fulfillment", 0x28BCE80, 0x28BCF16, "void(Character*, signed fixed value); clamp then extension+0xA0"),
    ("Character.FireRiteChangedOnAction", 0x289CE40, 0x289CFC2, "Character*, old full RiteID, old full FaithID"),
    ("Character.transfer_rite_definition_entries", 0x28B0910, 0x28B0A26, "Character*, Rite*; complete chained body; semantic collection names unresolved here"),
    ("Character.add_known_tenet_entry", 0x28B0CD0, 0x28B0E83, "Character*, Tenet*; deduplicated known collection; complete chained body"),
]
SITES = [
    ("rite_execute_to_setter", 0x29A5012, "jmp", 0x28B01A0),
    ("faith_execute_to_result_wrapper", 0x29A349D, "call", 0x29A8040),
    ("actual_conversion_cost_call", 0x29A813A, "call", 0x29A3DE0),
    ("negative_cost", 0x29A813F, "neg", None),
    ("cost_fixed_scale", 0x29A8143, "imul", None),
    ("piety_resource_address", 0x29A8156, "add", None),
    ("faith_result_to_setter", 0x29A81F7, "call", 0x28B01A0),
    ("full_rite_identity_write", 0x28B0516, "mov", None),
    ("faith_cache_absent_write", 0x28B057C, "mov", None),
    ("faith_cache_new_identity_write", 0x28B0597, "mov", None),
    ("native_default_fulfillment_call", 0x28B0635, "call", 0x2BFB4C0),
    ("native_baseline_update_call", 0x28B0640, "call", 0x28BD170),
    ("baseline_difference", 0x28BD1B6, "sub", None),
    ("current_fulfillment_plus_difference", 0x28BD1C6, "add", None),
    ("current_fulfillment_setter_call", 0x28BD1CC, "call", 0x28BCE80),
    ("baseline_cache_write", 0x28BD1D8, "mov", None),
    ("current_fulfillment_write", 0x28BCEB2, "mov", None),
    ("rite_definition_transfer_call", 0x28B064B, "call", 0x28B0910),
    ("character_definition_entry_insert", 0x28B09CC, "call", 0x880340),
    ("additional_rite_definition_transfer", 0x28B0A06, "call", 0x28B0CD0),
    ("known_doctrine_presence_check", 0x28B09AB, "call", 0x28B0A30),
    ("known_tenet_entry_insert", 0x28B0D63, "call", 0x880340),
    ("known_tenet_related_entry_insert", 0x28B0E56, "call", 0x880340),
    ("fire_rite_changed_onaction_call", 0x28B087E, "call", 0x289CE40),
    ("fire_rite_changed_name_anchor", 0x289CE8E, "lea", None),
]
COMMANDS = [
    ("CConvertRiteCommand", 0x5A163A8, 0x4E26418, 0x47700E8, 0x4E26440, 0x4770180, 0x29A4F90),
    ("CConvertFaithAndRiteCommand", 0x5A16768, 0x4E263F0, 0x4770340, 0x4E263C8, 0x47703D8, 0x29A3370),
]
# Explicitly omit military sections from mixed on_action files.
STOCK_WINDOWS = [
    ("common/on_action/religion_on_actions.txt", 834, 994),
    ("common/on_action/religion_on_actions.txt", 1114, 1158),
    ("common/on_action/religion_on_actions.txt", 1188, 1245),
    ("common/scripted_effects/pam_effects.txt", 11516, 11524),
    ("common/scripted_effects/pam_effects.txt", 1381, 1388),
    ("common/scripted_effects/pam_effects.txt", 8469, 8512),
    ("common/on_action/dlc/pam/pam_on_actions.txt", 91, 95),
    ("common/on_action/dlc/pam/pam_on_actions.txt", 268, 281),
    ("common/scripted_effects/00_religion_effects.txt", 1460, 1511),
    ("events/religion_events/faith_conversion_events.txt", 3, 67),
    ("events/religion_events/faith_conversion_events.txt", 199, 296),
    ("events/religion_events/faith_conversion_events.txt", 456, 541),
    ("common/script_values/pam_values.txt", 163, 170),
    ("common/script_values/pam_values.txt", 2172, 2184),
]


def extract(exe: Path, game: Path) -> tuple[dict, str, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXACT_SHA:
        raise ValueError("not the frozen CK3 1.20.0.2 executable")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True

    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + size]

    spans, dump = [], []
    for name, start, end, abi in SPANS:
        raw = read(start, end - start)
        ins = list(decoder.disasm(raw, start))
        if not ins or ins[-1].address + ins[-1].size != end:
            raise ValueError(f"instruction coverage differs for {name}")
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function_body", "abi": abi, "bytes": raw.hex(" "),
                      "sha256": hashlib.sha256(raw).hexdigest()})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}" for i in ins)
    sites = []
    for name, rva, mnemonic, target in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        direct = [op.imm for op in ins.operands if op.type == X86_OP_IMM]
        if ins.mnemonic != mnemonic or (target is not None and target not in direct):
            raise ValueError(f"semantic instruction differs: {name}")
        sites.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
                      "instruction": f"{ins.mnemonic} {ins.op_str}",
                      "direct_target": hex(target) if target is not None else None,
                      "rip_targets": [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                                      if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]})
    commands = []
    for cls, type_rva, col, vt, secondary_col, secondary_vt, execute in COMMANDS:
        wanted = f".?AV{cls}@@\0".encode()
        if read(type_rva + 16, len(wanted)) != wanted:
            raise ValueError(f"RTTI differs: {cls}")
        for crva, vrva, object_offset in ((col, vt, 0), (secondary_col, secondary_vt, 24)):
            values = struct.unpack("<IIIIII", read(crva, 24))
            if values[0] != 1 or values[1] != object_offset or values[3] != type_rva or values[5] != crva:
                raise ValueError(f"COL differs: {cls}")
            if struct.unpack("<Q", read(vrva - 8, 8))[0] != pe.image_base + crva:
                raise ValueError(f"vtable COL differs: {cls}")
        primary = struct.unpack("<18Q", read(vt, 18 * 8))
        secondary = struct.unpack("<5Q", read(secondary_vt, 5 * 8))
        if secondary[1] != pe.image_base + execute:
            raise ValueError(f"secondary execute slot differs: {cls}")
        commands.append({"class": cls, "type_descriptor_rva": hex(type_rva),
                         "primary_col_rva": hex(col), "primary_vtable_rva": hex(vt),
                         "primary_functions": [hex(v - pe.image_base) for v in primary],
                         "secondary_object_offset": 24, "secondary_col_rva": hex(secondary_col),
                         "secondary_vtable_rva": hex(secondary_vt),
                         "secondary_functions": [hex(v - pe.image_base) for v in secondary]})
    stock, stock_dump = [], []
    for relative, first, last in STOCK_WINDOWS:
        raw = (game / relative).read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        selected = lines[first - 1:last]
        if len(selected) != last - first + 1:
            raise ValueError(f"missing stock window: {relative}:{first}-{last}")
        stock.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                      "first_line": first, "last_line": last, "text": "\n".join(selected)})
        stock_dump.append(f"\n{relative}:{first}-{last}")
        stock_dump.extend(f"{line}: {lines[line - 1]}" for line in range(first, last + 1))
    return {"schema": "ck3_12002_religion_conversion_outcome_research_v1", "game_version": "1.20.0.2",
            "executable_sha256": EXACT_SHA, "executable_size": len(data), "readiness": "research",
            "native_source_status": "static-confirmed", "local_ck3_touched": False,
            "conversion_submitted": False, "provider_implemented": False, "live_verified": False,
            "native_spans": spans, "semantic_instructions": sites, "command_rtti_vtables": commands,
            "stock_evidence": stock,
            "unresolved": ["Rite+0x788 doctrine row status names (retain actual nonzero condition)",
                           "directional hostility breakdown and conversion-only opinion contribution",
                           "native cooldown flag expiry getter (reuse final-gate owner)",
                           "independent county/family after-read provider",
                           "actual delayed event dispatch, selected narrative option and cold persistence"]}, \
           "\n".join(dump) + "\n", "\n".join(stock_dump) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    args = p.parse_args()
    result, native, stock = extract(args.exe, args.game)
    if args.record:
        MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif result != json.loads(MANIFEST.read_text(encoding="utf-8")):
        raise ValueError("reviewed conversion outcome evidence differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "native-disassembly.txt").write_text(native, encoding="utf-8")
    (args.output_dir / "stock-evidence.txt").write_text(stock, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "research", "native_source_status": "static-confirmed",
               "local_ck3_touched": False, "conversion_submitted": False, "live_verified": False,
               "executable_sha256": EXACT_SHA, "complete_function_bodies": len(SPANS),
               "semantic_instructions": len(SITES), "command_rtti_vtables": len(COMMANDS),
               "stock_windows": len(STOCK_WINDOWS),
               "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "native_disassembly_sha256": hashlib.sha256(native.encode()).hexdigest(),
               "stock_evidence_sha256": hashlib.sha256(stock.encode()).hexdigest()}
    (args.output_dir / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
