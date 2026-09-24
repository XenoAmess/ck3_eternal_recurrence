"""Bind one native scheduled phase row to the day-26 battle event.

This proves the loaded row identity, not its internal effect draw tape or a
whole-battle win distribution. Source runs remain immutable outside the repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.phase_event_manifest import (  # noqa: E402
    load_stock_phase_event_manifest,
)

SOURCE_CHECKPOINT_SHA256 = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
TARGET_ID = 33437
REGIMENT_ID = 65
KILLER_ID = 34120
ROW_INDEX = 11
EVENT_KEY = "knight_killed"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _receipt(run: Path, stem: str) -> tuple[dict, str]:
    path = run / "ck3-output/interactive-requests-responses" / f"{stem}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native response incomplete: {stem}")
    return raw["body"], digest(path)


def project(run: Path, build_cache: Path, bridge_dll: Path) -> dict[str, object]:
    run = run.resolve()
    copied = json.loads((run / "ck3-output/checkpoint-copy.json").read_text(encoding="utf-8"))
    if (copied["source"]["save"]["sha256"].upper() != SOURCE_CHECKPOINT_SHA256
            or copied["old_attempt_modified"] is not False):
        raise ValueError("restored source checkpoint identity drifted")
    cache = build_cache.read_text(encoding="utf-8", errors="replace")
    if ("CMAKE_BUILD_TYPE:STRING=Release" not in cache
            or "XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1:BOOL=ON"
            not in cache):
        raise ValueError("new mapped-row bridge is not the Release trace build")
    v3, v3_sha = _receipt(run, "004-v3")
    phase = v3["combat_simulation_inputs"]["phase_event_inputs"]
    if (v3["status"] != "available" or phase["status"] != "available"
            or v3["combat_simulation_inputs"]["completeness"]["phase_event_inputs_ready"] is not True):
        raise ValueError("same-process v3 inputs unavailable")
    manifest = load_stock_phase_event_manifest()
    row = next((row for row in manifest.event_rows if row.global_load_index == ROW_INDEX), None)
    if row is None or row.key != EVENT_KEY or row.event_type != "knight":
        raise ValueError("stock event load order changed")
    if phase["rules_manifest_sha256"].upper() != manifest.canonical_manifest_sha256.upper():
        raise ValueError("v3 input and stock event manifest disagree")
    contexts = [
        context for context in phase["evaluation_contexts"]
        if context["root_character_id"] == TARGET_ID
    ]
    if (len(contexts) != 1 or contexts[0]["root_source_regiment_id"] != REGIMENT_ID
            or contexts[0]["combat_side_index"] != 1):
        raise ValueError("target pre-event native context drifted")
    finish, trace_sha = _receipt(run, "007-finish")
    trace = finish["managed_trace"]["trace"]
    records = trace["records"]
    if (finish["status"] != "bounded_trace_available"
            or trace["failure_flags"] != 0 or len(records) != 7
            or [record["capture_failure_flags"] for record in records] != [0] * 7
            or trace["readiness"]["loaded_event_row_identity_map_available"] is not True
            or trace["readiness"]["bounded_capture_complete"] is not True
            or trace["readiness"]["full_mutable_transition_bundle_complete"] is not False):
        raise ValueError("mapped-row seven-boundary trace incomplete")
    scheduled = []
    for index, record in enumerate(records):
        rows = record["sides"][1]["scheduled_knights"]
        if index == 0:
            if rows:
                raise ValueError("pre-schedule side already has a knight event")
            continue
        if (len(rows) != 1 or rows[0]["regiment_id"] != REGIMENT_ID
                or rows[0]["native_event_load_index"] != ROW_INDEX
                or rows[0]["current_character_id"] !=
                (TARGET_ID if index < 6 else -1)):
            raise ValueError("selected native row or stale schedule identity changed")
        scheduled.append(rows[0])
    tokens = {row["event_identity_token"] for row in scheduled}
    if len(tokens) != 1:
        raise ValueError("event object identity drifted across boundaries")
    expected_event = {
        "left_character_id": TARGET_ID,
        "right_character_id": KILLER_ID,
        "stable_key": "knight_killed_by_enemy",
        "type_raw": 3,
        "side_index": 1,
        "target_right": False,
    }
    if (records[5]["battle_events"] != records[4]["battle_events"] + [expected_event]
            or records[6]["battle_events"] != records[5]["battle_events"]):
        raise ValueError("same-row battle event append drifted")
    target_before = next(c for c in records[5]["characters"] if c["character_id"] == TARGET_ID)
    target_after = next(c for c in records[6]["characters"] if c["character_id"] == TARGET_ID)
    if (target_before["death_marker_present"] is not False
            or target_after["death_marker_present"] is not True
            or target_before["prowess"] != 4 or target_after["prowess"] != 2
            or any(k["regiment_id"] == REGIMENT_ID for k in records[6]["sides"][1]["knights"])):
        raise ValueError("post-fire death and detachment changed")
    after_save, after_save_sha = _receipt(run, "008-after-save")
    if after_save["checkpoint"]["date_raw"] != 53146872:
        raise ValueError("post-event save date drifted")

    return {
        "schema": "xar.ck3.episode01.selected-phase-event-row/v1",
        "game_build": "CK3 1.19.0.6",
        "capture_run": str(run),
        "restored_source_save_sha256": SOURCE_CHECKPOINT_SHA256,
        "release_build_cache_sha256": digest(build_cache),
        "release_bridge_dll_sha256": digest(bridge_dll),
        "v3_response_sha256": v3_sha,
        "trace_response_sha256": trace_sha,
        "after_save_receipt_sha256": after_save_sha,
        "after_native_save_sha256": after_save["checkpoint"]["sha256"].upper(),
        "stock_phase_event_manifest_sha256": manifest.canonical_manifest_sha256,
        "combat_id": 16777218,
        "source_day": 26,
        "target_character_id": TARGET_ID,
        "target_regiment_id": REGIMENT_ID,
        "native_event_global_load_index": ROW_INDEX,
        "native_event_key": EVENT_KEY,
        "native_selected_row_observed": True,
        "scheduled_event_identity_token": next(iter(tokens)),
        "mapped_boundaries": [1, 2, 3, 4, 5, 6],
        "appended_battle_event": expected_event,
        "event_appended_between_boundaries": [4, 5],
        "death_and_detachment_observed_at_boundary": 6,
        "target_derived_prowess_before_and_after": [4, 2],
        "native_effect_internal_draws_observed": False,
        "full_event_write_set_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--build-cache", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.run, args.build_cache, args.bridge_dll)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
