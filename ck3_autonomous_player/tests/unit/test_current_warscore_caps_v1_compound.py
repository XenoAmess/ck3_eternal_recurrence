"""Seven new native cases through the real MCP helper and GameplayBridgeService.

Six cases supply complete production control/resume JSON. The identity case
preserves an actual state_changed reader result and two empty serializers.
This sole compound consumes those outputs; it does not reconstruct cap leaves
or mirrors, start a server/SDK/pipe/game, or mock a production projection.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys


LEAF_KEY = "current_warscore_caps_v1"
PUBLIC_REVISION = 4
CASE_FILES = (
    "case-distinct.json",
    "case-zero.json",
    "case-negative.json",
    "case-large64.json",
    "case-identity-mismatch.json",
    "case-wrong-sha.json",
    "case-missing-source.json",
)
EXPECTED_PAIRS = {
    "case-distinct.json": (2_300_000, 1_700_000),
    "case-zero.json": (0, 1_900_000),
    "case-negative.json": (-12_345, -67_890),
    "case-large64.json": ((1 << 50) + 123, -((1 << 49) + 77)),
}
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


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class WholeWireFixtureDriver:
    """Copy real native outputs and supply the formal Service command envelope."""

    def __init__(self, case: dict[str, object], capability: str, step: str) -> None:
        self.case = copy.deepcopy(case)
        self.frame = self.case["battle_control_snapshot"]
        self.resume = self.case["active_combat_resume_inputs_v1"]
        self.context = self.case["fixture_snapshot_context"]
        self.capability = capability
        self.step = step
        self.queries = 0
        self.snapshots = 0
        self.backend_id = "warscore-cap-native-FIRST-fixture"

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
            "native_revision": self.context["native_revision"],
            "date_raw": self.context["date_raw"],
            "paused": True,
            "source": "named-pipe",
            "backend_id": self.backend_id,
            "episode_run_id": "offline-native-FIRST-warscore-caps",
            "diagnostics": {"fixture_only": True},
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None,
    ) -> dict[str, object]:
        require(step == self.step, "Service changed the selected subject query")
        require(expected_revision == PUBLIC_REVISION, "Service changed public revision")
        self.queries += 1
        # The empty-serializer case has no replacement control frame. Its native
        # state_changed status reaches the formal Service's unavailable branch.
        mirrors = {
            key: None if self.frame is None else copy.deepcopy(self.frame[key])
            for key in _RETREAT_MIRROR_KEYS
        }
        return {
            "step": step,
            "accepted": True,
            "status": self.case["native_control_status"],
            "query_sequence": self.queries,
            "snapshot_revision": self.context["native_revision"],
            "battle_control_snapshot": copy.deepcopy(self.frame),
            "active_combat_resume_inputs_v1": copy.deepcopy(self.resume),
            **mirrors,
            "backend_id": self.backend_id,
            "queried_snapshot_id": f"{self.backend_id}:4",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": self.context["native_revision"],
        }

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float):
        raise RuntimeError("readonly cap compound must not advance game time")


def run_compound(native_dir: Path, output_dir: Path) -> dict[str, object]:
    from xar_autoplayer.bridge.battle_control_contract import (
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
        normalize_battle_control_snapshot_v1,
        query_battle_control_snapshot_v1_step,
    )
    from xar_autoplayer.bridge.current_warscore_caps_contract_v1 import (
        select_current_warscore_cap_v1,
    )
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.mcp_server import _ck3_query_battle_control_snapshot_v1
    from xar_autoplayer.bridge.service import GameplayBridgeService

    def query(case: dict[str, object]):
        subject = case["fixture_snapshot_context"]["subject_public_cunit_id"]
        driver = WholeWireFixtureDriver(
            case,
            QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
            query_battle_control_snapshot_v1_step(subject),
        )
        service = GameplayBridgeService(driver)
        try:
            result = _ck3_query_battle_control_snapshot_v1(
                service, subject, PUBLIC_REVISION,
            )
        except BridgeUnavailableError:
            require(driver.queries == 1, "Service rejected before consuming native command result")
            raise
        require(driver.queries == 1, "formal facade must issue exactly one query")
        require(driver.snapshots >= 2, "formal Service did not verify paused frame")
        return result

    def reject(case: dict[str, object], label: str) -> dict[str, str]:
        try:
            query(case)
        except BridgeUnavailableError as error:
            return {"check": label, "status": "rejected", "reason": str(error)}
        raise RuntimeError(f"formal Service accepted {label}")

    receipts = []
    loaded_cases = {}
    normalized_cases = {}
    whole_count = 0
    for filename in CASE_FILES:
        case = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
        require(isinstance(case, dict), f"{filename} is not a native case object")
        original = copy.deepcopy(case)
        loaded_cases[filename] = case
        native_status = case["native_control_status"]
        require(native_status == case["expected_control_status"], "native reader status differs")
        require(case["membership_source"] == "explicit_same_invocation_fixture_condition",
                "packet membership lost its explicit conditional source")
        frame = case["battle_control_snapshot"]
        resume = case["active_combat_resume_inputs_v1"]
        expected = case["expected_current_warscore_caps_v1"]
        stem = Path(filename).stem

        if filename == "case-identity-mismatch.json":
            require(native_status == "state_changed", "strict identity mismatch lost reader status")
            require(frame is None and resume is None, "empty serializers became replacement frames")
            require(case["expected_serializer_output_empty"] is True, "missing empty serializer witness")
            require(expected is None, "identity mismatch emitted cap leaf")
            require(case["expected_cap_selection_status"] == "not_reached", "identity case claimed selection")
            rejection = reject(case, "native-identity-state-changed-empty-serializers")
            _write_json(output_dir / f"{stem}-service-rejection.json", rejection)
            receipts.append({
                "native_case": filename,
                "status": "passed",
                "native_control_status": native_status,
                "native_whole_wire_available": False,
                "empty_serializer_count": 2,
                "cap_selection_status": "not_reached",
                "service_rejection": rejection,
            })
            require(case == original, "identity compound mutated native packet")
            continue

        require(native_status == "available", "whole native frame is unavailable")
        require(isinstance(frame, dict) and isinstance(resume, dict), "whole native outputs absent")
        context = case["fixture_snapshot_context"]
        require(frame["snapshot_revision"] == context["native_revision"], "native revision context differs")
        require(frame["observed_date_raw"] == context["date_raw"], "native date context differs")
        require(frame["subject_public_cunit_id"] == context["subject_public_cunit_id"], "subject context differs")
        require(frame[LEAF_KEY] == expected, "native cap leaf differs from fixture expectation")
        require(resume["observed"][LEAF_KEY] == expected, "actual native observed mirror differs")
        require(type(frame["winner_raw"]) is int and frame["winner_raw"] in (0, 1),
                "FIRST available scene lacks its actual native winner")
        require(frame["winner_raw"] == case["expected_native_winner_raw"],
                "whole wire changed the fixture's actual native winner")
        if filename in EXPECTED_PAIRS:
            pair = EXPECTED_PAIRS[filename]
            require(expected is not None, "loaded cap pair unexpectedly null")
            require(expected["war_attacker_winner_cap_raw_q100000"] == pair[0], "attacker cap differs")
            require(expected["war_defender_winner_cap_raw_q100000"] == pair[1], "defender cap differs")
            require(expected["source_combat_id"] == frame["combat_id"], "cap source CombatID differs")
        else:
            require(expected is None, "wrong SHA/missing source became a cap value")

        result = query(case)
        normalized = result["battle_control_snapshot"]
        normalized_cases[filename] = normalized
        require(normalized[LEAF_KEY] == expected, "strict Service changed loaded caps")
        require(result["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY] == expected,
                "formal Service changed actual native mirror")
        require(result["active_combat_resume_inputs_v1"]["input_observation_ready"] is False,
                "current cap pair completed future active-resume input readiness")
        direct = normalize_battle_control_snapshot_v1(
            frame,
            expected_subject_public_cunit_id=context["subject_public_cunit_id"],
            expected_observed_date_raw=context["date_raw"],
            expected_snapshot_revision=context["native_revision"],
        )
        require(direct == normalized, "direct and formal normalized native frames differ")

        # This current battle-control wire has no actual winner War membership.
        # The named packet bool is an explicit same-invocation fixture condition,
        # never derived from current CombatSide or subject/player identity.
        membership = case["conditional_winner_is_war_attacker"]
        require(type(membership) is bool, "FIRST membership condition is not an explicit bool")
        selection = select_current_warscore_cap_v1(
            normalized, winner_is_war_attacker=membership,
        )
        require(selection["observed_frame"]["winner_raw"] == frame["winner_raw"],
                "selector changed the actual native winner")
        require(selection["status"] == case["expected_cap_selection_status"], "cap selection status differs")
        require(selection["selected_cap_raw_q100000"] == case["expected_selected_cap_raw_q100000"],
                "selected loaded cap differs")
        require(selection["native_winner_war_membership_observed"] is False,
                "conditional War membership became native observation")
        require(selection["winner_membership_context"] == "explicit_same_invocation_condition",
                "membership condition lost its scope")
        require(selection["row_admission_predicted"] is False and
                selection["future_battle_score_predicted"] is False and
                selection["whole_war_outcome_predicted"] is False,
                "cap operand became a row or outcome forecast")
        unknown_membership = select_current_warscore_cap_v1(
            normalized, winner_is_war_attacker=None,
        )
        require(case["expected_unknown_membership_status"] == "partial",
                "fixture claimed unknown membership was ready")
        require(unknown_membership["status"] == "partial" and
                unknown_membership["selected_cap_raw_q100000"] is None,
                "selector inferred War membership from native CombatSide")
        require(unknown_membership["observed_caps"] == expected,
                "unknown membership discarded independent loaded pair")
        require(case == original, "compound mutated input native wires")

        _write_json(output_dir / f"{stem}-service-result.json", result)
        _write_json(output_dir / f"{stem}-conditional-selection.json", selection)
        receipts.append({
            "native_case": filename,
            "status": "passed",
            "native_control_status": native_status,
            "native_whole_wire_available": True,
            "observed_native_winner_raw": frame["winner_raw"],
            "conditional_winner_is_war_attacker": membership,
            "native_winner_war_membership_observed": False,
            "cap_selection_status": selection["status"],
            "selected_cap_raw_q100000": selection["selected_cap_raw_q100000"],
        })
        whole_count += 1

    # New Python wire variants reuse the distinct FIRST wire in this one compound.
    # They are compatibility/parser checks, not extra native cases or live evidence.
    distinct = loaded_cases["case-distinct.json"]
    compatibility = []
    for state in ("absent", "null"):
        variant = copy.deepcopy(distinct)
        if state == "absent":
            del variant["battle_control_snapshot"][LEAF_KEY]
            del variant["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY]
        else:
            variant["battle_control_snapshot"][LEAF_KEY] = None
            variant["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY] = None
        result = query(variant)
        frame = result["battle_control_snapshot"]
        require((LEAF_KEY in frame) == (state == "null"), "legacy optional key shape changed")
        selection = select_current_warscore_cap_v1(frame, winner_is_war_attacker=True)
        require(selection["status"] == "partial" and
                selection["selected_cap_raw_q100000"] is None,
                "legacy unavailable caps became observed zero")
        compatibility.append({"leaf": state, "status": "passed"})

    unknown_winner = copy.deepcopy(normalized_cases["case-distinct.json"])
    unknown_winner["winner_raw"] = -1
    unknown_winner["winner_side"] = None
    unknown_selection = select_current_warscore_cap_v1(
        unknown_winner, winner_is_war_attacker=True,
    )
    require(unknown_selection["status"] == "partial" and
            unknown_selection["selected_cap_raw_q100000"] is None,
            "unknown native winner selected a current winner cap")
    require(unknown_selection["observed_caps"] ==
            normalized_cases["case-distinct.json"][LEAF_KEY],
            "unknown native winner discarded independently observed caps")

    rejected = []
    for label, key, invalid in (
        ("bool-as-source-id", "source_combat_id", True),
        ("wrong-source-combat", "source_combat_id", distinct["battle_control_snapshot"]["combat_id"] + 1),
        ("bool-as-cap", "war_attacker_winner_cap_raw_q100000", False),
        ("positive-int64-overflow", "war_attacker_winner_cap_raw_q100000", 1 << 63),
        ("negative-int64-overflow", "war_defender_winner_cap_raw_q100000", -(1 << 63) - 1),
    ):
        variant = copy.deepcopy(distinct)
        variant["battle_control_snapshot"][LEAF_KEY][key] = invalid
        rejected.append(reject(variant, label))
    mirror_drift = copy.deepcopy(distinct)
    mirror_drift["active_combat_resume_inputs_v1"]["observed"][LEAF_KEY][
        "war_attacker_winner_cap_raw_q100000"
    ] += 1
    rejected.append(reject(mirror_drift, "actual-observed-mirror-disagreement"))

    require(whole_count == 6 and len(receipts) == 7, "FIRST case/wire counts changed")
    return {
        "schema_version": 1,
        "status": "passed",
        "evidence_layer": "offline_native_production_reader_and_whole_wire_formal_service_compound",
        "native_FIRST_case_count": 7,
        "native_whole_wire_count": 6,
        "native_reader_rejection_case_count": 1,
        "production_path": [
            "actual ReadBattleControlSnapshot",
            "actual SerializeBattleControlSnapshot and SerializeActiveCombatResumeInputsV1",
            "existing MCP _ck3_query_battle_control_snapshot_v1 helper",
            "existing GameplayBridgeService.query_battle_control_snapshot_v1",
            "strict cap parser and native observed mirror validation",
            "current native winner plus explicit same-invocation War-membership condition",
            "production select_current_warscore_cap_v1",
        ],
        "native_cases": receipts,
        "legacy_wire_compatibility": compatibility,
        "rejected_distinct_wire_variants": rejected,
        "unknown_native_winner_variant": {
            "status": "passed",
            "cap_selection_status": unknown_selection["status"],
            "native_case_added": False,
        },
        "native_winner_war_membership_observed": False,
        "sdk_server_started": False,
        "pipe_or_ck3_process_used": False,
        "live_evidence": False,
        "future_battle_score_predicted": False,
        "whole_war_outcome_predicted": False,
        "actual_native_effects_executed": False,
        "actual_game_days_advanced": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player" / "src"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run_compound(args.native_dir, args.output_dir)
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "failed",
            "evidence_layer": "offline_native_production_reader_and_whole_wire_formal_service_compound",
            "error_type": type(error).__name__,
            "error": str(error),
            "live_evidence": False,
            "actual_native_effects_executed": False,
        }
        _write_json(args.output_dir / "compound-result.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return 1
    _write_json(args.output_dir / "compound-result.json", result)
    print(json.dumps({
        "status": result["status"],
        "native_FIRST_case_count": 7,
        "native_whole_wire_count": 6,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
