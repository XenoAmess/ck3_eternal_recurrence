#!/usr/bin/env python3
"""Read-only/no-launch preflight for the exact endgame rebind seam."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import re
from typing import Mapping

import zg361_phase2_cross_cycle_endgame_live_seam as seam
from zg361_phase2_cross_cycle_endgame_action_cell import (
    run_cross_cycle_endgame_action_cell,
)
from zhongguo_phase2_workforce_action import (
    select_typed_fixture_player_transition,
    submit_m360_route_action,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tools" / "zg361_phase2_cross_cycle_endgame_action_contract.json"
FIXTURE_PATH = ROOT / "tools" / "fixtures" / seam.TRANSITION_FIXTURE_ID
PROVIDER_ABI_PATH = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "zhongguo_workforce_collective_snapshot_v1_abi.json"
)
SERVICE_PATH = (
    ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "bridge" / "service.py"
)
M356_PATH = (
    ROOT / "mod_zhongguo_style" / "events"
    / "zg361_workforce_endgame_event_010_m356_outcome_timing_events.txt"
)
M360_PATH = (
    ROOT / "mod_zhongguo_style" / "events"
    / "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt"
)
M361_PATH = (
    ROOT / "mod_zhongguo_style" / "events"
    / "zg361_workforce_endgame_event_011b_al_m361_charter_events.txt"
)
EXPECTED_FIXTURE_FILES = (
    "common/scripted_guis/zga_phase2_endgame_rebind_guis.txt",
    "descriptor.mod",
    "events/zga_phase2_endgame_rebind_events.txt",
    "gui/scripted_widgets/zga_phase2_endgame_rebind_scripted_widgets.txt",
    "gui/zga_phase2_endgame_rebind_bridge.gui",
    "localization/english/zga_phase2_endgame_rebind_l_english.yml",
    "localization/simp_chinese/zga_phase2_endgame_rebind_l_simp_chinese.yml",
)


class CrossCycleEndgameRebindPreflightError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise CrossCycleEndgameRebindPreflightError(f"{path} is not an object")
    return value


def _fixture_check() -> bool:
    files = tuple(
        sorted(
            path.relative_to(FIXTURE_PATH).as_posix()
            for path in FIXTURE_PATH.rglob("*")
            if path.is_file()
        )
    )
    if files != EXPECTED_FIXTURE_FILES:
        return False
    if any(
        not (FIXTURE_PATH / relative).read_bytes().startswith(b"\xef\xbb\xbf")
        for relative in files
    ):
        return False
    event = (FIXTURE_PATH / EXPECTED_FIXTURE_FILES[2]).read_text(
        encoding="utf-8-sig"
    )
    gui = (FIXTURE_PATH / EXPECTED_FIXTURE_FILES[0]).read_text(
        encoding="utf-8-sig"
    )
    all_text = "\n".join(
        (FIXTURE_PATH / relative).read_text(encoding="utf-8-sig")
        for relative in files
    )
    return (
        len(re.findall(r"^zga_phase2_endgame_rebind\.\d+\s*=\s*\{", event, re.M))
        == 1
        and event.count("\n\toption = {") == 1
        and event.count("set_player_character =") == 1
        and "set_player_character = scope:zga_phase2_endgame_subject" in event
        and "this = scope:zga_phase2_endgame_owner" in event
        and "var:zg361_p2c_m360_source_subject = scope:zga_phase2_endgame_subject"
        in event
        and "var:zg361_p2c_m360_source_subject = {" in gui
        and "var:zg361_we_m360_receipt_choice = 3" in gui
        and "var:zg361_we_m361_evidence_ready = 1" in gui
        and "set_variable" not in all_text
        and "common/decisions" not in files
    )


def _product_path_check() -> bool:
    source = M356_PATH.read_text(encoding="utf-8-sig")
    m360 = M360_PATH.read_text(encoding="utf-8-sig")
    m361 = M361_PATH.read_text(encoding="utf-8-sig")
    return (
        "zg361we.356 = {" in source
        and source.count("\n\toption = {") >= 3
        and "name = zg361we.356.a" in source
        and "zg361we.360 = {" in m360
        and m360.count("\n\toption = {") == 3
        and "var:zg361_we_al_external_stage_receipts_verified = 1" in m360
        and "name = zg361we.360.c" in m360
        and "zg361_we_m360_route_c_effect = {" in m360
        and "zg361we.361 = {" in m361
        and m361.count("\n\toption = {") == 3
        and "name = zg361we.361.a" in m361
    )


def _contract_check(contract: Mapping[str, object]) -> bool:
    seam_contract = contract.get("exact_build_typed_rebind_seam")
    return (
        contract.get("readiness") == "static-ready-live-pending"
        and isinstance(seam_contract, Mapping)
        and seam_contract.get("module")
        == "zg361_phase2_cross_cycle_endgame_live_seam"
        and seam_contract.get("run")
        == "run_exact_build_cross_cycle_endgame_seam"
        and seam_contract.get("transition_fixture_id") == seam.TRANSITION_FIXTURE_ID
        and seam_contract.get("transition_event") == seam.TRANSITION_EVENT
        and seam_contract.get("arbitrary_rebind_exposed") is False
        and seam_contract.get("arbitrary_variable_query_exposed") is False
        and seam_contract.get("business_state_fixture_used") is False
        and seam_contract.get("ack_or_visibility_can_green") is False
    )


def build_preflight() -> dict[str, object]:
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_cross_cycle_endgame_rebind_no_launch_preflight",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "checks": {},
        "live_gate": {
            "ready": False,
            "required_checkpoint": "real owner-visible zg361we.361 paused save",
            "blockers": [
                "real zg361we.356 source checkpoint is not registered",
                "typed result-session fixture restore is not wired into the formal runner",
                "same-lineage subject Workforce provider artifact has not been captured",
            ],
        },
        "no_launch_boundary": {
            "service_instantiated": False,
            "ck3_started": False,
            "gameplay_action_executed": False,
            "registry_modified": False,
            "live_proof_claimed": False,
        },
        "failure_reason": None,
    }
    try:
        contract = _json(CONTRACT_PATH)
        abi = _json(PROVIDER_ABI_PATH)
        service_source = SERVICE_PATH.read_text(encoding="utf-8")
        checks = {
            "exact_build_frozen": (
                seam.EXACT_GAME_VERSION == "1.19.0.6"
                and seam.EXACT_EXE_SHA256
                == "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
            "real_product_356_360c_361_path_present": _product_path_check(),
            "typed_fixed_target_fixture_exact": _fixture_check(),
            "existing_received_self_workforce_provider_reused": (
                abi.get("contract") == "zhongguo_workforce_collective_snapshot_v1"
                and isinstance(abi.get("subject_acl"), Mapping)
                and abi["subject_acl"].get("scope") == "paused_played_character_only"
                and "def query_zhongguo_workforce_collective_snapshot_v1(" in service_source
            ),
            "seam_contract_live_pending": _contract_check(contract),
            "seam_callbacks_and_typed_helpers_callable": all(
                callable(value)
                for value in (
                    seam.run_exact_build_cross_cycle_endgame_seam,
                    run_cross_cycle_endgame_action_cell,
                    submit_m360_route_action,
                    select_typed_fixture_player_transition,
                )
            ),
            "activation_api_is_result_bound_only": (
                "activate_result_session"
                in inspect.signature(
                    seam.run_exact_build_cross_cycle_endgame_seam
                ).parameters
                and "target_character_id"
                not in inspect.signature(
                    seam.run_exact_build_cross_cycle_endgame_seam
                ).parameters
                and "variable_name"
                not in inspect.signature(
                    seam.run_exact_build_cross_cycle_endgame_seam
                ).parameters
            ),
            "no_public_generic_rebind_or_variable_reader_added": (
                "def set_player_character_v1(" not in service_source
                and "def query_character_variable_v1(" not in service_source
                and "def query_script_variable_v1(" not in service_source
            ),
            "ack_and_visibility_cannot_green": (
                "query_zhongguo_workforce_collective_snapshot_v1"
                in inspect.getsource(run_cross_cycle_endgame_action_cell)
            ),
        }
        report["checks"] = checks
        failed = sorted(name for name, passed in checks.items() if passed is not True)
        if failed:
            raise CrossCycleEndgameRebindPreflightError(
                "offline checks failed: " + ", ".join(failed)
            )
        report["result"] = "GREEN"
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_preflight()
    if args.output is not None:
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        f"{report['result']}: cross-cycle endgame typed rebind no-launch "
        f"({report['readiness']})"
    )
    if report.get("failure_reason"):
        print(report["failure_reason"])
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
