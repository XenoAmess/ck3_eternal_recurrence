#!/usr/bin/env python3
"""No-launch static preflight for the B6 career-HC workforce action cell."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
for item in (AUTOPLAYER_SRC, MOD_TOOLS):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from xar_autoplayer.bridge.zhongguo_career_hc_workforce_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
)
from zg361_effect_sharding import top_level_effect_entries  # noqa: E402


SOURCE_CONTRACT = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "zhongguo_career_hc_workforce_postcondition_v1_source_contract.json"
)
ACTION_CELL = ROOT / "tools" / "zg361_phase2_hc_workforce_b6_action_cell.py"
NATIVE_BRIDGE = ROOT / "ck3_autonomous_player" / "native_bridge"
NATIVE_HEADER = NATIVE_BRIDGE / "include" / "xar_bridge" / (
    "zhongguo_career_hc_workforce_postcondition_v1.hpp"
)
NATIVE_SOURCE = NATIVE_BRIDGE / "src" / (
    "zhongguo_career_hc_workforce_postcondition_v1.cpp"
)
NATIVE_SERIALIZER = NATIVE_BRIDGE / "src" / (
    "zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp"
)
NATIVE_MAILBOX = NATIVE_BRIDGE / "src" / (
    "zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp"
)
CK3_ADAPTER = NATIVE_BRIDGE / "src" / "ck3_11906_adapter.cpp"
SHARED_BRIDGE = NATIVE_BRIDGE / "src" / "bridge.cpp"
CMAKE = NATIVE_BRIDGE / "CMakeLists.txt"
SERVICE = AUTOPLAYER_SRC / "xar_autoplayer" / "bridge" / "service.py"
MCP_SERVER = AUTOPLAYER_SRC / "xar_autoplayer" / "bridge" / "mcp_server.py"
FORMAL_RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
ROUTE_B_EFFECT = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_workforce_endgame_059_al_m360_route_b_effects.txt"
)
CAREER_EFFECTS = (
    ROOT / "mod_zhongguo_style" / "common" / "scripted_effects"
)
PRIVATE_SWITCH = "XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1"


def _default_adapter_projection(source: str) -> str:
    return re.sub(
        rf"#if defined\({PRIVATE_SWITCH}\).*?#endif",
        "",
        source,
        flags=re.DOTALL,
    )


def run_preflight() -> dict[str, object]:
    contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
    route_b = ROUTE_B_EFFECT.read_text(encoding="utf-8-sig")
    action_cell = ACTION_CELL.read_text(encoding="utf-8")
    native_header = NATIVE_HEADER.read_text(encoding="utf-8")
    native_source = NATIVE_SOURCE.read_text(encoding="utf-8")
    native_serializer = NATIVE_SERIALIZER.read_text(encoding="utf-8")
    native_mailbox = NATIVE_MAILBOX.read_text(encoding="utf-8")
    ck3_adapter = CK3_ADAPTER.read_text(encoding="utf-8")
    shared_bridge = SHARED_BRIDGE.read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    mcp_server = MCP_SERVER.read_text(encoding="utf-8")
    formal_runner = FORMAL_RUNNER.read_text(encoding="utf-8")
    career_shards = sorted(CAREER_EFFECTS.glob("zg361_career_hc_[0-9][0-9][0-9]_*.txt"))
    counts = {
        path.name: len(top_level_effect_entries(path.read_bytes()))
        for path in career_shards
    }
    partition_keys = (
        "zg361_ch_hc_authorized",
        "zg361_ch_hc_available",
        "zg361_ch_hc_reserved",
        "zg361_ch_hc_occupied",
        "zg361_ch_hc_frozen",
        "zg361_ch_hc_reclaimed",
        "zg361_ch_hc_conserved",
    )
    career_text = "\n".join(
        path.read_text(encoding="utf-8-sig") for path in career_shards
    )
    checks = {
        "source_contract_live_pending": contract.get("readiness")
        == "static_and_fixture_ready_live_pending",
        "query_capability_exact": contract.get("capability")
        == QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
        "source_contract_counts_current": (
            contract.get("allowlist_count") == 14
            and contract.get("mailbox_fixed_slot_index") == 26
            and contract.get("adapter_capability_counts")
            == {
                "default": 76,
                "projects_metrics_only": 77,
                "career_hc_workforce_only": 77,
                "both_private_candidates": 78,
            }
        ),
        "focused_runner_registry_wired_default_off": contract.get("integration", {}).get(
            "formal_runner_registry_modified"
        )
        is True
        and contract.get("integration", {}).get("formal_runner_mode")
        == "--phase2-hc-workforce-route-b-live"
        and contract.get("integration", {}).get("formal_runner_provider_gate")
        == "default_off_explicit_enable_required"
        and '"--phase2-hc-workforce-route-b-live"' in formal_runner
        and "career_hc_live_gate_default_off" in formal_runner,
        "native_provider_wiring_complete_default_off": contract.get("integration", {}).get(
            "native_provider_wiring"
        )
        == "complete_default_off_until_live",
        "native_reader_fixed_allowlist": (
            "kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist"
            in native_header
            and "first != second" in native_source
            and "variable_name" not in native_header
        ),
        "native_typed_serializer_has_exact_provenance": all(
            token in native_serializer
            for token in (
                "native-headless",
                "kZhongguoCareerHcWorkforcePostconditionV1BackendId",
                "character_fallback_slot_rva",
            )
        ),
        "mailbox_slot_26_and_transport_wired": (
            "ExecuteZhongguoCareerHcWorkforceMailboxQueryV1" in native_mailbox
            and "permitted_executor_sexvigintary" in shared_bridge
            and "ZhongguoCareerHcWorkforceResultFrame" in shared_bridge
        ),
        "service_and_mcp_wired": (
            "def query_zhongguo_career_hc_workforce_postcondition_v1(" in service
            and "def ck3_query_zhongguo_career_hc_workforce_postcondition_v1("
            in mcp_server
        ),
        "private_candidate_switch_is_default_off": (
            re.search(
                rf"option\(\s*{PRIVATE_SWITCH}\s*.*?\s+OFF\s*\)",
                cmake,
                re.DOTALL,
            )
            is not None
            and re.search(
                rf"#if defined\({PRIVATE_SWITCH}\).*?"
                r"kZhongguoCareerHcWorkforcePostconditionV1Capability.*?#endif",
                ck3_adapter,
                re.DOTALL,
            )
            is not None
        ),
        "semantic_capability_default_off_until_live": (
            QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY
            not in _default_adapter_projection(ck3_adapter)
        ),
        "cell_requires_provider_postcondition": (
            "provider_postcondition_observed" in action_cell
            and "action_ack_is_business_postcondition" in action_cell
            and "subject_provider_session_required" in action_cell
        ),
        "route_b_product_effect_present": "zg361_we_m360_route_b_effect = {"
        in route_b,
        "route_b_receipt_state_choice_bound": all(
            token in route_b
            for token in (
                "RECEIPT_STATE_VAR = zg361_we_m360_receipt_state",
                "RECEIPT_CHOICE_VAR = zg361_we_m360_receipt_choice",
                "TICKET_STATE = 4",
                "CHOICE = 2",
            )
        ),
        "route_b_manager_cost_zero_present": (
            "var:zg361_we_al_external_collective_manager_cost_total = 0"
            in route_b
        ),
        "route_b_has_no_career_hc_read_or_write": "zg361_ch_hc_" not in route_b,
        "career_hc_partition_is_real_product_state": all(
            key in career_text for key in partition_keys
        ),
        "career_hc_effect_shards_present": bool(career_shards),
        "career_hc_effect_shards_target_1_to_10": bool(counts)
        and min(counts.values()) >= 1
        and max(counts.values()) <= 10,
    }
    failed = [name for name, value in checks.items() if value is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_hc_workforce_b6_no_launch_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending",
        "ck3_started": False,
        "gameplay_action_executed": False,
        "provider_live_result_claimed": False,
        "formal_runner_registry_modified": True,
        "formal_runner_provider_gate": "default_off_explicit_enable_required",
        "checks": checks,
        "failed_checks": failed,
        "career_hc_effect_shards": {
            "file_count": len(counts),
            "effect_count": sum(counts.values()),
            "minimum_effects_per_file": min(counts.values()) if counts else 0,
            "maximum_effects_per_file": max(counts.values()) if counts else 0,
        },
        "live_checkpoint_required": (
            "current cumulative projection; workforce transition fixture active; "
            "real zg361we.360 open before route-B selection; exact owner/subject "
            "subject-session rebind without date advance"
        ),
        "live_completion_requires": (
            "advertise the statically wired fixed provider, execute route B once, then "
            "capture one paused subject-side frame containing the exact state-4/"
            "choice-2 receipt, conserved six-bucket career-HC ledger, and zero "
            "manager cost"
        ),
    }


def main() -> int:
    result = run_preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
