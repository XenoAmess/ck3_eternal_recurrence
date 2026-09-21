#!/usr/bin/env python3
"""Capture one same-frame production Raiktor three-way recommendation.

The runner cold-restores an already admitted white-peace horizon checkpoint.
It performs the two narrow exit reads and two stable strategic-power reads on
one paused frame, then invokes the bounded v2 recommendation provider.  It
records the single planned action but never submits it or advances time.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import json
from pathlib import Path
import sys
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_active_war_strategic_power_live_acceptance as power  # noqa: E402
import run_gen034_white_peace_evaluation_live_acceptance as exit_read  # noqa: E402
import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    query_war_termination_options_step,
    query_war_termination_terms_step,
)
from xar_autoplayer.bridge.war_entry_contract import (  # noqa: E402
    query_war_entry_assessments_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (  # noqa: E402
    provide_raiktor_campaign_dominance,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (  # noqa: E402
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (  # noqa: E402
    provide_raiktor_exit_utility_model,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (  # noqa: E402
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (  # noqa: E402
    provide_raiktor_three_way_exit_action_gate,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (  # noqa: E402
    provide_raiktor_three_way_exit_recommendation,
)
from xar_autoplayer.raiktor_formal_exit import (  # noqa: E402
    _opponent_terminal_control_input,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)


REPORT_KIND = "ck3_gen034_three_way_recommendation_live_acceptance"


def _parser() -> argparse.ArgumentParser:
    parser = exit_read._parser()
    parser.description = __doc__
    parser.add_argument("--opponent-character-id", type=int, required=True)
    return parser


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
    opponent_character_id: int,
) -> dict[str, object]:
    exit_proof = exit_read._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
    )
    power_proof = power._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
        target_character_id=opponent_character_id,
    )
    checks = {
        **{
            f"exit_{key}": value
            for key, value in exit_proof["checks"].items()
        },
        **{
            f"power_{key}": value
            for key, value in power_proof["checks"].items()
        },
    }
    return {
        "exit_read_proof": exit_proof,
        "strategic_power_proof": power_proof,
        "checks": checks,
        "ok": all(checks.values()),
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
        return {"exact_read_only_command_delta": False}
    delta = [
        (row.get("command"), row.get("ok"))
        for row in after_history[len(before_history) :]
        if isinstance(row, dict)
    ]
    return {
        "exact_read_only_command_delta": delta
        == [(command, True) for command in expected_commands]
    }


def _compose_recommendation(
    snapshot: dict[str, object],
    options: dict[str, object],
    terms: dict[str, object],
    dominance_certificate: dict[str, object],
) -> dict[str, object]:
    projection = provide_raiktor_white_peace_narrow_projection(
        snapshot, options, terms, production_live=True
    )
    war_id = projection["white_peace_observation"]["frame"]["war_id"]
    opponent_character_id = projection["white_peace_observation"]["frame"][
        "primary_defender_character_id"
    ]
    matching_wars = [
        war
        for war in snapshot.get("active_wars", [])
        if isinstance(war, dict) and war.get("war_id") == war_id
    ]
    if len(matching_wars) != 1:
        raise RuntimeError("current Raiktor war is unavailable")
    terminal_control = _opponent_terminal_control_input(
        war=matching_wars[0],
        war_id=war_id,
        opponent_character_id=opponent_character_id,
        options_query=options,
        white_peace_projection=projection,
    )
    return provide_raiktor_three_way_exit_recommendation(
        projection,
        terms.get("raiktor_surrender_aggregate_session"),
        dominance_certificate,
        provide_raiktor_owner_budget_profile(None),
        provide_raiktor_exit_utility_model(),
        terminal_control,
    )


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    opponent_character_id: int,
) -> dict[str, object]:
    from mcp import Client

    server = base.create_server(driver)
    records: list[object] = []
    async with Client(server) as client:
        listed = await client.list_tools()
        tool_names = sorted(tool.name for tool in listed.tools)
        capabilities_result = await client.call_tool("ck3_get_capabilities", {})
        records.append(capabilities_result)
        capabilities = base._structured(
            capabilities_result, tool_name="ck3_get_capabilities"
        )
        before_result = await client.call_tool("ck3_take_snapshot", {})
        records.append(before_result)
        before = base._structured(
            before_result, tool_name="ck3_take_snapshot:before"
        )
        revision = before.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise AgentError("paused recommendation frame lacks a revision")
        # The power reader requires the application-main mailbox.  Query it
        # immediately while the freshly restored paused UI is still pumping;
        # the two exit readers below are worker-thread reads and do not need
        # that scheduling window.  R657 proved the inverse order can strand
        # the first power ticket after both exit reads have completed.
        power_before_result = before_result
        power_before = before
        power_arguments = {
            "target_character_ids": [opponent_character_id],
            "expected_revision": revision,
        }
        first_result = await client.call_tool(
            "ck3_query_war_entry_assessments", power_arguments
        )
        records.append(first_result)
        first = base._structured(
            first_result,
            tool_name="ck3_query_war_entry_assessments:first",
        )
        between_result = await client.call_tool("ck3_take_snapshot", {})
        records.append(between_result)
        between = base._structured(
            between_result, tool_name="ck3_take_snapshot:between"
        )
        second_result = await client.call_tool(
            "ck3_query_war_entry_assessments", power_arguments
        )
        records.append(second_result)
        second = base._structured(
            second_result,
            tool_name="ck3_query_war_entry_assessments:second",
        )
        power_after_result = await client.call_tool("ck3_take_snapshot", {})
        records.append(power_after_result)
        power_after = base._structured(
            power_after_result, tool_name="ck3_take_snapshot:power-after"
        )
        arguments = {"war_id": war_id, "expected_revision": revision}
        options_result = await client.call_tool(
            "ck3_query_war_termination_options", arguments
        )
        records.append(options_result)
        options = base._structured(
            options_result,
            tool_name="ck3_query_war_termination_options",
        )
        terms_result = await client.call_tool(
            "ck3_query_war_termination_terms", arguments
        )
        records.append(terms_result)
        terms = base._structured(
            terms_result,
            tool_name="ck3_query_war_termination_terms",
        )
        after_result = await client.call_tool("ck3_take_snapshot", {})
        records.append(after_result)
        after = base._structured(
            after_result, tool_name="ck3_take_snapshot:after"
        )

    dominance = provide_raiktor_campaign_dominance(
        power_before,
        first,
        between,
        second,
        power_after,
        war_id=war_id,
        opponent_character_id=opponent_character_id,
        source_artifact_sha256=canonical_policy_input_sha256(
            {
                "snapshot": power_before,
                "first": first,
                "between": between,
                "second": second,
                "after": power_after,
            }
        ),
    )
    recommendation = _compose_recommendation(
        before,
        options,
        terms,
        dominance["campaign_dominance_certificate"],
    )
    action_gate = provide_raiktor_three_way_exit_action_gate(
        recommendation, before, capabilities
    )
    option_step = query_war_termination_options_step(war_id)
    terms_step = query_war_termination_terms_step(war_id)
    power_step = query_war_entry_assessments_step([opponent_character_id])
    expected_commands = [power_step, power_step, option_step, terms_step]
    player = before.get("played_character")
    action = recommendation.get("action_literal")
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_war_termination_options",
                "ck3_query_war_termination_terms",
                "ck3_query_war_entry_assessments",
            )
        ),
        "mcp_results_not_errors": not any(
            bool(getattr(record, "is_error", False)) for record in records
        ),
        "expected_paused_identity": before.get("paused") is True
        and before.get("date_raw") == expected_date_raw
        and isinstance(player, dict)
        and player.get("character_id") == expected_character_id
        and power._active_war(
            before,
            war_id=war_id,
            target_character_id=opponent_character_id,
        )
        is not None,
        "power_before_same_frame": base._same_paused_binding(
            before, power_before
        ),
        "between_same_frame": base._same_paused_binding(before, between),
        "power_after_same_frame": base._same_paused_binding(
            before, power_after
        ),
        "after_same_frame": base._same_paused_binding(before, after),
        "dominance_ready": dominance.get("certificate_available") is True,
        "production_recommendation_ready": recommendation.get(
            "production_recommendation_ready"
        )
        is True,
        "exactly_one_action_planned": action_gate.get("action_ready") is True
        and action_gate.get("action_literal") == action
        and isinstance(action, str)
        and action in {
            "resume-map",
            f"offer-white-peace-{war_id}",
            f"surrender-war-{war_id}",
        },
        "action_not_submitted": all(
            not command.startswith(
                ("resume-map", "offer-white-peace-", "surrender-war-")
            )
            for command in expected_commands
        ),
        **_history_checks(
            before,
            after,
            expected_commands=expected_commands,
        ),
    }
    return {
        "allowed_gameplay_commands": expected_commands,
        "mutation_commands": [],
        "planned_action": action,
        "tool_names": tool_names,
        "capabilities": base._mcp_record(capabilities_result),
        "before_snapshot": base._mcp_record(before_result),
        "options_query": base._mcp_record(options_result),
        "terms_query": base._mcp_record(terms_result),
        "power_before_snapshot": base._mcp_record(power_before_result),
        "first_power_query": base._mcp_record(first_result),
        "between_snapshot": base._mcp_record(between_result),
        "second_power_query": base._mcp_record(second_result),
        "power_after_snapshot": base._mcp_record(power_after_result),
        "after_snapshot": base._mcp_record(after_result),
        "dominance": dominance,
        "recommendation": recommendation,
        "action_gate": action_gate,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 0 < args.opponent_character_id <= 2**31 - 1:
        print("ERROR: opponent-character-id must be a signed int32", file=sys.stderr)
        return 2
    try:
        preflight_payload, preflight_exit = preflight._no_launch_preflight(args)
        if args.preflight_only or preflight_exit != 0:
            payload = preflight_payload
            exit_code = preflight_exit
        else:
            sequence_runner = functools.partial(
                _run_mcp_sequence,
                opponent_character_id=args.opponent_character_id,
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
                    "time_advanced": False,
                    "maximum_ck3_launches": 1,
                    "termination_option_queries": 1,
                    "termination_terms_queries": 1,
                    "strategic_power_queries": 2,
                    "three_way_recommendation_enabled": True,
                    "termination_action_enabled": False,
                    "mutation_commands": [],
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
