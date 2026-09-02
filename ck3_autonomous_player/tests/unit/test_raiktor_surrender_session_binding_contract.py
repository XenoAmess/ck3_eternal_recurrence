from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.raiktor_surrender_session_binding_contract import (
    BACKEND_ID,
    bind_raiktor_surrender_aggregate_session,
    normalize_raiktor_surrender_aggregate_session_binding,
)
from xar_autoplayer.simulation.raiktor_surrender_execution_policy import (
    project_raiktor_surrender_execution_readiness,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    assess_raiktor_three_way_exit,
)
from test_raiktor_surrender_six_domain_contract import _aggregate
from test_raiktor_three_way_exit_policy import _complete_inputs


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_surrender_session_binding_v1_contract.json"
)


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "fixture-native:91",
        "revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "paused": True,
        "episode_run_id": "fixture-native-29829-episode",
        "episode_character_id": 29_829,
        "diagnostics": {
            "connection_generation": 12,
            "bridge_pid": 51_268,
        },
    }


def _receipt() -> dict[str, object]:
    return {
        "queried_snapshot_id": "fixture-native:91",
        "queried_revision": 91,
        "queried_native_revision": 7,
        "queried_connection_generation": 12,
        "episode_run_id": "fixture-native-29829-episode",
    }


def _bound() -> dict[str, object]:
    return bind_raiktor_surrender_aggregate_session(
        _snapshot(), _receipt(), _aggregate()
    )


class RaiktorSurrenderSessionBindingContractTests(unittest.TestCase):
    def test_binds_existing_snapshot_receipt_and_aggregate(self) -> None:
        result = _bound()

        self.assertEqual(result["backend_id"], BACKEND_ID)
        self.assertEqual(result["status"], "available")
        self.assertIsNone(result["failure"])
        self.assertEqual(
            result["binding"],
            {
                "snapshot_id": "fixture-native:91",
                "snapshot_revision": 91,
                "native_revision": 7,
                "date_raw": 53_175_816,
                "connection_generation": 12,
                "episode_run_id": "fixture-native-29829-episode",
                "episode_character_id": 29_829,
                "process_id": 51_268,
                "war_id": 50_331_699,
            },
        )
        self.assertTrue(
            result["readiness"]["aggregate_session_binding_ready"]
        )
        normalized = normalize_raiktor_surrender_aggregate_session_binding(
            result,
            expected_snapshot_id="fixture-native:91",
            expected_snapshot_revision=91,
            expected_native_revision=7,
            expected_date_raw=53_175_816,
            expected_connection_generation=12,
            expected_episode_run_id="fixture-native-29829-episode",
            expected_episode_character_id=29_829,
            expected_process_id=51_268,
            expected_war_id=50_331_699,
        )
        self.assertEqual(normalized, result)

    def test_missing_existing_fields_are_typed_red(self) -> None:
        cases = (
            ("snapshot", "episode_run_id"),
            ("receipt", "queried_connection_generation"),
            ("diagnostics", "bridge_pid"),
        )
        for owner, field in cases:
            with self.subTest(owner=owner, field=field):
                snapshot = _snapshot()
                receipt = _receipt()
                target = snapshot if owner == "snapshot" else receipt
                if owner == "diagnostics":
                    target = snapshot["diagnostics"]
                del target[field]

                result = bind_raiktor_surrender_aggregate_session(
                    snapshot, receipt, _aggregate()
                )

                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(
                    result["failure"]["code"], "missing_binding_fields"
                )
                self.assertIsNone(result["binding"])
                self.assertFalse(
                    result["readiness"]["aggregate_session_binding_ready"]
                )

    def test_cross_frame_fields_are_typed_red(self) -> None:
        cases = (
            ("queried_snapshot_id", "fixture-native:92"),
            ("queried_revision", 92),
            ("queried_native_revision", 8),
            ("queried_connection_generation", 13),
            ("episode_run_id", "fixture-other-episode"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                receipt = _receipt()
                receipt[field] = value
                result = bind_raiktor_surrender_aggregate_session(
                    _snapshot(), receipt, _aggregate()
                )
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(
                    result["failure"]["code"], "session_binding_mismatch"
                )

    def test_aggregate_revision_or_episode_owner_drift_is_typed_red(self) -> None:
        for field, value in (
            ("snapshot_revision", 92),
            ("native_revision", 8),
            ("date_raw", 53_175_840),
            ("primary_attacker_character_id", 29_830),
        ):
            with self.subTest(field=field):
                aggregate = _aggregate()
                aggregate["frame"][field] = value
                result = bind_raiktor_surrender_aggregate_session(
                    _snapshot(), _receipt(), aggregate
                )
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(
                    result["failure"]["code"], "aggregate_frame_mismatch"
                )

    def test_invalid_pid_and_malformed_aggregate_are_typed_red(self) -> None:
        snapshot = _snapshot()
        snapshot["diagnostics"]["bridge_pid"] = True
        invalid_pid = bind_raiktor_surrender_aggregate_session(
            snapshot, _receipt(), _aggregate()
        )
        self.assertEqual(invalid_pid["status"], "unavailable")
        self.assertEqual(
            invalid_pid["failure"]["code"], "invalid_binding_fields"
        )

        aggregate = _aggregate()
        aggregate["domains"]["gold"]["payload"]["same_frame_stable"] = False
        malformed = bind_raiktor_surrender_aggregate_session(
            _snapshot(), _receipt(), aggregate
        )
        self.assertEqual(malformed["status"], "unavailable")
        self.assertEqual(
            malformed["failure"]["code"], "aggregate_contract_unavailable"
        )

    def test_execution_gate_consumes_exact_bound_aggregate_only(self) -> None:
        inputs = _complete_inputs(
            continue_interval=(-100, -50),
            surrender_interval=(100, 120),
            white_interval=(0, 20),
        )
        decision = assess_raiktor_three_way_exit(*inputs)
        binding = _bound()

        result = project_raiktor_surrender_execution_readiness(
            decision, inputs[0], inputs[1], binding
        )

        self.assertTrue(result["terms"]["session_provenance_ready"])
        self.assertNotIn(
            "six_domain_session_provenance_not_bound",
            result["terms"]["blockers"],
        )
        self.assertFalse(result["action"]["ready"])
        self.assertIsNone(result["action"]["literal"])

        stale_terms = deepcopy(inputs[1])
        stale_terms["domains"]["gold"]["payload"][
            "attacker_current_gold"
        ]["value"]["raw"] += 1
        stale = project_raiktor_surrender_execution_readiness(
            decision, inputs[0], stale_terms, binding
        )
        self.assertFalse(stale["terms"]["session_provenance_ready"])

    def test_frozen_contract_has_no_new_native_reader_or_action(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["backend_id"], BACKEND_ID)
        self.assertEqual(
            contract["source_mapping"]["process_id"],
            "snapshot.diagnostics.bridge_pid",
        )
        self.assertTrue(contract["hard_boundaries"]["read_only"])
        self.assertFalse(contract["hard_boundaries"]["new_native_reader"])
        self.assertFalse(contract["hard_boundaries"]["mutation"])
        self.assertFalse(contract["readiness"]["production_live"])
        self.assertFalse(contract["readiness"]["automatic_surrender_ready"])


if __name__ == "__main__":
    unittest.main()
