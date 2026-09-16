"""One bounded LIFE2-only read inside an already owned paused CK3 driver.

This private acceptance read uses the existing native-driver endpoint and
slot43. It never starts CK3, selects a perk, or registers a public capability.
The caller owns CK3 startup, single-instance checks, and process reclamation.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


PRIVATE_STEP = "private-query-player-lifestyle-current-state-v1"
EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _frame(snapshot: dict[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "played_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "played_character_alive": played.get("alive") if isinstance(played, dict) else None,
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
    }


def _state_issue(state: dict[str, object], frame: dict[str, object]) -> str | None:
    if (state.get("private_build") is not True or state.get("advertised") is not False
            or state.get("status") != "available" or state.get("snapshot_id") != frame["snapshot_id"]
            or state.get("public_revision") != frame["native_revision"]
            or state.get("native_revision") != frame["native_revision"]
            or state.get("proof_epoch") != frame["native_revision"]
            or state.get("date_raw") != frame["date_raw"]
            or state.get("player_character_id") != frame["played_character_id"]):
        return "life2_snapshot_frame_or_private_binding_invalid"
    readiness = state.get("readiness")
    if not isinstance(readiness, dict) or any(
            readiness.get(key) is not True for key in (
                "current_focus_ready", "lifestyle_progress_ready",
                "owned_perks_ready", "same_frame_ready")):
        return "life2_current_state_readiness_invalid"
    focus = state.get("current_focus")
    progress = state.get("current_lifestyle_progress")
    owned = state.get("owned_perk_keys")
    if (not isinstance(focus, dict) or focus.get("presence") not in {"present", "absent"}
            or not isinstance(progress, dict) or progress.get("presence") not in {"present", "absent"}
            or not isinstance(owned, list) or any(not isinstance(key, str) or not key for key in owned)):
        return "life2_focus_progress_or_owned_perks_unknown"
    if focus["presence"] == "present" and any(
            not isinstance(focus.get(key), str) or not focus[key]
            for key in ("key", "lifestyle_key")):
        return "life2_present_focus_identity_unknown"
    if progress["presence"] == "present" and (
            not isinstance(progress.get("lifestyle_key"), str)
            or not progress["lifestyle_key"]
            or any(not _nonnegative_int(progress.get(key)) for key in (
                "xp_total_raw", "xp_within_level_raw", "unspent_perk_points", "used_perk_points"))
            or not _positive_int(progress.get("xp_per_level"))):
        return "life2_present_progress_or_points_unknown"
    for key in ("legal_focus_candidates", "legal_perk_candidates"):
        candidates = state.get(key)
        if (not isinstance(candidates, dict) or candidates.get("status") != "unavailable"
                or candidates.get("reason") != "lifestyle_window_unavailable"
                or candidates.get("items") != []):
            return "life2_final_candidates_promoted_or_untyped"
    return None


def run_owned_paused_life2_current_state_read(
    driver: Any,
    episode_run_id: str,
    frozen: dict[str, object],
    artifact_path: str | Path,
    *,
    timeout_seconds: float = 60.0,
) -> dict[str, object]:
    """Read a real current state once; retain unknowns and independent frame.

    The expected actor/date/revision are read from the current paused native
    frame. An ordinary window-unbound scene is qualified by the caller; LIFE2
    alone does not inspect a GUI window or prove final candidate legality.
    """
    artifact = Path(artifact_path)
    record: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_life2_paused_read_v1",
        "controlled_private_query_only": True,
        "public_advertised": False,
        "gameplay_actions": 0,
        "native_step": PRIVATE_STEP,
        "frozen": frozen,
        "timeout_seconds": timeout_seconds,
        "status": "unexecuted",
        "window_binding": "not_observed_by_life2",
    }
    try:
        if (not isinstance(episode_run_id, str) or not episode_run_id
                or not isinstance(frozen, dict) or not isinstance(timeout_seconds, (int, float))
                or isinstance(timeout_seconds, bool) or timeout_seconds <= 0):
            raise ValueError("LIFE2 query contract input invalid")
        starting = _frame(driver.state.semantic_snapshot())
        record["starting_frame"] = starting
        if (starting["paused"] is not True or starting["map_ready"] is not True
                or starting["played_character_alive"] is not True
                or not _positive_int(starting["native_revision"])
                or starting["snapshot_id"] != "native:" + str(starting["native_revision"])
                or not _positive_int(starting["played_character_id"])
                or not _nonnegative_int(starting["date_raw"])):
            record.update(status="ineligible_scene", issue="paused_actor_or_frame_unknown")
            return record
        request_id = "g2m4-life2-" + uuid.uuid4().hex
        request = {
            "type": "execute_step", "protocol_version": 1,
            "request_id": request_id, "step": PRIVATE_STEP,
            "expected_snapshot_id": starting["snapshot_id"],
            "expected_revision": starting["native_revision"],
            "expected_date_raw": starting["date_raw"],
            "expected_player_character_id": starting["played_character_id"],
            "episode_run_id": episode_run_id,
        }
        record["request"] = request
        driver.endpoint.send(request)
        response = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
        record["response"] = response
        if response is None:
            record.update(status="timeout", issue="life2_private_query_timeout")
            return record
        if (not isinstance(response, dict) or response.get("type") != "command_result"
                or response.get("protocol_version") != 1 or response.get("request_id") != request_id):
            raise ValueError("LIFE2 private command_result envelope malformed")
        if response.get("ok") is not True:
            record.update(status="red", issue="life2_private_query_rejected")
            return record
        result = response.get("result")
        if (not isinstance(result, dict) or result.get("step") != PRIVATE_STEP
                or result.get("private_build") is not True
                or result.get("advertised") is not False
                or result.get("status") != "available"
                or result.get("episode_run_id") != episode_run_id):
            raise ValueError("LIFE2 private result or episode binding malformed")
        state = result.get("snapshot")
        if not isinstance(state, dict):
            raise ValueError("LIFE2 typed snapshot absent")
        issue = _state_issue(state, starting)
        if issue:
            record.update(status="red", issue=issue)
            return record
        after = _frame(driver.state.semantic_snapshot())
        record["independent_after_frame"] = after
        if after != starting:
            record.update(status="red", issue="life2_read_changed_or_drifted_paused_frame")
            return record
        progress = state["current_lifestyle_progress"]
        record["observed"] = {
            "focus": state["current_focus"],
            "lifestyle_progress": progress,
            "owned_perk_keys": state["owned_perk_keys"],
            "final_candidates": "unavailable_not_queried",
        }
        record["status"] = (
            "state_observed_final_candidates_unavailable"
            if progress["presence"] == "present"
            else "typed_absent_progress_evidence_insufficient"
        )
    except Exception as error:
        record.update(status="red", issue=f"{type(error).__name__}: {error}")
    finally:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    return record
