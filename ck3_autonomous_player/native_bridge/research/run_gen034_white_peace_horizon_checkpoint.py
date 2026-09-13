#!/usr/bin/env python3
"""Prepare one bounded Raiktor checkpoint at the white-peace horizon.

The runner cold-restores an existing pre-action Raiktor checkpoint, resumes
time once through the official MCP surface, and polls read-only snapshots.  It
stops on the first event, identity drift, ended war, unexpected native pause,
or the requested date.  At the date boundary it pauses once, queries the
native termination options once, and saves only when the white-peace option
and its final recipient response are observable.  It never selects an event
or submits a war-termination action.
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
import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    normalize_war_termination_options,
    query_war_termination_options_step,
)


REPORT_KIND = "ck3_gen034_white_peace_horizon_checkpoint"
MAX_OVERSHOOT_RAW = 7 * 24


def _parser() -> argparse.ArgumentParser:
    parser = evaluation._parser()
    parser.description = __doc__
    parser.add_argument("--target-date-raw", type=int, required=True)
    parser.add_argument("--horizon-timeout", type=float, default=180.0)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    return parser


def _active_war(
    snapshot: dict[str, object], war_id: int
) -> dict[str, object] | None:
    rows = snapshot.get("active_wars")
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get("war_id") == war_id:
            return row
    return None


def _played_character_id(snapshot: dict[str, object]) -> int | None:
    played = snapshot.get("played_character")
    if not isinstance(played, dict):
        return None
    value = played.get("character_id")
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool)
        else None
    )


def _compact_snapshot(
    snapshot: dict[str, object], *, war_id: int
) -> dict[str, object]:
    event = snapshot.get("active_event")
    war = _active_war(snapshot, war_id)
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "speed": snapshot.get("speed"),
        "paused": snapshot.get("paused"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "character_id": _played_character_id(snapshot),
        "active_event": (
            {
                "instance_id": event.get("instance_id"),
                "title": event.get("title"),
                "source": event.get("source"),
                "option_count": len(event.get("options", []))
                if isinstance(event.get("options"), list)
                else None,
            }
            if isinstance(event, dict)
            else None
        ),
        "war": (
            {
                "war_id": war.get("war_id"),
                "player_side": war.get("player_side"),
                "player_is_primary_war_leader": war.get(
                    "player_is_primary_war_leader"
                ),
                "primary_opponent_character_id": war.get(
                    "primary_opponent_character_id"
                ),
                "player_relative_war_score": war.get(
                    "player_relative_war_score"
                ),
            }
            if isinstance(war, dict)
            else None
        ),
    }


def _history_checks(
    before: dict[str, object],
    after: dict[str, object],
    *,
    expected_commands: list[str],
) -> dict[str, bool]:
    before_history = before.get("native_command_history")
    after_history = after.get("native_command_history")
    if not isinstance(before_history, list) or not isinstance(
        after_history, list
    ):
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


def _white_peace_admission(
    query: dict[str, object], *, war_id: int
) -> tuple[dict[str, object], dict[str, bool]]:
    options = normalize_war_termination_options(
        query.get("war_termination_options"), expected_war_id=war_id
    )
    white = options["options"]["white_peace"]
    assert isinstance(white, dict)
    response = white.get("recipient_response")
    checks = {
        "war_duration_reached": isinstance(
            options.get("war_duration_days"), int
        )
        and int(options["war_duration_days"]) >= 365,
        "white_peace_context_constructed": white.get("context_constructed")
        is True,
        "white_peace_native_validator": white.get(
            "native_validator_passed"
        )
        is True,
        "white_peace_available": white.get("available") is True,
        "final_recipient_response_available": isinstance(response, dict)
        and response.get("status") == "available",
    }
    return options, checks


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    result = evaluation._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
    )
    raw = capabilities if isinstance(capabilities, dict) else {}
    steps = raw.get("action_steps")
    step_set = set(steps) if isinstance(steps, list) else set()
    result["checks"].update(
        {
            "resume_map_step": "resume-map" in step_set,
            "pause_map_step": "pause-map" in step_set,
            "save_checkpoint_step": "save-checkpoint" in step_set,
        }
    )
    result["ok"] = all(result["checks"].values())
    return result


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    target_date_raw: int,
    horizon_timeout: float,
    poll_interval: float,
) -> dict[str, object]:
    from mcp import Client

    if target_date_raw <= expected_date_raw:
        raise ValueError("target date must be later than the source date")
    if horizon_timeout <= 0 or poll_interval <= 0:
        raise ValueError("horizon timeout and poll interval must be positive")

    server = base.create_server(driver)
    mcp_results: list[object] = []
    expected_commands: list[str] = []
    samples: list[dict[str, object]] = []
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
            capabilities_result = await client.call_tool(
                "ck3_get_capabilities", {}
            )
            mcp_results.append(capabilities_result)
            before_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(before_result)
            before = base._structured(
                before_result, tool_name="ck3_take_snapshot:before"
            )
            final = before
            samples.append(_compact_snapshot(before, war_id=war_id))
            if (
                before.get("paused") is not True
                or before.get("active_event") is not None
                or before.get("date_raw") != expected_date_raw
                or _played_character_id(before) != expected_character_id
                or _active_war(before, war_id) is None
            ):
                raise RuntimeError("source frame is not the expected paused war")

            revision = before.get("revision")
            if isinstance(revision, bool) or not isinstance(revision, int):
                raise RuntimeError("source frame lacks a public revision")
            resume_result = await client.call_tool(
                "ck3_execute_step",
                {"step": "resume-map", "expected_revision": revision},
            )
            mcp_results.append(resume_result)
            base._structured(resume_result, tool_name="ck3_execute_step:resume")
            expected_commands.append("resume-map")

            deadline = time.monotonic() + horizon_timeout
            running_observed = False
            boundary: dict[str, object] | None = None
            while time.monotonic() < deadline:
                snapshot_result = await client.call_tool(
                    "ck3_take_snapshot", {}
                )
                mcp_results.append(snapshot_result)
                snapshot = base._structured(
                    snapshot_result, tool_name="ck3_take_snapshot:horizon"
                )
                final = snapshot
                compact = _compact_snapshot(snapshot, war_id=war_id)
                if not samples or compact != samples[-1]:
                    samples.append(compact)
                if _played_character_id(snapshot) != expected_character_id:
                    raise RuntimeError("played character changed during horizon")
                if _active_war(snapshot, war_id) is None:
                    raise RuntimeError("Raiktor war ended before the horizon")
                if snapshot.get("active_event") is not None:
                    raise RuntimeError("event encountered before the horizon")
                date_raw = snapshot.get("date_raw")
                if isinstance(date_raw, bool) or not isinstance(date_raw, int):
                    raise RuntimeError("horizon snapshot lacks date_raw")
                if snapshot.get("paused") is False:
                    running_observed = True
                elif running_observed and date_raw < target_date_raw:
                    raise RuntimeError("map paused before the horizon")
                if date_raw >= target_date_raw:
                    boundary = snapshot
                    break
                await asyncio.sleep(poll_interval)
            if boundary is None:
                raise RuntimeError("white-peace horizon timed out")
            if boundary.get("paused") is not True:
                pause_result = await client.call_tool(
                    "ck3_execute_step", {"step": "pause-map"}
                )
                mcp_results.append(pause_result)
                base._structured(
                    pause_result, tool_name="ck3_execute_step:pause"
                )
                expected_commands.append("pause-map")
                pause_deadline = time.monotonic() + 10.0
                while time.monotonic() < pause_deadline:
                    snapshot_result = await client.call_tool(
                        "ck3_take_snapshot", {}
                    )
                    mcp_results.append(snapshot_result)
                    boundary = base._structured(
                        snapshot_result,
                        tool_name="ck3_take_snapshot:paused-boundary",
                    )
                    compact = _compact_snapshot(boundary, war_id=war_id)
                    if not samples or compact != samples[-1]:
                        samples.append(compact)
                    if boundary.get("paused") is True:
                        break
                    await asyncio.sleep(poll_interval)
            if boundary.get("paused") is not True:
                raise RuntimeError("pause-map postcondition was not observed")
            final = boundary
            if boundary.get("active_event") is not None:
                raise RuntimeError("event occupied the horizon boundary")
            boundary_date = boundary.get("date_raw")
            if (
                isinstance(boundary_date, bool)
                or not isinstance(boundary_date, int)
                or boundary_date < target_date_raw
                or boundary_date > target_date_raw + MAX_OVERSHOOT_RAW
            ):
                raise RuntimeError("paused horizon exceeded its date bound")
            boundary_revision = boundary.get("revision")
            if isinstance(boundary_revision, bool) or not isinstance(
                boundary_revision, int
            ):
                raise RuntimeError("paused horizon lacks a public revision")

            options_result = await client.call_tool(
                "ck3_query_war_termination_options",
                {"war_id": war_id, "expected_revision": boundary_revision},
            )
            mcp_results.append(options_result)
            options_query = base._structured(
                options_result,
                tool_name="ck3_query_war_termination_options",
            )
            expected_commands.append(query_war_termination_options_step(war_id))
            options, admission_checks = _white_peace_admission(
                options_query, war_id=war_id
            )
            pre_save_result = await client.call_tool(
                "ck3_take_snapshot", {}
            )
            mcp_results.append(pre_save_result)
            pre_save = base._structured(
                pre_save_result, tool_name="ck3_take_snapshot:pre-save"
            )
            final = pre_save
            compact = _compact_snapshot(pre_save, war_id=war_id)
            if not samples or compact != samples[-1]:
                samples.append(compact)
            if not all(admission_checks.values()):
                raise RuntimeError("white peace is unavailable at the horizon")

            pre_save_revision = pre_save.get("revision")
            if isinstance(pre_save_revision, bool) or not isinstance(
                pre_save_revision, int
            ):
                raise RuntimeError("pre-save frame lacks a public revision")
            save_result = await client.call_tool(
                "ck3_save_checkpoint",
                {"expected_revision": pre_save_revision},
            )
            mcp_results.append(save_result)
            save = base._structured(
                save_result, tool_name="ck3_save_checkpoint"
            )
            expected_commands.append("save-checkpoint")
            checkpoint_value = save.get("checkpoint")
            checkpoint = (
                dict(checkpoint_value)
                if isinstance(checkpoint_value, dict)
                else None
            )
            final_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(final_result)
            final = base._structured(
                final_result, tool_name="ck3_take_snapshot:final"
            )
            samples.append(_compact_snapshot(final, war_id=war_id))
    except BaseException as error:
        sequence_error = f"{type(error).__name__}: {error}"

    history = _history_checks(
        before, final, expected_commands=expected_commands
    )
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
                "ck3_query_war_termination_options",
                "ck3_save_checkpoint",
            )
        ),
        "mcp_results_not_errors": bool(mcp_results)
        and not any(
            bool(getattr(result, "is_error", False))
            for result in mcp_results
        ),
        "sequence_error_absent": sequence_error is None,
        "target_reached": isinstance(final_date, int)
        and not isinstance(final_date, bool)
        and target_date_raw <= final_date <= target_date_raw + MAX_OVERSHOOT_RAW,
        "final_paused": final.get("paused") is True,
        "same_character": _played_character_id(final)
        == expected_character_id,
        "war_still_active": _active_war(final, war_id) is not None,
        "no_active_event": final.get("active_event") is None,
        "white_peace_admitted": bool(admission_checks)
        and all(admission_checks.values()),
        "checkpoint_materialized": isinstance(checkpoint, dict)
        and checkpoint.get("status") == "saved"
        and checkpoint.get("date_raw") == final_date
        and checkpoint_path is not None
        and checkpoint_path.is_file(),
        **history,
    }
    return {
        "source_date_raw": expected_date_raw,
        "target_date_raw": target_date_raw,
        "maximum_overshoot_raw": MAX_OVERSHOOT_RAW,
        "horizon_timeout_seconds": horizon_timeout,
        "poll_interval_seconds": poll_interval,
        "allowed_gameplay_commands": [
            "resume-map",
            "pause-map",
            query_war_termination_options_step(war_id),
            "save-checkpoint",
        ],
        "forbidden_commands": [
            "select-event-option-N",
            "surrender-war-N",
            "offer-white-peace-N",
            "enforce-demands-N",
            evaluation.DISABLED_BROAD_PREVIEW_COMMAND_PREFIX,
        ],
        "expected_command_delta": expected_commands,
        "snapshot_samples": samples,
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
        preflight_payload, preflight_exit = preflight._no_launch_preflight(
            args
        )
        if args.preflight_only or preflight_exit != 0:
            payload = preflight_payload
            exit_code = preflight_exit
        else:
            sequence_runner = functools.partial(
                _run_mcp_sequence,
                target_date_raw=args.target_date_raw,
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
                    "resume_commands": 1,
                    "pause_commands_maximum": 1,
                    "termination_option_queries": 1,
                    "checkpoint_saves_maximum": 1,
                    "mutation_commands": [
                        "resume-map",
                        "pause-map",
                        "save-checkpoint",
                    ],
                    "event_selection_enabled": False,
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
