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

ROOT = Path(__file__).resolve().parents[1]


def _ordered(source: str, tokens: tuple[str, ...]) -> bool:
    positions = [source.find(token) for token in tokens]
    return all(position >= 0 for position in positions) and positions == sorted(
        positions
    )


def run_preflight() -> dict[str, object]:
    scenario_source = inspect.getsource(
        runner.run_phase2_hc_workforce_route_b_checkpoint_capture_scenario
    )
    stage_source = (
        ROOT
        / "mod_zhongguo_style/common/scripted_effects/zg361_phase2_central_009_stage11_workforce_endgame_effects.txt"
    ).read_text(encoding="utf-8-sig")
    resume_event_source = (
        ROOT
        / "mod_zhongguo_style/events/zg361_phase2_central_003_m360_resume_events.txt"
    ).read_text(encoding="utf-8-sig")
    fixture_source = (
        ROOT
        / "tools/fixtures/zg361_phase2_workforce_action/common/scripted_guis/zga_phase2_workforce_guis.txt"
    ).read_text(encoding="utf-8-sig")
    checkpoint_source = inspect.getsource(
        __import__("zg361_phase2_hc_workforce_route_b_checkpoint")
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
        "production_ready_has_typed_d1_wait_boundary": (
            _ordered(
                stage_source,
                (
                    "zg361_p2c_prepare_m360_source_effect = yes",
                    "zg361_p2c_schedule_m360_resume_effect = yes",
                ),
            )
            and "zg361_p2c_m360_resume_pending value = 1" in stage_source
            and "zg361_p2c_wait_reason value = 360411" in stage_source
            and "id = zg361p2c.7 days = 1" in stage_source
            and "zg361_we_resume_m360_from_central_source_effect" not in stage_source
        ),
        "d1_ticket_resumes_real_product_in_subject_scope": (
            "this = scope:zg361_p2c_m360_resume_ticket_owner"
            in resume_event_source
            and "scope:zg361_p2c_m360_resume_ticket_subject = {"
            in resume_event_source
            and "zg361_we_resume_m360_from_central_source_effect = {"
            in resume_event_source
            and "EXPECTED_CHOICE = 2" in resume_event_source
        ),
        "transition_fixture_requires_production_ticket": (
            "var:zg361_p2c_m360_resume_pending = 1" in fixture_source
            and "var:zg361_p2c_m360_resume_owner = this" in fixture_source
            and "var:zg361_p2c_m360_resume_subject = root" in fixture_source
        ),
        "b4_seals_current_m360_without_claiming_m361": (
            "require_m361_charter=False" in checkpoint_source
            and '"provider_seal_scope": "m360_current_cycle_route_b"'
            in checkpoint_source
            and '"m361_charter_required": False' in checkpoint_source
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
            "advance the canonical paused seed through genuine product stages "
            "to typed WAIT 360411, then run the explicit managed capture mode; "
            "preserve its real pre-B archive, provider-sealed registry, and "
            "GREEN capture artifact"
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
