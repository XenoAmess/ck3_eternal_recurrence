"""Print a non-admitting, read-only schema summary of a candidate phase-trace receipt."""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    args = parser.parse_args()
    source = args.receipt.read_bytes()
    payload = json.loads(source)
    if not isinstance(payload, dict):
        raise ValueError("Trace candidate must have a JSON object envelope")
    body = payload.get("body") if isinstance(payload.get("body"), dict) else {}
    managed = body.get("managed_trace") if isinstance(body.get("managed_trace"), dict) else {}
    trace = managed.get("trace") if isinstance(managed.get("trace"), dict) else {}
    records = trace.get("records") if isinstance(trace.get("records"), list) else []
    source_shape_supported = (
        payload.get("result") == "CALL_COMPLETED"
        and body.get("step") == "experimental-combat-phase-event-trace-finish-v1"
        and managed.get("schema_version") == 1
        and trace.get("schema_version") == 1
        and isinstance(trace.get("records"), list)
    )
    summary = {
        "admission": False,
        "observation_only": True,
        "source_shape_supported": source_shape_supported,
        "target_33437_day27_life_status": "UNKNOWN",
        "life_status_reason": "no targeted paused-day query or strict same-run saved-state reader",
        "source": str(args.receipt.resolve()),
        "bytes": len(source),
        "sha256": hashlib.sha256(source).hexdigest().upper(),
        "result": payload.get("result"),
        "body_status": body.get("status"),
        "body_keys": sorted(body),
        "managed_keys": sorted(managed),
        "trace_keys": sorted(trace),
        "trace_status": trace.get("status"),
        "failure_flags": trace.get("failure_flags"),
        "record_count": trace.get("record_count"),
        "records_len": len(records),
        "knight_selects_presence": "knight_selects" in trace,
        "knight_selects_len": len(trace.get("knight_selects") or []),
        "counter_outputs_presence": "counter_outputs" in trace,
        "effect_roots_presence": "effect_roots" in trace,
        "record_boundaries": [row.get("boundary") for row in records],
        "record_failure_flags": [row.get("capture_failure_flags") for row in records],
        "target_33437_by_boundary": [
            {"boundary": row.get("boundary"), "date_raw": row.get("native_date_raw"),
             "character": next((item for item in row.get("characters") or []
                                if item.get("character_id") == 33437), None)}
            for row in records
        ],
        "stable_events": sorted({(event.get("stable_key"), event.get("left_character_id"),
                                   event.get("right_character_id"))
                                  for row in records for event in row.get("battle_events") or []
                                  if event.get("stable_key")}),
    }
    if args.bridge_dll is not None:
        dll = args.bridge_dll.read_bytes()
        summary["bridge_dll"] = {
            "path": str(args.bridge_dll.resolve()),
            "bytes": len(dll),
            "sha256": hashlib.sha256(dll).hexdigest().upper(),
            "wire_literal_knight_selects_present": b'knight_selects' in dll,
            "save_checkpoint_capability_present": b'game.command.save-checkpoint' in dll,
        }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
