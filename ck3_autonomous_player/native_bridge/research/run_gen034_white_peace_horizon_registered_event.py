#!/usr/bin/env python3
"""Reach the GEN-034 white-peace horizon through one registered event.

This runner cold-restores the pre-event Raiktor checkpoint, advances through
the official MCP, and may consume exactly one caller-named vanilla event in
the same live session.  The event is queried on its paused exact-build frame,
must be accepted by the shared registry, and is selected through the native
event command.  The runner then resumes toward the requested date, reads the
typed white-peace option once, and saves a successor checkpoint only when the
full admission is available.  It never submits a war-termination action.
"""

from __future__ import annotations

import argparse
import asyncio
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
import run_registered_event_checkpoint_continuation as registered  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.event_contract import event_option_step  # noqa: E402
from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    query_war_termination_options_step,
)


REPORT_KIND = "ck3_gen034_white_peace_horizon_registered_event"


def _parser() -> argparse.ArgumentParser:
    parser = evaluation._parser()
    parser.description = __doc__
    parser.add_argument("--target-date-raw", type=int, required=True)
    parser.add_argument("--expected-event-key", required=True)
    parser.add_argument("--horizon-timeout", type=float, default=180.0)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    return parser


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    result = horizon._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
    )
    raw = capabilities if isinstance(capabilities, dict) else {}
    steps = raw.get("action_steps")
    step_set = set(steps) if isinstance(steps, list) else set()
    result["checks"]["select_event_option_step"] = (
        "select-event-option-1" in step_set
    )
    result["ok"] = all(result["checks"].values())
    return result


def _append_sample(
    samples: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    war_id: int,
) -> None:
    compact = horizon._compact_snapshot(snapshot, war_id=war_id)
    if not samples or compact != samples[-1]:
        samples.append(compact)


def _plain_revision(snapshot: dict[str, object], *, label: str) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{label} lacks a public revision")
    return value


def _assert_live_identity(
    snapshot: dict[str, object],
    *,
    war_id: int,
    character_id: int,
) -> None:
    if horizon._played_character_id(snapshot) != character_id:
        raise RuntimeError("played character changed during horizon")
    if horizon._active_war(snapshot, war_id) is None:
        raise RuntimeError("Raiktor war ended before the horizon")


async def _take_snapshot(
    client: Any,
    results: list[object],
    *,
    label: str,
) -> dict[str, object]:
    result = await client.call_tool("ck3_take_snapshot", {})
    results.append(result)
    return base._structured(result, tool_name=f"ck3_take_snapshot:{label}")


