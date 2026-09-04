#!/usr/bin/env python3
"""No-launch static preflight for the B6 career-HC workforce action cell."""

from __future__ import annotations

import json
from pathlib import Path
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


def run_preflight() -> dict[str, object]:
    contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
    route_b = ROUTE_B_EFFECT.read_text(encoding="utf-8-sig")
    action_cell = ACTION_CELL.read_text(encoding="utf-8")
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
        "runner_registry_untouched_by_contract": contract.get("integration", {}).get(
            "formal_runner_registry_modified"
        )
        is False,
        "native_provider_wiring_remains_pending": contract.get("integration", {}).get(
            "native_provider_wiring"
        )
        == "pending",
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
        "formal_runner_registry_modified": False,
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
            "wire and advertise the fixed provider, execute route B once, then "
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
