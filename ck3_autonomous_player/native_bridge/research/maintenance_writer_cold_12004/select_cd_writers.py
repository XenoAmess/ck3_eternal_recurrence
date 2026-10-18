"""Select c/d post-PC candidates from a pinned existing actual-consumer result.

This reads no process, raw watch, EXE or SDK. It grants no producer/fee credit.
"""
import argparse
import hashlib
import json
from pathlib import Path

LIMIT = 8 * 1024 * 1024
OFFSETS = (0x2C0, 0x2C8, 0x28, 0x30)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def select(result):
    need(type(result) is dict, "Actual consumer result object required")
    need(result.get("origin") == "original_files_bound_to_Root_admission",
         "Existing actual consumer origin required")
    need(result.get("known_producer") is False
         and result.get("maintenance_attribution") == "unclosed"
         and result.get("actual_writer_game_date") is None
         and result.get("full_window_all_writes_covered") is False,
         "Source, date or business credit elevated")
    need(type(result.get("Root_binding")) is dict
         and type(result.get("input_pins")) is dict, "Original bindings/pins absent")
    hits, unknown = result.get("qualified_writers"), result.get("unknown_traps")
    need(type(hits) is list and type(unknown) is list, "Original writer arrays absent")
    need(type(result.get("issues")) is list
         and type(result.get("missing_or_unproved_live_restores")) is list,
         "Original issue/restore arrays absent")
    need(type(result.get("cleanup_proved")) is bool, "Cleanup proof missing")
    selected, unresolved = [], []
    for key, rows, destination in (("qualified_writers", hits, selected),
                                    ("unknown_traps", unknown, unresolved)):
        for index, row in enumerate(rows):
            need(type(row) is dict, "Writer object required")
            slot = row.get("slot")
            need(type(slot) is int and 0 <= slot < 4
                 and type(row.get("offset")) is int and row["offset"] == OFFSETS[slot],
                 "Frozen DR slot/offset differs")
            need(row.get("known_producer") is False
                 and row.get("maintenance_attribution") == "unclosed"
                 and row.get("actual_writer_game_date") is None
                 and row.get("writer_instruction_start") is None,
                 "Writer source/date/start elevated")
            if key == "qualified_writers":
                need(row.get("physical_write_qualified") is True
                     and row.get("unavailable_reasons") == [],
                     "Qualified writer contradicted")
            if slot in (2, 3):
                need(type(row.get("RIP_after")) is int and row["RIP_after"] > 0,
                     "Actual post-PC missing")
                destination.append({"source_pointer": "/" + key + "/" + str(index),
                                    "record": row})
    expected_status = ("ACTUAL_WRITERS_SOURCE_UNKNOWN" if hits
                       else "NO_QUALIFIED_WRITER_IN_FINITE_WINDOW")
    partial = bool(result["issues"] or unknown)
    need(result.get("status") == ("PARTIAL_" if partial else "") + expected_status,
         "Consumer status inconsistent")
    need(type(result.get("qualified_slot_count")) is int
         and result["qualified_slot_count"] == len(hits)
         and type(result.get("unknown_slot_count")) is int
         and result["unknown_slot_count"] == len(unknown), "Consumer counts differ")
    clean = (result["cleanup_proved"] is True and not partial
             and not result["missing_or_unproved_live_restores"])
    image_candidates = [x for x in selected
                        if type(x["record"].get("RIP_after_rva")) is int
                        and x["record"]["RIP_after_rva"] >= 0]
    return {
        "schema": "xar.r08.cd-writer-selection.v1",
        "status": ("C_D_POST_PC_AVAILABLE_FOR_BOUNDED_SOURCE" if clean and image_candidates
                   else "C_D_RETAINED_SOURCE_NOT_READY" if selected
                   else "NO_QUALIFIED_C_D_TRAP_RETAINED"),
        "evidence_machine_id": result.get("evidence_machine_id"),
        "Root_binding": result["Root_binding"], "original_input_pins": result["input_pins"],
        "original_consumer_status": result["status"],
        "original_qualified_slot_count": len(hits), "original_unknown_slot_count": len(unknown),
        "selected_c_d_writers": selected, "unresolved_c_d_traps": unresolved,
        "same_image_post_pc_count": len(image_candidates),
        "cleanup_proved": result["cleanup_proved"], "finite_window_clean": clean,
        "finite_window_reason": result.get("finite_window_reason"),
        "source_decode_candidate_available": bool(clean and image_candidates),
        "actual_writer_game_date": None, "known_producer": False,
        "maintenance_attribution": "unclosed", "paid_maintenance_raw": None,
        "same_net_invocation_proved": False, "payer_cadence_proved": False,
        "zero_hit_meaning": "No retained qualified c/d trap; no producer or fee absence inferred.",
        "a_b_records": "Retained unmodified in the pinned original actual-consumer result.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    need(not args.output.exists(), "Create-only output exists")
    need(args.result.stat().st_size <= LIMIT, "Consumer result exceeds 8 MiB")
    raw = args.result.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    need(digest == args.result_sha256, "Pinned actual-consumer result differs")
    selected = select(json.loads(raw.decode("utf-8-sig")))
    selected["actual_consumer_result"] = {
        "path": str(args.result.resolve()), "bytes": len(raw), "sha256": digest}
    selected["runtime_actions_performed"] = 0
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(selected, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": selected["status"],
                      "c_d_count": len(selected["selected_c_d_writers"]),
                      "source_decode_candidate_available": selected["source_decode_candidate_available"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
