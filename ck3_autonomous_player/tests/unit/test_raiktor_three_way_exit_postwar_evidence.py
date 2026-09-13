from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_three_way_exit_postcondition import (  # noqa: E402
    provide_raiktor_three_way_exit_postcondition,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_postwar_evidence import (  # noqa: E402
    PROVIDER_SCHEMA,
    ThreeWayExitPostwarEvidenceError,
    provide_raiktor_three_way_exit_postwar_evidence,
)
from test_g2_source_specific_war_loss_lifecycle import (  # noqa: E402
    _current_observation,
    _source_capture,
)
from test_raiktor_three_way_exit_postcondition import (  # noqa: E402
    _action_result,
    _authorized,
    _checkpoint_restore,
    _post,
)


SOURCE_CAPTURE_SHA256 = "A" * 64


def _active(gate: dict[str, object]) -> dict[str, object]:
    result = _current_observation()
    frame = gate["authorization"]["frame"]
    result["active_frame"].update(
        {
            "snapshot_revision": frame["snapshot_revision"],
            "native_revision": frame["native_revision"],
            "date_raw": frame["date_raw"],
        }
    )
    return result


def _cleanup_wire(
    gate: dict[str, object],
    active: dict[str, object],
    post: dict[str, object],
    *,
    status: str = "destroyed",
) -> dict[str, object]:
    observation = deepcopy(active)
    frame = gate["authorization"]["frame"]
    observation["active_frame"]["snapshot_revision"] = frame["native_revision"]
    observation["postwar_frame"] = {
        "snapshot_revision": post["native_revision"],
        "native_revision": post["native_revision"],
        "date_raw": post["date_raw"],
        "paused": True,
        "frozen_war_id": frame["war_id"],
        "frozen_war_absent_from_active_wars": True,
    }
    observation["cleanup"] = {"observable": True, "status": status}
    observation["readiness"]["postwar_cleanup_ready"] = True
    for regiment in observation["regiments"]:
        regiment["postwar_persistent_state"] = status
        for row in regiment["composition_rows"]:
            if row["current_army_regiment_id"] is None:
                row.update(
                    {
                        "current_army_regiment_state": "not_present",
                        "raised_carmy_state": "not_present",
                        "frozen_carmy_roster_evidence": "not_present",
                    }
                )
            else:
                row.update(
                    {
                        "current_army_regiment_state": status,
                        "raised_carmy_state": status,
                        "frozen_carmy_roster_evidence": (
                            "frozen_army_destroyed"
                            if status == "destroyed"
                            else "still_attached"
                        ),
                    }
                )
    return {
        "step": f"query-raiktor-war-bound-loss-cleanup-v1-{frame['war_id']}",
        "accepted": True,
        "query_sequence": 1,
        "snapshot_revision": post["native_revision"],
        "raiktor_war_bound_loss_cleanup": observation,
        "backend_id": "native-headless",
    }


def _truce_wire(
    gate: dict[str, object],
    post: dict[str, object],
    sequence: int,
    *,
    status: str = "available",
    expiry_delta: int = 0,
) -> dict[str, object]:
    authorization = gate["authorization"]
    expected = authorization["postcondition_plan"]["expectations"]
    truce = expected["truce"]
    available = status == "available"
    payload = {
        "schema_version": 1,
        "backend_id": "ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1",
        "status": status,
        "snapshot_revision": post["native_revision"],
        "current_date_raw": post["date_raw"],
        "owner_character_id": truce["owner_character_id"],
        "toward_character_id": truce["toward_character_id"],
        "native_has_truce": available,
        "actual_expiry_observable": available,
        "expiry_date_raw": (
            post["date_raw"] + truce["evaluated_days"] * 24 + expiry_delta
            if available
            else None
        ),
        "same_frame_stable": True,
        "readiness": available,
        "temporal_semantics": "post_application_persisted_relation_state",
        "unavailable_reason": None if available else "native_has_truce_false",
    }
    return {
        "step": (
            "query-raiktor-actual-truce-expiry-v1-"
            f"{truce['toward_character_id']}"
        ),
        "accepted": True,
        "query_sequence": sequence,
        "snapshot_revision": post["native_revision"],
        "raiktor_actual_truce_expiry": payload,
        "backend_id": "native-headless",
    }


def _inputs(route: str = "white_peace") -> dict[str, object]:
    gate = _authorized(route)
    post = _post(gate, route=route)
    active = _active(gate)
    return {
        "action_gate_value": gate,
        "source_capture_value": _source_capture(),
        "source_capture_sha256": SOURCE_CAPTURE_SHA256,
        "active_war_bound_value": active,
        "post_snapshot_value": post,
        "cleanup_result_value": _cleanup_wire(gate, active, post),
        "truce_result_values": [
            _truce_wire(gate, post, 10),
            _truce_wire(gate, post, 11),
        ],
    }


class RaiktorThreeWayExitPostwarEvidenceTests(unittest.TestCase):
    def test_composes_evidence_consumed_by_six_check_verifier(self) -> None:
        inputs = _inputs()
        for read in inputs["truce_result_values"]:
            read["actual_truce_expiry_proof"] = deepcopy(
                read["raiktor_actual_truce_expiry"]
            )
        result = provide_raiktor_three_way_exit_postwar_evidence(**inputs)

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["evidence_ready"])
        self.assertEqual(result["blockers"], [])

        gate = inputs["action_gate_value"]
        post = inputs["post_snapshot_value"]
        verified = provide_raiktor_three_way_exit_postcondition(
            gate,
            _action_result(gate, post),
            post,
            result["postwar_evidence"],
            _checkpoint_restore(gate, post),
        )
        self.assertTrue(verified["gen034_closed"])

    def test_rejects_generation_set_drift(self) -> None:
        inputs = _inputs()
        inputs["active_war_bound_value"]["regiments"][0][
            "persistent_regiment_id"
        ] += 1_000

        with self.assertRaisesRegex(
            ThreeWayExitPostwarEvidenceError,
            "generations do not match",
        ):
            provide_raiktor_three_way_exit_postwar_evidence(**inputs)

    def test_rejects_nonconsecutive_or_unstable_truce_reads(self) -> None:
        inputs = _inputs()
        inputs["truce_result_values"][1]["query_sequence"] = 12
        with self.assertRaisesRegex(
            ThreeWayExitPostwarEvidenceError,
            "not stable and consecutive",
        ):
            provide_raiktor_three_way_exit_postwar_evidence(**inputs)

        inputs = _inputs()
        inputs["truce_result_values"][1] = _truce_wire(
            inputs["action_gate_value"],
            inputs["post_snapshot_value"],
            11,
            expiry_delta=1,
        )
        with self.assertRaisesRegex(
            ThreeWayExitPostwarEvidenceError,
            "not stable and consecutive",
        ):
            provide_raiktor_three_way_exit_postwar_evidence(**inputs)

    def test_no_truce_retains_a_typed_red(self) -> None:
        inputs = _inputs()
        gate = inputs["action_gate_value"]
        post = inputs["post_snapshot_value"]
        inputs["truce_result_values"] = [
            _truce_wire(gate, post, 10, status="no_truce"),
            _truce_wire(gate, post, 11, status="no_truce"),
        ]

        result = provide_raiktor_three_way_exit_postwar_evidence(**inputs)

        self.assertEqual(result["status"], "red")
        self.assertFalse(result["evidence_ready"])
        self.assertEqual(
            result["blockers"], ["directional_persisted_truce_stable"]
        )

    def test_surviving_source_generation_retains_a_typed_red(self) -> None:
        inputs = _inputs()
        inputs["cleanup_result_value"] = _cleanup_wire(
            inputs["action_gate_value"],
            inputs["active_war_bound_value"],
            inputs["post_snapshot_value"],
            status="still_alive",
        )

        result = provide_raiktor_three_way_exit_postwar_evidence(**inputs)

        self.assertEqual(result["status"], "red")
        self.assertEqual(
            result["blockers"], ["source_specific_cleanup_destroyed"]
        )

    def test_continue_route_has_no_postwar_evidence_contract(self) -> None:
        inputs = _inputs()
        inputs["action_gate_value"] = _authorized("continue")
        with self.assertRaisesRegex(
            ThreeWayExitPostwarEvidenceError,
            "requires a termination authorization",
        ):
            provide_raiktor_three_way_exit_postwar_evidence(**inputs)


if __name__ == "__main__":
    unittest.main()
