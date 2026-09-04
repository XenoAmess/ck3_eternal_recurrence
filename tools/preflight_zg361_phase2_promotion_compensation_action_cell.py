#!/usr/bin/env python3
"""No-launch static preflight for the promotion/compensation action cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
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
RUNNER = ROOT / "tools/run_zhongguo_acceptance.py"
CAPTURE_CHOREOGRAPHY = ROOT / "tools/zhongguo_phase2_capture_choreography.py"
EVENT_CHOREOGRAPHY = ROOT / "tools/zhongguo_phase2_event_choreography.py"
SOURCE_CHECKPOINT_PROVIDER = (
    ROOT / "tools/zhongguo_phase2_source_checkpoint_provider.py"
)
ABI = (
    ROOT
    / "ck3_autonomous_player/native_bridge/research/"
    "zhongguo_promotion_compensation_postcondition_v1_abi.json"
)
SOURCE_CONTRACT = (
    ROOT
    / "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_compensation_postcondition_v1_source_contract.json"
)
HEADER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/include/xar_bridge/"
    "zhongguo_promotion_compensation_postcondition_v1.hpp"
)
READER_SERIALIZER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/src/"
    "zhongguo_promotion_compensation_postcondition_v1.cpp"
)
MAILBOX = (
    ROOT
    / "ck3_autonomous_player/native_bridge/src/"
    "zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp"
)
SHARED_MAILBOX_HEADER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/include/xar_bridge/"
    "main_thread_query_mailbox_v1.hpp"
)
SHARED_BRIDGE = ROOT / "ck3_autonomous_player/native_bridge/src/bridge.cpp"
GAME_ADAPTER = ROOT / "ck3_autonomous_player/native_bridge/src/game_adapter.cpp"
NATIVE_DRIVER = (
    ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
)
MCP_SERVER = (
    ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
)
SCHEMA = (
    ROOT
    / "ck3_autonomous_player/schemas/"
    "zhongguo-promotion-compensation-postcondition-v1.schema.json"
)
CMAKE = ROOT / "ck3_autonomous_player/native_bridge/CMakeLists.txt"
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


def _array_values(text: str, symbol: str) -> list[str]:
    match = re.search(
        rf"{re.escape(symbol)}[^{{]*\{{(?P<body>.*?)\}};",
        text,
        re.DOTALL,
    )
    return [] if match is None else re.findall(r'"([^"]+)"', match.group("body"))


def _array_integers(text: str, symbol: str) -> list[int]:
    match = re.search(
        rf"{re.escape(symbol)}[^{{]*\{{(?P<body>.*?)\}};",
        text,
        re.DOTALL,
    )
    if match is None:
        return []
    return [int(value) for value in re.findall(r"\b\d+\b", match.group("body"))]


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def run_preflight() -> dict[str, object]:
    """Inspect only repository files; never connect to or launch CK3."""

    contract = _load(CONTRACT)
    abi = _load(ABI)
    source_contract = _load(SOURCE_CONTRACT)
    schema = _load(SCHEMA)
    action = contract.get("action")
    source_checkpoint = contract.get("source_checkpoint")
    result_checkpoint = contract.get("result_checkpoint")
    runner_registration = contract.get("runner_registration")
    required = contract.get("required_bridge_capabilities")
    source_text = SOURCE_EVENTS.read_text(encoding="utf-8-sig")
    result_text = RESULT_EVENTS.read_text(encoding="utf-8-sig")
    runner_text = RUNNER.read_text(encoding="utf-8-sig")
    capture_choreography_text = CAPTURE_CHOREOGRAPHY.read_text(
        encoding="utf-8-sig"
    )
    event_choreography_text = EVENT_CHOREOGRAPHY.read_text(
        encoding="utf-8-sig"
    )
    source_checkpoint_provider_text = SOURCE_CHECKPOINT_PROVIDER.read_text(
        encoding="utf-8-sig"
    )
    adapter_text = ADAPTER.read_text(encoding="utf-8-sig")
    service_text = SERVICE.read_text(encoding="utf-8-sig")
    header_text = HEADER.read_text(encoding="utf-8-sig")
    reader_text = READER_SERIALIZER.read_text(encoding="utf-8-sig")
    mailbox_text = MAILBOX.read_text(encoding="utf-8-sig")
    shared_mailbox_text = SHARED_MAILBOX_HEADER.read_text(encoding="utf-8-sig")
    shared_bridge_text = SHARED_BRIDGE.read_text(encoding="utf-8-sig")
    game_adapter_text = GAME_ADAPTER.read_text(encoding="utf-8-sig")
    native_driver_text = NATIVE_DRIVER.read_text(encoding="utf-8-sig")
    mcp_server_text = MCP_SERVER.read_text(encoding="utf-8-sig")
    cmake_text = CMAKE.read_text(encoding="utf-8-sig")
    owner_allowlist = _array_values(
        header_text, "kZhongguoPromotionCompensationOwnerVariableAllowlist"
    )
    subject_allowlist = _array_values(
        header_text, "kZhongguoPromotionCompensationSubjectBaseVariableAllowlist"
    )
    mechanism_allowlist = _array_integers(
        header_text, "kZhongguoPromotionCompensationMechanismAllowlist"
    )
    source_allowlists = source_contract.get("allowlists")
    schema_defs = schema.get("$defs")
    typed_integer = (
        schema_defs.get("typed_integer") if isinstance(schema_defs, Mapping) else None
    )
    typed_boolean = (
        schema_defs.get("typed_boolean") if isinstance(schema_defs, Mapping) else None
    )
    mcp_signature = re.search(
        r"def ck3_query_zhongguo_promotion_compensation_postcondition_v1\("
        r"(?P<body>.*?)\)\s*->",
        mcp_server_text,
        re.DOTALL,
    )
    checks = {
        "contract_identity": contract.get("schema_version") == 1
        and contract.get("cell_id") == ACTION_CELL_ID
        and contract.get("span") == "promotion-compensation",
        "readiness_is_live_pending": contract.get("readiness")
        == IMPLEMENTATION_READINESS
        and contract.get("production_live") is False
        and contract.get("formal_runner_registered") is True,
        "formal_runner_registration_exact": isinstance(
            runner_registration, Mapping
        )
        and runner_registration.get("cell_id")
        == "promotion_compensation_gameplay_action_and_postcondition_matrix"
        and runner_registration.get("handler")
        == "capture_promotion_compensation"
        and runner_registration.get("source_checkpoint_provider")
        == "Phase2SourceCheckpointProvider"
        and runner_registration.get("source_checkpoint_evidence_class")
        == "real_ck3"
        and runner_registration.get("fixture_checkpoint_allowed") is False
        and runner_registration.get("console_checkpoint_allowed") is False
        and runner_registration.get("provider_capability_default_advertised")
        is False,
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
        "formal_runner_registry_and_driver_are_wired": all(
            token in runner_text
            for token in (
                '"promotion_compensation_gameplay_action_and_postcondition_matrix"',
                "QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY",
                '"zhongguo_promotion_compensation_v1_query_supported"',
                '"source_checkpoint_handler": PROMOTION_HANDLER',
                '"source_event_definition_key": PROMOTION_COMPENSATION_SOURCE_EVENT',
                '"source_option_number": PROMOTION_COMPENSATION_SOURCE_OPTION',
                '"result_event_definition_key": PROMOTION_COMPENSATION_RESULT_EVENT',
                "run_promotion_compensation_gameplay_action_cell(",
                "advance_to_result=_phase2_promotion_compensation_advance_to_result",
                '"action_ack_is_business_postcondition": False',
            )
        ),
        "capture_choreography_uses_exact_action_provider": all(
            token in capture_choreography_text
            for token in (
                '"capture_promotion_compensation"',
                '"run_promotion_compensation_gameplay_action_cell"',
                '"zg361pp.147"',
                '"zg361comp.1"',
                '"query-zhongguo-promotion-compensation-postcondition-v1"',
            )
        ),
        "event_plan_uses_exact_source_and_result": all(
            token in event_choreography_text
            for token in (
                '"capture_promotion_compensation"',
                '"zg361pp.147"',
                '"zg361comp.1"',
            )
        ),
        "source_checkpoint_provider_is_real_read_only": all(
            token in source_checkpoint_provider_text
            for token in (
                '"capture_promotion_compensation"',
                'receipt.get("evidence_class") == "real_ck3"',
                'receipt.get("fixture_used") is False',
                'receipt.get("console_used") is False',
                "path.is_file()",
                "_sha256(path) == expected_sha",
                'receipt.get("generic_character_rebind_used") is False',
                'entry.source_event_definition_key == plan.source_event',
            )
        )
        and "write_bytes" not in source_checkpoint_provider_text
        and "write_text" not in source_checkpoint_provider_text,
        "provider_source_contract_is_frozen": (
            source_contract.get("contract")
            == "zhongguo_promotion_compensation_postcondition_v1_source_contract"
            and source_contract.get("readiness")
            == "static_and_fixture_ready_live_pending"
            and source_contract.get("capability") == PROVIDER_CAPABILITY
            and source_contract.get("public_inputs")
            == ["request_nonce", "expected_revision"]
            and source_contract.get("caller_selected_variable_names") is False
            and source_contract.get("caller_selected_characters") is False
            and source_contract.get("wired_layers")
            == [
                "reader",
                "serializer",
                "schema",
                "mailbox",
                "bridge",
                "native_driver",
                "service",
                "mcp",
            ]
            and source_contract.get("shared_wiring")
            == "default_off_complete_not_advertised"
            and source_contract.get("default_adapter_advertised") is False
            and source_contract.get("production_live_ready") is False
        ),
        "exact_build_matches_source_contract": (
            isinstance(source_contract.get("exact_build"), Mapping)
            and source_contract["exact_build"].get("game_version")
            == abi.get("game_version")
            and source_contract["exact_build"].get("executable_sha256")
            == abi.get("executable_sha256")
            and abi.get("source_contract")
            == "fixtures/zhongguo_promotion_compensation_postcondition_v1_source_contract.json"
        ),
        "fixed_native_allowlists_match_contract": (
            isinstance(source_allowlists, Mapping)
            and len(owner_allowlist)
            == source_allowlists.get("owner_variable_count")
            == len(abi.get("owner_allowlist", []))
            and len(subject_allowlist)
            == source_allowlists.get("subject_base_variable_count")
            and mechanism_allowlist
            == source_allowlists.get("mechanism_ids")
            == abi.get("compensation_receipt_selector", {}).get(
                "mechanism_allowlist"
            )
        ),
        "reader_uses_only_posted_business_receipts": all(
            token in header_text + reader_text
            for token in (
                "zg361_pp_m147_receipt_serial",
                "zg361_pp_m147_receipt_revision",
                "zg361_comp_promotion_receipt_choice_serial",
                "zg361_comp_promotion_receipt_serial",
                "ready.receipt_serials_ready =",
                "IsMechanismAllowlisted",
            )
        )
        and "action_ack" not in reader_text,
        "typed_unavailable_is_reader_and_schema_enforced": all(
            token in reader_text
            for token in (
                'Unavailable(output, "variable_absent")',
                'Unavailable(output, "variable_kind_mismatch")',
                '"boolean_value_invalid"',
            )
        )
        and isinstance(typed_integer, Mapping)
        and isinstance(typed_integer.get("oneOf"), list)
        and len(typed_integer["oneOf"]) == 2
        and isinstance(typed_boolean, Mapping)
        and isinstance(typed_boolean.get("oneOf"), list)
        and len(typed_boolean["oneOf"]) == 2,
        "mailbox_and_shared_bridge_are_wired": (
            "ExecuteZhongguoPromotionCompensationMailboxQueryV1" in mailbox_text
            and "permitted_executor_trivigintary" in shared_mailbox_text
            and "ExecuteZhongguoPromotionCompensationMailboxQueryV1"
            in shared_bridge_text
            and "zhongguo_promotion_compensation_query_sequence"
            in shared_bridge_text
        ),
        "game_adapter_parser_is_wired": (
            "ParseZhongguoPromotionCompensationPostconditionV1Step(step)"
            in game_adapter_text
        ),
        "driver_service_and_mcp_are_wired": (
            "def _execute_zhongguo_promotion_compensation_v1_query("
            in native_driver_text
            and "def query_zhongguo_promotion_compensation_postcondition_v1("
            in service_text
            and mcp_signature is not None
            and "request_nonce" in mcp_signature.group("body")
            and "expected_revision" in mcp_signature.group("body")
            and "owner_character_id" not in mcp_signature.group("body")
            and "subject_character_id" not in mcp_signature.group("body")
            and "variable_name" not in mcp_signature.group("body")
        ),
        "native_provider_tests_are_registered": all(
            token in cmake_text
            for token in (
                "xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test",
                "xar_ck3_zg_promo_comp_mailbox_v1_test",
            )
        ),
        "ack_is_excluded_from_provider_evidence": (
            "action_ack_is_never_business_postcondition"
            in source_contract.get("required_invariants", [])
            and isinstance(action, Mapping)
            and action.get("action_ack_is_business_postcondition") is False
        ),
        "no_ck3_launch_attempted": True,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_compensation_no_launch_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": IMPLEMENTATION_READINESS,
        "production_live": False,
        "ck3_started": False,
        "ck3_launch_attempted": False,
        "provider_live_result_claimed": False,
        "formal_runner_registered": True,
        "provider_source_contract": str(SOURCE_CONTRACT.relative_to(ROOT)),
        "next_live_checkpoint": source_contract.get("next_live_checkpoint"),
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
