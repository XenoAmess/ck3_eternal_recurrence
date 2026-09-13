#!/usr/bin/env python3
"""Close one registered event recommendation/action/material loop.

The runner cold-restores an immutable checkpoint whose driver history binds a
source-reviewed current-event query to the save.  It rebinds that exact query
to the restored snapshot, runs the production registry policy, selects its one
recommended option, checks the material postcondition, then saves one successor
checkpoint.  It never resumes time or submits a war action.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import functools
import hashlib
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

import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.event_contract import event_option_step  # noqa: E402
from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.vanilla_events.outcome import (  # noqa: E402
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


REPORT_KIND = "ck3_registered_event_material_live_acceptance"
SELECT_EVENT_CAPABILITY = "game.command.select-event-option-N"
SAVE_CHECKPOINT_CAPABILITY = "game.command.save-checkpoint"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--expected-driver-state-sha256", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--expected-event-key", required=True)
    parser.add_argument("--expected-production-tree-sha256")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--readiness-timeout", type=float, default=180.0)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preflight-report", type=Path)
    return parser


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _format_sequence_error(error: BaseException) -> str:
    headline = f"{type(error).__name__}: {error}"
    nested = getattr(error, "exceptions", None)
    if not isinstance(nested, tuple) or not nested:
        return headline
    return headline + " [" + "; ".join(
        _format_sequence_error(item) for item in nested
    ) + "]"


def _source_event_anchor(
    driver_state_path: Path,
    *,
    expected_checkpoint_sha256: str,
    expected_date_raw: int,
    expected_event_key: str,
) -> dict[str, object]:
    """Return the last event query sealed by only read-only rows and a save."""

    try:
        state = json.loads(driver_state_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"source driver-state is unavailable: {error}") from error
    history = state.get("command_history") if isinstance(state, dict) else None
    checkpoint = state.get("last_checkpoint") if isinstance(state, dict) else None
    if not isinstance(history, list) or not isinstance(checkpoint, dict):
        raise RuntimeError("source driver-state lacks checkpoint history")
    save_index = checkpoint.get("history_index")
    if isinstance(save_index, bool) or not isinstance(save_index, int):
        raise RuntimeError("source checkpoint lacks its history index")
    by_index = {
        row.get("index"): row
        for row in history
        if isinstance(row, dict)
        and isinstance(row.get("index"), int)
        and not isinstance(row.get("index"), bool)
    }
    save_row = by_index.get(save_index)
    save_result = _mapping(_mapping(save_row).get("result"))
    saved_checkpoint = _mapping(save_result.get("checkpoint"))
    expected_hash = base._expected_sha256(
        expected_checkpoint_sha256, "expected checkpoint SHA-256"
    )
    if not (
        _mapping(save_row).get("command") == "save-checkpoint"
        and _mapping(save_row).get("ok") is True
        and save_result.get("accepted") is True
        and str(saved_checkpoint.get("sha256", "")).upper() == expected_hash
        and saved_checkpoint.get("date_raw") == expected_date_raw
        and str(checkpoint.get("sha256", "")).upper() == expected_hash
        and checkpoint.get("date_raw") == expected_date_raw
    ):
        raise RuntimeError("source save does not match the immutable checkpoint")

    query_row: Mapping[str, object] | None = None
    intervening: list[str] = []
    for index in range(save_index - 1, 0, -1):
        row = _mapping(by_index.get(index))
        command = row.get("command")
        if command == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP:
            query_row = row
            break
        if not (
            isinstance(command, str)
            and command.startswith("query-")
            and row.get("ok") is True
        ):
            raise RuntimeError(
                "source event query is separated from the checkpoint by mutation"
            )
        intervening.append(command)
    query_result = _mapping(_mapping(query_row).get("result"))
    context = _mapping(query_result.get("current_event_window_context"))
    if not (
        query_row is not None
        and query_row.get("ok") is True
        and query_result.get("accepted") is True
        and query_result.get("status") == "available"
        and context.get("status") == "available"
        and context.get("date_raw") == expected_date_raw
        and context.get("event_definition_key") == expected_event_key
        and isinstance(context.get("current_event_instance_id"), int)
        and not isinstance(context.get("current_event_instance_id"), bool)
    ):
        raise RuntimeError("source checkpoint is not bound to the expected event")
    result = {
        "event_definition_key": expected_event_key,
        "event_instance_id": context["current_event_instance_id"],
        "date_raw": expected_date_raw,
        "query_history_index": query_row["index"],
        "save_history_index": save_index,
        "intervening_read_only_commands": list(reversed(intervening)),
        "context": copy.deepcopy(dict(context)),
    }
    result["anchor_sha256"] = _canonical_sha256(result)
    return result


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    del war_id
    raw = _mapping(capabilities)
    diagnostics = _mapping(raw.get("diagnostics"))
    hello = _mapping(diagnostics.get("hello"))
    advertised = raw.get("bridge_capabilities")
    hello_capabilities = hello.get("capabilities")
    steps = raw.get("action_steps")
    checks = {
        "game_version": hello.get("expected_ck3_version")
        == base.EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == base.EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": str(
            hello.get("expected_ck3_sha256", "")
        ).upper()
        == base.EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == base.EXPECTED_EXECUTABLE_SHA256,
        "bridge_capabilities": isinstance(advertised, list)
        and all(
            item in advertised
            for item in (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
                SELECT_EVENT_CAPABILITY,
                SAVE_CHECKPOINT_CAPABILITY,
            )
        ),
        "hello_capabilities": isinstance(hello_capabilities, list)
        and all(
            item in hello_capabilities
            for item in (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
                SELECT_EVENT_CAPABILITY,
                SAVE_CHECKPOINT_CAPABILITY,
            )
        ),
        "action_steps": isinstance(steps, list)
        and QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP in steps
        and any(
            isinstance(item, str)
            and item.startswith("select-event-option-")
            and item.removeprefix("select-event-option-").isdigit()
            for item in steps
        )
        and "save-checkpoint" in steps,
    }
    return {"checks": checks, "ok": all(checks.values())}


def _played_character_id(snapshot: Mapping[str, object]) -> int | None:
    value = _mapping(snapshot.get("played_character")).get("character_id")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _history_delta(
    before: Mapping[str, object], after: Mapping[str, object]
) -> list[tuple[object, object]]:
    prior = before.get("native_command_history")
    final = after.get("native_command_history")
    if not isinstance(prior, list) or not isinstance(final, list):
        return []
    return [
        (row.get("command"), row.get("ok"))
        for row in final[len(prior) :]
        if isinstance(row, dict)
    ]


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    expected_event_key: str,
    source_event_anchor: Mapping[str, object],
) -> dict[str, object]:
    del war_id
    from mcp import Client

    server = base.create_server(driver)
    mcp_results: list[object] = []
    tool_names: list[str] = []
    before: dict[str, object] = {}
    after: dict[str, object] = {}
    decision: dict[str, object] = {}
    material_expectation: dict[str, object] = {}
    selection: dict[str, object] = {}
    material: dict[str, object] = {}
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
            active_event = _mapping(before.get("active_event"))
            if not (
                before.get("paused") is True
                and before.get("date_raw") == expected_date_raw
                and _played_character_id(before) == expected_character_id
                and active_event.get("instance_id")
                == source_event_anchor.get("event_instance_id")
            ):
                raise RuntimeError("restored frame differs from the source event anchor")

            source_context = _mapping(source_event_anchor.get("context"))
            options = active_event.get("options")
            option_count = (
                len(options)
                if isinstance(options, list)
                else active_event.get("option_count")
            )
            decision = recommend_registered_vanilla_event_option_v1(
                source_context,
                played_character_id=expected_character_id,
                snapshot_option_count=option_count,
            )
            option_number = decision.get("selected_option_number")
            if not (
                decision.get("status") == "recommended"
                and decision.get("event_definition_key") == expected_event_key
                and isinstance(option_number, int)
                and not isinstance(option_number, bool)
            ):
                raise RuntimeError("checkpoint-bound registry policy did not recommend")
            planned = plan_registered_event_material_postcondition_v1(
                decision,
                before.get("played_character"),
                played_character_gold=before.get("played_character_gold"),
                snapshot_id=before.get("snapshot_id"),
                revision=before.get("revision"),
            )
            material_expectation = dict(planned) if isinstance(planned, dict) else {}
            if material_expectation.get("status") != "ready":
                raise RuntimeError("registered event material expectation is unavailable")
            selected_step = event_option_step(option_number)
            revision = before.get("revision")
            if isinstance(revision, bool) or not isinstance(revision, int):
                raise RuntimeError("source snapshot lacks a public revision")
            selection_result = await client.call_tool(
                "ck3_select_event_option",
                {
                    "option_number": option_number,
                    "event_instance_id": source_event_anchor.get("event_instance_id"),
                    "expected_revision": revision,
                },
            )
            mcp_results.append(selection_result)
            selection = base._structured(
                selection_result, tool_name="ck3_select_event_option"
            )
            material = evaluate_registered_event_material_postcondition_v1(
                material_expectation,
                selection.get("event_selection"),
            )
            if not (
                material.get("status") == "verified_change"
                and material.get("material_change_observed") is True
                and material.get("event_definition_key") == expected_event_key
            ):
                raise RuntimeError("registered event material postcondition is not GREEN")

            after_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(after_result)
            after = base._structured(
                after_result, tool_name="ck3_take_snapshot:after"
            )
            after_event = _mapping(after.get("active_event"))
            if not (
                after.get("paused") is True
                and after.get("date_raw") == expected_date_raw
                and _played_character_id(after) == expected_character_id
                and after_event.get("instance_id")
                != source_event_anchor.get("event_instance_id")
            ):
                raise RuntimeError("event action did not produce the expected paused successor")
            revision = after.get("revision")
            if isinstance(revision, bool) or not isinstance(revision, int):
                raise RuntimeError("successor snapshot lacks a public revision")
            save_result = await client.call_tool(
                "ck3_save_checkpoint", {"expected_revision": revision}
            )
            mcp_results.append(save_result)
            save = base._structured(save_result, tool_name="ck3_save_checkpoint")
            value = save.get("checkpoint")
            checkpoint = dict(value) if isinstance(value, dict) else None
            final_result = await client.call_tool("ck3_take_snapshot", {})
            mcp_results.append(final_result)
            after = base._structured(final_result, tool_name="ck3_take_snapshot:final")
    except BaseException as error:
        sequence_error = _format_sequence_error(error)

    option_number = decision.get("selected_option_number")
    selected_step = (
        event_option_step(option_number)
        if isinstance(option_number, int) and not isinstance(option_number, bool)
        else None
    )
    delta = _history_delta(before, after)
    checkpoint_path = (
        Path(str(checkpoint.get("path"))).resolve()
        if isinstance(checkpoint, dict) and checkpoint.get("path")
        else None
    )
    checks = {
        "official_tools_listed": all(
            item in tool_names
            for item in (
                "ck3_get_capabilities",
                "ck3_save_checkpoint",
                "ck3_select_event_option",
                "ck3_take_snapshot",
            )
        ),
        "mcp_results_not_errors": bool(mcp_results)
        and not any(bool(getattr(result, "is_error", False)) for result in mcp_results),
        "sequence_error_absent": sequence_error is None,
        "checkpoint_event_context_rebound": bool(source_event_anchor.get(
            "anchor_sha256"
        )),
        "registry_recommended": decision.get("status") == "recommended"
        and decision.get("event_definition_key") == expected_event_key,
        "campaign_utility_ready": isinstance(
            decision.get("campaign_utility_profile"), dict
        ),
        "single_event_selection": selected_step is not None,
        "material_change_verified": material.get("status") == "verified_change"
        and material.get("material_change_observed") is True,
        "event_instance_advanced": _mapping(after.get("active_event")).get(
            "instance_id"
        )
        != source_event_anchor.get("event_instance_id"),
        "same_paused_identity": after.get("paused") is True
        and after.get("date_raw") == expected_date_raw
        and _played_character_id(after) == expected_character_id,
        "exact_command_delta": delta
        == [
            (selected_step, True),
            ("save-checkpoint", True),
        ],
        "checkpoint_materialized": isinstance(checkpoint, dict)
        and checkpoint.get("date_raw") == expected_date_raw
        and checkpoint_path is not None
        and checkpoint_path.is_file(),
    }
    return {
        "source_event_anchor": copy.deepcopy(dict(source_event_anchor)),
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
        ],
        "before_snapshot": before,
        "registry_decision": decision,
        "material_expectation": material_expectation,
        "selection": selection,
        "material_postcondition": dict(material),
        "successor_checkpoint": checkpoint,
        "final_snapshot": after,
        "command_delta": delta,
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
    anchor: dict[str, object] = {}
    identities: dict[str, object] = {}
    try:
        expected_checkpoint = base._expected_sha256(
            args.expected_checkpoint_sha256, "expected checkpoint SHA-256"
        )
        expected_driver = base._expected_sha256(
            args.expected_driver_state_sha256, "expected driver-state SHA-256"
        )
        identities = {
            "checkpoint_sha256": base._sha256_file(args.source_checkpoint.resolve()),
            "driver_state_sha256": base._sha256_file(
                args.source_driver_state.resolve()
            ),
            "game_executable_sha256": base._sha256_file(
                args.game_dir.resolve() / "binaries" / "ck3.exe"
            ),
            "bridge_dll_sha256": base._sha256_file(args.bridge_dll.resolve()),
            "bridge_injector_sha256": base._sha256_file(
                args.bridge_injector.resolve()
            ),
        }
        anchor = _source_event_anchor(
            args.source_driver_state.resolve(),
            expected_checkpoint_sha256=expected_checkpoint,
            expected_date_raw=args.expected_date_raw,
            expected_event_key=args.expected_event_key,
        )
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
        expected_checkpoint = str(args.expected_checkpoint_sha256).upper()
        expected_driver = str(args.expected_driver_state_sha256).upper()
    driver_anchor = (
        base._driver_anchor(args.source_driver_state.resolve())
        if error is None
        else {}
    )
    checks = {
        "attempt_dir_unused": not args.attempt_dir.resolve().exists(),
        "checkpoint_hash": identities.get("checkpoint_sha256") == expected_checkpoint,
        "driver_state_hash": identities.get("driver_state_sha256") == expected_driver,
        "exact_game_executable": identities.get("game_executable_sha256")
        == base.EXPECTED_EXECUTABLE_SHA256,
        "bridge_dll_present": isinstance(identities.get("bridge_dll_sha256"), str),
        "bridge_injector_present": isinstance(
            identities.get("bridge_injector_sha256"), str
        ),
        "driver_character": driver_anchor.get("episode_character_id")
        == args.expected_character_id,
        "checkpoint_event_bound": bool(anchor),
        "preflight_did_not_launch_ck3": True,
        "preflight_did_not_prepare_profile": True,
    }
    ok = error is None and all(checks.values())
    payload = {
        "format_version": 1,
        "kind": "ck3_registered_event_material_no_launch_preflight",
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
            "date_raw": args.expected_date_raw,
        },
        "identities": identities,
        "source_event_anchor": anchor,
        "checks": checks,
        "error": error,
    }
    base._write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.preflight_only:
            payload, exit_code = _preflight(args)
        else:
            source_anchor = _source_event_anchor(
                args.source_driver_state.resolve(),
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                expected_date_raw=args.expected_date_raw,
                expected_event_key=args.expected_event_key,
            )
            args.war_id = 0
            payload, exit_code = base._run(
                args,
                sequence_runner=functools.partial(
                    _run_mcp_sequence,
                    expected_event_key=args.expected_event_key,
                    source_event_anchor=source_anchor,
                ),
                exact_build_runner=_exact_build_proof,
                report_kind=REPORT_KIND,
                policy_override={
                    "mcp_first": True,
                    "production_non_debug": True,
                    "cold_checkpoint": True,
                    "maximum_ck3_launches": 1,
                    "fresh_event_context_queries": 0,
                    "checkpoint_replay_event_context": True,
                    "event_selections": 1,
                    "checkpoint_saves": 1,
                    "time_advanced": False,
                    "war_actions": 0,
                },
            )
            payload["requested_identity"] = {
                "event_definition_key": args.expected_event_key,
                "character_id": args.expected_character_id,
                "date_raw": args.expected_date_raw,
            }
            payload["source_event_anchor"] = source_anchor
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
