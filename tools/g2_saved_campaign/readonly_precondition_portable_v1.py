"""Pure, parameterized qualifications for a saved-campaign recovery control.

These functions never issue Game commands, clear a pending cycle, or award credit.
The caller must retain immutable source pins and check the Game kernel birth.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Mapping


_REVISION_ERROR = re.compile(
    r"Error executing tool ck3_auto_turn: native gameplay revision mismatch: "
    r"expected ([0-9]{1,19}), current ([0-9]{1,19})"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_revision_mismatch_before_submit(
    row: object,
    *,
    original_response: Path,
    prior_metrics: Path,
    before_plan: Path,
    pinned_sources: Mapping[Path, str],
    driver_mode: Path,
    expected_driver_source: Path,
) -> dict[str, object] | None:
    """Qualify one exact pre-submit error under the caller's frozen source set."""
    if not isinstance(row, dict):
        return None
    request, result = row.get("request"), row.get("result")
    if not (isinstance(request, dict)
            and request.get("tool") == "ck3_auto_turn"
            and request.get("arguments") == {}
            and type(request.get("sequence")) is int and request["sequence"] > 2
            and row.get("client_error") is None
            and isinstance(result, dict) and result.get("is_error") is True
            and result.get("structured_content") is None
            and result.get("result_type") == "complete"):
        return None
    content = result.get("content")
    if not (isinstance(content, list) and len(content) == 1
            and isinstance(content[0], dict) and content[0].get("type") == "text"):
        return None
    match = _REVISION_ERROR.fullmatch(content[0].get("text") or "")
    if match is None:
        return None
    old, new = (int(part) for part in match.groups())
    if str(old) != match[1] or str(new) != match[2] or old < 1 or new != old + 1:
        return None
    sequence = request["sequence"]
    if (original_response.name != f"{sequence:04d}-1-result.json"
            or prior_metrics.name != f"{sequence-1:04d}-1-result.json"
            or before_plan.name != f"{sequence:04d}-0-plan.json"
            or not pinned_sources or before_plan.exists()):
        return None
    try:
        if json.loads(original_response.read_text(encoding="utf-8-sig")) != row:
            return None
        if any(_sha256(Path(path)) != digest for path, digest in pinned_sources.items()):
            return None
        mode = json.loads(driver_mode.read_text(encoding="utf-8-sig"))
        if not (mode.get("driver_class") == "NativeHeadlessGameplayDriver"
                and mode.get("episode_projection") == "one_life"
                and mode.get("before_submit_observation") is True
                and mode.get("policy_replaced") is False
                and mode.get("transport_cap_replaced") is False
                and Path(mode.get("source_file", "")).resolve()
                    == expected_driver_source.resolve()
                and expected_driver_source in pinned_sources):
            return None
        previous = json.loads(prior_metrics.read_text(encoding="utf-8-sig"))
        source_request = previous.get("request") or {}
        if not (source_request.get("sequence") == sequence - 1
                and source_request.get("tool") == "root_current_runtime_metrics"
                and previous.get("result", {}).get("is_error") is False):
            return None
        before = previous["result"]["structured_content"]
        if not (isinstance(before, dict)
                and before.get("revision") == old
                and type(before.get("native_revision")) is int
                and before["native_revision"] > 0
                and before.get("snapshot_id") == f"native:{before['native_revision']}"
                and before.get("actor_alive") is True
                and type(before.get("actor_character_id")) is int
                and before["actor_character_id"] > 0
                and type(before.get("date_raw")) is int
                and isinstance(before.get("episode_run_id"), str)
                and bool(before["episode_run_id"])
                and type(before.get("connection_generation")) is int
                and before["connection_generation"] > 0
                and before.get("paused") is True
                and before.get("map_ready") is True):
            return None
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
    return {
        "classification": "native_revision_changed_before_pre_submit",
        "read_only_precondition": True,
        "business_submission": False,
        "expected_public_revision": old,
        "current_public_revision": new,
        "original_response": str(original_response),
        "before_submit_observation_present": False,
        "failed_native_command_sent": False,
        "source_pins": {str(path): digest for path, digest in pinned_sources.items()},
        "prior_metrics_sha256": _sha256(prior_metrics),
        "fresh_semantic_required_by_control": True,
        "source_guard": "reviewed NativeDriver pre-send revision check and Service pre-business-submit path",
    }


