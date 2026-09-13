from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_same_frame_white_peace_comparator import (
    provide_raiktor_same_frame_white_peace_comparison,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (
    PROVIDER_SCHEMA,
    WhitePeaceNarrowProjectionError,
    provide_raiktor_white_peace_narrow_projection,
)
from test_native_bridge_driver import _termination_options
from test_raiktor_same_frame_white_peace_comparator import _source
from test_raiktor_surrender_session_binding_contract import (
    _bound,
    _snapshot as _binding_snapshot,
)
from test_war_termination_terms_contract import (
    _available_raiktor_observed_terms,
)


WAR_ID = 50_331_699
ATTACKER_ID = 29_829
DEFENDER_ID = 17_116
CLAIMANT_ID = 41_001


def _snapshot() -> dict[str, object]:
    value = _binding_snapshot()
    value.update(
        {
            "played_character": {
                "character_id": ATTACKER_ID,
                "alive": True,
            },
            "active_wars": [
                {
                    "war_id": WAR_ID,
                    "player_side": "attacker",
                    "player_is_primary_war_leader": True,
                    "primary_opponent_character_id": DEFENDER_ID,
                    "player_relative_war_score": 41,
                    "targeted_title_ids": [1_800],
                }
            ],
        }
    )
    return value


def _options_query(
    *, available: bool = True, surrender_available: bool = True
) -> dict[str, object]:
    return {
        "accepted": True,
        "status": "available",
        "war_termination_options": _termination_options(
            WAR_ID,
            white_peace_available=available,
            surrender_available=surrender_available,
            white_peace_acceptance_raw=1_100_000,
            white_peace_decision_status_raw=0,
            casus_belli_database_index=411,
            casus_belli_key="raiktor_claim_cb",
        ),
        "queried_snapshot_id": "fixture-native:91",
        "queried_revision": 91,
        "queried_native_revision": 7,
        "queried_connection_generation": 12,
        "queried_episode_run_id": "fixture-native-29829-episode",
    }


def _terms() -> dict[str, object]:
    terms = deepcopy(_available_raiktor_observed_terms())
    terms["war_id"] = WAR_ID
    terms["casus_belli"]["database_index"] = 411
    terms["gold_reparations"]["defender_current_gold"][
        "character_id"
    ] = DEFENDER_ID
    terms["gold_reparations"]["defender_authoritative_monthly_gold_income"][
        "character_id"
    ] = DEFENDER_ID
    terms["gold_reparations"]["actual_transfer"][
        "to_character_id"
    ] = DEFENDER_ID
    terms["prisoner_release"]["defender_participant_ids"] = [DEFENDER_ID]
    terms["prisoner_release"]["defender_release_candidate_ids"] = [
        DEFENDER_ID
    ]
    terms["prisoner_release"]["release_pairs"][0][
        "jailer_character_id"
    ] = DEFENDER_ID
    terms["truce"].update(
        {
            "evaluated_days_observable": True,
            "evaluated_days": 1_825,
        }
    )
    terms["readiness"]["truce_ready"] = True
    return terms


def _terms_query() -> dict[str, object]:
    return {
        "accepted": True,
        "status": "available",
        "war_termination_terms": _terms(),
        "queried_snapshot_id": "fixture-native:91",
        "queried_revision": 91,
        "queried_native_revision": 7,
        "queried_connection_generation": 12,
        "episode_run_id": "fixture-native-29829-episode",
        "raiktor_surrender_aggregate_session": _bound(),
    }


class RaiktorWhitePeaceNarrowProjectionProviderTests(unittest.TestCase):
    def test_projects_complete_same_frame_observation_and_comparator_input(
        self,
    ) -> None:
        result = provide_raiktor_white_peace_narrow_projection(
            _snapshot(), _options_query(), _terms_query()
        )

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["observation_ready"])
        self.assertFalse(result["production_live"])
        self.assertEqual(result["blockers"], [])
        observation = result["white_peace_observation"]
        self.assertEqual(
            observation["terms"]["claim_disposition"],
            "retain_and_strengthen_weak",
        )
        self.assertEqual(
            observation["terms"]["attacker_prestige_delta_raw"],
            -3_500_000,
        )
        self.assertEqual(
            observation["terms"]["primary_gold_transfer_raw"], 0
        )
        self.assertEqual(
            observation["terms"]["truce_evaluated_days"], 1_825
        )
        self.assertEqual(
            observation["terms"]["prisoner_release_pairs"],
            [
                {
                    "jailer_character_id": DEFENDER_ID,
                    "prisoner_character_id": 30_003,
                }
            ],
        )
        self.assertTrue(
            observation["option"]["recipient_response"][
                "would_accept_now"
            ]
        )
        self.assertEqual(
            observation["option"]["recipient_response"]["status"],
            "available",
        )
        self.assertTrue(
            observation["option"]["same_frame_surrender"]["available"]
        )
        self.assertIn(
            "participant_ally_fame_deltas",
            result["unobserved_dynamic_effects"],
        )
        self.assertEqual(
            result["source_evidence"]["game_version"], "1.19.0.6"
        )
        self.assertIn(
            "war_bound_army_losses",
            result["surrender_unobserved_dynamic_effects"],
        )
        self.assertEqual(
            result["surrender_feature_observation"],
            {
                "primary_gold_transfer_raw": 15_000_000,
                "attacker_prestige_delta_raw": -7_000_000,
                "declared_claim_removed_count": 1,
                "favor_hook_applied": 1,
                "truce_day_count": 1_825,
                "pow_release_count": 1,
                "title_holder_change_count": 0,
                "hostage_transfer_count": 0,
                "war_bound_soldier_loss_count": 0,
            },
        )

        comparison = provide_raiktor_same_frame_white_peace_comparison(
            source_checkpoint_value=_source(observation["frame"]),
            white_peace_observation_value=observation,
            surrender_terms_value=_bound()["aggregate"],
        )
        self.assertTrue(comparison["same_frame_comparison_ready"])
        self.assertEqual(
            comparison["comparison_certificate"]["terms_comparison"][
                "attacker_prestige_delta_raw"
            ],
            {"white_peace": -3_500_000, "surrender": -7_000_000},
        )

    def test_cross_session_query_receipt_is_rejected(self) -> None:
        options = _options_query()
        options["queried_revision"] = 92
        with self.assertRaisesRegex(
            WhitePeaceNarrowProjectionError, "crossed its paused session"
        ):
            provide_raiktor_white_peace_narrow_projection(
                _snapshot(), options, _terms_query()
            )

    def test_unavailable_option_keeps_terms_and_execution_state(self) -> None:
        result = provide_raiktor_white_peace_narrow_projection(
            _snapshot(), _options_query(available=False), _terms_query()
        )
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["observation_ready"])
        self.assertEqual(result["blockers"], [])
        option = result["white_peace_observation"]["option"]
        self.assertFalse(option["available"])
        self.assertFalse(option["native_validator"])
        self.assertEqual(
            option["recipient_response"],
            {
                "status": "unavailable",
                "decision_status_raw": None,
                "would_accept_now": None,
            },
        )
        self.assertTrue(option["same_frame_surrender"]["available"])
        self.assertEqual(
            result["white_peace_observation"]["terms"][
                "claim_disposition"
            ],
            "retain_and_strengthen_weak",
        )

    def test_missing_truce_duration_remains_red(self) -> None:
        query = _terms_query()
        query["war_termination_terms"]["truce"].update(
            {
                "evaluated_days_observable": False,
                "evaluated_days": None,
            }
        )
        query["war_termination_terms"]["readiness"]["truce_ready"] = False
        result = provide_raiktor_white_peace_narrow_projection(
            _snapshot(), _options_query(), query
        )
        self.assertEqual(
            result["blockers"], ["white_peace_truce_duration_unavailable"]
        )

    def test_other_casus_belli_is_rejected(self) -> None:
        options = _options_query()
        options["war_termination_options"]["active_casus_belli_identity"] = {
            "database_index": 411,
            "canonical_key": "claim_cb",
        }
        with self.assertRaisesRegex(
            WhitePeaceNarrowProjectionError,
            "identify different wars",
        ):
            provide_raiktor_white_peace_narrow_projection(
                _snapshot(), options, _terms_query()
            )

    def test_missing_inputs_do_not_create_an_observation(self) -> None:
        result = provide_raiktor_white_peace_narrow_projection(
            None, None, None
        )
        self.assertFalse(result["observation_ready"])
        self.assertEqual(
            result["blockers"],
            [
                "paused_snapshot_unavailable",
                "termination_options_query_unavailable",
                "raiktor_terms_query_unavailable",
            ],
        )


if __name__ == "__main__":
    unittest.main()
