from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_war_bound_loss_candidate_v1_source_contract.json"
)


class RaiktorWarBoundLossCandidateV1ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_build_and_frozen_inputs(self) -> None:
        self.assertEqual(self.value["game_version"], "1.19.0.6")
        self.assertEqual(
            self.value["ck3_exe_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        for row in self.value["frozen_inputs"]:
            path = ROOT.parent / row["path"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                row["sha256"],
                row["path"],
            )

    def test_candidate_is_default_off_and_not_public(self) -> None:
        implementation = self.value["implementation"]
        boundary = self.value["hard_boundaries"]
        self.assertFalse(implementation["default_enabled"])
        self.assertTrue(implementation["read_only"])
        self.assertFalse(implementation["queues_command"])
        self.assertFalse(implementation["advances_time"])
        self.assertFalse(implementation["public_wire_changed"])
        self.assertFalse(implementation["production_readiness_changed"])
        self.assertFalse(boundary["source_specific_attribution_ready"])
        self.assertFalse(boundary["termination_action_bound"])
        self.assertFalse(boundary["surrender_causality_proven"])
        self.assertFalse(boundary["public_terms_ready"])
        self.assertFalse(boundary["gen_034_resolved"])
        self.assertFalse(boundary["production_live"])

        cmake = (ROOT / "native_bridge" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        option = implementation["cmake_option"]
        start = cmake.index(f"option(\n  {option}")
        self.assertIn("\n  OFF\n)", cmake[start : start + 260])

    def test_destroyed_math_uses_measured_checkpoint_not_authored_total(self) -> None:
        vector = self.value["fixture_vector"]
        self.assertEqual(vector["measured_pre_termination_soldiers"], 598)
        self.assertEqual(vector["destroyed_post_termination_soldiers"], 0)
        self.assertEqual(
            vector["destroyed_proven_boundary_soldiers_lost"],
            vector["measured_pre_termination_soldiers"]
            - vector["destroyed_post_termination_soldiers"],
        )
        self.assertFalse(
            self.value["hard_boundaries"]["authored_3000_is_measured_pre"]
        )
        self.assertFalse(
            self.value["hard_boundaries"]["post_for_survivors_observed"]
        )


if __name__ == "__main__":
    unittest.main()
