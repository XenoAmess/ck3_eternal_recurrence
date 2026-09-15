"""Controlled, read-only G2-M4 query in an already owned native driver process.

Call ``run_owned_paused_player_view_read(driver, frozen, artifact_path)`` from
the CK3 owner's Python process. This module never starts CK3 or a named-pipe
server, opens a GUI, submits a construction action, or registers a capability.
The private step is intentionally absent from NativeHeadlessGameplayDriver's
public action steps; this one bounded acceptance read sends the protocol frame
through that driver's existing endpoint.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


ROOT_STEP = "query-campaign-root-context-v1"
PRIVATE_STEP = "g2_player_construction_view_probe_v1"
EXACT_EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _frame_binding(snapshot: dict[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "played_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "played_character_alive": played.get("alive") if isinstance(played, dict) else None,
        "active_war_count": len(snapshot["active_wars"]) if isinstance(snapshot.get("active_wars"), list) else None,
        "player_army_count": len(snapshot["player_armies"]) if isinstance(snapshot.get("player_armies"), list) else None,
        "active_event": snapshot.get("active_event"),
        "pending_character_interaction": snapshot.get("pending_character_interaction"),
    }


def _scene_issue(binding: dict[str, object]) -> str | None:
    if binding["paused"] is not True or binding["map_ready"] is not True:
        return "not_paused_map_ready"
    if not _positive_int(binding["native_revision"]) or not isinstance(binding["snapshot_id"], str):
        return "missing_native_frame_binding"
    if not _positive_int(binding["played_character_id"]) or binding["played_character_alive"] is not True:
        return "no_live_played_actor"
    if not isinstance(binding["date_raw"], int) or isinstance(binding["date_raw"], bool):
        return "missing_date"
    if binding["active_war_count"] != 0 or binding["player_army_count"] != 0:
        return "not_peaceful_or_residual_army"
    if binding["active_event"] is not None or binding["pending_character_interaction"] is not None:
        return "forced_pending_state"
    return None


def _read_step(driver: Any, step: str, revision: int, timeout_seconds: float) -> tuple[str, dict[str, object] | None]:
    request_id = f"g2m4-read-{uuid.uuid4().hex}"
    driver.endpoint.send({
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": step,
        "expected_revision": revision,
    })
    frame = driver.state.wait_for_command_result(request_id, timeout_seconds)
    if frame is None:
        return request_id, None
    if frame.get("type") != "command_result" or frame.get("request_id") != request_id or frame.get("protocol_version") != 1:
        raise ValueError(f"{step} returned a malformed command_result")
    return request_id, frame


def _root_issue(result: dict[str, object], binding: dict[str, object], frozen: dict[str, object]) -> str | None:
    if result.get("step") != ROOT_STEP or result.get("accepted") is not True:
        return "campaign_root_query_not_accepted"
    if result.get("status") != "available":
        return "campaign_root_unavailable"
    context = result.get("campaign_root_context")
    if not isinstance(context, dict) or context.get("status") != "available":
        return "campaign_root_context_unavailable"
    if result.get("snapshot_revision") != binding["native_revision"] or context.get("snapshot_revision") != binding["native_revision"]:
        return "campaign_root_stale_frame"
    if context.get("date_raw") != binding["date_raw"] or context.get("player_character_id") != binding["played_character_id"]:
        return "campaign_root_actor_or_date_mismatch"
    if context.get("player_character_alive") is not True:
        return "campaign_root_actor_not_alive"
    government = context.get("government")
    if not isinstance(government, dict) or government.get("key") != "feudal_government":
        return "government_out_of_preview_scope"
    partition = context.get("held_title_partition")
    if not isinstance(partition, list) or not any(
        isinstance(row, dict) and isinstance(row.get("title"), dict)
        and row["title"].get("tier_key") == "county"
        and _positive_int(row["title"].get("title_id")) for row in partition
    ):
        return "no_player_held_county_in_root_partition"
    if not _positive_int(context.get("capital_province_id")):
        return "capital_province_missing"
    provenance = context.get("provenance")
    if not isinstance(provenance, dict) or str(provenance.get("executable_sha256", "")).casefold() != EXACT_EXE_SHA256:
        return "campaign_root_wrong_exact_build"
    if str(frozen.get("ck3_exe_sha256", "")).casefold() != EXACT_EXE_SHA256:
        return "frozen_manifest_wrong_exact_build"
    return None


def _probe_issue(result: dict[str, object], binding: dict[str, object]) -> str | None:
    if result.get("step") != PRIVATE_STEP or result.get("accepted") is not True:
        return "private_probe_not_accepted"
    probe = result.get("private_probe")
    if not isinstance(probe, dict) or probe.get("schema_version") != 1 or probe.get("private_key") != PRIVATE_STEP:
        return "private_probe_payload_missing"
    if probe.get("advertised") is not False or probe.get("failure") != "none" or probe.get("view_present") is not True:
        return "private_probe_view_or_source_unavailable"
    if probe.get("executor_invocations") != 1:
        return "private_probe_executor_not_once"
    if probe.get("snapshot_revision") != binding["native_revision"] or probe.get("date_raw") != binding["date_raw"]:
        return "private_probe_stale_frame"
    visibility = probe.get("holding_view_visibility")
    if not isinstance(visibility, dict) or visibility.get("widget_key") != "holding_view":
        return "private_probe_visibility_receipt_missing"
    if visibility.get("status") == "available":
        if not isinstance(visibility.get("effective_visible"), bool):
            return "private_probe_visibility_receipt_invalid"
    elif visibility.get("status") == "unavailable":
        if visibility.get("effective_visible") is not None:
            return "private_probe_visibility_receipt_invalid"
    else:
        return "private_probe_visibility_receipt_invalid"
    count = probe.get("cached_candidate_count")
    capacity = probe.get("candidate_capacity")
    if not isinstance(count, int) or isinstance(count, bool) or not isinstance(capacity, int) or isinstance(capacity, bool):
        return "private_probe_invalid_candidate_span"
    if count < 0 or capacity < count:
        return "private_probe_invalid_candidate_span"
    if probe.get("status") == "view_candidate_cache_empty" and count == 0:
        return None
    if probe.get("status") == "view_candidate_cache_present" and count > 0:
        return None
    return "private_probe_status_count_mismatch"


def _manifest_complete(frozen: dict[str, object]) -> bool:
    return (
        all(isinstance(frozen.get(key), str) and bool(frozen[key]) for key in (
            "candidate_id", "round_id", "seed", "source_save_path",
            "ck3_exe_path", "native_dll_path", "agent_commit"
        ))
        and all(isinstance(frozen.get(key), str) and len(frozen[key]) == 64 for key in (
            "source_save_sha256", "ck3_exe_sha256", "native_dll_sha256"
        ))
        and isinstance(frozen.get("dlc_mod_load_order"), list)
        and isinstance(frozen.get("configuration"), dict)
    )


def run_owned_paused_player_view_read(
    driver: Any,
    frozen: dict[str, object],
    artifact_path: str | Path,
    *,
    timeout_seconds: float = 12.0,
) -> dict[str, object]:
    """Perform two bounded read-only queries on one owned paused native frame.

    ``frozen`` is the owner's existing run manifest with candidate/round,
    source-save SHA, CK3 EXE SHA, agent/native DLL commits or SHA, and DLC/mod
    configuration. The private native result supplies an application-main
    holding_view visibility receipt bound to the same revision and date.
    Capital province identity is observed, but its holder is not emitted by
    campaign-root v1. Held county holder=played actor is guaranteed by the
    exact native root collector before it emits an available partition.
    """
    if not isinstance(frozen, dict):
        raise TypeError("frozen must be the owner's run manifest dict")
    if not isinstance(timeout_seconds, (float, int)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    artifact = Path(artifact_path)
    record: dict[str, object] = {
        "schema_version": 1,
        "package_id": "G2-M4-PAUSED-PLAYER-VIEW-READ",
        "controlled_query_only": True,
        "advertised": False,
        "frozen": frozen,
        "timeout_seconds_per_query": timeout_seconds,
        "status": "unexecuted",
    }
    try:
        starting = _frame_binding(driver.state.semantic_snapshot())
        record["starting_frame"] = starting
        issue = _scene_issue(starting)
        if issue:
            record.update(status="ineligible_scene", issue=issue)
            return record
        revision = starting["native_revision"]
        root_request_id, root_frame = _read_step(driver, ROOT_STEP, revision, timeout_seconds)
        record["campaign_root_request_id"] = root_request_id
        if root_frame is None:
            record.update(status="timeout", issue="campaign_root_query_timeout")
            return record
        record["campaign_root_frame"] = root_frame
        if root_frame.get("ok") is not True:
            record.update(status="red", issue="campaign_root_query_rejected")
            return record
        root_result = root_frame.get("result")
        if not isinstance(root_result, dict):
            record.update(status="red", issue="campaign_root_result_missing")
            return record
        issue = _root_issue(root_result, starting, frozen)
        if issue:
            record.update(status="ineligible_scene" if issue in {
                "government_out_of_preview_scope", "no_player_held_county_in_root_partition"
            } else "red", issue=issue)
            return record
        middle = _frame_binding(driver.state.semantic_snapshot())
        record["after_root_frame"] = middle
        if middle != starting:
            record.update(status="red", issue="frame_changed_after_root_query")
            return record
        probe_request_id, probe_frame = _read_step(driver, PRIVATE_STEP, revision, timeout_seconds)
        record["private_probe_request_id"] = probe_request_id
        if probe_frame is None:
            record.update(status="timeout", issue="private_probe_timeout")
            return record
        record["private_probe_frame"] = probe_frame
        if probe_frame.get("ok") is not True:
            record.update(status="red", issue="private_probe_rejected")
            return record
        probe_result = probe_frame.get("result")
        if not isinstance(probe_result, dict):
            record.update(status="red", issue="private_probe_result_missing")
            return record
        issue = _probe_issue(probe_result, starting)
        if issue:
            record.update(status="red", issue=issue)
            return record
        ending = _frame_binding(driver.state.semantic_snapshot())
        record["ending_frame"] = ending
        if ending != starting:
            record.update(status="red", issue="frame_changed_after_private_probe")
            return record
        probe = probe_result["private_probe"]
        record["cache_branch"] = probe["status"]
        visibility = probe["holding_view_visibility"]
        record["holding_view_visibility_receipt"] = {
            "snapshot_id": starting["snapshot_id"],
            "native_revision": probe["snapshot_revision"],
            "date_raw": probe["date_raw"],
            **visibility,
        }
        record["closed_county_view_bound"] = (
            visibility["status"] == "available"
            and visibility["effective_visible"] is False
        )
        record["frozen_manifest_complete"] = _manifest_complete(frozen)
        record["held_county_holder_proof"] = "exact campaign_root_context_v1.cpp title holder equality before available partition"
        record["capital_province_holder_observed"] = False
        record["next_read"] = (
            "player_model_holding_enumerator" if probe["status"] == "view_candidate_cache_empty"
            else "typed_row_cost_and_final_can_construct"
        )
        record["status"] = (
            "frozen_manifest_evidence_insufficient" if not record["frozen_manifest_complete"]
            else "cache_branch_observed" if record["closed_county_view_bound"]
            else "closed_view_evidence_insufficient" if visibility["status"] == "unavailable"
            else "open_view_scene"
        )
        return record
    except Exception as error:
        record.update(status="red", issue=f"{type(error).__name__}: {error}")
        return record
    finally:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
