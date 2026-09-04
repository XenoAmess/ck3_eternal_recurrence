#!/usr/bin/env python3
"""No-CK3 source/contract preflight for the projects-metrics action cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tools/zg361_phase2_projects_metrics_action_contract.json"
ABI = (
    ROOT
    / "ck3_autonomous_player/native_bridge/research/"
    "zhongguo_projects_metrics_postcondition_v1_abi.json"
)
ADAPTER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
)
CMAKE = ROOT / "ck3_autonomous_player/native_bridge/CMakeLists.txt"
SERVICE = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"
CENTRAL = ROOT / "mod_zhongguo_style/tools/gen_361_phase2_central_runtime.py"
CP_EVENTS = ROOT / "mod_zhongguo_style/events/zg361_credit_project_runtime_events.txt"
P3_EVENTS = (
    ROOT
    / "mod_zhongguo_style/events/zg361_phase3_metrics_delivery_runtime_events.txt"
)

CAPABILITY = "game.command.query-zhongguo-projects-metrics-postcondition-v1"
PRIVATE_SWITCH = "XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1"


def _event_block(text: str, event_id: str, next_id: str | None) -> str:
    start = text.find(f"{event_id} = {{")
    if start < 0:
        return ""
    if next_id is None:
        return text[start:]
    end = text.find(f"{next_id} = {{", start + len(event_id) + 4)
    return text[start:] if end < 0 else text[start:end]


def audit_projects_metrics_action_cell_contract(
    root: Path = ROOT,
) -> dict[str, object]:
    """Prove static wiring and preserve the exact remaining live blockers."""

    # ``root`` is injectable for tests, while the canonical constants keep the
    # command-line path simple.
    contract_path = root / CONTRACT.relative_to(ROOT)
    abi_path = root / ABI.relative_to(ROOT)
    adapter_path = root / ADAPTER.relative_to(ROOT)
    cmake_path = root / CMAKE.relative_to(ROOT)
    service_path = root / SERVICE.relative_to(ROOT)
    central_path = root / CENTRAL.relative_to(ROOT)
    cp_path = root / CP_EVENTS.relative_to(ROOT)
    p3_path = root / P3_EVENTS.relative_to(ROOT)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    adapter = adapter_path.read_text(encoding="utf-8")
    cmake = cmake_path.read_text(encoding="utf-8")
    service = service_path.read_text(encoding="utf-8")
    central = central_path.read_text(encoding="utf-8-sig")
    cp_event = _event_block(
        cp_path.read_text(encoding="utf-8-sig"), "zg361cp.26", "zg361cp.27"
    )
    p3_event = _event_block(
        p3_path.read_text(encoding="utf-8-sig"), "zg361p3.229", "zg361p3.230"
    )
    phase3_generator = (
        root / "mod_zhongguo_style/tools/gen_361_phase3_metrics_delivery_runtime.py"
    ).read_text(encoding="utf-8")
    stage_7 = central.find('(7, "metrics_delivery", "zg361_p3_open_portfolio_effect")')
    stage_8 = central.find('(8, "credit_project", "zg361_cp_open_portfolio_effect")')
    guarded_capability = (
        f"#if defined({PRIVATE_SWITCH})" in adapter
        and "ck3_11906::kZhongguoProjectsMetricsPostconditionV1Capability"
        in adapter
    )
    adapter_default_projection = adapter
    guarded_start = adapter.find(f"#if defined({PRIVATE_SWITCH})")
    if guarded_start >= 0:
        guarded_end = adapter.find("#endif", guarded_start)
        if guarded_end >= 0:
            adapter_default_projection = (
                adapter[:guarded_start] + adapter[guarded_end + len("#endif") :]
            )
    checks = {
        "contract_identity": contract.get("kind")
        == "zg361_phase2_projects_metrics_action_cell"
        and contract.get("span_id") == "phase2_projects_metrics"
        and contract.get("producer_key") == "projects-metrics",
        "readiness_is_static_live_pending": contract.get("readiness")
        == "static-ready-live-pending",
        "ack_explicitly_not_postcondition": contract.get(
            "query_action_postcondition", {}
        ).get("action_ack_is_business_postcondition")
        is False,
        "provider_abi_static_not_live": abi.get("status")
        == "static_and_fixture_ready_not_live"
        and abi.get("readiness", {}).get("production_live_ready") is False,
        "service_reuses_existing_provider": (
            "def query_zhongguo_projects_metrics_postcondition_v1(" in service
        ),
        "provider_capability_still_withheld_by_default": (
            CAPABILITY not in adapter_default_projection
        ),
        "private_candidate_switch_is_default_off": (
            f"option(\n  {PRIVATE_SWITCH}" in cmake
            and "\n  OFF\n)" in cmake[cmake.find(PRIVATE_SWITCH) :][:500]
            and guarded_capability
        ),
        "cp26_visible_event_is_owner_only": (
            "is_ai = no" in cp_event
            and "this = scope:zg361_cp_e_owner" in cp_event
        ),
        "p3m229_visible_event_is_owner_only": (
            "is_ai = no" in p3_event
            and "this = scope:zg361_p3_aa_owner" in p3_event
        ),
        "central_metrics_precedes_credit": (
            stage_7 >= 0 and stage_8 > stage_7
        ),
        "ai_initialization_and_m229_route_are_atomic": (
            "zg361_p3_initialize_portfolio_effect = yes" in phase3_generator
            and "zg361_p3_{domain}_run_authorized_ai_effect = yes"
            in phase3_generator
        ),
        "formal_registry_untouched_by_contract": contract.get(
            "future_runner_integration", {}
        ).get("formal_registry_modified")
        is False,
        "no_live_claim": contract.get("no_launch_boundary", {}).get(
            "live_proof_claimed"
        )
        is False,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_projects_metrics_action_cell_static_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending" if not failed else "research",
        "checks": checks,
        "failed_checks": failed,
        "ck3_started": False,
        "live_proof_claimed": False,
        "next_live_checkpoint": contract.get("exact_live_checkpoint"),
        "known_live_gaps": contract.get("known_live_gaps"),
        "future_runner_integration": contract.get("future_runner_integration"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="exit nonzero when static wiring is RED"
    )
    args = parser.parse_args()
    report = audit_projects_metrics_action_cell_contract()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report["result"] != "GREEN" else 0


if __name__ == "__main__":
    raise SystemExit(main())
