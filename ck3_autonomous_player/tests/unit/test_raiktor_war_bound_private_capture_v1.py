from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native_bridge/research/raiktor_war_bound_private_capture_v1.cpp"
MANIFEST = ROOT / "native_bridge/research/raiktor_war_bound_private_capture_v1_manifest.json"
CMAKE = ROOT / "native_bridge/CMakeLists.txt"


class RaiktorWarBoundPrivateCaptureV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.cmake = CMAKE.read_text(encoding="utf-8")

    def test_exact_build_observation_window_is_pinned(self) -> None:
        self.assertIn("kObservationStopRva = 0x2E7F951", self.source)
        self.assertIn("kObservationWindowEndRva = 0x2E7F9A6", self.source)
        self.assertIn("kSpawnArmyRuntimeVtableRva = 0x443C6E8", self.source)
        self.assertIn(
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            self.source,
        )

    def test_action_filter_requires_exact_option_and_six_unique_nodes(self) -> None:
        action_filter = self.manifest["action_filter"]
        self.assertIn("bookmark.1071.a", action_filter["arm_file_exact_utf8"])
        self.assertEqual(action_filter["required_unique_loaded_nodes"], 6)
        self.assertEqual(action_filter["required_unique_army_generation_ids"], 6)
        self.assertIn("loaded_nodes.insert(row.loaded_node)", self.source)
        self.assertIn("row.war_id != capture.exact_raiktor_war_id", self.source)

    def test_capture_reads_generation_ids_and_measured_soldiers(self) -> None:
        self.assertIn("kCurrentRegimentSoldiersOffset = 0x38", self.source)
        self.assertIn("kCurrentRegimentArmyIdOffset = 0x140", self.source)
        self.assertIn("kPersistentRegimentBoundWarIdOffset = 0x13C", self.source)
        self.assertIn("initial_soldiers += soldiers", self.source)
        self.assertNotIn("authored_total_soldiers", self.source)

    def test_target_is_opt_in_and_does_not_touch_public_bridge_target(self) -> None:
        self.assertIn("XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1", self.cmake)
        self.assertIn("xar_ck3_raiktor_war_bound_private_capture_v1", self.cmake)
        self.assertFalse(self.manifest["production_installed"])
        self.assertFalse(self.manifest["production_abi_changed"])
        self.assertFalse(self.manifest["readiness_promotion"])
        self.assertIn("public_bridge_abi_changed", self.source)
        self.assertIn("production_detour_installed", self.source)

    def test_staged_runner_budget_is_accepted_by_private_capture(self) -> None:
        self.assertIn("parsed > 1200000", self.source)
        self.assertEqual(
            self.manifest["readiness_contract"]["capture_process_timeout_ms"],
            1200000,
        )


if __name__ == "__main__":
    unittest.main()
