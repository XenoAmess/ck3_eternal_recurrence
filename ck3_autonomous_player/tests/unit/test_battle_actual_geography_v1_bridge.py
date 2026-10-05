from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import test_battle_control_snapshot_v1_bridge as control
import test_battle_transition_v1_bridge as transition
from xar_autoplayer.bridge.battle_actual_geography_contract import (
    normalize_actual_geography_v1,
)
from xar_autoplayer.bridge.battle_control_contract import (
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.bridge.battle_transition_contract import (
    normalize_battle_transition_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


def geography(*, unavailable: bool = False, width: int = 0) -> dict[str, object]:
    return {
        "terrain": {
            "status": "unavailable" if unavailable else "available",
            "key": None if unavailable else "forest",
            "combat_width_multiplier_raw": None if unavailable else width,
            "scale": 100000,
            "unavailable_reason": "terrain_unavailable" if unavailable else None,
        },
        "constructor_adjacency_kind_raw": 0,
        "holding_defender": False,
    }


class TransitionServiceDriver(transition._ServiceDriver):
    def __init__(self, leaf: dict[str, object]) -> None:
        super().__init__()
        self.leaf = leaf

    def execute_step(self, step: str, *, expected_revision=None):
        result = super().execute_step(step, expected_revision=expected_revision)
        result["battle_transition_snapshot"]["actual_geography_v1"] = copy.deepcopy(self.leaf)
        result["actual_geography_v1"] = copy.deepcopy(self.leaf)
        return result


class ControlServiceDriver(control._ServiceDriver):
    def __init__(self, leaf: dict[str, object]) -> None:
        super().__init__()
        self.leaf = leaf

    def execute_step(self, step: str, *, expected_revision=None):
        result = super().execute_step(step, expected_revision=expected_revision)
        result["battle_control_snapshot"]["actual_geography_v1"] = copy.deepcopy(self.leaf)
        return result


class ActualGeographyBridgeTests(unittest.TestCase):
    def test_optional_leaf_preserves_signed_zero_false_and_old_shape(self):
        for leaf in (geography(), geography(width=-(2**63)), geography(unavailable=True), None):
            with self.subTest(leaf=leaf):
                frame = transition._frame()
                frame["actual_geography_v1"] = copy.deepcopy(leaf)
                normalized = normalize_battle_transition_v1(
                    frame, expected_combat_id=transition.COMBAT_ID,
                    expected_observed_date_raw=transition.DATE_RAW,
                    expected_snapshot_revision=transition.NATIVE_REVISION,
                )
                self.assertEqual(normalized["actual_geography_v1"], leaf)
                self.assertTrue(normalized["battle_transition_ready"])
                owned = control._battle_frame()
                owned["actual_geography_v1"] = copy.deepcopy(leaf)
                normalized_owned = normalize_battle_control_snapshot_v1(
                    owned, expected_subject_public_cunit_id=control.SUBJECT,
                    expected_observed_date_raw=control.DATE_RAW,
                    expected_snapshot_revision=control.NATIVE_REVISION,
                )
                self.assertEqual(normalized_owned["actual_geography_v1"], leaf)
                self.assertTrue(normalized_owned["battle_control_ready"])
        old = transition._frame()
        self.assertNotIn("actual_geography_v1", normalize_battle_transition_v1(
            old, expected_combat_id=transition.COMBAT_ID,
            expected_observed_date_raw=transition.DATE_RAW,
            expected_snapshot_revision=transition.NATIVE_REVISION,
        ))

    def test_native_driver_and_service_preserve_transition_geography(self):
        for leaf in (geography(), geography(unavailable=True)):
            with self.subTest(leaf=leaf):
                driver, endpoint = transition._native_driver()
                def response():
                    result = transition._native_result()
                    result["battle_transition_snapshot"]["actual_geography_v1"] = copy.deepcopy(leaf)
                    return result
                transition._answer_with(endpoint, response)
                result = driver.execute_step(
                    transition.STEP,
                    expected_revision=int(driver.take_snapshot()["revision"]),
                )
                self.assertEqual(result["actual_geography_v1"], leaf)
                self.assertEqual(result["battle_transition_snapshot"]["actual_geography_v1"], leaf)
                service_result = GameplayBridgeService(TransitionServiceDriver(leaf)).query_battle_transition_v1(
                    transition.COMBAT_ID, expected_revision=transition.PUBLIC_REVISION,
                )
                self.assertEqual(service_result["actual_geography_v1"], leaf)
                self.assertEqual(service_result["battle_transition_snapshot"]["actual_geography_v1"], leaf)

    def test_owned_control_native_cache_and_service_preserve_geography(self):
        leaf = geography(width=-123456)
        driver, endpoint = control._native_driver()
        def response():
            result = control._native_result()
            result["battle_control_snapshot"]["actual_geography_v1"] = copy.deepcopy(leaf)
            return result
        control._answer_with(endpoint, response)
        result = driver.execute_step(
            control.STEP, expected_revision=int(driver.take_snapshot()["revision"]),
        )
        self.assertEqual(result["battle_control_snapshot"]["actual_geography_v1"], leaf)
        self.assertEqual(driver.take_snapshot()["battle_control_snapshot_v1"]["actual_geography_v1"], leaf)
        service_result = GameplayBridgeService(ControlServiceDriver(leaf)).query_battle_control_snapshot_v1(
            control.SUBJECT, expected_revision=4,
        )
        self.assertEqual(service_result["battle_control_snapshot"]["actual_geography_v1"], leaf)

    def test_unobserved_combat_has_no_geography(self):
        frame = transition._frame("combat_not_found")
        frame["actual_geography_v1"] = geography()
        with self.assertRaisesRegex(ValueError, "invented actual geography"):
            normalize_battle_transition_v1(
                frame, expected_combat_id=transition.COMBAT_ID,
                expected_observed_date_raw=transition.DATE_RAW,
                expected_snapshot_revision=transition.NATIVE_REVISION,
            )

    def test_native_nullable_values_are_distinct_from_boolean_numbers(self):
        leaf = geography()
        leaf["constructor_adjacency_kind_raw"] = None
        leaf["holding_defender"] = None
        self.assertEqual(normalize_actual_geography_v1(leaf), leaf)
        leaf["constructor_adjacency_kind_raw"] = True
        with self.assertRaises(ValueError):
            normalize_actual_geography_v1(leaf)


if __name__ == "__main__":
    unittest.main()
