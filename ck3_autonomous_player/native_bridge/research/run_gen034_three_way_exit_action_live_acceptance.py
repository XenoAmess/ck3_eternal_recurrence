#!/usr/bin/env python3
"""Execute one authorized GEN-034-D action and verify its bounded result.

The runner first reuses the same-process recommendation sequence, then checks
that its authorized paused frame is unchanged before submitting exactly one
semantic action.  A termination result is followed only by exact-store
cleanup, two persisted-truce reads, one checkpoint save and one cold restore.
The command-line entry is live and must be run only by the exclusive CK3 owner;
importing this module or testing ``_execute_action_tail`` starts no process.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import functools
import json
from pathlib import Path
import sys
import time
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_gen034_three_way_recommendation_live_acceptance as recommendation  # noqa: E402
import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.raiktor_actual_truce_expiry_contract import (  # noqa: E402
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX,
)
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    normalize_raiktor_source_specific_capture,
)
from xar_autoplayer.bridge.raiktor_war_bound_loss_cleanup_contract import (  # noqa: E402
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_postcondition import (  # noqa: E402
    normalize_raiktor_three_way_exit_authorization,
    provide_raiktor_three_way_exit_postcondition,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_postwar_evidence import (  # noqa: E402
    normalize_raiktor_three_way_exit_source_binding,
    provide_raiktor_three_way_exit_postwar_evidence,
)


REPORT_KIND = "ck3_gen034_three_way_exit_action_live_acceptance"
RESULT_SCHEMA = "xar.ck3.gen034_three_way_exit_action_live_acceptance.v1"
CONTINUE_SUCCESSOR_TIMEOUT_SECONDS = 5.0
CONTINUE_SUCCESSOR_POLL_SECONDS = 0.1


class Gen034ActionRunnerError(RuntimeError):
    """The bounded action sequence crossed an identity or result contract."""


def _parser() -> argparse.ArgumentParser:
    parser = recommendation._parser()
    parser.description = __doc__
    parser.add_argument("--source-capture", type=Path, required=True)
    parser.add_argument("--expected-source-capture-sha256", required=True)
    return parser


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
    opponent_character_id: int,
) -> dict[str, object]:
    result = recommendation._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
        opponent_character_id=opponent_character_id,
    )
    raw = capabilities if isinstance(capabilities, dict) else {}
    hello_value = base._diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    advertised = raw.get("bridge_capabilities")
    hello_capabilities = hello.get("capabilities")
    action_steps = raw.get("action_steps")
    composite_steps = raw.get("composite_action_steps")
    required_private = {
        QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
    }
    added = {
        "postwar_bridge_capabilities": isinstance(advertised, list)
        and required_private <= set(advertised),
        "postwar_hello_capabilities": isinstance(hello_capabilities, list)
        and required_private <= set(hello_capabilities),
        "checkpoint_save_step": isinstance(action_steps, list)
        and "save-checkpoint" in action_steps,
        "checkpoint_cold_restore_step": isinstance(composite_steps, list)
        and "restore-checkpoint" in composite_steps,
    }
    result["checks"].update(added)
    result["required_postwar_capabilities"] = sorted(required_private)
    result["checks"]["broad_preview_still_disabled"] = (
        result["checks"].get("exit_broad_preview_not_advertised") is True
    )
    result["ok"] = all(result["checks"].values())
    return result


def _structured_record(value: object, name: str) -> dict[str, object]:
    record = value if isinstance(value, dict) else {}
    content = record.get("structured_content")
    if not isinstance(content, dict) or record.get("is_error") is True:
        raise Gen034ActionRunnerError(f"{name} has no successful MCP payload")
    return copy.deepcopy(content)


def _active_war_bound(read_phase: dict[str, object]) -> dict[str, object]:
    terms = _structured_record(read_phase.get("terms_query"), "terms query")
    wrapper = terms.get("raiktor_surrender_aggregate_session")
    aggregate = wrapper.get("aggregate") if isinstance(wrapper, dict) else None
    domains = aggregate.get("domains") if isinstance(aggregate, dict) else None
    domain = (
        domains.get("generic_war_bound_current")
        if isinstance(domains, dict)
        else None
    )
    payload = domain.get("payload") if isinstance(domain, dict) else None
    if not isinstance(payload, dict) or domain.get("available") is not True:
        raise Gen034ActionRunnerError(
            "recommendation terms lack the active generic war-bound payload"
        )
    return copy.deepcopy(payload)


def _played_character_id(snapshot: dict[str, object]) -> object:
    played = snapshot.get("played_character")
    return played.get("character_id") if isinstance(played, dict) else None


def _war_opponent(
    snapshot: dict[str, object], war_id: object
) -> object | None:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    matches = [
        row
        for row in wars
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    if len(matches) != 1:
        return None
    return matches[0].get("primary_opponent_character_id")


def _authorized_frame_matches(
    snapshot: dict[str, object], authorization: dict[str, object]
) -> bool:
    frame = authorization.get("frame")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(frame, dict) or not isinstance(diagnostics, dict):
        return False
    connection = frame.get("connection_id")
    prefix = "connection-generation:"
    expected_connection = (
        int(connection.removeprefix(prefix))
        if isinstance(connection, str)
        and connection.startswith(prefix)
        and connection.removeprefix(prefix).isascii()
        and connection.removeprefix(prefix).isdecimal()
        else None
    )
    return bool(
        expected_connection is not None
        and snapshot.get("paused") is True
        and snapshot.get("active_event") is None
        and snapshot.get("snapshot_id") == frame.get("snapshot_id")
        and snapshot.get("revision") == frame.get("snapshot_revision")
        and snapshot.get("native_revision") == frame.get("native_revision")
        and snapshot.get("date_raw") == frame.get("date_raw")
        and snapshot.get("episode_run_id") == frame.get("episode_id")
        and diagnostics.get("bridge_pid") == frame.get("ck3_pid")
        and diagnostics.get("connection_generation") == expected_connection
        and _played_character_id(snapshot)
        == frame.get("primary_attacker_character_id")
        and _war_opponent(snapshot, frame.get("war_id"))
        == frame.get("primary_defender_character_id")
    )


def _same_postwar_frame(
    left: dict[str, object], right: dict[str, object]
) -> bool:
    left_diagnostics = left.get("diagnostics")
    right_diagnostics = right.get("diagnostics")
    return bool(
        left.get("paused") is True
        and right.get("paused") is True
        and isinstance(left_diagnostics, dict)
        and isinstance(right_diagnostics, dict)
        and all(
            left.get(key) == right.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
        and left_diagnostics.get("bridge_pid")
        == right_diagnostics.get("bridge_pid")
        and left_diagnostics.get("connection_generation")
        == right_diagnostics.get("connection_generation")
        and _played_character_id(left) == _played_character_id(right)
    )


def _same_saved_semantics(
    post: dict[str, object], after_save: dict[str, object], war_id: int
) -> bool:
    post_diagnostics = post.get("diagnostics")
    saved_diagnostics = after_save.get("diagnostics")
    return bool(
        post.get("paused") is True
        and after_save.get("paused") is True
        and isinstance(post_diagnostics, dict)
        and isinstance(saved_diagnostics, dict)
        and after_save.get("revision", -1) > post.get("revision", -1)
        and after_save.get("native_revision", -1)
        > post.get("native_revision", -1)
        and after_save.get("date_raw") == post.get("date_raw")
        and after_save.get("episode_run_id") == post.get("episode_run_id")
        and saved_diagnostics.get("bridge_pid")
        == post_diagnostics.get("bridge_pid")
        and saved_diagnostics.get("connection_generation")
        == post_diagnostics.get("connection_generation")
        and _played_character_id(after_save) == _played_character_id(post)
        and _war_opponent(after_save, war_id) is None
    )


async def _execute_action_tail(
    client: Any,
    *,
    read_phase: dict[str, object],
    source_capture: dict[str, object],
    source_capture_sha256: str,
) -> dict[str, object]:
    """Execute the already-planned action on the unchanged connected frame."""

    if read_phase.get("ok") is not True:
        raise Gen034ActionRunnerError("recommendation phase is not GREEN")
    action_gate = read_phase.get("action_gate")
    authorization = normalize_raiktor_three_way_exit_authorization(action_gate)
    action = authorization["action"]
    route = action["semantic_action"]
    action_step = action["literal"]
    war_id = action["war_id"]
    read_commands = read_phase.get("allowed_gameplay_commands")
    if not isinstance(read_commands, list) or len(read_commands) not in {2, 4}:
        raise Gen034ActionRunnerError(
            "recommendation phase lacks an admitted two- or four-read command list"
        )
    origin = _structured_record(
        read_phase.get("before_snapshot"), "recommendation source snapshot"
    )
    before_action_result = await client.call_tool("ck3_take_snapshot", {})
    before_action = base._structured(
        before_action_result, tool_name="ck3_take_snapshot:before-action"
    )
    if not _authorized_frame_matches(before_action, authorization):
        raise Gen034ActionRunnerError(
            "authorized recommendation frame changed before submission"
        )

    active_war_bound = None
    if route != "continue":
        active_war_bound = _active_war_bound(read_phase)
        try:
            normalize_raiktor_three_way_exit_source_binding(
                action_gate,
                source_capture,
                source_capture_sha256=source_capture_sha256,
                active_war_bound_value=active_war_bound,
            )
        except ValueError as error:
            raise Gen034ActionRunnerError(
                f"pre-action source binding failed: {error}"
            ) from error

    action_result_value = await client.call_tool(
        "ck3_execute_step",
        {"step": action_step, "expected_revision": action["expected_revision"]},
    )
    action_result = base._structured(
        action_result_value, tool_name="ck3_execute_step:authorized-action"
    )
    post_result = await client.call_tool("ck3_take_snapshot", {})
    post = base._structured(post_result, tool_name="ck3_take_snapshot:post-action")
    issued_commands = [action_step]

    if route == "continue":
        postcondition = provide_raiktor_three_way_exit_postcondition(
            action_gate,
            action_result,
            post,
        )
        observation_attempts = 1
        deadline = time.monotonic() + CONTINUE_SUCCESSOR_TIMEOUT_SECONDS
        while (
            postcondition.get("postcondition_verified") is not True
            and time.monotonic() < deadline
        ):
            await asyncio.sleep(CONTINUE_SUCCESSOR_POLL_SECONDS)
            post_result = await client.call_tool("ck3_take_snapshot", {})
            post = base._structured(
                post_result,
                tool_name="ck3_take_snapshot:continue-successor",
            )
            observation_attempts += 1
            postcondition = provide_raiktor_three_way_exit_postcondition(
                action_gate,
                action_result,
                post,
            )
        history = recommendation._history_checks(
            origin,
            post,
            expected_commands=[*read_commands, action_step],
        )
        checks = {
            "authorized_frame_unchanged": True,
            "exactly_one_exit_action": issued_commands == [action_step],
            "exact_command_delta": history["exact_read_only_command_delta"],
            "continue_postcondition_verified": postcondition.get(
                "postcondition_verified"
            )
            is True,
            "continue_does_not_close_gen034": postcondition.get(
                "gen034_closed"
            )
            is False,
        }
        return {
            "schema": RESULT_SCHEMA,
            "status": "verified_continue" if all(checks.values()) else "red",
            "route": route,
            "read_phase": read_phase,
            "action_result": action_result,
            "post_snapshot": post,
            "postwar_evidence": None,
            "checkpoint_restore": None,
            "postcondition": postcondition,
            "continue_observation_attempts": observation_attempts,
            "issued_commands": issued_commands,
            "exit_action_commands": [action_step],
            "checks": checks,
            "gen034_closed": False,
            "ok": all(checks.values()),
        }

    cleanup_step = QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX + str(
        war_id
    )
    opponent_id = authorization["postcondition_plan"]["expectations"][
        "opponent_character_id"
    ]
    truce_step = QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX + str(
        opponent_id
    )
    post_revision = post.get("revision")
    if isinstance(post_revision, bool) or not isinstance(post_revision, int):
        raise Gen034ActionRunnerError("post-action snapshot has no revision")
    cleanup_result_value = await client.call_tool(
        "ck3_execute_step",
        {"step": cleanup_step, "expected_revision": post_revision},
    )
    cleanup_result = base._structured(
        cleanup_result_value, tool_name="ck3_execute_step:postwar-cleanup"
    )
    issued_commands.append(cleanup_step)
    first_truce_value = await client.call_tool(
        "ck3_execute_step",
        {"step": truce_step, "expected_revision": post_revision},
    )
    first_truce = base._structured(
        first_truce_value, tool_name="ck3_execute_step:first-truce"
    )
    issued_commands.append(truce_step)
    between_result = await client.call_tool("ck3_take_snapshot", {})
    between = base._structured(
        between_result, tool_name="ck3_take_snapshot:between-truce"
    )
    second_truce_value = await client.call_tool(
        "ck3_execute_step",
        {"step": truce_step, "expected_revision": post_revision},
    )
    second_truce = base._structured(
        second_truce_value, tool_name="ck3_execute_step:second-truce"
    )
    issued_commands.append(truce_step)
    after_truce_result = await client.call_tool("ck3_take_snapshot", {})
    after_truce = base._structured(
        after_truce_result, tool_name="ck3_take_snapshot:after-truce"
    )
    if not (
        _same_postwar_frame(post, between)
        and _same_postwar_frame(post, after_truce)
    ):
        raise Gen034ActionRunnerError("postwar truce reads crossed paused frames")

    evidence = provide_raiktor_three_way_exit_postwar_evidence(
        action_gate,
        source_capture,
        source_capture_sha256=source_capture_sha256,
        active_war_bound_value=active_war_bound,
        post_snapshot_value=post,
        cleanup_result_value=cleanup_result,
        truce_result_values=[first_truce, second_truce],
    )
    if evidence.get("evidence_ready") is not True:
        checks = {
            "authorized_frame_unchanged": True,
            "exactly_one_exit_action": issued_commands.count(action_step) == 1,
            "postwar_frame_stable": True,
            "postwar_evidence_ready": False,
            "checkpoint_not_attempted_after_evidence_red": True,
        }
        return {
            "schema": RESULT_SCHEMA,
            "status": "red",
            "route": route,
            "read_phase": read_phase,
            "action_result": action_result,
            "post_snapshot": post,
            "postwar_evidence": evidence,
            "checkpoint_restore": None,
            "postcondition": None,
            "issued_commands": issued_commands,
            "exit_action_commands": [action_step],
            "checks": checks,
            "gen034_closed": False,
            "ok": False,
        }

    save_value = await client.call_tool(
        "ck3_save_checkpoint", {"expected_revision": post_revision}
    )
    save = base._structured(save_value, tool_name="ck3_save_checkpoint")
    issued_commands.append("save-checkpoint")
    after_save_value = await client.call_tool("ck3_take_snapshot", {})
    after_save = base._structured(
        after_save_value, tool_name="ck3_take_snapshot:after-save"
    )
    if not _same_saved_semantics(post, after_save, war_id):
        raise Gen034ActionRunnerError("checkpoint save changed postwar semantics")
    restore_revision = after_save.get("revision")
    restore_value = await client.call_tool(
        "ck3_restore_checkpoint", {"expected_revision": restore_revision}
    )
    restore = base._structured(
        restore_value, tool_name="ck3_restore_checkpoint"
    )
    issued_commands.append("restore-checkpoint")
    restored_value = await client.call_tool("ck3_take_snapshot", {})
    restored = base._structured(
        restored_value, tool_name="ck3_take_snapshot:restored"
    )
    checkpoint_restore = {
        "save_result": save,
        "restore_result": restore,
        "restored_snapshot": restored,
    }
    postcondition = provide_raiktor_three_way_exit_postcondition(
        action_gate,
        action_result,
        post,
        evidence["postwar_evidence"],
        checkpoint_restore,
    )
    pre_restore_history = recommendation._history_checks(
        origin,
        after_save,
        expected_commands=[
            *read_commands,
            action_step,
            cleanup_step,
            truce_step,
            truce_step,
            "save-checkpoint",
        ],
    )
    checks = {
        "authorized_frame_unchanged": True,
        "exactly_one_exit_action": issued_commands.count(action_step) == 1,
        "postwar_frame_stable": True,
        "postwar_evidence_ready": evidence.get("evidence_ready") is True,
        "exact_pre_restore_command_delta": pre_restore_history[
            "exact_read_only_command_delta"
        ],
        "checkpoint_cold_restore_verified": postcondition.get(
            "checkpoint_cold_restore_verified"
        )
        is True,
        "gen034_closed": postcondition.get("gen034_closed") is True,
    }
    return {
        "schema": RESULT_SCHEMA,
        "status": "verified" if all(checks.values()) else "red",
        "route": route,
        "read_phase": read_phase,
        "action_result": action_result,
        "post_snapshot": post,
        "postwar_evidence": evidence,
        "checkpoint_restore": checkpoint_restore,
        "postcondition": postcondition,
        "issued_commands": issued_commands,
        "exit_action_commands": [action_step],
        "checks": checks,
        "gen034_closed": postcondition.get("gen034_closed") is True,
        "ok": all(checks.values()),
    }


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    opponent_character_id: int,
    source_capture: dict[str, object],
    source_capture_sha256: str,
) -> dict[str, object]:
    """Keep recommendation and action phases on the same managed driver."""

    read_phase: dict[str, object] | None = None
    try:
        read_phase = await recommendation._run_mcp_sequence(
            driver,
            war_id=war_id,
            expected_character_id=expected_character_id,
            expected_date_raw=expected_date_raw,
            opponent_character_id=opponent_character_id,
        )
        if read_phase.get("ok") is not True:
            raise Gen034ActionRunnerError("recommendation phase returned RED")
        from mcp import Client

        server = base.create_server(driver)
        async with Client(server) as client:
            return await _execute_action_tail(
                client,
                read_phase=read_phase,
                source_capture=source_capture,
                source_capture_sha256=source_capture_sha256,
            )
    except BaseException as error:
        return {
            "schema": RESULT_SCHEMA,
            "status": "red",
            "read_phase": read_phase,
            "sequence_error": f"{type(error).__name__}: {error}",
            "gen034_closed": False,
            "ok": False,
        }


def _load_source_capture(path: Path, expected_sha256: str) -> dict[str, object]:
    source = path.expanduser().resolve()
    expected = base._expected_sha256(
        expected_sha256, "expected source-capture SHA-256"
    )
    if not source.is_file() or base._sha256_file(source) != expected:
        raise Gen034ActionRunnerError("source capture path/hash disagrees")
    try:
        value = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Gen034ActionRunnerError(
            f"source capture JSON is unavailable: {error}"
        ) from error
    if not isinstance(value, dict):
        raise Gen034ActionRunnerError("source capture JSON must be an object")
    normalize_raiktor_source_specific_capture(value, capture_sha256=expected)
    return value


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        source_capture = _load_source_capture(
            args.source_capture,
            args.expected_source_capture_sha256,
        )
        source_capture_sha256 = base._expected_sha256(
            args.expected_source_capture_sha256,
            "expected source-capture SHA-256",
        )
        preflight_payload, preflight_exit = preflight._no_launch_preflight(args)
        preflight_payload["source_capture"] = {
            "path": str(args.source_capture.expanduser().resolve()),
            "sha256": source_capture_sha256,
            "normalized": True,
        }
        if args.preflight_only or preflight_exit != 0:
            payload = preflight_payload
            exit_code = preflight_exit
        else:
            sequence_runner = functools.partial(
                _run_mcp_sequence,
                opponent_character_id=args.opponent_character_id,
                source_capture=source_capture,
                source_capture_sha256=source_capture_sha256,
            )
            exact_build_runner = functools.partial(
                _exact_build_proof,
                opponent_character_id=args.opponent_character_id,
            )
            payload, exit_code = base._run(
                args,
                sequence_runner=sequence_runner,
                exact_build_runner=exact_build_runner,
                report_kind=REPORT_KIND,
                policy_override={
                    "mcp_first": True,
                    "production_non_debug": True,
                    "cold_checkpoint": True,
                    "ocr_used": False,
                    "visual_input_used": False,
                    "time_advanced_only_if_continue_wins": True,
                    "maximum_ck3_launches": 2,
                    "continue_route_ck3_launches": 1,
                    "termination_route_ck3_launches": 2,
                    "recommendation_queries": 4,
                    "war_exit_actions": 1,
                    "postwar_cleanup_queries": 1,
                    "persisted_truce_queries": 2,
                    "termination_route_checkpoint_saves": 1,
                    "termination_route_checkpoint_cold_restores": 1,
                    "continue_route_checkpoint_saves": 0,
                    "continue_route_checkpoint_cold_restores": 0,
                    "broad_loaded_effect_preview_enabled": False,
                },
            )
            payload["no_launch_preflight"] = preflight_payload
            payload["source_capture"] = preflight_payload["source_capture"]
            base._write_json_atomic(Path(str(payload["report_path"])), payload)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "status": payload.get("status"),
                "report_path": payload.get("report_path"),
                "ck3_started": payload.get("ck3_started"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
