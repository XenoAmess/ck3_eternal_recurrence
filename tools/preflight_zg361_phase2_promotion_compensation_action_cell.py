#!/usr/bin/env python3
"""No-launch static preflight for the promotion/compensation action cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from zg361_phase2_promotion_compensation_action_cell import (
    ACTION_CELL_ID,
    IMPLEMENTATION_READINESS,
    RESULT_EVENT_DEFINITION_KEY,
    SOURCE_EVENT_DEFINITION_KEY,
    SOURCE_OPTION_NUMBER,
)


CONTRACT = (
    ROOT
    / "tools/fixtures/zg361_phase2_promotion_compensation_action_cell_v1.json"
)
ABI = (
    ROOT
    / "ck3_autonomous_player/native_bridge/research/"
    "zhongguo_promotion_compensation_postcondition_v1_abi.json"
)
ADAPTER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
)
SERVICE = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"
SOURCE_EVENTS = (
    ROOT
    / "mod_zhongguo_style/events/"
    "zg361_feedback_promotion_pip_runtime_events.txt"
)
RESULT_EVENTS = (
    ROOT
    / "mod_zhongguo_style/events/zg361_generated_compensation_runtime_events.txt"
)
PROVIDER_CAPABILITY = (
    "game.command.query-zhongguo-promotion-compensation-postcondition-v1"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def run_preflight() -> dict[str, object]:
    """Inspect only repository files; never connect to or launch CK3."""

    contract = _load(CONTRACT)
    abi = _load(ABI)
    action = contract.get("action")
    source_checkpoint = contract.get("source_checkpoint")
    result_checkpoint = contract.get("result_checkpoint")
    required = contract.get("required_bridge_capabilities")
    source_text = SOURCE_EVENTS.read_text(encoding="utf-8-sig")
    result_text = RESULT_EVENTS.read_text(encoding="utf-8-sig")
    adapter_text = ADAPTER.read_text(encoding="utf-8-sig")
    service_text = SERVICE.read_text(encoding="utf-8-sig")
    checks = {
        "contract_identity": contract.get("schema_version") == 1
        and contract.get("cell_id") == ACTION_CELL_ID
        and contract.get("span") == "promotion-compensation",
        "readiness_is_live_pending": contract.get("readiness")
        == IMPLEMENTATION_READINESS
        and contract.get("production_live") is False
        and contract.get("formal_runner_registered") is False,
        "action_contract_exact": isinstance(action, Mapping)
        and action.get("source_event_definition_key")
        == SOURCE_EVENT_DEFINITION_KEY
        and action.get("result_event_definition_key")
        == RESULT_EVENT_DEFINITION_KEY
        and action.get("option_number") == SOURCE_OPTION_NUMBER
        and action.get("action_ack_is_business_postcondition") is False,
        "source_checkpoint_complete": isinstance(source_checkpoint, Mapping)
        and source_checkpoint.get("paused") is True
        and source_checkpoint.get("map_ready") is True
        and source_checkpoint.get("played_character_is_root_and_owner") is True
        and source_checkpoint.get("expected_option_count") == 3,
        "result_checkpoint_complete": isinstance(result_checkpoint, Mapping)
        and result_checkpoint.get("paused") is True
        and result_checkpoint.get("map_ready") is True
        and result_checkpoint.get("same_connection_generation") is True
        and result_checkpoint.get("same_played_owner") is True
        and result_checkpoint.get("snapshot_revision_advanced") is True,
        "required_capabilities_exact": isinstance(required, list)
        and set(required)
        == {
            "game.command.query-current-event-window-context-v1",
            PROVIDER_CAPABILITY,
            "game.command.select-event-option-N",
        },
        "source_event_authored": "zg361pp.147 = {" in source_text
        and source_text.count("zg361_pp_m147_manager_apply_effect = {") == 3,
        "result_event_authored": "zg361comp.1 = {" in result_text,
        "service_facade_available": (
            "def query_zhongguo_promotion_compensation_postcondition_v1("
            in service_text
        ),
        "abi_static_ready_default_off": isinstance(abi.get("readiness"), Mapping)
        and abi["readiness"].get("production_live_ready") is False
        and abi["readiness"].get("default_adapter_advertised") is False
        and abi.get("status")
        == "static_fixture_and_shared_wiring_ready_default_off_not_live",
        "default_adapter_remains_unadvertised": PROVIDER_CAPABILITY
        not in adapter_text,
        "no_ck3_launch_attempted": True,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_compensation_no_launch_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": IMPLEMENTATION_READINESS,
        "production_live": False,
        "ck3_launch_attempted": False,
        "formal_runner_registered": False,
        "source_checkpoint": source_checkpoint,
        "result_checkpoint": result_checkpoint,
        "live_blocker": contract.get("live_blocker"),
        "checks": checks,
        "failed_checks": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_preflight()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run_preflight"]
