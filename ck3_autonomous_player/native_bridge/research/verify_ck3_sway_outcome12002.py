"""Verify frozen file-only Sway scopes/opinion/source contract; never attaches to CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile

from ck3_sway_outcome12002_sources import EXE_SHA, SPECS
from ck3_12002_nonwar_event_sources import SourceTree, portable_definition

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ck3_sway_outcome12002_abi.json"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--installed-game-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--record-contract", action="store_true")
    args = parser.parse_args()
    payload = args.exe.read_bytes()
    if sha(payload) != EXE_SHA:
        raise ValueError("Frozen executable mismatch")
    image = pefile.PE(data=payload, fast_load=True)

    def at(rva: int, length: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return payload[offset:offset + length]

    spans = []
    for name, first, last in [("scheme_scope_type_getter", 0x1B9D650, 0x1B9D656),
                              ("scheme_scope_native_resolver", 0x1B9D670, 0x1B9D72E)]:
        spans.append({"name": name, "start_rva": hex(first), "end_rva": hex(last), "sha256": sha(at(first, last - first))})
    if at(0x1B9D650, 6) != bytes.fromhex("b809000000c3"):
        raise ValueError("Scheme generic type is not nine")
    if struct.unpack("<Q", at(0x4753CE8, 8))[0] - image.OPTIONAL_HEADER.ImageBase != 0x1B9D650:
        raise ValueError("Scheme generic RTTI vtable getter differs")
    gift = json.loads((HERE / "ck3_12002_gift_opinion_abi.json").read_text(encoding="utf-8-sig"))
    shared_names = {"recipient_total_opinion", "find_active_opinion_group", "sum_active_modifier", "opinion_modifier_lookup"}
    for row in gift["native_spans"]:
        if row["name"] not in shared_names:
            continue
        first, last = int(row["rva_start"], 0), int(row["rva_end_exclusive"], 0)
        actual = sha(at(first, last - first))
        if actual != row["sha256"]:
            raise ValueError(f"Shared opinion span changed: {row['name']}")
        spans.append({"name": row["name"], "start_rva": hex(first), "end_rva": hex(last), "sha256": actual,
                      "provenance": "ck3_12002_gift_opinion_abi.json"})
    tree = SourceTree(args.game_root)
    blocks = [portable_definition(tree.definition(path, key)) for path, key in SPECS]
    installed = args.installed_game_root or args.exe.parents[6] / "Crusader Kings III/game"
    supplemental = []
    for relative in ["common/messages/01_scheme_messages.txt", "common/opinion_modifiers/00_scheme_sway_opinions.txt",
                     "gui/event_window_widgets/event_window_widget_scheme.gui"]:
        file = args.game_root / relative
        origin = "frozen installation game"
        if not file.is_file():
            file = installed / relative
            origin = "installed stock supplemental; missing in frozen partial game copy"
        supplemental.append({"relative_path": relative, "file_sha256": sha(file.read_bytes()), "source_origin": origin})
    candidate = {"schema": "xar.ck3.sway-outcome-abi.v1", "build": "1.20.0.2", "exe_sha256": EXE_SHA,
                 "readiness": "static-ready", "live_verified": False,
                 "native_spans": spans, "stock_blocks": blocks, "supplemental_stock_files": supplemental,
                 "scheme_scope": {"type_descriptor_rva": "0x59F3E80", "primary_col_rva": "0x4DFA410",
                                  "primary_vtable_rva": "0x4753CE0", "generic_type_index": 9,
                                  "payload_offset": "0x08", "storage_slot_rva": "0x5D1FC58",
                                  "storage_rows_offset": "0x20", "storage_count_offset": "0x2C",
                                  "storage_row_stride": "0x10", "storage_object_offset": "0x08",
                                  "scheme_full_id_offset": "0x10", "fallback_accepted": False},
                 "native_scheme_join": {"layout_provenance": "ck3_12002_sway_state.cpp and sway_state12002_plan.json",
                                        "instance_vtable_rva": "0x47794E8", "type_pointer_offset": "0x20",
                                        "type_vtable_rva": "0x48B9F20", "owner_id_offset": "0x2C",
                                        "target_kind_offset": "0x30", "character_target_kind": 0,
                                        "target_id_offset": "0x34", "canonical_type_key": "sway"},
                 "current_event_layout_provenance": "existing ck3_12002_event_window_context reader and ABI",
                 "opinion_layout_provenance": "ck3_12002_gift_opinion_abi.json; dedicated scheme_sway_opinion and sway_blocker_opinion keys",
                 "interface": {"step": "query-sway-outcome-event-v1-private",
                               "payload_fields": ["expected_revision", "event_instance_id", "actor_character_id", "target_character_id", "scheme_instance_id"],
                               "result_field": "result.sway_outcome_event",
                               "opinion_step": "query-sway-outcome-opinion-v1-private",
                               "opinion_payload_fields": ["expected_revision", "actor_character_id", "target_character_id"],
                               "opinion_result_field": "result.sway_outcome_opinion"},
                 "terminal_boundary": "presented outcome precedes selection; phase/source projections and modifier measurements never prove instance end or cancel"}
    if args.record_contract:
        CONTRACT.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        expected = json.loads(CONTRACT.read_text(encoding="utf-8"))
        if expected != candidate:
            raise ValueError("Frozen Sway source/native ABI contract differs")
    report = {"status": "GREEN", "exe_sha256": EXE_SHA, "contract_file": str(CONTRACT),
              "contract_sha256": sha(CONTRACT.read_bytes()), "native_span_count": len(spans),
              "stock_block_count": len(blocks), "supplemental_file_count": len(supplemental),
              "read_only": True, "game_process_access": False, "live_verified": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
