"""Two native whole-wire FIRST fixtures through the formal Service/MCP facade.

Candidate test source only; no execution accompanies this delivery. The CLI
consumes case-zero.json and case-nonzero.json produced by the owned C++ fixture.
It never constructs a replacement leaf, mocks a production kernel, starts the
SDK/server, uses a pipe, launches CK3, or changes the source projection.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import sys


LEAF_KEY = "current_finalizer_manager_inputs_v1"
PUBLIC_REVISION = 4
_RETREAT_MIRROR_KEYS = (
    "selected_public_cunit_id",
    "selected_native_carmy_id",
    "selected_owner_character_id",
    "combat_province_id",
    "side_index",
    "side_scope",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order",
    "side_flags",
    "legality",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _json_default(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError(f"unsupported receipt type: {type(value).__name__}")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )


class WholeWireFixtureDriver:
    """Supply the native serialized wires to the unmodified formal Service.

    Only the Service command envelope and its existing retreat mirrors are
    fixture plumbing. The manager leaf and active-resume observed mirror are
    independent actual serializer outputs read from the C++ case file.
    """

    def __init__(self, case: dict[str, object], capability: str, step: str) -> None:
        self.case = copy.deepcopy(case)
        self.frame = self.case["battle_control_snapshot"]
        self.resume = self.case["active_combat_resume_inputs_v1"]
        self.capability = capability
        self.step = step
        self.queries = 0
        self.snapshots = 0
        self.backend_id = "pending-sweep-native-whole-wire-fixture"

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": self.backend_id,
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [self.step],
            "bridge_capabilities": [self.capability],
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshots += 1
        return {
            "format_version": 1,
            "snapshot_id": f"{self.backend_id}:4",
            "revision": PUBLIC_REVISION,
            "native_revision": self.frame["snapshot_revision"],
            "date_raw": self.frame["observed_date_raw"],
            "paused": True,
            "source": "named-pipe",
            "backend_id": self.backend_id,
            "episode_run_id": "offline-native-FIRST-pending-sweep",
            "diagnostics": {"fixture_only": True},
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None,
    ) -> dict[str, object]:
        require(step == self.step, "Service changed the subject query")
        require(expected_revision == PUBLIC_REVISION, "Service changed public revision")
        self.queries += 1
        return {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": self.queries,
            "snapshot_revision": self.frame["snapshot_revision"],
            "battle_control_snapshot": copy.deepcopy(self.frame),
            "active_combat_resume_inputs_v1": copy.deepcopy(self.resume),
            **{key: copy.deepcopy(self.frame[key]) for key in _RETREAT_MIRROR_KEYS},
            "backend_id": self.backend_id,
            "queried_snapshot_id": f"{self.backend_id}:4",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": self.frame["snapshot_revision"],
        }

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float):
        raise RuntimeError("readonly compound must not advance game time")


def run_compound(native_dir: Path, output_dir: Path) -> dict[str, object]:
    # These are the production code paths in the patched source projection.
    # The MCP facade imports its optional SDK only inside create_server(),
    # which this fixture does not call.
    from xar_autoplayer.bridge.battle_control_contract import (
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
        normalize_battle_control_snapshot_v1,
        query_battle_control_snapshot_v1_step,
    )
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.mcp_server import _ck3_query_battle_control_snapshot_v1
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
    from xar_autoplayer.simulation.battle_current_normal_finalizer import (
        project_current_normal_finalizer,
    )
    from xar_autoplayer.simulation.current_finalizer_manager_inputs_mapper_v1 import (
        current_finalizer_manager_inputs_from_frame_v1,
    )

    def query(case: dict[str, object]):
        source_frame = case["battle_control_snapshot"]
        subject = source_frame["subject_public_cunit_id"]
        driver = WholeWireFixtureDriver(
            case,
            QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
            query_battle_control_snapshot_v1_step(subject),
        )
        result = _ck3_query_battle_control_snapshot_v1(
            GameplayBridgeService(driver), subject, PUBLIC_REVISION,
        )
        require(driver.queries == 1, "formal facade must issue exactly one query")
        require(driver.snapshots >= 2, "Service did not verify its paused source frame")
        return result

    def reject(case: dict[str, object], label: str) -> dict[str, str]:
        try:
            query(case)
        except BridgeUnavailableError as error:
            return {"check": label, "status": "rejected", "reason": str(error)}
        raise RuntimeError(f"formal Service accepted {label}")

    receipts = []
    loaded_cases = []
    for filename, expected_raw, expected_branch in (
        ("case-zero.json", 0, "normal"),
        ("case-nonzero.json", 7, "suppressed"),
    ):
        case = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
        require(isinstance(case, dict), f"{filename} is not a case object")
        original = copy.deepcopy(case)
        expected = case["expected_current_finalizer_manager_inputs_v1"]
        frame = case["battle_control_snapshot"]
        resume = case["active_combat_resume_inputs_v1"]
        require(frame[LEAF_KEY] == expected, "native leaf disagrees with fixture expectation")
        require(resume["observed"][LEAF_KEY] == expected, "native serializer mirror disagrees")
        require(case["expected_dispatch_branch"] == expected_branch, "fixture branch expectation differs")
        require(type(expected["pending_suppression_sweep_raw"]) is int, "raw byte became boolean")
        require(expected["pending_suppression_sweep_raw"] == expected_raw, "wrong native FIRST raw byte")
        require(expected["pending_suppression_sweep"] is (expected_raw != 0), "wrong native FIRST bool")
        require(expected["combat_manager_row_admitted"] is True, "genuine selected manager row not admitted")
        require(expected["source_combat_id"] == frame["combat_id"], "FIRST source CombatID differs")
        require(frame["phase_raw"] == 3 and frame["phase_day"] == 0, "FIRST is not a phase3 daily-row case")

        service_result = query(case)
        normalized = service_result["battle_control_snapshot"]
        require(normalized[LEAF_KEY] == expected, "strict Service normalization changed leaf")
        require(
            service_result["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY] == expected,
            "formal Service dropped actual serializer mirror",
        )
        require(service_result["active_combat_resume_inputs_v1"]["input_observation_ready"] is False,
                "current pending observation falsely completed future active resume inputs")
        # One explicit direct normalizer boundary also proves that no fixture
        # driver code is standing in for the production wire parser.
        direct = normalize_battle_control_snapshot_v1(
            frame,
            expected_subject_public_cunit_id=frame["subject_public_cunit_id"],
            expected_observed_date_raw=frame["observed_date_raw"],
            expected_snapshot_revision=frame["snapshot_revision"],
        )
        require(direct == normalized, "direct/formal normalized frames disagree")

        unconditional = current_finalizer_manager_inputs_from_frame_v1(normalized)
        require(unconditional.primary_hostile is None and unconditional.finalized is None,
                "mapper invented later sweep operands")
        require(unconditional.processing is None and unconditional.result_present is None,
                "mapper inferred optional finalizer conditions")
        require(unconditional.source_context["future_manager_state_observed"] is False,
                "mapper claimed actual future state")
        require(unconditional.source_context["native_primary_hostility_observed"] is False,
                "mapper claimed native hostility")
        condition = adapt_current_battle_condition(normalized)
        if expected_raw:
            incomplete = project_current_normal_finalizer(condition, manager=unconditional)
            require(incomplete["dispatch"]["branch"] == "unknown_reached_operand",
                    "raw7 must need explicit caller primary hostility")
            require(incomplete["normal_numeric_accounting"] is None,
                    "incomplete sweep emitted normal numerics")
            manager = current_finalizer_manager_inputs_from_frame_v1(
                normalized, entry_kind="daily_row", primary_hostile=False, finalized=False,
            )
        else:
            manager = unconditional

        # Fixture-only maximum10 and baseline10 Q are caller conditions. The
        # current9 whole census comes from the serialized all-Army input. No
        # component is selected for recomputation and no current loss is reapplied.
        backing = normalized["full_backing_inputs_v1"]
        require(backing["enumeration_complete"] is True, "native whole census incomplete")
        maxima = {}
        for side in backing["sides"]:
            require(len(side["ordered_armies"]) == 1, "FIRST requires one Army per side")
            for army in side["ordered_armies"]:
                require(len(army["ordered_regiments"]) == 1, "FIRST requires one backing Regiment")
                for row in army["ordered_regiments"]:
                    require(row["current_soldiers"] == 9, "native current9 census differs")
                    maxima[(army["native_carmy_id"], row["regiment_id"])] = 10
        projection = project_current_normal_finalizer(
            condition,
            manager=manager,
            backing_inputs_v1=backing,
            recomputed_regiments=set(),
            captured_maximum_by_regiment=maxima,
            side_baseline_raw_by_side={0: 1_000_000, 1: 1_000_000},
            winner_raw=0,
            wipe_raw=False,
        )
        require(projection["dispatch"]["branch"] == expected_branch, "existing kernel branch differs")
        require(projection["dispatch"]["status"] == "available", "manager dispatch remains partial")
        require(not any(gap.stage == "manager_dispatch" for gap in projection["typed_gaps"]),
                "observed pending leaf failed to close reached manager operands")
        if expected_raw == 0:
            require(projection["dispatch"]["normal_result_intent"] is True, "raw0 did not unlock normal")
            require(projection["dispatch"]["suppression_argument"] is False, "raw0 enabled suppression")
            require(projection["normal_numeric_accounting"] is not None, "normal numerics absent")
            for row in projection["normal_numeric_accounting"]["sides"]:
                require(row["backing_current_whole_signed32"] == 9, "whole current count changed")
                require(row["final_survivors_raw_q100000"] == 900_000, "whole-to-Q count changed")
        else:
            require(projection["dispatch"]["normal_result_intent"] is False, "sweep fell through to normal")
            require(projection["dispatch"]["suppression_argument"] is True, "raw7 lost sweep precedence")
            require(projection["normal_numeric_accounting"] is None, "suppressed case emitted normal numerics")
            require(projection["backing_reaggregation"] is None, "suppression executed normal count")
        require(projection["complete_native_finalizer"] is False, "subset claimed complete finalizer")
        require(projection["actual_native_effects_executed"] is False, "projection claimed native execution")
        require(projection["actual_game_days_advanced"] == 0, "projection advanced game time")
        require(projection["prior_losses_reapplied"] is False, "projection reapplied losses")
        require(projection["owner_hard_ledger_debited"] is False, "projection debited owner ledger")
        require(case == original, "compound mutated input wires")

        stem = Path(filename).stem
        _write_json(output_dir / f"{stem}-service-result.json", service_result)
        _write_json(output_dir / f"{stem}-conditional-projection.json", projection)
        receipts.append({
            "native_case": filename,
            "status": "passed",
            "dispatch_branch": expected_branch,
            "pending_raw": expected_raw,
            "caller_context": manager.source_context["caller_conditional_context"],
            "actual_future_state_observed": False,
            "native_primary_hostility_observed": False,
            "normal_numeric_produced": projection["normal_numeric_accounting"] is not None,
        })
        loaded_cases.append(case)

    # Compatibility and rejection checks reuse the zero FIRST whole wire; they
    # are Python wire variants, not new native scenes or independent live evidence.
    zero = loaded_cases[0]
    compatibility = []
    for state in ("absent", "null"):
        variant = copy.deepcopy(zero)
        if state == "absent":
            del variant["battle_control_snapshot"][LEAF_KEY]
            del variant["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY]
        else:
            variant["battle_control_snapshot"][LEAF_KEY] = None
            variant["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY] = None
        result = query(variant)
        frame = result["battle_control_snapshot"]
        require((LEAF_KEY in frame) == (state == "null"), "legacy leaf shape changed")
        mapped = current_finalizer_manager_inputs_from_frame_v1(frame)
        require(mapped.combat_manager_row_admitted is None and mapped.pending_suppression_sweep is None,
                "legacy unavailable data became observed false")
        projection = project_current_normal_finalizer(adapt_current_battle_condition(frame), manager=mapped)
        require(projection["dispatch"]["branch"] == "unknown_reached_operand",
                "legacy absence/null unlocked a manager branch")
        compatibility.append({"leaf": state, "status": "passed", "dispatch": "unknown_reached_operand"})

    rejected = []
    for label, key, invalid in (
        ("bool-as-source-id", "source_combat_id", True),
        ("wrong-source-combat", "source_combat_id", zero["battle_control_snapshot"]["combat_id"] + 1),
        ("numeric-row-admission", "combat_manager_row_admitted", 1),
        ("bool-as-raw-byte", "pending_suppression_sweep_raw", False),
        ("negative-raw-byte", "pending_suppression_sweep_raw", -1),
        ("oversized-raw-byte", "pending_suppression_sweep_raw", 256),
        ("raw-boolean-disagreement", "pending_suppression_sweep", True),
    ):
        variant = copy.deepcopy(zero)
        variant["battle_control_snapshot"][LEAF_KEY][key] = invalid
        rejected.append(reject(variant, label))
    mirror_drift = copy.deepcopy(zero)
    mirror_drift["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY] = copy.deepcopy(
        loaded_cases[1]["expected_current_finalizer_manager_inputs_v1"]
    )
    rejected.append(reject(mirror_drift, "actual-resume-mirror-disagreement"))

    return {
        "schema_version": 1,
        "status": "passed",
        "evidence_layer": "offline_native_whole_wire_formal_service_compound",
        "native_FIRST_scene_count": 2,
        "production_path": [
            "native whole SerializeBattleControlSnapshot + SerializeActiveCombatResumeInputsV1",
            "existing MCP _ck3_query_battle_control_snapshot_v1 helper",
            "existing GameplayBridgeService.query_battle_control_snapshot_v1",
            "strict battle-control leaf parser + active-resume mirror validation",
            "owned pure DTO mapper",
            "existing project_current_normal_finalizer",
        ],
        "native_cases": receipts,
        "legacy_wire_compatibility": compatibility,
        "rejected_zero_wire_variants": rejected,
        "sdk_server_started": False,
        "pipe_or_ck3_process_used": False,
        "live_evidence": False,
        "complete_native_finalizer": False,
        "actual_native_effects_executed": False,
        "actual_game_days_advanced": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player" / "src"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run_compound(args.native_dir, args.output_dir)
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "failed",
            "evidence_layer": "offline_native_whole_wire_formal_service_compound",
            "error_type": type(error).__name__,
            "error": str(error),
            "live_evidence": False,
            "actual_native_effects_executed": False,
        }
        _write_json(args.output_dir / "compound-result.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return 1
    _write_json(args.output_dir / "compound-result.json", result)
    print(json.dumps({"status": result["status"], "native_FIRST_scene_count": 2}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
