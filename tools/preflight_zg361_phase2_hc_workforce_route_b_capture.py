#!/usr/bin/env python3
"""No-launch preflight for the HC-workforce Route-B checkpoint producer."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

import run_zhongguo_acceptance as runner
from zg361_phase2_hc_workforce_route_b_checkpoint_registry import (
    write_route_b_checkpoint_registry,
)


def _ordered(source: str, tokens: tuple[str, ...]) -> bool:
    positions = [source.find(token) for token in tokens]
    return all(position >= 0 for position in positions) and positions == sorted(
        positions
    )


def run_preflight() -> dict[str, object]:
    scenario_source = inspect.getsource(
        runner.run_phase2_hc_workforce_route_b_checkpoint_capture_scenario
    )
    checks = {
        "explicit_capture_live_mode_registered": (
            "phase2_hc_workforce_route_b_capture_live: bool = False"
            in inspect.getsource(runner.main)
            and callable(
                runner.run_phase2_hc_workforce_route_b_checkpoint_capture_scenario
            )
        ),
        "explicit_non_overwriting_outputs_required": (
            "checkpoint_archive_path" in scenario_source
            and "phase2_hc_workforce_route_b_registry_output"
            in inspect.getsource(runner.main)
            and "Route-B capture output paths must differ and not already exist"
            in inspect.getsource(runner.main)
        ),
        "canonical_seed_fixture_real_event_freeze_order": _ordered(
            scenario_source,
            (
                "canonical_seed_binding",
                "install_phase2_workforce_action_fixture(",
                "select_typed_fixture_player_transition(",
                "wait_for_phase2_exact_event(\n            service,\n            expected_definition_key=M360_EVENT_DEFINITION_KEY",
                "freeze_route_b_pre_action_checkpoint(",
            ),
        ),
        "provider_seal_precedes_registry_writer": _ordered(
            scenario_source,
            (
                "run_route_b_and_collect_postconditions(",
                "restore_route_b_pre_action_checkpoint(",
                "write_route_b_checkpoint_registry(",
            ),
        ),
        "ack_and_fixture_output_rejected_as_postcondition": (
            '"action_ack_is_business_postcondition": False' in scenario_source
            and '"fixture_output_is_business_postcondition": False'
            in scenario_source
            and "provider_observed_postcondition_required" in scenario_source
        ),
        "career_hc_provider_default_off": (
            "career_hc_hook=_route_b_career_hc_default_off_hook"
            in scenario_source
        ),
        "strict_registry_writer_available": callable(
            write_route_b_checkpoint_registry
        ),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_capture_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending",
        "ck3_started": False,
        "service_instantiated": False,
        "checkpoint_created": False,
        "registry_created": False,
        "gameplay_action_executed": False,
        "provider_live_result_claimed": False,
        "career_hc_provider_default_off": True,
        "checks": checks,
        "failed_checks": failed,
        "live_gate_ready": False,
        "explicit_live_execute_requires": [
            "--phase2-hc-workforce-route-b-capture-live",
            "--phase2-hc-workforce-route-b-checkpoint-output",
            "--phase2-hc-workforce-route-b-registry-output",
        ],
        "remaining_live_checkpoint": (
            "run the explicit managed capture mode against the canonical paused "
            "seed; preserve its real pre-B archive, provider-sealed registry, "
            "and GREEN capture artifact"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_preflight()
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output is not None:
        output = arguments.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
