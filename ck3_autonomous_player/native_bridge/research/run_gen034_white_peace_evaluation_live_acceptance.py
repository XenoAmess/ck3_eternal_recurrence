#!/usr/bin/env python3
"""Close GEN-034-C on one read-only paused production frame.

The runner restores the frozen R459 checkpoint through the shared managed
session owner, then issues exactly one termination-options query and one
narrow Raiktor terms query at the same public revision.  The resulting values
feed the exact-build white-peace projection and the versioned immediate-exit
utility evaluator.  It never invokes the disabled broad effect preview,
advances time, or submits a termination action.
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

import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
    query_war_termination_options_step,
    query_war_termination_terms_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.simulation.raiktor_exit_utility_evaluator import (  # noqa: E402
    evaluate_raiktor_immediate_exit_utilities,
)
from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (  # noqa: E402
    provide_raiktor_exit_utility_model,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (  # noqa: E402
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)


REPORT_KIND = "ck3_gen034_white_peace_evaluation_live_acceptance"
DISABLED_BROAD_PREVIEW_COMMAND_PREFIX = "query-war-termination-exit-terms-v2"


def _parser() -> argparse.ArgumentParser:
    parser = preflight._parser()
    parser.description = __doc__
    return parser


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    result = base._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
    )
    raw = capabilities if isinstance(capabilities, dict) else {}
    hello_value = base._diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    advertised = raw.get("bridge_capabilities")
    hello_capabilities = hello.get("capabilities")
    action_steps = raw.get("action_steps")
    option_step = query_war_termination_options_step(war_id)
    added = {
        "options_bridge_capability": isinstance(advertised, list)
        and QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY in advertised,
        "options_hello_capability": isinstance(hello_capabilities, list)
        and QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY in hello_capabilities,
        "options_action_step": isinstance(action_steps, list)
        and option_step in action_steps,
        "broad_preview_not_advertised": isinstance(action_steps, list)
        and not any(
            isinstance(step, str)
            and step.startswith(DISABLED_BROAD_PREVIEW_COMMAND_PREFIX)
            for step in action_steps
        ),
    }
    result["required_options_capability"] = (
        QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY
    )
    result["required_options_step"] = option_step
    result["disabled_broad_preview_prefix"] = (
        DISABLED_BROAD_PREVIEW_COMMAND_PREFIX
    )
    result["checks"].update(added)
    result["ok"] = all(result["checks"].values())
    return result


def _history_checks(
    before: dict[str, object],
    after: dict[str, object],
    *,
    options_step: str,
    terms_step: str,
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
        == [(options_step, True), (terms_step, True)]
    }


def _evaluate_live_inputs(
    snapshot: dict[str, object],
    options: dict[str, object],
    terms: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    projection = provide_raiktor_white_peace_narrow_projection(
        snapshot,
        options,
        terms,
        production_live=True,
    )
    evaluation = evaluate_raiktor_immediate_exit_utilities(
        projection,
        terms.get("raiktor_surrender_aggregate_session"),
        provide_raiktor_owner_budget_profile(None),
        provide_raiktor_exit_utility_model(),
    )
    return projection, evaluation


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    from mcp import Client

    server = base.create_server(driver)
    async with Client(server) as client:
        listed = await client.list_tools()
        tool_names = sorted(tool.name for tool in listed.tools)
        capabilities_result = await client.call_tool("ck3_get_capabilities", {})
        before_result = await client.call_tool("ck3_take_snapshot", {})
        before = base._structured(
            before_result, tool_name="ck3_take_snapshot:before"
        )
        revision = before.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise AgentError("paused MCP snapshot lacks a public revision")
        options_result = await client.call_tool(
            "ck3_query_war_termination_options",
            {"war_id": war_id, "expected_revision": revision},
        )
        options = base._structured(
            options_result,
            tool_name="ck3_query_war_termination_options",
        )
        terms_result = await client.call_tool(
            "ck3_query_war_termination_terms",
            {"war_id": war_id, "expected_revision": revision},
        )
        terms = base._structured(
            terms_result,
            tool_name="ck3_query_war_termination_terms",
        )
        after_result = await client.call_tool("ck3_take_snapshot", {})
        after = base._structured(
            after_result, tool_name="ck3_take_snapshot:after"
        )

    projection, evaluation = _evaluate_live_inputs(before, options, terms)
    player_value = before.get("played_character")
    player = player_value if isinstance(player_value, dict) else {}
    options_step = query_war_termination_options_step(war_id)
    terms_step = query_war_termination_terms_step(war_id)
    history = _history_checks(
        before,
        after,
        options_step=options_step,
        terms_step=terms_step,
    )
    certificate_value = evaluation.get("evaluation_certificate")
    certificate = (
        certificate_value if isinstance(certificate_value, dict) else {}
    )
    boundaries_value = certificate.get("boundaries")
    boundaries = (
        boundaries_value if isinstance(boundaries_value, dict) else {}
    )
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_war_termination_options",
                "ck3_query_war_termination_terms",
            )
        ),
        "mcp_results_not_errors": not any(
            bool(getattr(result, "is_error", False))
            for result in (
                capabilities_result,
                before_result,
                options_result,
                terms_result,
                after_result,
            )
        ),
        "initial_paused": before.get("paused") is True,
        "expected_character": player.get("character_id")
        == expected_character_id,
        "expected_date": before.get("date_raw") == expected_date_raw,
        "after_same_paused_binding": base._same_paused_binding(before, after),
        "projection_ready": projection.get("observation_ready") is True,
        "projection_production_live": projection.get("production_live")
        is True,
        "evaluation_ready": evaluation.get("utility_evaluation_ready")
        is True,
        "evaluation_production_live": evaluation.get(
            "production_live_inputs"
        )
        is True,
        "continue_still_closed": boundaries.get("continue_utility_ready")
        is False,
        "full_recommendation_still_closed": evaluation.get(
            "full_three_way_recommendation_ready"
        )
        is False,
        "action_still_closed": evaluation.get("action_ready") is False
        and evaluation.get("action_literal") is None,
        **history,
    }
    return {
        "allowed_gameplay_commands": [options_step, terms_step],
        "mutation_commands": [],
        "disabled_broad_preview_prefix": (
            DISABLED_BROAD_PREVIEW_COMMAND_PREFIX
        ),
        "tool_names": tool_names,
        "public_revision": revision,
        "capabilities": base._mcp_record(capabilities_result),
        "before_snapshot": base._mcp_record(before_result),
        "options_query": base._mcp_record(options_result),
        "terms_query": base._mcp_record(terms_result),
        "after_snapshot": base._mcp_record(after_result),
        "white_peace_projection": projection,
        "immediate_exit_evaluation": evaluation,
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
            payload, exit_code = base._run(
                args,
                sequence_runner=_run_mcp_sequence,
                exact_build_runner=_exact_build_proof,
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
                    "termination_option_queries": 1,
                    "termination_terms_queries": 1,
                    "broad_loaded_effect_preview_enabled": False,
                    "continue_utility_enabled": False,
                    "full_recommendation_enabled": False,
                    "termination_action_enabled": False,
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