async def _pause_boundary(
    client: Any,
    results: list[object],
    commands: list[str],
    samples: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    war_id: int,
    poll_interval: float,
) -> dict[str, object]:
    if snapshot.get("paused") is not True:
        commands.append("pause-map")
        result = await client.call_tool("ck3_execute_step", {"step": "pause-map"})
        results.append(result)
        base._structured(result, tool_name="ck3_execute_step:pause")
    deadline = time.monotonic() + 10.0
    current = snapshot
    while current.get("paused") is not True and time.monotonic() < deadline:
        await asyncio.sleep(poll_interval)
        current = await _take_snapshot(client, results, label="paused-boundary")
        _append_sample(samples, current, war_id=war_id)
    if current.get("paused") is not True:
        raise RuntimeError("pause-map postcondition was not observed")
    return current


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    target_date_raw: int,
    expected_event_key: str,
    horizon_timeout: float,
    poll_interval: float,
) -> dict[str, object]:
    from mcp import Client

    if target_date_raw <= expected_date_raw:
        raise ValueError("target date must be later than the source date")
    if horizon_timeout <= 0 or poll_interval <= 0:
        raise ValueError("horizon timeout and poll interval must be positive")

    server = base.create_server(driver)
    results: list[object] = []
    commands: list[str] = []
    samples: list[dict[str, object]] = []
    event_continuations: list[dict[str, object]] = []
    sequence_error: str | None = None
    options: dict[str, object] | None = None
    admission_checks: dict[str, bool] = {}
    checkpoint: dict[str, object] | None = None
    before: dict[str, object] = {}
    final: dict[str, object] = {}
    tool_names: list[str] = []

    try:
        async with Client(server) as client:
            listed = await client.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)
            capability_result = await client.call_tool("ck3_get_capabilities", {})
            results.append(capability_result)
            before = await _take_snapshot(client, results, label="before")
            final = before
            _append_sample(samples, before, war_id=war_id)
            if (
                before.get("paused") is not True
                or before.get("active_event") is not None
                or before.get("date_raw") != expected_date_raw
            ):
                raise RuntimeError("source frame is not the expected paused war")
            _assert_live_identity(
                before, war_id=war_id, character_id=expected_character_id
            )

            deadline = time.monotonic() + horizon_timeout
            current = before
            target_reached = False
            while time.monotonic() < deadline:
                if current.get("active_event") is None:
                    revision = _plain_revision(current, label="resume frame")
                    commands.append("resume-map")
                    resume = await client.call_tool(
                        "ck3_execute_step",
                        {"step": "resume-map", "expected_revision": revision},
                    )
                    results.append(resume)
                    base._structured(resume, tool_name="ck3_execute_step:resume")

                running_observed = False
                boundary: dict[str, object] | None = None
                while time.monotonic() < deadline:
                    current = await _take_snapshot(client, results, label="horizon")
                    final = current
                    _append_sample(samples, current, war_id=war_id)
                    _assert_live_identity(
                        current,
                        war_id=war_id,
                        character_id=expected_character_id,
                    )
                    date_raw = current.get("date_raw")
                    if isinstance(date_raw, bool) or not isinstance(date_raw, int):
                        raise RuntimeError("horizon snapshot lacks date_raw")
                    if current.get("active_event") is not None:
                        boundary = current
                        break
                    if current.get("paused") is False:
                        running_observed = True
                    elif running_observed and date_raw < target_date_raw:
                        raise RuntimeError("map paused before the horizon")
                    if date_raw >= target_date_raw:
                        boundary = current
                        target_reached = True
                        break
                    await asyncio.sleep(poll_interval)
                if boundary is None:
                    raise RuntimeError("white-peace horizon timed out")

                current = await _pause_boundary(
                    client,
                    results,
                    commands,
                    samples,
                    boundary,
                    war_id=war_id,
                    poll_interval=poll_interval,
                )
                final = current
                _assert_live_identity(
                    current, war_id=war_id, character_id=expected_character_id
                )
                if target_reached:
                    break

                if event_continuations:
                    raise RuntimeError("a second event interrupted the bounded horizon")
                active_event = current.get("active_event")
                event_instance_id = (
                    active_event.get("instance_id")
                    if isinstance(active_event, dict)
                    else None
                )
                if (
                    isinstance(event_instance_id, bool)
                    or not isinstance(event_instance_id, int)
                    or event_instance_id <= 0
                ):
                    raise RuntimeError("event boundary lacks a stable instance")
                revision = _plain_revision(current, label="event boundary")
                commands.append(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
                context_result = await client.call_tool(
                    "ck3_query_current_event_window_context_v1",
                    {
                        "event_instance_id": event_instance_id,
                        "expected_revision": revision,
                    },
                )
                results.append(context_result)
                context_query = base._structured(
                    context_result,
                    tool_name="ck3_query_current_event_window_context_v1",
                )
                context = context_query.get("current_event_window_context")
                if not isinstance(context, dict):
                    raise RuntimeError("event query returned no typed context")
                decision = registered._recommend_exact_registered_option(
                    snapshot=current,
                    event_context=context,
                    expected_event_key=expected_event_key,
                    expected_character_id=expected_character_id,
                )
                option_number = decision.get("selected_option_number")
                if isinstance(option_number, bool) or not isinstance(option_number, int):
                    raise RuntimeError("registry recommendation lacks an option number")
                step = event_option_step(option_number)
                commands.append(step)
                selection_result = await client.call_tool(
                    "ck3_select_event_option",
                    {
                        "option_number": option_number,
                        "event_instance_id": event_instance_id,
                        "expected_revision": revision,
                    },
                )
                results.append(selection_result)
                selection = base._structured(
                    selection_result, tool_name="ck3_select_event_option"
                )
                current = await _take_snapshot(
                    client, results, label="after-event-selection"
                )
                final = current
                _append_sample(samples, current, war_id=war_id)
                _assert_live_identity(
                    current, war_id=war_id, character_id=expected_character_id
                )
                if current.get("active_event") is not None:
                    raise RuntimeError("registered event did not resolve cleanly")
                if current.get("paused") is not True:
                    raise RuntimeError("event selection postcondition is not paused")
                event_continuations.append(
                    {
                        "event_context": context,
                        "registry_decision": decision,
                        "selection": selection,
                        "post_snapshot": horizon._compact_snapshot(
                            current, war_id=war_id
                        ),
                    }
                )

            if not target_reached:
                raise RuntimeError("white-peace horizon timed out")
            date_raw = final.get("date_raw")
            if (
                isinstance(date_raw, bool)
                or not isinstance(date_raw, int)
                or date_raw < target_date_raw
                or date_raw > target_date_raw + horizon.MAX_OVERSHOOT_RAW
            ):
                raise RuntimeError("paused horizon exceeded its date bound")
            if final.get("active_event") is not None:
                raise RuntimeError("event occupied the horizon boundary")

            revision = _plain_revision(final, label="termination boundary")
            options_step = query_war_termination_options_step(war_id)
            commands.append(options_step)
            options_result = await client.call_tool(
                "ck3_query_war_termination_options",
                {"war_id": war_id, "expected_revision": revision},
            )
            results.append(options_result)
            options_query = base._structured(
                options_result, tool_name="ck3_query_war_termination_options"
            )
            options, admission_checks = horizon._white_peace_admission(
                options_query, war_id=war_id
            )
            if not all(admission_checks.values()):
                raise RuntimeError("white peace is unavailable at the horizon")

            final = await _take_snapshot(client, results, label="pre-save")
            _append_sample(samples, final, war_id=war_id)
            revision = _plain_revision(final, label="pre-save frame")
            commands.append("save-checkpoint")
            save_result = await client.call_tool(
                "ck3_save_checkpoint", {"expected_revision": revision}
            )
            results.append(save_result)
            save = base._structured(save_result, tool_name="ck3_save_checkpoint")
            value = save.get("checkpoint")
            checkpoint = dict(value) if isinstance(value, dict) else None
            final = await _take_snapshot(client, results, label="final")
            _append_sample(samples, final, war_id=war_id)
    except BaseException as error:
        sequence_error = registered._format_sequence_error(error)

    final_date = final.get("date_raw")
    checkpoint_path = (
        Path(str(checkpoint.get("path"))).resolve()
        if isinstance(checkpoint, dict) and checkpoint.get("path")
        else None
    )
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_execute_step",
                "ck3_query_current_event_window_context_v1",
                "ck3_select_event_option",
                "ck3_query_war_termination_options",
                "ck3_save_checkpoint",
            )
        ),
        "mcp_results_not_errors": bool(results)
        and not any(bool(getattr(result, "is_error", False)) for result in results),
        "sequence_error_absent": sequence_error is None,
        "one_registered_event_continued": len(event_continuations) == 1,
        "target_reached": isinstance(final_date, int)
        and not isinstance(final_date, bool)
        and target_date_raw
        <= final_date
        <= target_date_raw + horizon.MAX_OVERSHOOT_RAW,
        "final_paused": final.get("paused") is True,
        "same_character": horizon._played_character_id(final)
        == expected_character_id,
        "war_still_active": horizon._active_war(final, war_id) is not None,
        "no_active_event": final.get("active_event") is None,
        "white_peace_admitted": bool(admission_checks)
        and all(admission_checks.values()),
        "checkpoint_materialized": isinstance(checkpoint, dict)
        and checkpoint.get("status") == "saved"
        and checkpoint.get("date_raw") == final_date
        and checkpoint_path is not None
        and checkpoint_path.is_file(),
        **horizon._history_checks(before, final, expected_commands=commands),
    }
    return {
        "source_date_raw": expected_date_raw,
        "target_date_raw": target_date_raw,
        "maximum_overshoot_raw": horizon.MAX_OVERSHOOT_RAW,
        "horizon_timeout_seconds": horizon_timeout,
        "poll_interval_seconds": poll_interval,
        "expected_event_key": expected_event_key,
        "maximum_event_continuations": 1,
        "allowed_gameplay_commands": [
            "resume-map",
            "pause-map",
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "select-event-option-N",
            query_war_termination_options_step(war_id),
            "save-checkpoint",
        ],
        "forbidden_commands": [
            "surrender-war-N",
            "offer-white-peace-N",
            "enforce-demands-N",
            evaluation.DISABLED_BROAD_PREVIEW_COMMAND_PREFIX,
        ],
        "expected_command_delta": commands,
        "snapshot_samples": samples,
        "event_continuations": event_continuations,
        "normalized_termination_options": options,
        "white_peace_admission_checks": admission_checks,
        "prepared_checkpoint": checkpoint,
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
            sequence_runner = functools.partial(
                _run_mcp_sequence,
                target_date_raw=args.target_date_raw,
                expected_event_key=args.expected_event_key,
                horizon_timeout=args.horizon_timeout,
                poll_interval=args.poll_interval,
            )
            payload, exit_code = base._run(
                args,
                sequence_runner=sequence_runner,
                exact_build_runner=_exact_build_proof,
                report_kind=REPORT_KIND,
                policy_override={
                    "mcp_first": True,
                    "production_non_debug": True,
                    "cold_checkpoint": True,
                    "ocr_used": False,
                    "visual_input_used": False,
                    "time_advanced": True,
                    "maximum_ck3_launches": 1,
                    "resume_commands_maximum": 2,
                    "pause_commands_maximum": 2,
                    "event_context_queries": 1,
                    "event_selections": 1,
                    "termination_option_queries": 1,
                    "checkpoint_saves_maximum": 1,
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
