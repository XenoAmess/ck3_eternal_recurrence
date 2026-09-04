#!/usr/bin/env python3
"""Offline B4 action-cell preflight for the ``hc-workforce`` promo span.

The real product action and provider proof already live in
``zhongguo_phase2_workforce_action``.  This module closes the remaining
offline integration contract: one selected route, the concrete service
surface, the existing runner entrypoints, a hash-bound seed, and the exact
live checkpoint that still has to be captured.  It never creates a service,
starts CK3, submits an action, or treats an ACK as a business receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402

import zhongguo_phase2_workforce_action as action  # noqa: E402


CONTRACT_PATH = ROOT / "tools" / "zg361_phase2_hc_workforce_b4_action_contract.json"
DEFAULT_SEED_CONTRACT_PATH = ROOT / "tools" / "zg361_phase2_seed_contract.json"
RUNNER_PATH = ROOT / "tools" / "run_zhongguo_acceptance.py"
PRODUCT_EVENT_PATH = (
    ROOT
    / "mod_zhongguo_style"
    / "events"
    / "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt"
)
ROUTE_B_EFFECT_PATH = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_workforce_endgame_059_al_m360_route_b_effects.txt"
)
PROVIDER_ABI_PATH = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "zhongguo_workforce_collective_snapshot_v1_abi.json"
)
PROVIDER_SOURCE_CONTRACT_PATH = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "zhongguo_workforce_collective_snapshot_v1_source_contract.json"
)
TRANSITION_FIXTURE_PATH = (
    ROOT / "tools" / "fixtures" / "zg361_phase2_workforce_action"
)

READINESS = "static-ready-live-pending"
SELECTED_ROUTE = "B"
SELECTED_NATIVE_OPTION_INDEX = 1
SELECTED_OPTION_NUMBER = 2
EXPECTED_SERVICE_METHODS = (
    "snapshot",
    "query_current_event_window_context_v1",
    "select_event_option",
    "query_zhongguo_workforce_collective_snapshot_v1",
    "execute_step",
)
EXPECTED_POSTCONDITION_FACTS = (
    "exact_owner_subject_cycle_case",
    "m360_receipt_state_4_choice_2",
    "route_b_collective_sealed_consumed_settled",
    "three_distinct_cohorts",
    "each_cohort_forced_equals_quota",
    "each_cohort_exception_zero",
    "each_cohort_manager_cost_zero",
    "collective_totals_conserved",
)
EXPECTED_FIXTURE_FILES = (
    "descriptor.mod",
    "common/scripted_guis/zga_phase2_workforce_guis.txt",
    "events/zga_phase2_workforce_events.txt",
    "gui/zga_phase2_workforce_bridge.gui",
    "gui/scripted_widgets/zga_phase2_workforce_scripted_widgets.txt",
    "localization/english/zga_phase2_workforce_l_english.yml",
    "localization/simp_chinese/zga_phase2_workforce_l_simp_chinese.yml",
)


class B4WorkforcePreflightError(RuntimeError):
    """The offline action-cell contract is missing or contradictory."""


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise B4WorkforcePreflightError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise B4WorkforcePreflightError(f"{label} must be a JSON object")
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise B4WorkforcePreflightError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise B4WorkforcePreflightError(f"{label} must be a list of strings")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise B4WorkforcePreflightError(f"{label} contains duplicates")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fixture_inventory() -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(TRANSITION_FIXTURE_PATH).as_posix()
            for path in TRANSITION_FIXTURE_PATH.rglob("*")
            if path.is_file()
        )
    )


def _service_surface_ready(contract: Mapping[str, Any]) -> bool:
    service_contract = _mapping(contract.get("service_contract"), "service_contract")
    declared = _strings(service_contract.get("required_methods"), "required_methods")
    if declared != EXPECTED_SERVICE_METHODS:
        return False
    for name in declared:
        protocol_method = getattr(action.WorkforceService, name, None)
        implementation_method = getattr(GameplayBridgeService, name, None)
        if not callable(protocol_method) or not callable(implementation_method):
            return False
        if inspect.signature(protocol_method) != inspect.signature(implementation_method):
            return False
    return True


def _action_surface_ready(contract: Mapping[str, Any]) -> bool:
    selected = _mapping(contract.get("selected_action"), "selected_action")
    cell = _mapping(contract.get("action_cell"), "action_cell")
    return (
        selected.get("event_definition_key") == action.M360_EVENT_DEFINITION_KEY
        and selected.get("route") == SELECTED_ROUTE
        and selected.get("native_option_index") == SELECTED_NATIVE_OPTION_INDEX
        and selected.get("option_number") == SELECTED_OPTION_NUMBER
        and action.ROUTE_NUMBER.get(SELECTED_ROUTE) == SELECTED_OPTION_NUMBER
        and selected.get("product_option_key") == "zg361we.360.b"
        and selected.get("product_effect") == "zg361_we_m360_route_b_effect"
        and cell.get("action_ack_is_business_receipt") is False
        and cell.get("provider_observed_postcondition_required") is True
        and callable(action.submit_m360_route_action)
        and callable(action.prove_m360_postcondition)
        and callable(action.run_m360_action_and_postcondition)
    )


def _product_route_ready() -> bool:
    try:
        event_text = PRODUCT_EVENT_PATH.read_text(encoding="utf-8-sig")
        route_text = ROUTE_B_EFFECT_PATH.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return False
    start = event_text.find("zg361we.360 = {")
    end = event_text.find("zg361we.361 = {", start + 1)
    if start >= 0 and end < 0:
        end = len(event_text)
    event_block = event_text[start:end] if start >= 0 and end > start else ""
    return (
        bool(event_block)
        and "type = character_event" in event_block
        and "hidden = yes" not in event_block
        and "is_ai = no" in event_block
        and event_block.count("\n\toption = {") == 3
        and "name = zg361we.360.b" in event_block
        and "zg361_we_materialize_m360_route_b_from_central_effect = {" in event_block
        and "zg361_we_m360_route_b_effect = {" in event_block
        and "zg361_we_m360_route_b_effect = {" in route_text
        and "set_variable = { name = zg361_we_m360_choice value = 2 }" in route_text
    )


def _provider_contract_ready(contract: Mapping[str, Any]) -> bool:
    try:
        abi = _load_json(PROVIDER_ABI_PATH, "Workforce provider ABI")
        source = _load_json(
            PROVIDER_SOURCE_CONTRACT_PATH, "Workforce provider source contract"
        )
    except B4WorkforcePreflightError:
        return False
    service = _mapping(contract.get("service_contract"), "service_contract")
    postcondition = _mapping(contract.get("postcondition"), "postcondition")
    facts = _strings(postcondition.get("required_facts"), "postcondition.required_facts")
    return (
        facts == EXPECTED_POSTCONDITION_FACTS
        and postcondition.get("provider")
        == "query_zhongguo_workforce_collective_snapshot_v1"
        and postcondition.get("provider_seal_scope")
        == "m360_current_cycle_route_b"
        and postcondition.get("m361_charter_required") is False
        and abi.get("contract") == "zhongguo_workforce_collective_snapshot_v1"
        and abi.get("status") == "static_and_fixture_ready_not_live"
        and abi.get("capability") == service.get("query_capability")
        and abi.get("case_kind") == action.WORKFORCE_CASE_KIND
        and _mapping(abi.get("collective_routes"), "collective_routes").get(
            "route_b_forced"
        )
        is not None
        and source.get("readiness") == "static_and_fixture_ready_not_live"
        and source.get("capability") == service.get("query_capability")
        and "route_b_has_three_distinct_cohorts_and_forced_conservation"
        in _strings(source.get("required_source_properties"), "required_source_properties")
    )


def _runner_and_fixture_ready(contract: Mapping[str, Any]) -> bool:
    seed_runner = _mapping(contract.get("seed_and_runner"), "seed_and_runner")
    try:
        runner_text = RUNNER_PATH.read_text(encoding="utf-8")
        fixture_inventory = _fixture_inventory()
        event_text = (
            TRANSITION_FIXTURE_PATH / "events" / "zga_phase2_workforce_events.txt"
        ).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return False
    return (
        seed_runner.get("runner") == "tools/run_zhongguo_acceptance.py"
        and seed_runner.get("runner_preflight")
        == "preflight_phase2_workforce_m360_gameplay_action_cell"
        and seed_runner.get("runner_cell")
        == "run_phase2_workforce_m360_gameplay_action_cell"
        and seed_runner.get("requires_distinct_owner_and_subject") is True
        and seed_runner.get("requires_current_source_projection") is True
        and fixture_inventory == tuple(sorted(EXPECTED_FIXTURE_FILES))
        and "def preflight_phase2_workforce_m360_gameplay_action_cell(" in runner_text
        and "def run_phase2_workforce_m360_gameplay_action_cell(" in runner_text
        and "set_player_character = scope:zga_phase2_workforce_owner" in event_text
        and "set_player_character = scope:zga_phase2_workforce_subject" in event_text
        and "var:zg361_p2c_m360_resume_pending = 1" in event_text
        and "zg361_we_resume_m360_from_central_source_effect = {" in event_text
    )


def _seed_evidence(seed_contract_path: Path) -> tuple[bool, dict[str, object]]:
    seed = _load_json(seed_contract_path, "Phase 2 seed contract")
    source = _mapping(seed.get("source"), "seed.source")
    saved = _mapping(seed.get("saved_state"), "seed.saved_state")
    matrix = _mapping(seed.get("domain_query_matrix"), "seed.domain_query_matrix")
    runtime = _mapping(seed.get("runtime"), "seed.runtime")
    save_value = source.get("absolute_save")
    save_path = Path(save_value) if isinstance(save_value, str) else Path()
    owner = matrix.get("workforce_owner_character_id")
    subject = saved.get("played_character_id")
    expected_bytes = source.get("bytes")
    expected_sha256 = source.get("sha256")
    observed_bytes = save_path.stat().st_size if save_path.is_file() else None
    observed_sha256 = _sha256(save_path) if save_path.is_file() else None
    ready = (
        seed.get("kind") == "zg361_phase2_paused_seed"
        and seed.get("status") == "ready"
        and seed.get("ready") is True
        and saved.get("paused_on_load") is True
        and saved.get("map_ready") is True
        and isinstance(owner, int)
        and not isinstance(owner, bool)
        and isinstance(subject, int)
        and not isinstance(subject, bool)
        and owner > 0
        and subject > 0
        and owner != subject
        and observed_bytes == expected_bytes
        and observed_sha256 == expected_sha256
        and runtime.get("game_version") == "1.19.0.6"
        and re.fullmatch(r"[0-9a-fA-F]{64}", str(runtime.get("executable_sha256")))
        is not None
    )
    return ready, {
        "contract": str(seed_contract_path.resolve()),
        "checkpoint": str(save_path),
        "bytes": observed_bytes,
        "sha256": observed_sha256,
        "date_raw": saved.get("date_raw"),
        "subject_character_id": subject,
        "owner_character_id": owner,
        "paused_on_load": saved.get("paused_on_load"),
        "map_ready": saved.get("map_ready"),
        "source_git_commit": _mapping(seed.get("provenance"), "seed.provenance").get(
            "source_git_commit"
        ),
        "entry_ready": ready,
        "is_pre_action_checkpoint": False,
    }


def build_preflight(
    *,
    contract_path: Path = CONTRACT_PATH,
    seed_contract_path: Path = DEFAULT_SEED_CONTRACT_PATH,
) -> dict[str, object]:
    """Build a read-only static report; no gameplay service is instantiated."""

    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_hc_workforce_b4_no_launch_preflight",
        "result": "RED",
        "readiness": READINESS,
        "selected_action": None,
        "checks": {},
        "seed_entry": None,
        "live_gate": {
            "ready": False,
            "required_checkpoint_stage": (
                "after workforce transition fixture activation and before "
                "selecting zg361we.360 route B"
            ),
            "blockers": [
                "current cumulative product projection has not been live-bound",
                "pre-zg361we.360 route-B checkpoint has not been captured",
                "provider-observed route-B postcondition has not been captured",
            ],
        },
        "no_launch_boundary": {
            "service_instantiated": False,
            "ck3_started_by_preflight": False,
            "gameplay_action_executed": False,
            "action_ack_observed": False,
            "business_postcondition_claimed": False,
            "live_proof_claimed": False,
            "process_inventory_checked": False,
        },
        "failure_reason": None,
    }
    try:
        contract = _load_json(contract_path, "B4 action contract")
        selected = _mapping(contract.get("selected_action"), "selected_action")
        boundary = _mapping(contract.get("no_launch_boundary"), "no_launch_boundary")
        contract_ready = (
            contract.get("schema_version") == 1
            and contract.get("kind") == "zg361_phase2_hc_workforce_b4_action_cell"
            and contract.get("span_id") == "phase2_hc_workforce"
            and contract.get("producer_key") == "hc-workforce"
            and contract.get("readiness") == READINESS
            and boundary.get("ck3_started") is False
            and boundary.get("gameplay_action_executed") is False
            and boundary.get("business_postcondition_claimed") is False
            and boundary.get("live_proof_claimed") is False
            and boundary.get("registry_modified") is False
        )
        seed_ready, seed_evidence = _seed_evidence(seed_contract_path)
        checks = {
            "contract_is_live_pending": contract_ready,
            "existing_action_cell_exact_route_b": _action_surface_ready(contract),
            "concrete_service_surface_complete": _service_surface_ready(contract),
            "real_product_visible_route_b_present": _product_route_ready(),
            "provider_observed_postcondition_contract_complete": (
                _provider_contract_ready(contract)
            ),
            "existing_runner_and_transition_fixture_ready": (
                _runner_and_fixture_ready(contract)
            ),
            "hash_bound_current_seed_entry_ready": seed_ready,
            "ack_cannot_satisfy_business_postcondition": (
                _mapping(contract.get("action_cell"), "action_cell").get(
                    "action_ack_is_business_receipt"
                )
                is False
                and len(EXPECTED_POSTCONDITION_FACTS) == 8
            ),
        }
        report["checks"] = checks
        report["seed_entry"] = seed_evidence
        report["selected_action"] = {
            "event_definition_key": selected.get("event_definition_key"),
            "route": selected.get("route"),
            "native_option_index": selected.get("native_option_index"),
            "option_number": selected.get("option_number"),
            "visible_result": selected.get("visible_result"),
            "provider": _mapping(contract.get("postcondition"), "postcondition").get(
                "provider"
            ),
            "required_postcondition_facts": list(EXPECTED_POSTCONDITION_FACTS),
        }
        failed = sorted(name for name, value in checks.items() if value is not True)
        if failed:
            raise B4WorkforcePreflightError(
                "offline B4 checks failed: " + ", ".join(failed)
            )
        report["result"] = "GREEN"
        return report
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        return report


def write_report(path: Path, report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--seed-contract", type=Path, default=DEFAULT_SEED_CONTRACT_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_preflight(
        contract_path=args.contract.resolve(),
        seed_contract_path=args.seed_contract.resolve(),
    )
    if args.output is not None:
        write_report(args.output.resolve(), report)
    print(
        f"{report['result']}: B4 hc-workforce no-launch preflight "
        f"({report['readiness']})"
    )
    if report.get("failure_reason"):
        print(report["failure_reason"])
    return 0 if report.get("result") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
