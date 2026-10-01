"""Extract the saved R6 event-admission incident; never access a live process."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def snapshot_fields(value: dict[str, object]) -> dict[str, object]:
    keys = (
        "snapshot_id", "revision", "native_revision", "date_raw", "paused",
        "map_ready", "played_character", "active_event", "backend_id", "source",
    )
    return {key: value.get(key) for key in keys}


def source_pin(source: Path, candidate: Path, relative: str,
               spans: list[tuple[int, int]]) -> dict[str, object]:
    path = source / relative
    other = candidate / relative
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return {
        "relative_path": relative,
        "r6_source_path": str(path),
        "r6_source_sha256": digest(path),
        "candidate_source_sha256": digest(other),
        "candidate_byte_identical": path.read_bytes() == other.read_bytes(),
        "spans": [
            {
                "first_line": first,
                "last_line": last,
                "text": "\n".join(lines[first - 1:last]),
            }
            for first, last in spans
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    b = args.artifact_root
    early = "construction-live-next/root-r6-fresh-material-01/snapshot-before.json"
    sdk = "targeted-sdk-r6/r6-current-event14-context-20261001T115859Z"
    fresh = "construction-live-next/root-r6-fresh-material-02"
    law = "targeted-sdk-r6/r6-crown-action-readonly-20261001T120433Z"
    paths = [early, f"{sdk}/plan.json"]
    paths += [f"{sdk}/{name}" for name in (
        "001-ck3_take_snapshot.json", "002-ck3_take_snapshot.json",
        "003-ck3_query_current_event_window_context_v1.json",
        "004-ck3_take_snapshot.json",
    )]
    paths += [f"{fresh}/{name}" for name in (
        "snapshot-before.json", "snapshot-after.json", "summary.json",
        "query-source.json",
    )]
    paths += [f"{law}/result.json"]
    artifacts = [
        {"relative_path": rel, "path": str(b / rel), "sha256": digest(b / rel)}
        for rel in paths
    ]
    observations = [
        {"artifact": early, "snapshot": snapshot_fields(read_json(b / early))}
    ]
    for name in ("001-ck3_take_snapshot.json", "002-ck3_take_snapshot.json",
                 "004-ck3_take_snapshot.json"):
        rel = f"{sdk}/{name}"
        packet = read_json(b / rel)["packet"]
        observations.append({
            "artifact": rel,
            "is_error": packet.get("isError"),
            "snapshot": snapshot_fields(packet["structuredContent"]),
        })
    query = read_json(b / f"{sdk}/003-ck3_query_current_event_window_context_v1.json")
    pins = [
        source_pin(args.source_root, args.candidate_root,
                   "ck3_autonomous_player/native_bridge/src/ck3_12002_adapter.cpp",
                   [(95, 105), (107, 125), (153, 171), (412, 417)]),
        source_pin(args.source_root, args.candidate_root,
                   "ck3_autonomous_player/native_bridge/src/bridge.cpp",
                   [(4693, 4709), (9858, 9862), (10289, 10332),
                    (10440, 10445), (10868, 10875), (10926, 10928),
                    (10939, 10971), (11132, 11137), (11304, 11312),
                    (11414, 11417)]),
        source_pin(args.source_root, args.candidate_root,
                   "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                   [(863, 868), (882, 907), (1007, 1034), (2426, 2439),
                    (21987, 22009)]),
        source_pin(args.source_root, args.candidate_root,
                   "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
                   [(10277, 10349)]),
    ]
    report = {
        "schema": "event12002_r6_event_adapter_saved_review_v1",
        "scope": "Saved evidence and source routes only; no live read or new test.",
        "exact_game_build": {
            "version": "1.20.0.2",
            "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        },
        "artifacts": artifacts,
        "observations": observations,
        "sdk_request": {
            "arguments": query["arguments"],
            "is_error": query["packet"]["isError"],
            "message": query["packet"]["content"][0]["text"],
            "admission_location": "bridge/service.py:10327-10332",
            "native_event_context_executed": False,
        },
        "later_root_material": {
            "construction_summary": read_json(b / f"{fresh}/summary.json"),
            "construction_source_status": read_json(b / f"{fresh}/query-source.json").get("status"),
            "law_sdk_result": read_json(b / f"{law}/result.json"),
        },
        "source_pins": pins,
        "conclusions": {
            "verified": [
                "Saved early native:5 has event 14; SDK snapshots native:8 have active_event=null at the same date_raw 53169336.",
                "SDK request event 14 / public revision 2 is rejected before execute_step in the existing service admission.",
                "Public revision is a Python client state counter; native_revision is copied from the received native frame revision.",
                "The current adapter binds new EventsBindings and ReadEventsSnapshot; publication serializes Snapshot active-event fields directly.",
                "The 1.20.0.2 typed route precedes the old event route; reuse of the old parser/step identity does not select the old native reader.",
                "Root later saved construction source native:10 and law SDK native:11 success; the current blocker is cleared.",
            ],
            "not_proved": [
                "The precise cause of the early event-14 observation.",
                "A defective cache implementation, native event ABI, or mixed-version callback.",
                "Positive native event-window context execution in this failed SDK attempt.",
            ],
            "production_changes": [],
            "further_abi_or_vm_read": "Stopped by root steering; no new plan.",
            "tests": "None added or run; only existing saved evidence extracted.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "artifacts": len(artifacts), "source_pins": len(pins)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
