from __future__ import annotations

import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NATIVE = PROJECT_ROOT / "native_bridge"
HEADER = (
    NATIVE
    / "include"
    / "xar_bridge"
    / "zhongguo_scoreboard_production_v1.hpp"
)
SOURCE = NATIVE / "src" / "zhongguo_scoreboard_production_v1.cpp"
CONTRACT = (
    NATIVE
    / "research"
    / "fixtures"
    / "zhongguo_scoreboard_production_v1_source_contract.json"
)
BRIDGE = NATIVE / "src" / "bridge.cpp"
CMAKE = NATIVE / "CMakeLists.txt"
DOC = (
    PROJECT_ROOT.parent
    / "docs"
    / "ck3-native-ai"
    / "zhongguo-scoreboard-production-promotion-v1.md"
)


class ZhongguoScoreboardProductionReadinessTests(unittest.TestCase):
    def test_contract_keeps_production_promotion_live_pending(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["game_version"], "1.19.0.6")
        self.assertEqual(
            contract["executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertFalse(contract["production_capability_advertised_by_default"])
        self.assertFalse(contract["candidate_verifier_enabled_by_default"])
        self.assertFalse(contract["candidate_switch_promotes_capability"])
        self.assertEqual(
            contract["promotion_evidence_status"],
            "paused_live_artifact_pending",
        )
        self.assertEqual(
            contract["current_readiness"], "static-ready-live-pending"
        )
        self.assertEqual(
            contract["minimum_serial_live"]["runner_invocations"], 1
        )
        self.assertEqual(
            contract["minimum_serial_live"][
                "managed_checkpoint_clean_restarts"
            ],
            2,
        )
        batch = contract["batch_collector"]
        self.assertEqual(batch["schema_version"], 3)
        self.assertFalse(batch["global_single_session_required"])
        self.assertEqual(
            batch["binding_policy"],
            "per-surface-single-session-with-canonical-clean-restart",
        )
        self.assertTrue(
            batch[
                "accepted_postconditions_are_verified_when_advertisement_is_false"
            ]
        )
        self.assertEqual(batch["false_advertisement_result"], "RED")
        self.assertFalse(batch["false_advertisement_promotion_eligible"])

    def test_candidate_switch_is_explicit_and_default_off(self) -> None:
        header = HEADER.read_text(encoding="utf-8")
        self.assertIn(
            "XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1", header
        )
        self.assertIn(
            "kZhongguoScoreboardProductionCandidateEnabledV1 = true",
            header,
        )
        self.assertIn(
            "kZhongguoScoreboardProductionCandidateEnabledV1 = false",
            header,
        )
        self.assertEqual(
            header.count(
            "kZhongguoScoreboardActionV1ProductionCapabilityAdvertised = false",
            ),
            1,
        )
        self.assertNotIn(
            "kZhongguoScoreboardActionV1ProductionCapabilityAdvertised = true",
            header,
        )
        self.assertIn("paused_live_artifact_pending", header)

        cmake = CMAKE.read_text(encoding="utf-8")
        option_block = cmake.split(
            "XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1", 1
        )[1].split(")", 1)[0]
        self.assertIn("OFF", option_block)
        self.assertIn("src/zhongguo_scoreboard_production_v1.cpp", cmake)
        self.assertIn(
            "xar_ck3_zhongguo_scoreboard_production_v1_candidate_test",
            cmake,
        )

    def test_verifier_is_read_only_and_checks_the_real_postcondition(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for required in (
            "observed_public_revision != ack.source.revision",
            "observed_connection_generation != ack.source.connection_generation",
            "post_state.provider_session_id != ack.source.provider_session_id",
            "post_state.tree_fingerprint_v1 != ack.source.tree_fingerprint_v1",
            "post_state.observation_sequence <",
            "post_state.observed_state_revision <",
            "post_state.semantic_fingerprint_v1 ==",
            "modal_visibility_mismatch",
            "active_page_mismatch",
            "closed_page_mismatch",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "WriteProcessMemory",
            "CreateRemoteThread",
            "activate_shortcut",
            "provider_revision_tracker",
            "DispatchZhongguoScoreboard",
        ):
            self.assertNotIn(forbidden, source)

    def test_shared_frame_exposes_candidate_but_remains_fail_closed(self) -> None:
        bridge = BRIDGE.read_text(encoding="utf-8")
        symbolic_gate = (
            "kZhongguoScoreboardActionV1ProductionCapabilityAdvertised"
        )
        self.assertIn(symbolic_gate, bridge)
        self.assertIn(
            "zhongguo_scoreboard_production_candidate_enabled", bridge
        )
        self.assertIn(
            "zhongguo_scoreboard_production_capability_advertised", bridge
        )
        self.assertNotIn('"production_capability_advertised\\":true', bridge)

    def test_documented_live_contract_does_not_promote_fixture_evidence(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        forbidden = set(contract["forbidden_promotion_evidence"])
        self.assertTrue(
            {
                "fixture",
                "native_handled_boolean",
                "action_ack_without_later_query",
                "query_sequence",
            }.issubset(forbidden)
        )
        documentation = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "单个 surface 内**：六个动作必须保持同一 PID", documentation
        )
        self.assertIn("绝不把跨 PID 说成同 session", documentation)
        self.assertIn("source query", documentation)
        self.assertIn("independent read-only later query", documentation)
        self.assertIn("managed cleanup receipt", documentation)


if __name__ == "__main__":
    unittest.main()
