#!/usr/bin/env python3
"""Execute one GEN-034 action using immutable-checkpoint power evidence.

The managed live phase performs two fresh exit reads on the restored paused
frame.  It rebinds an earlier direct double-sample power certificate only when
the checkpoint, driver state and gameplay identity agree, then authorizes and
submits exactly one recommendation.  It never issues a fresh power query.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
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

import prepare_gen034_checkpoint_replay_recommendation as replay_tool  # noqa: E402
import run_gen034_three_way_exit_action_live_acceptance as action  # noqa: E402
import run_gen034_three_way_recommendation_live_acceptance as recommendation  # noqa: E402
import run_raiktor_surrender_session_binding_live_acceptance as preflight  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    query_war_termination_options_step,
    query_war_termination_terms_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (  # noqa: E402
    normalize_raiktor_campaign_dominance_certificate,
    provide_raiktor_checkpoint_replay_dominance,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (  # noqa: E402
    provide_raiktor_three_way_exit_action_gate,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)


REPORT_KIND = "ck3_gen034_checkpoint_replay_action_live_acceptance"
RESULT_SCHEMA = "xar.ck3.gen034_checkpoint_replay_action_live_acceptance.v1"


def _parser() -> argparse.ArgumentParser:
    parser = action._parser()
    parser.description = __doc__
    parser.add_argument("--replay-recommendation", type=Path, required=True)
    parser.add_argument("--expected-replay-recommendation-sha256", required=True)
    return parser


def _load_replay_source(
    path: Path,
    expected_sha256: str,
    *,
    expected_checkpoint_sha256: str,
    expected_driver_state_sha256: str,
) -> dict[str, object]:
    source = path.expanduser().resolve()
    expected = base._expected_sha256(
        expected_sha256, "expected replay-recommendation SHA-256"
    )
    if not source.is_file() or base._sha256_file(source) != expected:
        raise action.Gen034ActionRunnerError(
            "replay recommendation path/hash disagrees"
        )
    try:
        value = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise action.Gen034ActionRunnerError(
            f"replay recommendation JSON is unavailable: {error}"
        ) from error
    if not isinstance(value, dict):
        raise action.Gen034ActionRunnerError(
            "replay recommendation must be an object"
        )
    boundaries = value.get("boundaries")
    inputs = value.get("inputs")
    direct = value.get("direct_dominance_receipt")
    provider = direct.get("provider_result") if isinstance(direct, dict) else None
    certificate = (
        provider.get("campaign_dominance_certificate")
        if isinstance(provider, dict)
        else None
    )
    checkpoint = inputs.get("checkpoint") if isinstance(inputs, dict) else None
    driver = inputs.get("source_driver_state") if isinstance(inputs, dict) else None
    if (
        value.get("schema") != replay_tool.OUTPUT_SCHEMA
        or value.get("status") != "GREEN"
        or value.get("ok") is not True
        or value.get("source_live_attempt_status") != "RED_preserved"
        or not isinstance(boundaries, dict)
        or boundaries.get("same_runtime_frame_claimed") is not False
        or boundaries.get("immutable_checkpoint_state_replay") is not True
        or boundaries.get("source_red_reclassified") is not False
        or boundaries.get("action_submitted") is not False
        or not isinstance(checkpoint, dict)
        or checkpoint.get("sha256") != expected_checkpoint_sha256
        or not isinstance(driver, dict)
        or driver.get("sha256") != expected_driver_state_sha256
    ):
        raise action.Gen034ActionRunnerError(
            "replay recommendation admission boundary drifted"
        )
    try:
        normalized = normalize_raiktor_campaign_dominance_certificate(
            certificate
        )
    except ValueError as error:
        raise action.Gen034ActionRunnerError(
            f"direct replay source is invalid: {error}"
        ) from error
    if normalized.get("schema_version") != 2:
        raise action.Gen034ActionRunnerError(
            "replay source must retain a direct v2 power certificate"
        )
    return {
        "path": str(source),
        "sha256": expected,
        "direct_dominance_certificate": copy.deepcopy(normalized),
    }


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
    opponent_character_id: int,
) -> dict[str, object]:
    result = action._exact_build_proof(
        capabilities,
        managed_executable_sha256=managed_executable_sha256,
        war_id=war_id,
        opponent_character_id=opponent_character_id,
    )
    result["checks"]["replay_mode_uses_no_power_query"] = True
    result["ok"] = all(result["checks"].values())
    return result


async def _run_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    opponent_character_id: int,
    source_capture: dict[str, object],
    source_capture_sha256: str,
    replay_source: dict[str, object],
    checkpoint_sha256: str,
    driver_state_sha256: str,
) -> dict[str, object]:
    """Take two fresh reads, replay power, then execute on the same client."""

    read_phase: dict[str, object] | None = None
    try:
        from mcp import Client

        server = base.create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)
            capabilities_result = await client.call_tool(
                "ck3_get_capabilities", {}
            )
            capabilities = base._structured(
                capabilities_result, tool_name="ck3_get_capabilities"
            )
            before_result = await client.call_tool("ck3_take_snapshot", {})
            before = base._structured(
                before_result, tool_name="ck3_take_snapshot:before"
            )
            revision = before.get("revision")
            if isinstance(revision, bool) or not isinstance(revision, int):
                raise AgentError("paused replay frame lacks a revision")
            arguments = {"war_id": war_id, "expected_revision": revision}
            options_result = await client.call_tool(
                "ck3_query_war_termination_options", arguments
            )
            options = base._structured(
                options_result,
                tool_name="ck3_query_war_termination_options",
            )
            terms_result = await client.call_tool(
                "ck3_query_war_termination_terms", arguments
            )
            terms = base._structured(
                terms_result,
                tool_name="ck3_query_war_termination_terms",
            )
            after_result = await client.call_tool("ck3_take_snapshot", {})
            after = base._structured(
                after_result, tool_name="ck3_take_snapshot:after"
            )

            projection = provide_raiktor_white_peace_narrow_projection(
                before, options, terms, production_live=True
            )
            observation = projection.get("white_peace_observation")
            if not isinstance(observation, dict):
                raise action.Gen034ActionRunnerError(
                    "fresh exit reads did not produce a projection"
                )
            frame = observation.get("frame")
            if not isinstance(frame, dict):
                raise action.Gen034ActionRunnerError(
                    "fresh projection lacks a frame"
                )
            replay = provide_raiktor_checkpoint_replay_dominance(
                replay_source["direct_dominance_certificate"],
                replay_tool._dominance_frame(frame),
                source_checkpoint_sha256=checkpoint_sha256,
                target_checkpoint_sha256=checkpoint_sha256,
                source_driver_state_sha256=driver_state_sha256,
                target_driver_state_sha256=driver_state_sha256,
            )
            result = recommendation._compose_recommendation(
                before,
                options,
                terms,
                replay["campaign_dominance_certificate"],
            )
            action_gate = provide_raiktor_three_way_exit_action_gate(
                result, before, capabilities
            )
            option_step = query_war_termination_options_step(war_id)
            terms_step = query_war_termination_terms_step(war_id)
            expected_commands = [option_step, terms_step]
            player = before.get("played_character")
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
                "expected_paused_identity": before.get("paused") is True
                and before.get("date_raw") == expected_date_raw
                and isinstance(player, dict)
                and player.get("character_id") == expected_character_id
                and recommendation.power._active_war(
                    before,
                    war_id=war_id,
                    target_character_id=opponent_character_id,
                )
                is not None,
                "after_same_frame": base._same_paused_binding(before, after),
                "checkpoint_replay_ready": replay.get(
                    "certificate_available"
                )
                is True,
                "production_recommendation_ready": result.get(
                    "production_recommendation_ready"
                )
                is True,
                "action_authorized": action_gate.get("action_ready") is True,
                "no_power_query_issued": all(
                    "war-entry-assessments" not in command
                    for command in expected_commands
                ),
                **recommendation._history_checks(
                    before,
                    after,
                    expected_commands=expected_commands,
                ),
            }
            read_phase = {
                "ok": all(checks.values()),
                "allowed_gameplay_commands": expected_commands,
                "mutation_commands": [],
                "tool_names": tool_names,
                "capabilities": base._mcp_record(capabilities_result),
                "before_snapshot": base._mcp_record(before_result),
                "options_query": base._mcp_record(options_result),
                "terms_query": base._mcp_record(terms_result),
                "after_snapshot": base._mcp_record(after_result),
                "exit_projection": projection,
                "checkpoint_replay_dominance": replay,
                "recommendation": result,
                "action_gate": action_gate,
                "checks": checks,
            }
            if read_phase["ok"] is not True:
                raise action.Gen034ActionRunnerError(
                    "checkpoint-replay recommendation phase returned RED"
                )
            executed = await action._execute_action_tail(
                client,
                read_phase=read_phase,
                source_capture=source_capture,
                source_capture_sha256=source_capture_sha256,
            )
            executed["schema"] = RESULT_SCHEMA
            executed["power_query_count"] = 0
            executed["checkpoint_replay_source"] = {
                "path": replay_source["path"],
                "sha256": replay_source["sha256"],
            }
            return executed
    except BaseException as error:
        return {
            "schema": RESULT_SCHEMA,
            "status": "red",
            "read_phase": read_phase,
            "sequence_error": f"{type(error).__name__}: {error}",
            "power_query_count": 0,
            "gen034_closed": False,
            "ok": False,
        }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        checkpoint_sha256 = base._expected_sha256(
            args.expected_checkpoint_sha256,
            "expected checkpoint SHA-256",
        )
        driver_state_sha256 = base._expected_sha256(
            args.expected_driver_state_sha256,
            "expected driver-state SHA-256",
        )
        replay_source = _load_replay_source(
            args.replay_recommendation,
            args.expected_replay_recommendation_sha256,
            expected_checkpoint_sha256=checkpoint_sha256,
            expected_driver_state_sha256=driver_state_sha256,
        )
        source_capture = action._load_source_capture(
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
        preflight_payload["checkpoint_replay_source"] = {
            "path": replay_source["path"],
            "sha256": replay_source["sha256"],
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
                replay_source=replay_source,
                checkpoint_sha256=checkpoint_sha256,
                driver_state_sha256=driver_state_sha256,
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
                    "maximum_ck3_launches": 1,
                    "fresh_exit_queries": 2,
                    "fresh_power_queries": 0,
                    "checkpoint_replay_power": True,
                    "war_exit_actions": 1,
                    "continue_route_checkpoint_saves": 0,
                    "continue_route_checkpoint_cold_restores": 0,
                    "broad_loaded_effect_preview_enabled": False,
                },
            )
            payload["no_launch_preflight"] = preflight_payload
            payload["source_capture"] = preflight_payload["source_capture"]
            payload["checkpoint_replay_source"] = preflight_payload[
                "checkpoint_replay_source"
            ]
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
