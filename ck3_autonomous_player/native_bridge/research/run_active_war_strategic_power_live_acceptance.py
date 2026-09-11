#!/usr/bin/env python3
"""Query one current active-war opponent's exact strategic power twice.

This runner restores one immutable checkpoint/driver-state pair into a fresh
production profile, launches one managed non-debug CK3 process, and performs
only official MCP snapshot, capability, and strategic-power reads. It never
advances time or submits a gameplay mutation. Both GREEN and RED attempts are
retained, while the managed CK3 process is always stopped by the shared
single-process session owner.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
from pathlib import Path
import sys
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.war_entry_contract import (  # noqa: E402
    EXECUTABLE_SHA256,
    GAME_VERSION,
    QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
    query_war_entry_assessments_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402


REPORT_KIND = "ck3_active_war_strategic_power_live_acceptance"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"


def _parser() -> argparse.ArgumentParser:
    parser = base._parser()
    parser.description = __doc__
    parser.add_argument("--target-character-id", type=int, required=True)
    return parser


def _active_war(
    snapshot: dict[str, object],
    *,
    war_id: int,
    target_character_id: int,
) -> dict[str, object] | None:
    rows = snapshot.get("active_wars")
    if not isinstance(rows, list):
        return None
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("war_id") == war_id
        and row.get("primary_opponent_character_id") == target_character_id
    ]
    return copy.deepcopy(matches[0]) if len(matches) == 1 else None


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
    target_character_id: int,
) -> dict[str, object]:
    del war_id
    raw = capabilities if isinstance(capabilities, dict) else {}
    hello_value = base._diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    observed_sha = hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
    observed_version = hello.get("expected_ck3_version", hello.get("game_version"))
    advertised = raw.get("bridge_capabilities")
    hello_capabilities = hello.get("capabilities")
    action_steps = raw.get("action_steps")
    required_step = query_war_entry_assessments_step([target_character_id])
    checks = {
        "game_version": observed_version == GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper() == EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == EXECUTABLE_SHA256,
        "bridge_capability": isinstance(advertised, list)
        and QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY in advertised,
        "hello_capability": isinstance(hello_capabilities, list)
        and QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY in hello_capabilities,
        "active_target_action_step": isinstance(action_steps, list)
        and required_step in action_steps,
    }
    return {
        "expected_game_version": GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": EXECUTABLE_SHA256,
        "required_capability": QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
        "required_action_step": required_step,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _query_checks(
    payload: dict[str, object],
    *,
    snapshot: dict[str, object],
    target_character_id: int,
) -> dict[str, bool]:
    native_value = payload.get("war_entry_assessments")
    native = native_value if isinstance(native_value, dict) else {}
    readiness_value = native.get("readiness")
    readiness = readiness_value if isinstance(readiness_value, dict) else {}
    rows_value = native.get("assessments")
    rows = rows_value if isinstance(rows_value, list) else []
    scopes_value = payload.get("target_scopes")
    scopes = scopes_value if isinstance(scopes_value, list) else []
    scope = scopes[0] if len(scopes) == 1 and isinstance(scopes[0], dict) else {}
    row = rows[0] if len(rows) == 1 and isinstance(rows[0], dict) else {}
    player_value = snapshot.get("played_character")
    player = player_value if isinstance(player_value, dict) else {}
    return {
        "available": payload.get("status") == "available",
        "target_identity": payload.get("target_character_ids")
        == [target_character_id],
        "active_war_scope": scope.get("target_character_id")
        == target_character_id
        and isinstance(scope.get("sources"), list)
        and "active_war_primary_opponent" in scope["sources"],
        "native_available": native.get("status") == "available",
        "native_target_identity": native.get("requested_target_character_ids")
        == [target_character_id]
        and row.get("target_character_id") == target_character_id,
        "native_actor_identity": native.get("actor_character_id")
        == player.get("character_id"),
        "native_revision_binding": native.get("snapshot_revision")
        == snapshot.get("native_revision"),
        "outer_revision_binding": payload.get("queried_snapshot_id")
        == snapshot.get("snapshot_id")
        and payload.get("queried_revision") == snapshot.get("revision")
        and payload.get("queried_native_revision")
        == snapshot.get("native_revision"),
        "native_readiness": readiness.get("ready") is True,
        "strategic_totals_observed": all(
            isinstance(row.get(key), int) and not isinstance(row.get(key), bool)
            for key in (
                "actor_power_base_raw",
                "actor_network_contribution_raw",
                "actor_power_total_raw",
                "target_power_base_raw",
                "target_network_contribution_raw",
                "target_pre_adjustment_total_raw",
                "target_adjustment_delta_raw",
                "target_power_total_raw",
                "actual_power_ratio_raw",
            )
        ),
    }


def _query_history_checks(
    *,
    before: dict[str, object],
    between: dict[str, object],
    after: dict[str, object],
    step: str,
) -> dict[str, bool]:
    histories = [
        snapshot.get("native_command_history")
        for snapshot in (before, between, after)
    ]
    if not all(isinstance(history, list) for history in histories):
        return {
            "history_first_query_only": False,
            "history_two_queries_only": False,
        }
    before_history, between_history, after_history = histories
    before_count = len(before_history)
    observed_between = [
        (row.get("command"), row.get("ok"))
        for row in between_history[before_count:]
        if isinstance(row, dict)
    ]
    observed_after = [
        (row.get("command"), row.get("ok"))
        for row in after_history[before_count:]
        if isinstance(row, dict)
    ]
    return {
        "history_first_query_only": observed_between == [(step, True)],
        "history_two_queries_only": observed_after
        == [(step, True), (step, True)],
    }


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    target_character_id: int,
) -> dict[str, object]:
    from mcp import Client

    server = base.create_server(driver)
    async with Client(server) as client:
        listed = await client.list_tools()
        tool_names = sorted(tool.name for tool in listed.tools)
        capabilities_result = await client.call_tool("ck3_get_capabilities", {})
        capabilities = base._structured(
            capabilities_result, tool_name="ck3_get_capabilities"
        )
        before_result = await client.call_tool("ck3_take_snapshot", {})
        before = base._structured(
            before_result, tool_name="ck3_take_snapshot:before"
        )
        revision = before.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise AgentError("paused MCP snapshot lacks a public revision")
        arguments = {
            "target_character_ids": [target_character_id],
            "expected_revision": revision,
        }
        first_result = await client.call_tool(
            "ck3_query_war_entry_assessments", arguments
        )
        first = base._structured(
            first_result, tool_name="ck3_query_war_entry_assessments:first"
        )
        between_result = await client.call_tool("ck3_take_snapshot", {})
        between = base._structured(
            between_result, tool_name="ck3_take_snapshot:between"
        )
        second_result = await client.call_tool(
            "ck3_query_war_entry_assessments", arguments
        )
        second = base._structured(
            second_result, tool_name="ck3_query_war_entry_assessments:second"
        )
        after_result = await client.call_tool("ck3_take_snapshot", {})
        after = base._structured(
            after_result, tool_name="ck3_take_snapshot:after"
        )

    first_checks = _query_checks(
        first, snapshot=before, target_character_id=target_character_id
    )
    second_checks = _query_checks(
        second, snapshot=before, target_character_id=target_character_id
    )
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    step = query_war_entry_assessments_step([target_character_id])
    player_value = before.get("played_character")
    player = player_value if isinstance(player_value, dict) else {}
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_war_entry_assessments",
            )
        ),
        "mcp_results_not_errors": not any(
            bool(getattr(result, "is_error", False))
            for result in (
                capabilities_result,
                before_result,
                first_result,
                between_result,
                second_result,
                after_result,
            )
        ),
        "initial_paused": before.get("paused") is True,
        "expected_character": player.get("character_id") == expected_character_id,
        "expected_date": before.get("date_raw") == expected_date_raw,
        "unique_active_war_target": _active_war(
            before,
            war_id=war_id,
            target_character_id=target_character_id,
        )
        is not None,
        "between_same_paused_binding": base._same_paused_binding(before, between),
        "after_same_paused_binding": base._same_paused_binding(before, after),
        "first_query": all(first_checks.values()),
        "second_query": all(second_checks.values()),
        "query_sequence_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "normalized_payloads_equal": base._without_query_sequence(first)
        == base._without_query_sequence(second),
        **_query_history_checks(
            before=before,
            between=between,
            after=after,
            step=step,
        ),
    }
    return {
        "allowed_gameplay_commands": [step, step],
        "mutation_commands": [],
        "target_character_id": target_character_id,
        "active_war": _active_war(
            before,
            war_id=war_id,
            target_character_id=target_character_id,
        ),
        "tool_names": tool_names,
        "public_revision": revision,
        "capabilities": base._mcp_record(capabilities_result),
        "before_snapshot": base._mcp_record(before_result),
        "first_query": base._mcp_record(first_result),
        "between_snapshot": base._mcp_record(between_result),
        "second_query": base._mcp_record(second_result),
        "after_snapshot": base._mcp_record(after_result),
        "first_query_checks": first_checks,
        "second_query_checks": second_checks,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.target_character_id <= 0 or args.target_character_id > 2**31 - 1:
        print("ERROR: target-character-id must be a positive signed-int32", file=sys.stderr)
        return 2
    sequence_runner = lambda driver, **kwargs: _run_mcp_sequence(  # noqa: E731
        driver, target_character_id=args.target_character_id, **kwargs
    )
    exact_build_runner = lambda capabilities, **kwargs: _exact_build_proof(  # noqa: E731
        capabilities, target_character_id=args.target_character_id, **kwargs
    )
    try:
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
                "time_advanced": False,
                "mutation_commands": [],
                "maximum_ck3_launches": 1,
                "maximum_strategic_power_queries": 2,
                "campaign_dominance_decision_ready": False,
                "surrender_action_enabled": False,
                "remaining_gen034_providers": [
                    "campaign_dominance_policy",
                    "owner_authored_budget",
                    "same_frame_white_peace_comparison",
                ],
            },
        )
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
