"""Root-only FIRST consumer of the native owned-memory event-trait wire fixture.

Reads the fixture's original state_snapshot files. No SDK, pipe, process or game
access, and no production-live event is represented by these caller-owned rows.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _event_context(snapshot: dict[str, object]) -> dict[str, object]:
    """Existing GREEN event reader's typed input, explicitly offline fixture data."""
    def scope(character_id: int) -> dict[str, object]:
        return {"status": "available", "raw_type_index": 4, "type_key": "character",
            "subtype": 0, "typed_identity": {"status": "available",
                "kind": "character", "character_id": character_id}}

    options = []
    for index in range(3):
        rows = []
        if index < 2:
            rows.append({"kind": "trait", "operation": "add", "trait": {
                "status": "available", "native_id": 100 + index,
                "key": "lifestyle_poet" if index == 0 else "journaller"}})
        if index in (1, 2):
            rows.append({"kind": "stress", "direction": "decrease",
                "magnitude": {"status": "unavailable"}, "affected_by_trait": True,
                "critical": False})
        options.append({"rendered_index": index, "native_option_index": index,
            "shown": True, "enabled": True, "fallback": False, "cancel": False,
            "effect_indicators": {"status": "available", "coverage":
                "played-character-event-icon-indicators-1.20.0.4-v1",
                "complete_effect_set": False, "rows": rows}})
    return {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "event_definition_key": "trait_specific.9001",
        "snapshot_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
        "current_event_instance_id": snapshot["active_event"]["instance_id"],
        "window_match_count": 1, "root_scope": scope(snapshot["played_character"]["character_id"]),
        "saved_scopes": [{"name": "subject", "scope": scope(30400)}],
        "options": options, "readiness": {"event_definition_identity_ready": True,
            "root_scope_ready": True, "saved_scopes_ready": True,
            "option_presentation_ready": True},
        "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1"}}


class _OwnedFrameDriver:
    """Fixture endpoint for the existing production event-selection consumer."""
    command_timeout_seconds = 1.0

    def __init__(self, before: dict[str, object], after: dict[str, object]) -> None:
        self.before = before
        self.after = after
        self.submitted = False
        self.submissions: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.after if self.submitted else self.before)

    def _execute_primitive_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        _require(step == "select-event-option-2", "consumer changed the selected typed step")
        _require(expected_revision == self.before["revision"], "consumer changed public revision")
        self.submissions.append({"step": step, "expected_revision": expected_revision})
        self.submitted = True
        return {"status": "submitted", "scope": "offline_owned_frame_endpoint"}

    def _wait_for_snapshot(self, snapshot, predicate, *, timeout_seconds):
        _require(timeout_seconds == self.command_timeout_seconds and predicate(snapshot),
            "production event-selection consumer did not observe old-instance disappearance")
        return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    sys.path[:0] = [str(source_root / "ck3_autonomous_player" / "src"),
        str(source_root / "tools")]
    from xar_autoplayer.bridge.native_driver import (
        NativeHeadlessGameplayDriver, _semantic_snapshot_from_frame,
    )
    from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
    from xar_autoplayer.vanilla_events.outcome import (
        plan_registered_event_material_postcondition_v1,
        evaluate_registered_event_material_postcondition_v1,
    )

    def load(name: str, public_revision: int) -> dict[str, object]:
        frame = json.loads((args.wire_dir / name).read_text(encoding="utf-8"))
        snapshot = _semantic_snapshot_from_frame(frame)
        # Independent public publication counter, as in NativeProtocolState.
        snapshot.update(native_revision=snapshot["revision"], revision=public_revision,
            episode_run_id="offline-event-trait-pipeline", diagnostics={
                "connection_generation": 1, "bridge_pid": 4242})
        return snapshot

    before = load("before.json", 7)
    closed_only = load("event-closed-without-gain.json", 8)
    gained = load("after-journaller.json", 9)
    _require(before["active_event"] is not None and closed_only["active_event"] is None
        and gained["active_event"] is None, "native fixture did not close the event")
    decision = recommend_registered_vanilla_event_option_v1(
        _event_context(before), played_character_id=before["played_character"]["character_id"],
        snapshot_option_count=before["active_event"]["option_count"], ck3_build="1.20.0.4",
        played_character=before["played_character"])
    _require(decision["status"] == "recommended" and
        decision["selected_native_option_index"] == 1,
        "actual registry consumer did not choose permanent journaller relief")
    expectation = plan_registered_event_material_postcondition_v1(
        decision, before["played_character"], snapshot_id=before["snapshot_id"],
        revision=before["revision"], native_revision=before["native_revision"],
        date_raw=before["date_raw"])
    _require(expectation and expectation["status"] == "ready",
        "native pre-choice membership did not reach the registered material planner")

    def consume(after: dict[str, object]) -> dict[str, object]:
        endpoint = _OwnedFrameDriver(before, after)
        action = NativeHeadlessGameplayDriver._execute_event_option_step(
            endpoint, "select-event-option-2", option_number=2, expected_revision=7)
        _require(len(endpoint.submissions) == 1, "fixture consumer submitted more than once")
        material = evaluate_registered_event_material_postcondition_v1(
            expectation, action["event_selection"])
        return {"action": action, "material": material}

    no_gain = consume(closed_only)
    with_gain = consume(gained)
    _require(no_gain["action"]["event_selection"]["postcondition_verified"] is True
        and no_gain["material"]["status"] == "failed"
        and no_gain["material"]["material_change_observed"] is False,
        "event disappearance was incorrectly credited as persistent material gain")
    _require(with_gain["material"]["status"] == "verified_change"
        and with_gain["material"]["material_change_observed"] is True,
        "native membership gain did not survive publication and Driver retention")
    retained = with_gain["action"]["event_selection"]
    _require(retained["starting_played_character_event_traits"]["snapshot_revision"] == 51
        and retained["ending_played_character_event_traits"]["snapshot_revision"] == 53,
        "Driver replaced native trait revisions with public revisions")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = {"schema": "xar.ck3.player-event-trait-pipeline-first/v1", "status": "GREEN",
        "scope": "offline_native_owned_memory_and_driver_endpoint",
        "source_root": str(source_root), "wire_dir": str(args.wire_dir.resolve()),
        "native_wire_files": ["before.json", "event-closed-without-gain.json", "after-journaller.json"],
        "sdk_calls": 0, "game_actions": 0, "native_rva_invocations": 0,
        "event_context_scope": "offline_typed_fixture_existing_event_reader_not_requalified",
        "decision": decision, "expectation": expectation,
        "event_closed_without_gain": no_gain, "event_closed_with_journaller": with_gain}
    (args.output_dir / "registered-consumer.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("native membership -> public Snapshot -> production Driver -> registered poet outcome GREEN (offline fixture)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