def qualify_observed_successor(
    body: object,
    *,
    before: Mapping[str, object],
    retained_goal: Mapping[str, object],
    expected_lifecycle: Mapping[str, object],
    game_pid: int,
    pipe_name: str,
    expected_adapter_id: str,
    same_game_kernel_birth_verified: bool,
) -> dict[str, object] | None:
    """Admit only a fresh, matched successor frame for the existing handoff.

    A positive result is a read-only preflight, not a Continue action or credit.
    """
    if not (same_game_kernel_birth_verified is True
            and type(game_pid) is int and game_pid > 0
            and isinstance(pipe_name, str) and pipe_name
            and isinstance(expected_adapter_id, str) and expected_adapter_id
            and isinstance(body, dict) and isinstance(before, Mapping)
            and isinstance(retained_goal, Mapping)
            and isinstance(expected_lifecycle, Mapping)):
        return None
    played, diag = body.get("played_character"), body.get("diagnostics")
    if not (body.get("map_ready") is True and body.get("paused") is True
            and body.get("one_life_terminal") is True
            and body.get("one_life_terminal_reason") == "played_character_changed"
            and body.get("succession_lifecycle") == expected_lifecycle
            and expected_lifecycle.get("lifecycle") == "ordinary_campaign_succession"
            and expected_lifecycle.get("xar_enabled") == "xar_off"
            and isinstance(played, dict) and played.get("alive") is True
            and type(played.get("character_id")) is int
            and played["character_id"] > 0
            and isinstance(diag, dict) and diag.get("connected") is True):
        return None
    hello = diag.get("hello")
    if not (isinstance(hello, dict)
            and diag.get("bridge_pid") == hello.get("pid") == game_pid
            and diag.get("pipe_name") == pipe_name
            and type(diag.get("connection_generation")) is int
            and diag["connection_generation"] > 0
            and diag["connection_generation"] == hello.get("connection_generation")
            and hello.get("ck3_build_match") is True
            and hello.get("game_adapter_status") == "ready"
            and hello.get("game_adapter_id") == expected_adapter_id):
        return None
    old_actor, heir = before.get("actor_character_id"), played["character_id"]
    if not (type(old_actor) is int and old_actor > 0 and heir != old_actor
            and retained_goal.get("current_character_id") == old_actor
            and body.get("campaign_goal") == retained_goal
            and body.get("episode_character_id") == old_actor
            and isinstance(before.get("episode_run_id"), str)
            and body.get("episode_run_id") == before["episode_run_id"]
            and type(before.get("date_raw")) is int
            and type(body.get("date_raw")) is int
            and body["date_raw"] >= before["date_raw"]
            and type(before.get("revision")) is int
            and type(body.get("revision")) is int
            and body["revision"] >= before["revision"]
            and type(before.get("native_revision")) is int
            and type(body.get("native_revision")) is int
            and body["native_revision"] >= before["native_revision"]
            and body.get("snapshot_id") == f"native:{body['native_revision']}"):
        return None
    expectation, reconciliation = body.get("succession_expectation"), body.get("succession_reconciliation")
    if not (isinstance(expectation, dict)
            and expectation.get("schema") == "xar.ck3.succession-expectation/v1"
            and expectation.get("status") == "available"
            and expectation.get("expectation_state") == "successor_expected"
            and expectation.get("predecessor_character_id") == old_actor
            and expectation.get("expected_successor_character_id") == heir
            and isinstance(expectation.get("title_expectations"), list)
            and bool(expectation["title_expectations"])
            and all(isinstance(item, dict) and isinstance(item.get("title"), dict)
                    and type(item["title"].get("title_id")) is int
                    for item in expectation["title_expectations"])
            and isinstance(expectation.get("binding"), dict)
            and expectation["binding"].get("episode_character_id") == old_actor
            and expectation["binding"].get("episode_run_id") == before["episode_run_id"]
            and type(expectation["binding"].get("date_raw")) is int
            and expectation["binding"]["date_raw"] <= body["date_raw"]
            and isinstance(reconciliation, dict)
            and reconciliation.get("status") == "available"
            and reconciliation.get("verdict") == "matched"
            and reconciliation.get("successor_match") is True
            and reconciliation.get("title_distribution_match") is True
            and reconciliation.get("predecessor_character_id") == old_actor
            and reconciliation.get("expected_successor_character_id") == heir
            and reconciliation.get("actual_successor_character_id") == heir
            and reconciliation.get("predecessor_binding") == expectation["binding"]):
        return None
    binding = reconciliation.get("successor_binding")
    if not (isinstance(binding, dict)
            and all(binding.get(key) == body[key] for key in
                    ("snapshot_id", "revision", "native_revision", "date_raw"))):
        return None
    return {
        "status": "matched_successor_observed_only",
        "successor_character_id": heir,
        "predecessor_character_id": old_actor,
        "frame": {key: body[key] for key in
                  ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")},
        "connection_generation": diag["connection_generation"],
        "original_auto_business_credit": 0,
        "handoff_actions_performed": False,
    }
