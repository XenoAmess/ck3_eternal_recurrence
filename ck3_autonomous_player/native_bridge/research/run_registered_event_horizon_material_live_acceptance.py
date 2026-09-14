#!/usr/bin/env python3
"""Reach and close one registered event with a material postcondition.

Cold-restore an immutable paused checkpoint, resolve an ordered list of
registered prelude events through the production registry, then close the
target event and verify its registered material state change.  Time may advance
only as far as the caller's exact target date.
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
from typing import Any, Mapping


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_registered_event_material_live_acceptance as material  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.event_contract import event_option_step  # noqa: E402
from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.vanilla_events.outcome import (  # noqa: E402
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


REPORT_KIND = "ck3_registered_event_horizon_material_live_acceptance"
RESUME_CAPABILITY = "game.command.resume-map"
PAUSE_CAPABILITY = "game.command.pause-map"


def _parser() -> argparse.ArgumentParser:
    parser = material._parser()
    parser.description = __doc__
    parser.add_argument("--target-date-raw", type=int, required=True)
    parser.add_argument(
        "--expected-prelude-event",
        action="append",
        default=[],
        help="Expected registered event key before the target; repeat in order.",
    )
    parser.add_argument("--horizon-timeout", type=float, default=180.0)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    return parser


def _source_checkpoint_anchor(
    driver_state_path: Path,
    *,
    expected_checkpoint_sha256: str,
    expected_date_raw: int,
) -> dict[str, object]:
    anchor = base._driver_anchor(driver_state_path)
    checkpoint = material._mapping(anchor.get("last_checkpoint"))
    expected_hash = base._expected_sha256(
        expected_checkpoint_sha256, "expected checkpoint SHA-256"
    )
    if not (
        str(checkpoint.get("sha256", "")).upper() == expected_hash
        and checkpoint.get("date_raw") == expected_date_raw
        and checkpoint.get("status") == "saved"
        and isinstance(checkpoint.get("history_index"), int)
        and not isinstance(checkpoint.get("history_index"), bool)
    ):
        raise RuntimeError("source driver-state does not bind the requested checkpoint")
    return {
        "episode_character_id": anchor.get("episode_character_id"),
        "episode_run_id": anchor.get("episode_run_id"),
        "pipe_name": anchor.get("pipe_name"),
        "checkpoint": copy.deepcopy(dict(checkpoint)),
    }


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    result = material._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
    )
    raw = material._mapping(capabilities)
    advertised = raw.get("bridge_capabilities")
    steps = raw.get("action_steps")
    # The cold source is deliberately event-free, so concrete query/select
    # steps are not present until the first event becomes active. Their generic
    # capabilities remain required and every live call is checked after the
    # event appears.
    result["checks"]["action_steps"] = (
        isinstance(steps, list)
        and "save-checkpoint" in steps
        and "resume-map" in steps
        and "pause-map" in steps
    )
    result["checks"].update(
        {
            "timeline_capabilities": isinstance(advertised, list)
            and RESUME_CAPABILITY in advertised
            and PAUSE_CAPABILITY in advertised,
            "timeline_steps": isinstance(steps, list)
            and "resume-map" in steps
            and "pause-map" in steps,
        }
    )
    result["ok"] = all(result["checks"].values())
    return result


def _revision(snapshot: Mapping[str, object], *, label: str) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{label} lacks a public revision")
    return value


def _event_instance(snapshot: Mapping[str, object]) -> int | None:
    value = material._mapping(snapshot.get("active_event")).get("instance_id")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _compact_snapshot(snapshot: Mapping[str, object]) -> dict[str, object]:
    player = material._mapping(snapshot.get("played_character"))
    gold = material._mapping(snapshot.get("played_character_gold"))
    active = material._mapping(snapshot.get("active_event"))
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "character_id": player.get("character_id"),
        "stress_points": player.get("stress_points"),
        "gold": copy.deepcopy(dict(gold)) if gold else None,
        "active_event": {
            "instance_id": active.get("instance_id"),
            "option_count": active.get("option_count"),
        }
        if active
        else None,
    }


async def _snapshot(client: Any, results: list[object], *, label: str) -> dict[str, object]:
    result = await client.call_tool("ck3_take_snapshot", {})
    results.append(result)
    return base._structured(result, tool_name=f"ck3_take_snapshot:{label}")


def _assert_identity(
    snapshot: Mapping[str, object],
    *,
    expected_character_id: int,
    maximum_date_raw: int,
) -> None:
    if material._played_character_id(snapshot) != expected_character_id:
        raise RuntimeError("played character changed during event horizon")
    date_raw = snapshot.get("date_raw")
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or date_raw > maximum_date_raw
    ):
        raise RuntimeError("event horizon exceeded its exact date bound")


async def _pause_if_needed(
    client: Any,
    results: list[object],
    commands: list[str],
    snapshot: dict[str, object],
    *,
    poll_interval: float,
) -> dict[str, object]:
    current = snapshot
    if current.get("paused") is not True:
        commands.append("pause-map")
        result = await client.call_tool(
            "ck3_execute_step",
            {"step": "pause-map", "expected_revision": _revision(current, label="pause")},
        )
        results.append(result)
        base._structured(result, tool_name="ck3_execute_step:pause")
    deadline = time.monotonic() + 10.0
    while current.get("paused") is not True and time.monotonic() < deadline:
        await asyncio.sleep(poll_interval)
        current = await _snapshot(client, results, label="pause-postcondition")
    if current.get("paused") is not True:
        raise RuntimeError("pause-map postcondition was not observed")
    return current


def _recommend(
    *,
    snapshot: Mapping[str, object],
    context: Mapping[str, object],
    expected_event_key: str,
    expected_character_id: int,
) -> dict[str, object]:
    active = material._mapping(snapshot.get("active_event"))
    options = active.get("options")
    option_count = len(options) if isinstance(options, list) else active.get("option_count")
    decision = recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=expected_character_id,
        snapshot_option_count=option_count,
    )
    if not (
        context.get("event_definition_key") == expected_event_key
        and decision.get("status") == "recommended"
        and decision.get("event_definition_key") == expected_event_key
    ):
        raise RuntimeError(
            "production registry did not authorize the expected event: "
            f"{decision.get('unavailable_reason')}"
        )
    return decision


async def _query_event(
    client: Any,
    results: list[object],
    commands: list[str],
    snapshot: Mapping[str, object],
) -> dict[str, object]:
    instance_id = _event_instance(snapshot)
    if instance_id is None:
        raise RuntimeError("event boundary lacks a stable instance")
    commands.append(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
    result = await client.call_tool(
        "ck3_query_current_event_window_context_v1",
        {
            "event_instance_id": instance_id,
            "expected_revision": _revision(snapshot, label="event query"),
        },
    )
    results.append(result)
    response = base._structured(
        result, tool_name="ck3_query_current_event_window_context_v1"
    )
    context = response.get("current_event_window_context")
    if not (
        isinstance(context, dict)
        and context.get("status") == "available"
        and context.get("current_event_instance_id") == instance_id
        and context.get("date_raw") == snapshot.get("date_raw")
    ):
        raise RuntimeError("event query did not bind the paused event frame")
    return dict(context)


async def _select(
    client: Any,
    results: list[object],
    commands: list[str],
    *,
    snapshot: Mapping[str, object],
    decision: Mapping[str, object],
) -> dict[str, object]:
    option_number = decision.get("selected_option_number")
    if isinstance(option_number, bool) or not isinstance(option_number, int):
        raise RuntimeError("registry recommendation lacks an option number")
    instance_id = _event_instance(snapshot)
    if instance_id is None:
        raise RuntimeError("event selection lacks a stable instance")
    commands.append(event_option_step(option_number))
    result = await client.call_tool(
        "ck3_select_event_option",
        {
            "option_number": option_number,
            "event_instance_id": instance_id,
            "expected_revision": _revision(snapshot, label="event selection"),
        },
    )
    results.append(result)
    return base._structured(result, tool_name="ck3_select_event_option")


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    target_date_raw: int,
    expected_event_key: str,
    expected_prelude_events: list[str],
    horizon_timeout: float,
    poll_interval: float,
) -> dict[str, object]:
    del war_id
    from mcp import Client

    if target_date_raw <= expected_date_raw:
        raise ValueError("target date must be later than the source date")
    if horizon_timeout <= 0 or poll_interval <= 0:
        raise ValueError("horizon timeout and poll interval must be positive")

    server = base.create_server(driver)
    results: list[object] = []
    commands: list[str] = []
    samples: list[dict[str, object]] = []
    preludes: list[dict[str, object]] = []
    tool_names: list[str] = []
    before: dict[str, object] = {}
    target_before: dict[str, object] = {}
    target_context: dict[str, object] = {}
    target_decision: dict[str, object] = {}
    target_selection: dict[str, object] = {}
    material_expectation: dict[str, object] = {}
    material_postcondition: dict[str, object] = {}
    final: dict[str, object] = {}
    checkpoint: dict[str, object] | None = None
    sequence_error: str | None = None

    try:
        async with Client(server) as client:
            listed = await client.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)
            results.append(await client.call_tool("ck3_get_capabilities", {}))
            before = await _snapshot(client, results, label="before")
            final = before
            samples.append(_compact_snapshot(before))
            if not (
                before.get("paused") is True
                and before.get("active_event") is None
                and before.get("date_raw") == expected_date_raw
            ):
                raise RuntimeError("source frame is not the expected paused event-free map")
            _assert_identity(
                before,
                expected_character_id=expected_character_id,
                maximum_date_raw=target_date_raw,
            )

            deadline = time.monotonic() + horizon_timeout
            current = before
            while time.monotonic() < deadline:
                if current.get("active_event") is None:
                    if current.get("date_raw") >= target_date_raw:
                        raise RuntimeError("target event did not appear by its exact date")
                    commands.append("resume-map")
                    resume = await client.call_tool(
                        "ck3_execute_step",
                        {
                            "step": "resume-map",
                            "expected_revision": _revision(current, label="resume"),
                        },
                    )
                    results.append(resume)
                    base._structured(resume, tool_name="ck3_execute_step:resume")

                boundary: dict[str, object] | None = None
                while time.monotonic() < deadline:
                    current = await _snapshot(client, results, label="horizon")
                    final = current
                    compact = _compact_snapshot(current)
                    if not samples or compact != samples[-1]:
                        samples.append(compact)
                    _assert_identity(
                        current,
                        expected_character_id=expected_character_id,
                        maximum_date_raw=target_date_raw,
                    )
                    if current.get("active_event") is not None or current.get("date_raw") >= target_date_raw:
                        boundary = current
                        break
                    await asyncio.sleep(poll_interval)
                if boundary is None:
                    raise RuntimeError("registered event horizon timed out")

                current = await _pause_if_needed(
                    client,
                    results,
                    commands,
                    boundary,
                    poll_interval=poll_interval,
                )
                final = current
                _assert_identity(
                    current,
                    expected_character_id=expected_character_id,
                    maximum_date_raw=target_date_raw,
                )
                if current.get("active_event") is None:
                    raise RuntimeError("target event was absent at the exact date boundary")

                context = await _query_event(client, results, commands, current)
                event_key = context.get("event_definition_key")
                expected_next = (
                    expected_prelude_events[len(preludes)]
                    if len(preludes) < len(expected_prelude_events)
                    else expected_event_key
                )
                if event_key != expected_next:
                    raise RuntimeError(
                        f"event order drifted: expected {expected_next}, observed {event_key}"
                    )
                decision = _recommend(
                    snapshot=current,
                    context=context,
                    expected_event_key=expected_next,
                    expected_character_id=expected_character_id,
                )

                if expected_next == expected_event_key:
                    if current.get("date_raw") != target_date_raw:
                        raise RuntimeError("target event reached outside its declared boundary")
                    target_before = current
                    target_context = context
                    target_decision = decision
                    planned = plan_registered_event_material_postcondition_v1(
                        decision,
                        current.get("played_character"),
                        played_character_gold=current.get("played_character_gold"),
                        snapshot_id=current.get("snapshot_id"),
                        revision=current.get("revision"),
                    )
                    material_expectation = dict(planned) if isinstance(planned, dict) else {}
                    if material_expectation.get("status") != "ready":
                        raise RuntimeError("target material expectation is unavailable")
                    target_selection = await _select(
                        client,
                        results,
                        commands,
                        snapshot=current,
                        decision=decision,
                    )
                    material_postcondition = dict(
                        evaluate_registered_event_material_postcondition_v1(
                            material_expectation,
                            target_selection.get("event_selection"),
                        )
                    )
                    if not (
                        material_postcondition.get("status") == "verified_change"
                        and material_postcondition.get("material_change_observed") is True
                    ):
                        raise RuntimeError("target material postcondition is not GREEN")
                    final = await _snapshot(client, results, label="target-after")
                    if not (
                        final.get("paused") is True
                        and final.get("date_raw") == target_date_raw
                        and material._played_character_id(final) == expected_character_id
                        and _event_instance(final) != _event_instance(target_before)
                    ):
                        raise RuntimeError("target event did not produce a paused successor")
                    commands.append("save-checkpoint")
                    save_result = await client.call_tool(
                        "ck3_save_checkpoint",
                        {"expected_revision": _revision(final, label="successor save")},
                    )
                    results.append(save_result)
                    save = base._structured(save_result, tool_name="ck3_save_checkpoint")
                    value = save.get("checkpoint")
                    checkpoint = dict(value) if isinstance(value, dict) else None
                    final = await _snapshot(client, results, label="final")
                    break

                selection = await _select(
                    client,
                    results,
                    commands,
                    snapshot=current,
                    decision=decision,
                )
                successor = await _snapshot(client, results, label="prelude-after")
                if not (
                    successor.get("paused") is True
                    and successor.get("active_event") is None
                    and _event_instance(successor) != _event_instance(current)
                ):
                    raise RuntimeError("registered prelude event did not resolve cleanly")
                preludes.append(
                    {
                        "event_context": context,
                        "registry_decision": decision,
                        "selection": selection,
                        "post_snapshot": _compact_snapshot(successor),
                    }
                )
                current = successor
            else:
                raise RuntimeError("registered event horizon timed out")
    except BaseException as error:
        sequence_error = material._format_sequence_error(error)

    delta = material._history_delta(before, final)
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
                "ck3_save_checkpoint",
            )
        ),
        "mcp_results_not_errors": bool(results)
        and not any(bool(getattr(result, "is_error", False)) for result in results),
        "sequence_error_absent": sequence_error is None,
        "ordered_preludes_resolved": [
            material._mapping(item.get("event_context")).get("event_definition_key")
            for item in preludes
        ]
        == expected_prelude_events,
        "target_registry_recommended": target_decision.get("status") == "recommended"
        and target_decision.get("event_definition_key") == expected_event_key,
        "target_campaign_utility_ready": isinstance(
            target_decision.get("campaign_utility_profile"), dict
        ),
        "target_material_change_verified": material_postcondition.get("status")
        == "verified_change"
        and material_postcondition.get("material_change_observed") is True,
        "target_event_instance_advanced": _event_instance(final)
        != _event_instance(target_before),
        "final_paused_identity": final.get("paused") is True
        and final.get("date_raw") == target_date_raw
        and material._played_character_id(final) == expected_character_id,
        "exact_command_delta": delta == [(command, True) for command in commands],
        "checkpoint_materialized": isinstance(checkpoint, dict)
        and checkpoint.get("status") == "saved"
        and checkpoint.get("date_raw") == target_date_raw
        and checkpoint_path is not None
        and checkpoint_path.is_file(),
    }
    return {
        "source_date_raw": expected_date_raw,
        "target_date_raw": target_date_raw,
        "expected_event_key": expected_event_key,
        "expected_prelude_events": expected_prelude_events,
        "horizon_timeout_seconds": horizon_timeout,
        "poll_interval_seconds": poll_interval,
        "allowed_gameplay_commands": [
            "resume-map",
            "pause-map",
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "select-event-option-N",
            "save-checkpoint",
        ],
        "forbidden_commands": [
            "life-advance",
            "surrender-war-N",
            "offer-white-peace-N",
            "enforce-demands-N",
        ],
        "snapshot_samples": samples,
        "prelude_events": preludes,
        "target_before_snapshot": _compact_snapshot(target_before),
        "target_event_context": target_context,
        "target_registry_decision": target_decision,
        "target_material_expectation": material_expectation,
        "target_selection": target_selection,
        "target_material_postcondition": material_postcondition,
        "successor_checkpoint": checkpoint,
        "final_snapshot": _compact_snapshot(final),
        "command_delta": delta,
        "expected_command_delta": commands,
        "sequence_error": sequence_error,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _preflight_path(args: argparse.Namespace) -> Path:
    if isinstance(args.preflight_report, Path):
        return args.preflight_report.expanduser().resolve()
    attempt = args.attempt_dir.expanduser().resolve()
    return attempt.with_name(attempt.name + "-no-launch-preflight.json")


def _preflight(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    report_path = _preflight_path(args)
    if report_path.exists():
        raise RuntimeError(f"preflight report already exists: {report_path}")
    error: str | None = None
    identities: dict[str, object] = {}
    anchor: dict[str, object] = {}
    try:
        expected_checkpoint = base._expected_sha256(
            args.expected_checkpoint_sha256, "expected checkpoint SHA-256"
        )
        expected_driver = base._expected_sha256(
            args.expected_driver_state_sha256, "expected driver-state SHA-256"
        )
        identities = {
            "checkpoint_sha256": base._sha256_file(args.source_checkpoint.resolve()),
            "driver_state_sha256": base._sha256_file(args.source_driver_state.resolve()),
            "game_executable_sha256": base._sha256_file(
                args.game_dir.resolve() / "binaries" / "ck3.exe"
            ),
            "bridge_dll_sha256": base._sha256_file(args.bridge_dll.resolve()),
            "bridge_injector_sha256": base._sha256_file(args.bridge_injector.resolve()),
        }
        anchor = _source_checkpoint_anchor(
            args.source_driver_state.resolve(),
            expected_checkpoint_sha256=expected_checkpoint,
            expected_date_raw=args.expected_date_raw,
        )
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
        expected_checkpoint = str(args.expected_checkpoint_sha256).upper()
        expected_driver = str(args.expected_driver_state_sha256).upper()
    checks = {
        "attempt_dir_unused": not args.attempt_dir.resolve().exists(),
        "checkpoint_hash": identities.get("checkpoint_sha256") == expected_checkpoint,
        "driver_state_hash": identities.get("driver_state_sha256") == expected_driver,
        "exact_game_executable": identities.get("game_executable_sha256")
        == base.EXPECTED_EXECUTABLE_SHA256,
        "bridge_dll_present": isinstance(identities.get("bridge_dll_sha256"), str),
        "bridge_injector_present": isinstance(identities.get("bridge_injector_sha256"), str),
        "driver_character": anchor.get("episode_character_id")
        == args.expected_character_id,
        "checkpoint_bound": bool(anchor),
        "bounded_target_date": args.target_date_raw > args.expected_date_raw,
        "declared_event_order": all(
            isinstance(item, str) and bool(item.strip())
            for item in args.expected_prelude_event
        ),
        "preflight_did_not_launch_ck3": True,
        "preflight_did_not_prepare_profile": True,
    }
    ok = error is None and all(checks.values())
    payload = {
        "format_version": 1,
        "kind": "ck3_registered_event_horizon_material_no_launch_preflight",
        "status": "ready-to-run" if ok else "red",
        "ok": ok,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ck3_started": False,
        "profile_prepared": False,
        "attempt_dir": str(args.attempt_dir.resolve()),
        "report_path": str(report_path),
        "requested_identity": {
            "event_definition_key": args.expected_event_key,
            "character_id": args.expected_character_id,
            "source_date_raw": args.expected_date_raw,
            "target_date_raw": args.target_date_raw,
            "expected_prelude_events": args.expected_prelude_event,
        },
        "identities": identities,
        "source_checkpoint_anchor": anchor,
        "checks": checks,
        "error": error,
    }
    base._write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        preflight_payload, preflight_exit = _preflight(args)
        if args.preflight_only or preflight_exit != 0:
            payload = preflight_payload
            exit_code = preflight_exit
        else:
            args.war_id = 0
            payload, exit_code = base._run(
                args,
                sequence_runner=functools.partial(
                    _run_mcp_sequence,
                    target_date_raw=args.target_date_raw,
                    expected_event_key=args.expected_event_key,
                    expected_prelude_events=list(args.expected_prelude_event),
                    horizon_timeout=args.horizon_timeout,
                    poll_interval=args.poll_interval,
                ),
                exact_build_runner=_exact_build_proof,
                report_kind=REPORT_KIND,
                policy_override={
                    "mcp_first": True,
                    "production_non_debug": True,
                    "cold_checkpoint": True,
                    "maximum_ck3_launches": 1,
                    "time_advanced": True,
                    "maximum_date_raw": args.target_date_raw,
                    "expected_prelude_events": list(args.expected_prelude_event),
                    "target_event_selections": 1,
                    "checkpoint_saves": 1,
                    "war_actions": 0,
                },
            )
            payload["requested_identity"] = preflight_payload["requested_identity"]
            payload["source_checkpoint_anchor"] = preflight_payload[
                "source_checkpoint_anchor"
            ]
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
