"""Freeze and verify the Sway repeat-phase contract from exact offline inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage
from ck3_12002_nonwar_event_sources import SourceTree, assignments, portable_definition

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ANCHORS = (
    ("script_value_registration", 0x5975E1, "488d05d8fb1204"),
    ("script_value_factory_thunk", 0x2B3EC50, "e9ab090000"),
    ("script_value_factory_vtable", 0x2B3F641, "488d0578b2c801"),
    ("script_value_typed_scheme", 0x2B3C2DC, "66833809"),
    ("script_value_full_scheme_id", 0x2B3C319, "44394110"),
    ("script_value_native_getter", 0x2B3C326, "e8d5e0f0ff"),
    ("chance_cached_max", 0x2A4A42E, "488b8b48030000"),
    ("chance_growth", 0x2A4A435, "488b8388020000"),
    ("chance_cached_base", 0x2A4A43C, "48038338030000"),
    ("chance_signed_clamp", 0x2A4A443, "483bc8"),
    ("chance_signed_min", 0x2A4A446, "480f4cc1"),
    ("chance_out", 0x2A4A44A, "488907"),
    ("chance_recalculate", 0x2A4A469, "e8520e0000"),
    ("chance_recalculated_growth", 0x2A4A46E, "488b9388020000"),
    ("default_hundred_percent", 0x2A49199, "48c7874803000080969800"),
    ("ui_hundred_percent_clamp", 0x13CEA81, "4981ff80969800"),
    ("progress_advance_goal", 0x2A4F2D2, "448b8150030000"),
    ("progress_advance_value", 0x2A4F2D9, "8b4978"),
    ("progress_advance_delta", 0x2A4F2DE, "03ca"),
    ("phase_pending_marker", 0x2A4F2F4, "c6837002000001"),
    ("phase_callback_field", 0x2A4F377, "4881c198040000"),
    ("phase_callback_execute", 0x2A4F383, "e8f863d100"),
    ("phase_progress_zero", 0x2A4F3F1, "897378"),
    ("opportunity_phase_counter", 0x2A4F3F4, "ff8394020000"),
    ("opportunity_period_compare", 0x2A4F404, "3b88d0080000"),
    ("opportunity_increment", 0x2A4F414, "e8e7210000"),
    ("opportunity_phase_counter_zero", 0x2A4F419, "89b394020000"),
    ("opportunity_basic_gate", 0x2A5162B, "80b84e0a000000"),
    ("opportunity_basic_skip", 0x2A51632, "0f85a2010000"),
    ("reset_registration", 0x5CFA01, "488d0520232804"),
    ("reset_growth_zero", 0x2D10A6B, "48898888020000"),
    ("reset_opportunities_zero", 0x2D10A72, "898898020000"),
    ("reset_progress_zero", 0x2D10A78, "894878"),
)
SPECS = (
    ("common/schemes/scheme_types/sway_scheme.txt", "sway"),
    ("common/on_action/schemes/sway_on_actions.txt", "sway_success"),
    ("common/on_action/schemes/sway_on_actions.txt", "sway_failure"),
    ("common/scripted_effects/00_scheme_scripted_effects.txt", "sway_end_effect"),
    ("common/scripted_effects/00_scheme_scripted_effects.txt", "reset_failed_scheme_effect"),
    ("common/script_values/00_scheme_values.txt", "sway_max_value"),
    ("common/script_values/00_scheme_values.txt", "sway_opinion_increase_per_success"),
)
SPANS = ((0x2A4A400, 0x2A4A496), (0x2B3C2D0, 0x2B3C334),
         (0x2A4F2B0, 0x2A4F4B5), (0x2D10A20, 0x2D10A7C))


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def collect(exe: Path, game_root: Path) -> dict:
    data = exe.read_bytes()
    require(hashlib.sha256(data).hexdigest().upper() == EXE_SHA256, "Frozen executable mismatch")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    native = []
    for name, rva, expected in ANCHORS:
        encoded = bytes.fromhex(expected)
        offset = pe.rva_to_offset(rva)
        require(data[offset:offset + len(encoded)] == encoded, "Native anchor mismatch: " + name)
        instruction = next(decoder.disasm(encoded, rva))
        native.append({"name": name, "rva": hex(rva), "bytes": expected,
                       "instruction": instruction.mnemonic + " " + instruction.op_str})
    for table, index, function in ((0x47CA8C0, 32, 0x2B3C2D0), (0x48529C8, 24, 0x2D10A20)):
        pointer = struct.unpack_from("<Q", data, pe.rva_to_offset(table) + index * 8)[0]
        require(pointer - pe.image_base == function, "Native virtual edge mismatch")
    tree = SourceTree(game_root)
    stock = {}
    for path, key in SPECS:
        definition = tree.definition(path, key)
        row = portable_definition(definition)
        _, text, _ = tree.read(path)
        tokens = definition["token_objects"]
        row["source"] = text[tokens[0].offset:tokens[-1].end].replace("\r\n", "\n").replace("\r", "")
        stock[key] = row
    scheme = tree.definition(SPECS[0][0], "sway")
    names = {name for name, _ in assignments(scheme["token_objects"][3:-1])}
    require("on_phase_completed" in names and "on_invalidated" in names, "Stock callback fields mismatch")
    require("on_end" not in names, "Stock Sway now adds an on_end callback")
    require("base_progress_goal = 365" in stock["sway"]["source"], "Stock basic phase goal mismatch")
    require("is_basic = yes" in stock["sway"]["source"], "Stock basic Sway mismatch")
    require("reset_scheme_progress = yes" in stock["reset_failed_scheme_effect"]["source"], "Stock reset mismatch")
    end = stock["sway_end_effect"]["source"]
    require(all(token in end for token in ("modifier = scheme_sway_opinion", "value >= sway_max_value",
        "reset_failed_scheme_effect = yes", "is_ai = yes", "title = sway_complete", "end_scheme = yes")),
        "Stock phase/terminal branch mismatch")
    spans = []
    for first, last in SPANS:
        offset = pe.rva_to_offset(first)
        spans.append({"start_rva": hex(first), "end_rva": hex(last),
                      "sha256": hashlib.sha256(data[offset:offset + last - first]).hexdigest()})
    return {"schema": "xar.ck3.sway-completion-phase-contract.v1", "status": "GREEN",
        "game_version": "1.20.0.2", "executable_sha256": EXE_SHA256,
        "readiness": "static-ready", "live_verified": False, "ck3_touched": False,
        "stock": stock, "anchors": native, "native_spans": spans,
        "virtual_edges": [{"vtable_rva": "0x47ca8c0", "slot_offset": "0x100", "function_rva": "0x2b3c2d0"},
                          {"vtable_rva": "0x48529c8", "slot_offset": "0xc0", "function_rva": "0x2d10a20"}],
        "provider_contract": {
            "success_chance_getter_rva": "0x2a4a400",
            "success_chance_signature": "int64_t* __fastcall(const CActiveScheme*, int64_t* out)",
            "success_chance_return": "same out pointer", "success_chance_scale": 100000,
            "success_chance_unit": "percentage points", "success_chance_input_only": True,
            "phase_success_not_inferred": True, "instance_terminal_not_inferred": True,
            "native_progression_rva": "0x2a4f2b0",
            "native_phase_callback_field": "+0x498 on scheme type; invoked at phase goal",
            "reset_fields": {"growth": "int64 +0x288", "opportunities": "int32 +0x298", "progress": "int32 +0x78"},
            "opportunity_cycle_counter": "int32 +0x294; increments and resets; not a Sway outcome/history counter",
            "hidden_phase_result_dependency": "exact event/message result with actor, target and full SchemeID",
            "end_dependency": "actual native terminal state plus exact branch/source and independent material readback"}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = collect(args.exe, args.game_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "anchors": len(result["anchors"]),
        "stock_blocks": len(result["stock"]), "native_spans": len(result["native_spans"]),
        "virtual_edges": len(result["virtual_edges"]), "live_verified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
