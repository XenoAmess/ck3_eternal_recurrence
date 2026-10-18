"""Pure post-Continue UI observation; no transaction or action authorization.

Callers supply the existing guarded Service reads and retain their source pins.
This projection cannot establish process ownership, complete an inheritance,
authorize SAVE/Close, select an event, or replace independent post-action reads.
"""
from __future__ import annotations

from collections.abc import Mapping

from ..m5_observed_opportunity_selector import observed_frame
from .event_window_context_contract import normalize_current_event_window_context_v1
from .nonwar_private_build import private_native_build_identity
from .timeline_blocker_context_contract import normalize_current_timeline_blocker_context_v1


def project_successor_ui_observation_v1(snapshot, *, timeline_context, event_context=None):
    """Keep native ``none + open/blocked`` unresolved, including old-root events.

    This is source-only reusable classification. It sends no query and installs
    no ordinary-turn gate. Read availability does not authorize event selection.
    """
    if not isinstance(snapshot, Mapping):
        raise ValueError("successor UI snapshot must be an object")
    frame = observed_frame(snapshot)
    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("episode_identity_pending") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or not isinstance(played, Mapping) or played.get("alive") is not True
            or played.get("character_id") != frame["played_character_id"]
            or snapshot.get("episode_character_id") != frame["played_character_id"]
            or not isinstance(diagnostics, Mapping)
            or type(diagnostics.get("bridge_pid")) is not int or diagnostics["bridge_pid"] <= 0
            or type(diagnostics.get("connection_generation")) is not int
            or diagnostics["connection_generation"] < 0
            or not isinstance(diagnostics.get("hello"), Mapping)
            or "active_event" not in snapshot):
        raise ValueError("successor UI requires a stable paused living successor frame")
    build = private_native_build_identity(snapshot)
    timeline = normalize_current_timeline_blocker_context_v1(
        timeline_context, expected_date_raw=frame["date_raw"],
        expected_snapshot_revision=frame["native_revision"])
    active = snapshot["active_event"]
    event = None
    if active is not None:
        if (not isinstance(active, Mapping) or type(active.get("instance_id")) is not int
                or not 0 < active["instance_id"] < 2**31):
            raise ValueError("successor UI active event identity is incomplete")
        if event_context is not None:
            event = normalize_current_event_window_context_v1(
                event_context, expected_event_instance_id=active["instance_id"],
                expected_date_raw=frame["date_raw"],
                expected_snapshot_revision=frame["native_revision"])
            if event["provenance"]["backend_id"] != build.backend_id("event-window-v1"):
                raise ValueError("successor UI event belongs to another exact build")
    elif event_context is not None:
        raise ValueError("successor UI cannot attach a stale event after its disappearance")

    if timeline["status"] != "available":
        clearance = "unknown"
    elif timeline["identity"] != "none":
        clearance = "modal_present"
    elif (timeline["blocks_simulation"]["value"] is True
          or timeline["has_open_succession"]["value"] is True or active is not None):
        clearance = "unresolved"
    else:
        clearance = "clear"
    return {
        "schema": "xar.ck3.successor-ui-observation/v1",
        "frame": {**frame, "bridge_pid": diagnostics["bridge_pid"],
                  "connection_generation": diagnostics["connection_generation"]},
        "exact_ck3_build": build.game_version, "exe_sha256": build.executable_sha256,
        "ui_clearance": clearance, "timeline": timeline,
        "event_instance_id": active["instance_id"] if active is not None else None,
        "event_context_status": event["status"] if event is not None else "not_observed",
        "event_definition_key": event["event_definition_key"] if event is not None else None,
        # A predecessor-root event can coexist with the living successor. Never
        # rewrite that root to the current player or infer its option effects.
        "event_root_scope": event["root_scope"] if event is not None else None,
        "event_semantic_decision_ready": event["readiness"]["semantic_decision_ready"]
            if event is not None else None,
        "fresh_timeline_read_after_event_required": active is not None,
        "ordinary_event_policy_unchanged": True,
        "caller_owned_process_and_query_source_proof_required": True,
        "authorizes_close_or_save": False, "authorizes_event_selection": False,
        "business_cycle_credit": 0, "action_replay_authorized": False,
    }
