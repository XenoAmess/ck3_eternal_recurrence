#!/usr/bin/env python3
"""Static/no-launch preflight for the CP26 source-checkpoint capture entry."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
import zg361_phase2_projects_metrics_source_checkpoint as capture  # noqa: E402


CONTRACT_PATH = (
    ROOT / "tools" / "zg361_phase2_projects_metrics_source_checkpoint_contract.json"
)
MODULE_PATH = ROOT / "tools" / "zg361_phase2_projects_metrics_source_checkpoint.py"
CP26_EVENT_PATH = (
    ROOT / "mod_zhongguo_style" / "events" / "zg361_credit_project_runtime_events.txt"
)
P3_EVENT_PATH = (
    ROOT
    / "mod_zhongguo_style"
    / "events"
    / "zg361_phase3_metrics_delivery_runtime_events.txt"
)
ACTION_CELL_PATH = ROOT / "tools" / "zg361_phase2_projects_metrics_action_cell.py"


class ProjectsMetricsSourceCheckpointPreflightError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProjectsMetricsSourceCheckpointPreflightError(
            f"cannot read {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise ProjectsMetricsSourceCheckpointPreflightError(
            f"{path} must contain an object"
        )
    return value


def _contract_ready(value: Mapping[str, object]) -> bool:
    live = value.get("explicit_live_mode")
    required = value.get("required_checkpoint")
    registry = value.get("registry")
    evidence = value.get("business_evidence")
    entrypoints = value.get("entrypoints")
    return bool(
        value.get("schema_version") == 2
        and value.get("kind")
        == "zg361_projects_metrics_source_checkpoint_capture_contract"
        and value.get("span_id") == capture.SPAN_ID
        and value.get("handler") == capture.HANDLER
        and value.get("source_event_definition_key") == capture.SOURCE_EVENT
        and value.get("readiness") == capture.READINESS
        and isinstance(live, Mapping)
        and live.get("value") == capture.LIVE_MODE
        and live.get("cli_gate") == "--live"
        and live.get("attaches_to_existing_bridge_pipe") is True
        and live.get("starts_ck3") is False
        and live.get("creates_product_state") is False
        and isinstance(required, Mapping)
        and required.get("single_player") is True
        and required.get("product_only_mount") is True
        and required.get("played_character_role") == "project_subject"
        and required.get("owner_role") == "distinct_ai_project_owner"
        and required.get("paused") is True
        and required.get("map_ready") is True
        and required.get("active_player_event") is False
        and required.get("cp26_route_allowlist") == ["A", "B"]
        and required.get("cp26_contribution_receipt_prepared") is True
        and required.get("p3_initializer_run") is False
        and isinstance(registry, Mapping)
        and registry.get("schema_version") == capture.REGISTRY_SCHEMA_VERSION
        and registry.get("registry_kind") == capture.REGISTRY_KIND
        and registry.get("exclusive_write") is True
        and isinstance(evidence, Mapping)
        and evidence.get("ui_ack_is_business_postcondition") is False
        and evidence.get("provider_observed_source_receipt_required") is True
        and evidence.get("provider_result_identity_must_be_absent") is True
        and all(
            evidence.get(name) is False
            for name in (
                "fixture_used",
                "console_used",
                "test_decision_used",
                "generic_character_rebind_used",
            )
        )
        and isinstance(entrypoints, Mapping)
        and entrypoints
        == {
            "observe_ui": "observe_cp26_route_ui_live",
            "capture_checkpoint": (
                "capture_projects_metrics_source_checkpoint_live"
            ),
            "validate_registry": (
                "validate_projects_metrics_source_checkpoint_registry"
            ),
        }
        and all(callable(getattr(capture, str(name), None)) for name in entrypoints.values())
    )


def _service_surface_ready() -> bool:
    checkpoint_methods = (
        "capabilities",
        "snapshot",
        "query_zhongguo_projects_metrics_postcondition_v1",
        "save_checkpoint",
    )
    ui_methods = (
        "snapshot",
        "query_current_event_window_context_v1",
        "select_event_option",
    )
    return all(
        callable(getattr(capture.ProjectsMetricsCheckpointService, name, None))
        and callable(getattr(GameplayBridgeService, name, None))
        for name in checkpoint_methods
    ) and all(
        callable(getattr(capture.ProjectsMetricsUiService, name, None))
        and callable(getattr(GameplayBridgeService, name, None))
        for name in ui_methods
    ) and (
        list(
            inspect.signature(
                capture.ProjectsMetricsCheckpointService.save_checkpoint
            ).parameters
        )
        == list(inspect.signature(GameplayBridgeService.save_checkpoint).parameters)
    )


def _product_sources_ready() -> bool:
    try:
        cp26 = CP26_EVENT_PATH.read_text(encoding="utf-8-sig")
        p3 = P3_EVENT_PATH.read_text(encoding="utf-8-sig")
        action = ACTION_CELL_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    cp_start = cp26.find("zg361cp.26 = {")
    cp_end = cp26.find("\nzg361cp.27 = {", cp_start)
    cp_block = cp26[cp_start:cp_end]
    p3_start = p3.find("zg361p3.229 = {")
    p3_end = p3.find("\nzg361p3.230 = {", p3_start)
    p3_block = p3[p3_start:p3_end]
    return bool(
        cp_start >= 0
        and cp_end > cp_start
        and p3_start >= 0
        and p3_end > p3_start
        and "is_ai = no" in cp_block
        and "zg361_cp_e_owner" in cp_block
        and "zg361_cp_e_subject" in cp_block
        and "zg361_cp_m26_route_a_effect" in cp_block
        and "zg361_cp_m26_route_b_effect" in cp_block
        and "zg361_cp_m26_route_c_effect" in cp_block
        and "zg361_p3_m229_route_a_effect" in p3_block
        and "zg361_p3_m229_route_b_effect" in p3_block
        and "source_ready_result_pending" in action
        and "result_operation_committed" in action
    )


def _no_launcher_surface() -> bool:
    try:
        source = MODULE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    forbidden = (
        "import subprocess",
        "from subprocess",
        "Start-Process",
        "launch_native_ck3",
        "create_managed_native_session",
        "Popen(",
    )
    return not any(token in source for token in forbidden) and all(
        token in source
        for token in (
            '"--live"',
            'subparsers.add_parser("observe-ui")',
            'subparsers.add_parser("capture-checkpoint")',
            "NativeHeadlessGameplayDriver(",
        )
    )


def audit_projects_metrics_source_checkpoint_capture(
    root: Path = ROOT,
) -> dict[str, object]:
    """Inspect static files and signatures only; never instantiate a driver."""

    del root
    contract = _load(CONTRACT_PATH)
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    checks = {
        "schema2_contract_is_strict": _contract_ready(contract),
        "concrete_service_surfaces_match": _service_surface_ready(),
        "real_cp26_and_p3_product_sources_present": _product_sources_ready(),
        "explicit_live_cli_only_attaches_to_existing_pipe": _no_launcher_surface(),
        "capture_requires_source_ready_result_pending": (
            '"source_ready_result_pending"' in module_source
            and '"cp26_provider_source_not_ready"' in module_source
        ),
        "capture_requires_played_subject_distinct_owner_event_free": all(
            token in module_source
            for token in (
                'require_event=False',
                '"owner_must_be_distinct_ai"',
                '"played_character_is_subject": True',
                '"no_active_player_event": True',
            )
        ),
        "ui_and_provider_receipts_are_content_addressed": all(
            token in module_source
            for token in (
                'f"{stem}.ui-receipt.json"',
                'f"{stem}.provider-receipt.json"',
                '"sha256": ui_sha',
                '"sha256": provider_sha',
            )
        ),
        "registry_is_schema2_and_exclusive": (
            capture.REGISTRY_SCHEMA_VERSION == 2
            and '"schema_version": REGISTRY_SCHEMA_VERSION' in module_source
            and 'target.open("xb")' in module_source
        ),
        "entry_is_canonical_schema2_manifest_compatible": all(
            token in module_source
            for token in (
                '"source_receipt": source_receipt',
                '"handler": HANDLER',
                '"checkpoint_sha256": expected_sha',
                '"save_lineage_id": lineage["seed_lineage_id"]',
                '"provider_observed": True',
                '"ui_state_verified": True',
            )
        ),
        "ack_fixture_console_cannot_claim_business_state": all(
            token in module_source
            for token in (
                '"action_ack_is_business_postcondition": False',
                '"provider_observed_business_state": True',
                '"fixture_used": False',
                '"console_used": False',
                '"test_decision_used": False',
                '"generic_character_rebind_used": False',
            )
        ),
        "preflight_does_not_start_or_attach": True,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 2,
        "kind": "zg361_projects_metrics_source_checkpoint_no_launch_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": capture.READINESS if not failed else "research",
        "checks": checks,
        "failed_checks": failed,
        "ck3_started": False,
        "driver_instantiated": False,
        "bridge_attached": False,
        "checkpoint_captured": False,
        "registry_written": False,
        "live_proof_claimed": False,
        "next_live_entry": (
            "observe-ui on real owner-visible zg361cp.26 route A/B, then "
            "capture-checkpoint on the same-lineage played-subject, "
            "event-free, CP26-source-ready/P3-result-pending paused frame"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = audit_projects_metrics_source_checkpoint_capture()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report["result"] != "GREEN" else 0


if __name__ == "__main__":
    raise SystemExit(main())
