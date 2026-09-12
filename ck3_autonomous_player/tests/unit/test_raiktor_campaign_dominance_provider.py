from __future__ import annotations

import copy
import unittest

from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (
    normalize_raiktor_campaign_dominance_certificate,
    provide_raiktor_campaign_dominance,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_intake import (
    provide_raiktor_three_way_exit_intake,
)


REPORT_SHA = "A" * 64


def _snapshot() -> dict[str, object]:
    return {
        "structured_content": {
            "snapshot_id": "native:3",
            "revision": 4,
            "native_revision": 3,
            "date_raw": 53183856,
            "paused": True,
            "map_ready": True,
            "episode_run_id": "native-29829-test",
            "played_character": {"character_id": 29829},
            "active_wars": [{
                "war_id": 33554473,
                "player_side": "attacker",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": 28551,
            }],
            "diagnostics": {
                "connection_generation": 1,
                "bridge_pid": 207372,
            },
        }
    }


def _query(sequence: int) -> dict[str, object]:
    return {
        "structured_content": {
            "accepted": True,
            "status": "available",
            "query_sequence": sequence,
            "queried_snapshot_id": "native:3",
            "queried_revision": 4,
            "queried_native_revision": 3,
            "target_scopes": [{
                "target_character_id": 28551,
                "sources": ["active_war_primary_opponent"],
            }],
            "war_entry_assessments": {
                "status": "available",
                "snapshot_revision": 3,
                "date_raw": 53183856,
                "actor_character_id": 29829,
                "requested_target_character_ids": [28551],
                "assessments": [{
                    "target_character_id": 28551,
                    "effective_target_character_id": 28551,
                    "actor_power_base_raw": 13075500000,
                    "actor_network_contribution_raw": 0,
                    "actor_power_total_raw": 13075500000,
                    "target_power_base_raw": 15460500000,
                    "target_network_contribution_raw": 0,
                    "target_pre_adjustment_total_raw": 15460500000,
                    "target_adjustment_delta_raw": 1310400000,
                    "target_power_total_raw": 16770900000,
                    "actual_power_ratio_raw": 128262,
                }],
                "readiness": {
                    "actor_identity_ready": True,
                    "targets_declarable_ready": True,
                    "effective_targets_ready": True,
                    "ai_context_ready": True,
                    "native_output_ready": True,
                    "network_decomposition_ready": True,
                    "same_frame_ready": True,
                    "ready": True,
                },
                "provenance": {"fixed_point_scale": 100000},
            },
        }
    }


def _provide() -> dict[str, object]:
    snapshot = _snapshot()
    return provide_raiktor_campaign_dominance(
        snapshot,
        _query(1),
        copy.deepcopy(snapshot),
        _query(2),
        copy.deepcopy(snapshot),
        war_id=33554473,
        opponent_character_id=28551,
        source_artifact_sha256=REPORT_SHA,
    )


class CampaignDominanceProviderTests(unittest.TestCase):
    def test_measured_opponent_advantage_is_available_without_action(self) -> None:
        result = _provide()
        certificate = result["campaign_dominance_certificate"]
        self.assertEqual("available", result["status"])
        self.assertEqual("opponent_stronger", certificate["power"]["relation"])
        self.assertEqual(3695400000, certificate["power"]["target_minus_actor_raw"])
        self.assertFalse(certificate["boundaries"]["campaign_outcome_forecast_ready"])
        self.assertFalse(certificate["boundaries"]["action_ready"])
        self.assertIsNone(certificate["boundaries"]["recommended_outcome"])
        self.assertEqual(
            certificate,
            normalize_raiktor_campaign_dominance_certificate(certificate),
        )

    def test_query_sequence_must_be_consecutive(self) -> None:
        snapshot = _snapshot()
        with self.assertRaisesRegex(ValueError, "sequence"):
            provide_raiktor_campaign_dominance(
                snapshot, _query(1), snapshot, _query(3), snapshot,
                war_id=33554473,
                opponent_character_id=28551,
                source_artifact_sha256=REPORT_SHA,
            )

    def test_snapshot_change_is_rejected(self) -> None:
        changed = _snapshot()
        changed["structured_content"]["date_raw"] += 24
        with self.assertRaisesRegex(ValueError, "frame changed"):
            provide_raiktor_campaign_dominance(
                _snapshot(), _query(1), changed, _query(2), _snapshot(),
                war_id=33554473,
                opponent_character_id=28551,
                source_artifact_sha256=REPORT_SHA,
            )

    def test_target_scope_must_be_active_war_opponent(self) -> None:
        second = _query(2)
        second["structured_content"]["target_scopes"][0]["sources"] = [
            "current_declaration_target"
        ]
        with self.assertRaisesRegex(ValueError, "target scope"):
            provide_raiktor_campaign_dominance(
                _snapshot(), _query(1), _snapshot(), second, _snapshot(),
                war_id=33554473,
                opponent_character_id=28551,
                source_artifact_sha256=REPORT_SHA,
            )

    def test_three_way_intake_retains_the_factual_certificate(self) -> None:
        certificate = _provide()["campaign_dominance_certificate"]
        result = provide_raiktor_three_way_exit_intake(
            candidate_value=None,
            surrender_terms_value=None,
            campaign_value=None,
            owner_budget_source_path=None,
            white_peace_observation_value=None,
            white_peace_utility_evaluation_value=None,
            power_dominance_certificate_value=certificate,
        )
        self.assertTrue(result["inputs"]["measured_power_dominance_ready"])
        retained = result["providers"]["measured_power_dominance"]
        self.assertEqual("available", retained["status"])
        self.assertEqual(certificate, retained["certificate"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])


if __name__ == "__main__":
    unittest.main()
