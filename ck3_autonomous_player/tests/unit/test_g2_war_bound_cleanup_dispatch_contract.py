from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.raiktor_war_bound_loss_cleanup_contract import (
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
    parse_query_raiktor_war_bound_loss_cleanup_v1_step,
)


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = ROOT.parent
CONTRACT = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_war_bound_cleanup_dispatch_v1_source_contract.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class G2WarBoundCleanupDispatchContractTests(unittest.TestCase):
    def test_generation_safe_step_is_canonical(self) -> None:
        self.assertEqual(
            parse_query_raiktor_war_bound_loss_cleanup_v1_step(
                "query-raiktor-war-bound-loss-cleanup-v1-50331699"
            ),
            50331699,
        )
        for value in (
            "query-raiktor-war-bound-loss-cleanup-v1-0",
            "query-raiktor-war-bound-loss-cleanup-v1-050331699",
            "query-raiktor-war-bound-loss-cleanup-v1--1",
            QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
        ):
            self.assertIsNone(
                parse_query_raiktor_war_bound_loss_cleanup_v1_step(value)
            )

    def test_source_contract_is_exact_build_and_hash_bound(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["game_version"], "1.19.0.6")
        self.assertEqual(
            contract["game_executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertFalse(contract["default_enabled"])
        self.assertEqual(
            contract["private_capability"],
            QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
        )
        for row in contract["source_files"]:
            path = REPOSITORY_ROOT / row["path"]
            self.assertEqual(_sha256(path), row["sha256"], row["path"])

    def test_bridge_requires_baseline_then_surrender_and_consumes_it(self) -> None:
        bridge = (
            ROOT / "native_bridge" / "src" / "bridge.cpp"
        ).read_text(encoding="utf-8")
        for token in (
            "raiktor_war_bound_loss_baseline.reset();",
            "same-connection surrender ACK is required",
            "ReadRaiktorWarBoundLossCleanup",
            "raiktor_war_bound_loss_surrender_submitted = false;",
            "frozen WarID remains active; cleanup is ",
        ):
            self.assertIn(token, bridge)
        self.assertLess(
            bridge.index("same-connection surrender ACK is required"),
            bridge.index("ReadRaiktorWarBoundLossCleanup"),
        )

    def test_default_build_does_not_enable_private_candidate(self) -> None:
        cmake = (ROOT / "native_bridge" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        option = cmake.index("XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1")
        self.assertIn("OFF", cmake[option : option + 180])
        boundaries = json.loads(CONTRACT.read_text(encoding="utf-8"))[
            "hard_boundaries"
        ]
        self.assertFalse(boundaries["public_terms_ready"])
        self.assertFalse(boundaries["action_readiness_promoted"])
        self.assertFalse(boundaries["automatic_surrender_ready"])
        self.assertFalse(boundaries["gen034_closed"])


if __name__ == "__main__":
    unittest.main()
