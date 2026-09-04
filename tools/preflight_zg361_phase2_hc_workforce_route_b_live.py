#!/usr/bin/env python3
"""No-launch preflight for the formal HC-workforce Route-B registry entry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping

import run_zhongguo_acceptance as runner
from zg361_phase2_hc_workforce_route_b_checkpoint_registry import (
    ROUTE_B_CHECKPOINT_REGISTRY_KIND,
    RouteBCheckpointRegistryError,
    RouteBCheckpointRegistryProvider,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_zhongguo_acceptance.py"
SERVICE_PATH = (
    ROOT
    / "ck3_autonomous_player"
    / "src"
    / "xar_autoplayer"
    / "bridge"
    / "service.py"
)
DRIVER_PATH = SERVICE_PATH.with_name("native_driver.py")


def _load_registry(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(
            path.expanduser().resolve().read_text(encoding="utf-8-sig")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_unreadable",
            {
                "registry_path": str(path),
                "error": f"{type(error).__name__}: {error}",
            },
        ) from error
    if not isinstance(value, dict):
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_not_an_object",
            {
                "registry_path": str(path),
                "root_type": type(value).__name__,
            },
        )
    return value


def run_preflight(registry_path: Path | None = None) -> dict[str, object]:
    runner_source = RUNNER_PATH.read_text(encoding="utf-8-sig")
    service_source = SERVICE_PATH.read_text(encoding="utf-8-sig")
    driver_source = DRIVER_PATH.read_text(encoding="utf-8-sig")
    checks = {
        "formal_runtime_mode_registered": (
            '"--phase2-hc-workforce-route-b-live"' in runner_source
            and callable(runner.run_phase2_hc_workforce_route_b_registry_scenario)
        ),
        "strict_registry_cli_registered": (
            '"--phase2-hc-workforce-route-b-checkpoint-registry"'
            in runner_source
        ),
        "career_provider_gate_explicit_default_off": (
            "phase2_hc_workforce_enable_career_provider: bool = False"
            in runner_source
            and "career_hc_live_gate_default_off" in runner_source
        ),
        "fixture_bound_restore_service_registered": (
            "def restore_hc_workforce_route_b_checkpoint_v1(" in service_source
            and "def restore_hc_workforce_route_b_checkpoint_v1(" in driver_source
        ),
        "ack_not_business_postcondition": (
            '"action_ack_is_business_postcondition": False' in runner_source
            and '"provider_observed_postcondition_required": True'
            in runner_source
        ),
    }
    failed = [name for name, value in checks.items() if value is not True]
    live_registry: dict[str, object]
    if registry_path is None:
        live_registry = {
            "result": "RED",
            "reason_code": "route_b_checkpoint_registry_missing",
            "registry_kind": ROUTE_B_CHECKPOINT_REGISTRY_KIND,
            "qualified_checkpoint_found": False,
        }
    else:
        try:
            seed_contract = runner.load_phase2_seed_contract(
                runner.PHASE2_SEED_CONTRACT_PATH
            )
            live_registry = RouteBCheckpointRegistryProvider(
                _load_registry(registry_path),
                expected_seed_lineage_id=runner._phase2_seed_lineage_id(
                    seed_contract
                ),
                expected_source_git_commit=runner.git_text(
                    "rev-parse", "HEAD"
                ),
            ).preflight()
            live_registry["qualified_checkpoint_found"] = True
        except RouteBCheckpointRegistryError as error:
            live_registry = dict(error.evidence)
            live_registry["qualified_checkpoint_found"] = False
    return {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_live_entry_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending",
        "ck3_started": False,
        "service_instantiated": False,
        "gameplay_action_executed": False,
        "provider_live_result_claimed": False,
        "checks": checks,
        "failed_checks": failed,
        "live_registry": live_registry,
        "live_gate_ready": live_registry.get("result") == "GREEN",
        "career_hc_provider_default_off": True,
        "formal_execute_requires": [
            "--phase2-hc-workforce-route-b-live",
            "--phase2-hc-workforce-route-b-checkpoint-registry",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_preflight(arguments.registry)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output is not None:
        output = arguments.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
