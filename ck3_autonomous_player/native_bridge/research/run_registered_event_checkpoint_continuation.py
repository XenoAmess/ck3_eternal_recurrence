#!/usr/bin/env python3
"""Resolve one exact-build registered event from a frozen checkpoint.

The runner cold-restores a caller-supplied checkpoint, queries the current
event through the official MCP, asks the shared vanilla-event registry for its
source-reviewed bounded continuation, selects exactly that option and saves a
successor checkpoint.  It never resumes time or submits a war-exit action.
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

import run_gen034_white_peace_evaluation_live_acceptance as evaluation  # noqa: E402
import run_gen034_white_peace_horizon_checkpoint as horizon  # noqa: E402
import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.event_contract import event_option_step  # noqa: E402
from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


REPORT_KIND = "ck3_registered_event_checkpoint_continuation"


def _format_sequence_error(error: BaseException) -> str:
    """Preserve the concrete MCP failure hidden by anyio TaskGroup wrapping."""

    headline = f"{type(error).__name__}: {error}"
    nested = getattr(error, "exceptions", None)
    if not isinstance(nested, tuple) or not nested:
        return headline
    details = "; ".join(_format_sequence_error(item) for item in nested)
    return f"{headline} [{details}]"


def _checkpoint_bound_event_context(
    driver_state_path: Path,
    *,
    expected_checkpoint_sha256: str,
    expected_date_raw: int,
    expected_event_key: str,
) -> dict[str, object]:
    """Recover the exact event query immediately sealed by the checkpoint."""

    try:
        state = json.loads(driver_state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"source driver-state is unavailable: {error}") from error
    history = state.get("command_history") if isinstance(state, dict) else None
    checkpoint = state.get("last_checkpoint") if isinstance(state, dict) else None
    if not isinstance(history, list) or not isinstance(checkpoint, dict):
        raise RuntimeError("source driver-state lacks checkpoint history")
    history_index = checkpoint.get("history_index")
    if isinstance(history_index, bool) or not isinstance(history_index, int):
        raise RuntimeError("source checkpoint lacks its history index")
    by_index = {
        row.get("index"): row
        for row in history
        if isinstance(row, dict)
        and isinstance(row.get("index"), int)
        and not isinstance(row.get("index"), bool)
    }
    query_row = by_index.get(history_index - 1)
    save_row = by_index.get(history_index)
    query_result = (
        query_row.get("result") if isinstance(query_row, dict) else None
    )
    save_result = save_row.get("result") if isinstance(save_row, dict) else None
    saved_checkpoint = (
        save_result.get("checkpoint") if isinstance(save_result, dict) else None
    )
    context = (
        query_result.get("current_event_window_context")
        if isinstance(query_result, dict)
        else None
    )
    expected_hash = str(expected_checkpoint_sha256).upper()
    if not (
        isinstance(query_row, dict)
        and query_row.get("command") == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        and query_row.get("ok") is True
        and isinstance(query_result, dict)
        and query_result.get("step") == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        and query_result.get("accepted") is True
        and query_result.get("status") == "available"
        and isinstance(context, dict)
        and context.get("status") == "available"
        and context.get("date_raw") == expected_date_raw
        and context.get("event_definition_key") == expected_event_key
        and isinstance(save_row, dict)
        and save_row.get("command") == "save-checkpoint"
        and save_row.get("ok") is True
        and isinstance(save_result, dict)
        and save_result.get("step") == "save-checkpoint"
        and save_result.get("accepted") is True
        and isinstance(saved_checkpoint, dict)
        and str(saved_checkpoint.get("sha256", "")).upper() == expected_hash
        and saved_checkpoint.get("date_raw") == expected_date_raw
        and str(checkpoint.get("sha256", "")).upper() == expected_hash
        and checkpoint.get("date_raw") == expected_date_raw
    ):
        raise RuntimeError(
            "source checkpoint is not immediately bound to the exact event query"
        )
    return copy.deepcopy(context)


def _parser() -> argparse.ArgumentParser:
    parser = evaluation._parser()
    parser.description = __doc__
    parser.add_argument("--expected-event-key", required=True)
    parser.add_argument("--settle-timeout", type=float, default=10.0)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    return parser


def _recommend_exact_registered_option(
    *,
    snapshot: dict[str, object],
    event_context: dict[str, object],
    expected_event_key: str,
    expected_character_id: int,
) -> dict[str, object]:
    if event_context.get("event_definition_key") != expected_event_key:
        raise RuntimeError("current event differs from the requested event key")
    active_event = snapshot.get("active_event")
    if not isinstance(active_event, dict):
        raise RuntimeError("source frame has no active event")
    options = active_event.get("options")
    snapshot_option_count = (
        len(options) if isinstance(options, list) else active_event.get("option_count")
    )
    decision = recommend_registered_vanilla_event_option_v1(
        event_context,
        played_character_id=expected_character_id,
        snapshot_option_count=snapshot_option_count,
    )
    if decision.get("status") != "recommended":
        raise RuntimeError(
            "registered event policy did not authorize a continuation: "
            f"{decision.get('unavailable_reason')}"
        )
    return decision


def _history_checks(
    before: dict[str, object],
    after: dict[str, object],
    *,
    expected_commands: list[str],
) -> dict[str, bool]:
    before_history = before.get("native_command_history")
    after_history = after.get("native_command_history")
    if not isinstance(before_history, list) or not isinstance(after_history, list):
        return {"exact_command_delta": False}
    delta = [
        (row.get("command"), row.get("ok"))
        for row in after_history[len(before_history) :]
        if isinstance(row, dict)
    ]
    return {
        "exact_command_delta": delta
        == [(command, True) for command in expected_commands]
    }


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    expected_event_key: str,
    frozen_event_context: dict[str, object],
    settle_timeout: float,
    poll_interval: float,
) -> dict[str, object]:
    from mcp import Client

    if settle_timeout <= 0 or poll_interval <= 0:
        raise ValueError("settle timeout and poll interval must be positive")

    server = base.create_server(driver)
    mcp_results: list[object] = []
    expected_commands: list[str] = []
    tool_names: list[str] = []
    before: dict[str, object] = {}
    final: dict[str, object] = {}
    event_context: dict[str, object] | None = None
    decision: dict[str, object] | None = None
    selection: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    sequence_error: str | None = None

    try:
        async with Client(server) as client:
            listed = await client.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)
            capabilities_result = await client.call_tool("ck3_get_capabilities", {})
            mcp_results.append(capabilities_result)
            before_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(before_result)
            before = base._structured(
                before_result, tool_name="ck3_take_snapshot:before"
            )
            final = before
            active_event = before.get("active_event")
            war = horizon._active_war(before, war_id)
            if (
                before.get("paused") is not True
                or before.get("date_raw") != expected_date_raw
                or horizon._played_character_id(before) != expected_character_id
                or war is None
                or not isinstance(active_event, dict)
            ):
                raise RuntimeError("source frame is not the expected paused event war")
            event_instance_id = active_event.get("instance_id")
            revision = before.get("revision")
            if (
                isinstance(event_instance_id, bool)
                or not isinstance(event_instance_id, int)
                or event_instance_id <= 0
                or isinstance(revision, bool)
                or not isinstance(revision, int)
            ):
                raise RuntimeError("source event lacks stable instance/revision identity")

            if frozen_event_context.get("current_event_instance_id") != event_instance_id:
                raise RuntimeError("checkpoint-bound event instance differs after restore")
            event_context = copy.deepcopy(frozen_event_context)
            decision = _recommend_exact_registered_option(
                snapshot=before,
                event_context=event_context,
                expected_event_key=expected_event_key,
                expected_character_id=expected_character_id,
            )
            option_number = decision.get("selected_option_number")
            if isinstance(option_number, bool) or not isinstance(option_number, int):
                raise RuntimeError("registry recommendation lacks an option number")
            selected_step = event_option_step(option_number)
            selection_result = await client.call_tool(
                "ck3_select_event_option",
                {
                    "option_number": option_number,
                    "event_instance_id": event_instance_id,
                    "expected_revision": revision,
                },
            )
            mcp_results.append(selection_result)
            selection = base._structured(
                selection_result, tool_name="ck3_select_event_option"
            )
            expected_commands.append(selected_step)

            deadline = time.monotonic() + settle_timeout
            while time.monotonic() < deadline:
                snapshot_result = await client.call_tool("ck3_take_snapshot", {})
                mcp_results.append(snapshot_result)
                final = base._structured(
                    snapshot_result, tool_name="ck3_take_snapshot:after-selection"
                )
                successor = final.get("active_event")
                if not isinstance(successor, dict):
                    break
                if successor.get("instance_id") != event_instance_id:
                    raise RuntimeError("event selection opened a successor event")
                await asyncio.sleep(poll_interval)
            if final.get("active_event") is not None:
                raise RuntimeError("selected event did not close before timeout")
            if (
                final.get("paused") is not True
                or final.get("date_raw") != expected_date_raw
                or horizon._played_character_id(final) != expected_character_id
                or horizon._active_war(final, war_id) is None
            ):
                raise RuntimeError("event postcondition changed paused war identity")
            final_revision = final.get("revision")
            if isinstance(final_revision, bool) or not isinstance(final_revision, int):
                raise RuntimeError("resolved frame lacks a public revision")
            save_result = await client.call_tool(
                "ck3_save_checkpoint", {"expected_revision": final_revision}
            )
            mcp_results.append(save_result)
            save = base._structured(save_result, tool_name="ck3_save_checkpoint")
            expected_commands.append("save-checkpoint")
            checkpoint_value = save.get("checkpoint")
            checkpoint = (
                dict(checkpoint_value) if isinstance(checkpoint_value, dict) else None
            )
            final_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(final_result)
            final = base._structured(
                final_result, tool_name="ck3_take_snapshot:final"
            )
    except BaseException as error:
        sequence_error = _format_sequence_error(error)

    checkpoint_path = (
        Path(str(checkpoint.get("path"))).resolve()
        if isinstance(checkpoint, dict) and checkpoint.get("path")
        else None
    )
    option_number = (
        decision.get("selected_option_number") if isinstance(decision, dict) else None
    )
    selected_step = (
        event_option_step(option_number)
        if isinstance(option_number, int) and not isinstance(option_number, bool)
        else None
    )
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_current_event_window_context_v1",
                "ck3_select_event_option",
                "ck3_save_checkpoint",
            )
        ),
        "mcp_results_not_errors": bool(mcp_results)
        and not any(bool(getattr(result, "is_error", False)) for result in mcp_results),
        "sequence_error_absent": sequence_error is None,
        "registry_recommended": isinstance(decision, dict)
        and decision.get("status") == "recommended"
        and decision.get("event_definition_key") == expected_event_key,
        "selection_bound_to_recommendation": isinstance(selection, dict)
        and selection.get("event_instance_id")
        == (before.get("active_event") or {}).get("instance_id")
        and selection.get("option_number") == option_number,
        "event_resolved": final.get("active_event") is None,
        "final_paused": final.get("paused") is True,
        "same_date": final.get("date_raw") == expected_date_raw,
        "same_character": horizon._played_character_id(final)
        == expected_character_id,
        "war_still_active": horizon._active_war(final, war_id) is not None,
        "checkpoint_materialized": isinstance(checkpoint, dict)
        and checkpoint.get("status") == "saved"
        and checkpoint.get("date_raw") == expected_date_raw
        and checkpoint_path is not None
        and checkpoint_path.is_file(),
        **_history_checks(before, final, expected_commands=expected_commands),
    }
    return {
        "expected_event_key": expected_event_key,
        "event_context_source": "checkpoint_bound_driver_receipt",
        "allowed_gameplay_commands": [
            selected_step,
            "save-checkpoint",
        ],
        "forbidden_commands": [
            "resume-map",
            "life-advance",
            "surrender-war-N",
            "offer-white-peace-N",
            "enforce-demands-N",
            evaluation.DISABLED_BROAD_PREVIEW_COMMAND_PREFIX,
        ],
        "expected_command_delta": expected_commands,
        "before_snapshot": horizon._compact_snapshot(before, war_id=war_id),
        "event_context": event_context,
        "registry_decision": decision,
        "selection": selection,
        "prepared_checkpoint": checkpoint,
        "final_snapshot": horizon._compact_snapshot(final, war_id=war_id),
        "sequence_error": sequence_error,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        preflight_payload, preflight_exit = preflight._no_launch_preflight(args)
        if args.preflight_only or preflight_exit != 0:
            payload = preflight_payload
            exit_code = preflight_exit
        else:
            frozen_event_context = _checkpoint_bound_event_context(
                args.source_driver_state.expanduser().resolve(),
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                expected_date_raw=args.expected_date_raw,
                expected_event_key=args.expected_event_key,
            )
            sequence_runner = functools.partial(
                _run_mcp_sequence,
                expected_event_key=args.expected_event_key,
                frozen_event_context=frozen_event_context,
                settle_timeout=args.settle_timeout,
                poll_interval=args.poll_interval,
            )
            payload, exit_code = base._run(
                args,
                sequence_runner=sequence_runner,
                exact_build_runner=horizon._exact_build_proof,
                report_kind=REPORT_KIND,
                policy_override={
                    "mcp_first": True,
                    "production_non_debug": True,
                    "cold_checkpoint": True,
                    "ocr_used": False,
                    "visual_input_used": False,
                    "time_advanced": False,
                    "maximum_ck3_launches": 1,
                    "event_context_queries": 0,
                    "event_context_source": "checkpoint_bound_driver_receipt",
                    "event_selections": 1,
                    "checkpoint_saves": 1,
                    "mutation_commands": [
                        "select-event-option-N",
                        "save-checkpoint",
                    ],
                    "war_termination_action_enabled": False,
                    "broad_loaded_effect_preview_enabled": False,
                },
            )
            payload["no_launch_preflight"] = preflight_payload
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
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
