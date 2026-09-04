#!/usr/bin/env python3
"""No-launch preflight for the HC-workforce route-B checkpoint plumbing."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402

import zg361_phase2_hc_workforce_route_b_checkpoint as route_b  # noqa: E402


CONTRACT_PATH = (
    ROOT / "tools" / "zg361_phase2_hc_workforce_route_b_checkpoint_contract.json"
)
MODULE_PATH = ROOT / "tools" / "zg361_phase2_hc_workforce_route_b_checkpoint.py"
RUNNER_PATH = ROOT / "tools" / "run_zhongguo_acceptance.py"
B6_SOURCE_CONTRACT = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "zhongguo_career_hc_workforce_postcondition_v1_source_contract.json"
)
PRODUCT_EVENT = (
    ROOT
    / "mod_zhongguo_style"
    / "events"
    / "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt"
)
DOC_PATH = (
    ROOT
    / "docs"
    / "phase2-promo"
    / "zg361-hc-workforce-b4-route-b-checkpoint.md"
)


class RouteBCheckpointPreflightError(RuntimeError):
    pass


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RouteBCheckpointPreflightError(
            f"cannot read {label} {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise RouteBCheckpointPreflightError(f"{label} must be an object")
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise RouteBCheckpointPreflightError(f"{label} must be an object")
    return value


def _contract_ready(contract: Mapping[str, Any]) -> bool:
    route = _mapping(contract.get("route"), "route")
    checkpoint = _mapping(
        contract.get("checkpoint_contract"), "checkpoint_contract"
    )
    identity = _mapping(
        contract.get("case_identity_contract"), "case_identity_contract"
    )
    postcondition = _mapping(
        contract.get("postcondition_contract"), "postcondition_contract"
    )
    boundary = _mapping(contract.get("no_launch_boundary"), "no_launch_boundary")
    return (
        contract.get("schema_version") == 1
        and contract.get("kind")
        == "zg361_phase2_hc_workforce_route_b_checkpoint"
        and contract.get("span_id") == route_b.SPAN_ID
        and contract.get("producer_key") == route_b.PRODUCER_KEY
        and contract.get("readiness") == route_b.READINESS
        and route
        == {
            "event_definition_key": "zg361we.360",
            "route": "B",
            "native_option_index": 1,
            "option_number": 2,
        }
        and checkpoint.get("requires_current_cumulative_product_tree_hash") is True
        and checkpoint.get("requires_transition_fixture_tree_hash") is True
        and checkpoint.get("requires_native_checkpoint_path_size_sha256_date_owner")
        is True
        and checkpoint.get("archives_verified_bytes_before_action") is True
        and checkpoint.get("restore_requires_same_size_sha256_date_owner_event")
        is True
        and identity.get("owner_subject_observed_before_save") is True
        and identity.get("cycle_case_available_before_action") is False
        and identity.get("cycle_case_source")
        == "post-action query_zhongguo_workforce_collective_snapshot_v1"
        and identity.get("restored_replay_must_match_owner_subject_cycle_case")
        is True
        and postcondition.get("required_fact_count")
        == len(route_b.WORKFORCE_REQUIRED_FACTS)
        == 13
        and postcondition.get("action_ack_is_business_postcondition") is False
        and postcondition.get("career_hc_capability")
        == route_b.CAREER_CAPABILITY
        and postcondition.get("same_paused_revision_join_required") is True
        and all(value is False for value in boundary.values())
    )


def _entrypoints_ready(contract: Mapping[str, Any]) -> bool:
    entrypoints = _mapping(contract.get("entrypoints"), "entrypoints")
    expected = {
        "projection_binding": "bind_current_cumulative_projection",
        "freeze": "freeze_route_b_pre_action_checkpoint",
        "postcondition": "run_route_b_and_collect_postconditions",
        "restore": "restore_route_b_pre_action_checkpoint",
        "career_hook": "query_career_hc_if_available",
    }
    return entrypoints == expected and all(
        callable(getattr(route_b, name, None)) for name in expected.values()
    )


def _service_surface_ready(contract: Mapping[str, Any]) -> bool:
    methods = contract.get("service_methods")
    if not isinstance(methods, list) or methods != [
        "capabilities",
        "snapshot",
        "query_current_event_window_context_v1",
        "select_event_option",
        "query_zhongguo_workforce_collective_snapshot_v1",
        "execute_step",
        "save_checkpoint",
        "restore_checkpoint",
    ]:
        return False
    return all(
        callable(getattr(route_b.RouteBCheckpointService, name, None))
        and callable(getattr(GameplayBridgeService, name, None))
        and inspect.signature(getattr(route_b.RouteBCheckpointService, name))
        == inspect.signature(getattr(GameplayBridgeService, name))
        for name in methods
    )


def _runner_seam_ready() -> bool:
    try:
        source = RUNNER_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    start = source.find("def run_phase2_workforce_m360_gameplay_action_cell(")
    end = source.find("\ndef ", start + 1)
    body = source[start:end] if start >= 0 and end > start else ""
    required = (
        "install_phase2_workforce_action_fixture(",
        "select_typed_fixture_player_transition(",
        "expected_definition_key=M360_EVENT_DEFINITION_KEY",
        "run_m360_action_and_postcondition(",
    )
    positions = [body.find(token) for token in required]
    return bool(body) and all(position >= 0 for position in positions) and (
        positions == sorted(positions)
    )


def _career_hook_ready() -> bool:
    try:
        source = _load(B6_SOURCE_CONTRACT, "career-HC source contract")
    except RouteBCheckpointPreflightError:
        return False
    return (
        source.get("capability") == route_b.CAREER_CAPABILITY
        and source.get("readiness") == "static_and_fixture_ready_live_pending"
        and _mapping(source.get("integration"), "career integration").get(
            "native_provider_wiring"
        )
        == "complete_default_off_until_live"
        and _mapping(source.get("native_provider"), "career native provider").get(
            "shared_wiring"
        )
        == "default_off_complete_not_advertised"
        and callable(route_b.query_career_hc_if_available)
    )


def _real_product_route_ready() -> bool:
    try:
        text = PRODUCT_EVENT.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return False
    start = text.find("zg361we.360 = {")
    block = text[start:] if start >= 0 else ""
    return all(
        token in block
        for token in (
            "type = character_event",
            "is_ai = no",
            "name = zg361we.360.b",
            "zg361_we_materialize_m360_route_b_from_central_effect = {",
            "zg361_we_m360_route_b_effect = {",
        )
    )


def _no_launch_source_ready() -> bool:
    try:
        source = MODULE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    forbidden = (
        "import subprocess",
        "from subprocess",
        "Start-Process",
        "ck3.exe",
        "GameplayBridgeService(",
    )
    return not any(token in source for token in forbidden)


def build_preflight(
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, object]:
    """Inspect only repository files and Python call signatures."""

    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_checkpoint_no_launch_preflight",
        "result": "RED",
        "readiness": route_b.READINESS,
        "checks": {},
        "no_launch_boundary": {
            "service_instantiated": False,
            "ck3_started": False,
            "checkpoint_captured": False,
            "checkpoint_restored": False,
            "route_b_selected": False,
            "postcondition_observed": False,
            "live_claimed": False,
        },
        "live_gate": {
            "ready": False,
            "next_checkpoint": (
                "current cumulative projection + transition fixture, paused on "
                "real zg361we.360 as exact owner before option B"
            ),
            "required_after_action": (
                "Workforce 13 facts seal owner/subject/cycle/case; career-HC is "
                "joined only if its fixed capability is advertised"
            ),
            "required_restore_proof": (
                "same checkpoint bytes/date/event, followed by provider replay "
                "matching the sealed case identity"
            ),
        },
        "failure_reason": None,
    }
    try:
        contract = _load(Path(contract_path), "route-B checkpoint contract")
        checks = {
            "contract_is_strict_and_live_pending": _contract_ready(contract),
            "checkpoint_entrypoints_exist": _entrypoints_ready(contract),
            "concrete_service_surface_matches_protocol": _service_surface_ready(
                contract
            ),
            "existing_transition_fixture_runner_seam_is_ordered": (
                _runner_seam_ready()
            ),
            "real_product_route_b_is_present": _real_product_route_ready(),
            "career_hc_hook_respects_default_off_provider": _career_hook_ready(),
            "documentation_records_scalar_scope_boundary": DOC_PATH.is_file()
            and "cycle/case" in DOC_PATH.read_text(encoding="utf-8"),
            "module_has_no_launcher_or_process_surface": _no_launch_source_ready(),
        }
        report["checks"] = checks
        failed = [name for name, ready in checks.items() if ready is not True]
        if failed:
            raise RouteBCheckpointPreflightError(
                "offline checks failed: " + ", ".join(failed)
            )
        report["result"] = "GREEN"
        return report
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        return report


def write_report(path: Path, report: Mapping[str, object]) -> None:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = build_preflight(args.contract.resolve())
    if args.output is not None:
        write_report(args.output, report)
    print(
        f"{report['result']}: hc-workforce route-B checkpoint preflight "
        f"({report['readiness']})"
    )
    if report.get("failure_reason"):
        print(report["failure_reason"])
    return 0 if report.get("result") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
