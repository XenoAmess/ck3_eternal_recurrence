"""Bounded failure evidence for the existing sentinel pause-boundary verdict.

The owning Driver supplies its actual pure predicates. No verdict, Native query,
game action, retry, or ordinary MCP error text is changed by this observer.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import json
import sys


def record_failure_v1(
    *, step: str, starting: dict[str, object], before_pause: dict[str, object],
    after_pause: dict[str, object], pause_actions: list[dict[str, object]],
    inspected_boundary: dict[str, object] | None, expected_boundary: dict[str, object] | None,
    original_verified_boundary: bool,
    frame_binding: Callable[..., dict[str, object]], boundary_of: Callable[..., dict[str, object] | None],
    same_boundary: Callable[..., bool], fresh_boundary: Callable[..., bool], decision_is_new: Callable[..., bool],
) -> dict[str, object]:
    """Preserve the actual failed operands and call the unchanged predicates.

    Observations are facts, not a duplicated implementation of the verifier.
    In particular, date/actor differences may be valid for a terminal boundary;
    only results from the supplied original predicates are named failures.
    """
    def scalar(value: object) -> object:
        return value[:96] if isinstance(value, str) else value if type(value) in (int, bool) or value is None else None

    def frame(snapshot: dict[str, object]) -> dict[str, object]:
        result = {key: scalar(value) for key, value in frame_binding(snapshot).items()}
        result.update({key: scalar(snapshot.get(key)) for key in (
            "snapshot_id", "revision", "native_revision", "paused", "map_ready")})
        player = snapshot.get("played_character")
        result["played_character_alive"] = scalar(player.get("alive")) if isinstance(player, dict) else None
        return result

    def boundary(value: object) -> dict[str, object] | None:
        return ({key: scalar(value.get(key)) for key in (
            "kind", "instance_id", "observed_date_raw", "terminal_reason", "bridge_pid",
            "connection_generation", "episode_character_id", "episode_run_id", "played_character_id")}
                if isinstance(value, dict) else None)

    before, after = frame(before_pause), frame(after_pause)
    current_boundary = boundary_of(after_pause)
    old_public, new_public = before.get("revision"), after.get("revision")
    old_native, new_native = before.get("native_revision"), after.get("native_revision")
    predicates = {
        "original_verified_boundary": original_verified_boundary,
        "original_fresh_boundary": fresh_boundary(before_pause, after_pause, expected_boundary=expected_boundary),
        "original_decision_is_new": decision_is_new(starting, after_pause),
        "original_expected_boundary_identity": expected_boundary is None or same_boundary(expected_boundary, current_boundary),
    }
    record = {
        "schema": "xar.tactical-pause-boundary-failure.v1", "at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_id": "unknown", "machine_identity_binding": "owning SDK source-epoch stderr capture receipt required",
        "step": step[:256], "status": "original_postcondition_failed", "diagnostic_only": True,
        "starting": frame(starting), "before_pause": before, "after_pause": after,
        "expected_boundary": boundary(expected_boundary), "inspected_boundary": boundary(inspected_boundary),
        "pause_action_count": len(pause_actions), "predicates": predicates,
        "failed_predicates": [key for key, passed in predicates.items() if not passed],
        "observations": {
            "after_paused": after.get("paused") is True, "after_map_ready": after.get("map_ready") is True,
            "date_equal": before.get("observed_date_raw") == after.get("observed_date_raw"),
            "owner_fields_equal": all(before.get(key) == after.get(key) for key in (
                "bridge_pid", "connection_generation", "episode_character_id", "episode_run_id", "played_character_id")),
            "public_revision_increased": type(old_public) is int and type(new_public) is int and new_public > old_public,
            "native_revision_non_decreasing": type(old_native) is int and type(new_native) is int and new_native >= old_native,
        },
        "original_action_replayed": False, "new_native_queries": 0,
    }
    line = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
    if len(line.encode("utf-8")) > 8192:
        record = {key: value for key, value in record.items() if key not in ("expected_boundary", "inspected_boundary")}
        record["boundary_details_omitted_for_log_bound"] = True
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
    try:
        if len(line.encode("utf-8")) <= 8192:
            sys.stderr.write(line + "\n")
            sys.stderr.flush()
    except (OSError, ValueError):
        pass  # An unavailable diagnostic sink must not replace the action error.
    return record
