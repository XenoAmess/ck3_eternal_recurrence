from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (  # noqa: E402
    PROVIDER_ID as DOMINANCE_PROVIDER_ID,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (  # noqa: E402
    CONTINUE_POSTCONDITIONS,
    OPPONENT_TERMINAL_CONTROL_CONTRACT,
    PROVIDER_SCHEMA,
    TERMINATION_POSTCONDITIONS,
    ThreeWayExitRecommendationError,
    provide_raiktor_three_way_exit_recommendation,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)
from test_raiktor_exit_utility_evaluator import _inputs  # noqa: E402
from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    _options_query,
    _snapshot,
    _terms_query,
)


def _dominance(
    projection: dict[str, object], *, relation: str = "opponent_stronger"
) -> dict[str, object]:
    observation = projection["white_peace_observation"]
    frame = observation["frame"]
    if relation == "opponent_stronger":
        actor, target = 100_000, 128_262
    elif relation == "actor_stronger":
        actor, target = 128_262, 100_000
    else:
        actor = target = 100_000
    scale = 100_000
    return {
        "schema_version": 2,
        "contract": "raiktor-campaign-dominance-certificate-v2",
        "status": "complete",
        "frame": {
            "snapshot_id": frame["snapshot_id"],
            "snapshot_revision": frame["snapshot_revision"],
            "native_revision": frame["native_revision"],
            "date_raw": frame["date_raw"],
            "connection_generation": 12,
            "ck3_pid": frame["ck3_pid"],
            "episode_run_id": frame["episode_id"],
            "paused": True,
            "war_id": frame["war_id"],
            "actor_character_id": frame["primary_attacker_character_id"],
            "opponent_character_id": frame["primary_defender_character_id"],
        },
        "power": {
            "actor_power_total_raw": actor,
            "target_power_total_raw": target,
            "fixed_point_scale": scale,
            "actual_power_ratio_raw": target * scale // actor,
            "relation": relation,
            "target_minus_actor_raw": target - actor,
        },
        "evidence": {
            "first_query_sequence": 1,
            "second_query_sequence": 2,
            "double_sample_stable": True,
            "source_artifact_sha256": "A" * 64,
            "query_payload_sha256": "B" * 64,
        },
        "producer": {
            "producer_id": DOMINANCE_PROVIDER_ID,
            "producer_version": "1.0.0",
            "production_live_input": True,
        },
        "boundaries": {
            "measured_strategic_power_ready": True,
            "campaign_outcome_forecast_ready": False,
            "exit_utility_ready": False,
            "recommended_outcome": None,
            "action_ready": False,
            "action_literal": None,
        },
    }


def _complete(*, production_live: bool) -> list[dict[str, object]]:
    values = list(_inputs())
    projection = deepcopy(values[0])
    if production_live:
        projection["production_live"] = True
        projection["white_peace_observation"]["producer"][
            "production_live"
        ] = True
    values[0] = projection
    return values


def _terminal_control(
    projection: dict[str, object],
    *,
    score: int = 41,
    production_live: bool,
) -> dict[str, object]:
    frame = projection["white_peace_observation"]["frame"]
    return {
        "schema_version": 1,
        "contract": OPPONENT_TERMINAL_CONTROL_CONTRACT,
        "status": "complete",
        "frame": deepcopy(frame),
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": score,
        "absolute_war_scores_observable": True,
        "attacker_war_score": score,
        "defender_war_score": -score,
        "opponent_terminal_control": score <= -100,
        "source_options_query_sha256": "C" * 64,
        "producer": {
            "producer_id": "test-terminal-control-v1",
            "production_live_input": production_live,
        },
    }


def _provide(
    *,
    production_live: bool = False,
    relation: str = "opponent_stronger",
    allow_white_favor: bool = False,
    opponent_penalty: int | None = None,
    minimum_margin: int | None = None,
    score: int = 41,
) -> dict[str, object]:
    projection, session, budget, model = _complete(
        production_live=production_live
    )
    if allow_white_favor:
        budget = deepcopy(budget)
        budget["owner_budget_profile"]["white_peace_limits"][
            "allow_favor_hook"
        ] = True
    if minimum_margin is not None:
        budget = deepcopy(budget)
        budget["owner_budget_profile"]["pairwise_limits"][
            "minimum_switch_margin_raw"
        ] = minimum_margin
    if opponent_penalty is not None:
        model = deepcopy(model)
        model["exit_utility_model"]["tail_risk_policy"]["parameters_raw"][
            "opponent_stronger_continue_penalty_raw"
        ] = opponent_penalty
    power = _dominance(projection, relation=relation)
    return provide_raiktor_three_way_exit_recommendation(
        projection,
        session,
        power,
        budget,
        model,
        _terminal_control(
            projection, score=score, production_live=production_live
        ),
    )


class RaiktorThreeWayExitRecommendationTests(unittest.TestCase):
    def test_static_inputs_recommend_continue_but_emit_no_action(self) -> None:
        result = _provide()

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertTrue(result["recommendation_ready"])
        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        certificate = result["recommendation_certificate"]
        self.assertEqual(
            certificate["options"]["continue"]["utility_raw"], -50_000_000
        )
        self.assertFalse(
            certificate["options"]["continue"][
                "campaign_outcome_forecast_ready"
            ]
        )
        self.assertEqual(
            certificate["postcondition_plan"]["requirements"],
            list(CONTINUE_POSTCONDITIONS),
        )

    def test_live_bound_white_peace_winner_emits_one_typed_action(self) -> None:
        result = _provide(production_live=True, allow_white_favor=True)

        self.assertEqual(result["recommended_outcome"], "white_peace")
        self.assertTrue(result["production_recommendation_ready"])
        self.assertTrue(result["action_ready"])
        self.assertEqual(result["action_literal"], "offer-white-peace-50331699")
        plan = result["recommendation_certificate"]["action_plan"]
        self.assertTrue(plan["single_action_only"])
        self.assertEqual(plan["semantic_action"], "white_peace")
        self.assertEqual(
            result["recommendation_certificate"]["postcondition_plan"][
                "requirements"
            ],
            list(TERMINATION_POSTCONDITIONS),
        )
        expectations = result["recommendation_certificate"][
            "postcondition_plan"
        ]["expectations"]
        self.assertEqual(
            expectations["resources"]["gold"],
            {"pre_raw": 35_000_000, "delta_raw": 0, "post_raw": 35_000_000},
        )
        self.assertEqual(
            expectations["resources"]["prestige"],
            {
                "pre_raw": 12_345_678,
                "delta_raw": -3_500_000,
                "post_raw": 8_845_678,
            },
        )
        self.assertEqual(expectations["truce"]["evaluated_days"], 1825)
        self.assertFalse(result["postcondition_verified"])
        self.assertFalse(result["gen034_closed"])

    def test_live_bound_surrender_winner_emits_surrender_action(self) -> None:
        result = _provide(production_live=True, opponent_penalty=100_000_000)

        self.assertEqual(result["recommended_outcome"], "surrender")
        self.assertTrue(result["action_ready"])
        self.assertEqual(result["action_literal"], "surrender-war-50331699")
        expectations = result["recommendation_certificate"][
            "postcondition_plan"
        ]["expectations"]
        self.assertEqual(
            expectations["resources"]["gold"],
            {
                "pre_raw": 35_000_000,
                "delta_raw": -15_000_000,
                "post_raw": 20_000_000,
            },
        )
        self.assertEqual(
            expectations["resources"]["prestige"],
            {
                "pre_raw": 12_345_678,
                "delta_raw": -7_000_000,
                "post_raw": 5_345_678,
            },
        )

    def test_unavailable_white_peace_cannot_emit_its_action(self) -> None:
        terms = _terms_query()
        projection = provide_raiktor_white_peace_narrow_projection(
            _snapshot(), _options_query(available=False), terms
        )
        projection["production_live"] = True
        projection["white_peace_observation"]["producer"][
            "production_live"
        ] = True
        _, session, budget, model = _inputs()
        budget = deepcopy(budget)
        budget["owner_budget_profile"]["white_peace_limits"][
            "allow_favor_hook"
        ] = True

        result = provide_raiktor_three_way_exit_recommendation(
            projection,
            session,
            _dominance(projection),
            budget,
            model,
            _terminal_control(projection, production_live=True),
        )

        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertEqual(result["action_literal"], "resume-map")
        white = result["recommendation_certificate"]["options"][
            "white_peace"
        ]
        self.assertFalse(white["eligible"])
        self.assertEqual(
            white["execution_blockers"],
            ["white_peace_native_execution_unavailable"],
        )

    def test_actor_stronger_relation_selects_continue(self) -> None:
        result = _provide(production_live=True, relation="actor_stronger")

        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertEqual(
            result["recommendation_certificate"]["postcondition_plan"][
                "expectations"
            ],
            {
                "war_id": 50331699,
                "played_character_id": 29829,
                "episode_id": "fixture-native-29829-episode",
                "successor_revision_required": True,
            },
        )
        self.assertEqual(result["action_literal"], "resume-map")

    def test_minus_100_excludes_continue_and_selects_legal_surrender(
        self,
    ) -> None:
        result = _provide(production_live=True, score=-100)

        self.assertEqual(result["recommended_outcome"], "surrender")
        self.assertEqual(result["action_literal"], "surrender-war-50331699")
        certificate = result["recommendation_certificate"]
        self.assertEqual(
            certificate["opponent_terminal_control"],
            {
                "active": True,
                "player_relative_war_score": -100,
                "attacker_war_score": -100,
                "defender_war_score": 100,
            },
        )
        continuing = certificate["options"]["continue"]
        self.assertFalse(continuing["eligible"])
        self.assertEqual(
            continuing["execution_blockers"],
            ["opponent_has_enforceable_terminal_war_score"],
        )
        self.assertEqual(continuing["utility_raw"], -50_000_000)

    def test_minus_99_keeps_existing_continue_behavior(self) -> None:
        result = _provide(production_live=True, score=-99)

        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertEqual(result["action_literal"], "resume-map")
        continuing = result["recommendation_certificate"]["options"][
            "continue"
        ]
        self.assertTrue(continuing["eligible"])
        self.assertEqual(continuing["execution_blockers"], [])

    def test_minus_100_still_allows_white_peace_to_win(self) -> None:
        result = _provide(
            production_live=True,
            allow_white_favor=True,
            score=-100,
        )

        self.assertEqual(result["recommended_outcome"], "white_peace")
        self.assertEqual(
            result["action_literal"], "offer-white-peace-50331699"
        )

    def test_minus_100_with_no_legal_terminal_fails_closed(self) -> None:
        terms = _terms_query()
        projection = provide_raiktor_white_peace_narrow_projection(
            _snapshot(),
            _options_query(available=False, surrender_available=False),
            terms,
        )
        projection["production_live"] = True
        projection["white_peace_observation"]["producer"][
            "production_live"
        ] = True
        _, session, budget, model = _inputs()

        result = provide_raiktor_three_way_exit_recommendation(
            projection,
            session,
            _dominance(projection),
            budget,
            model,
            _terminal_control(
                projection, score=-100, production_live=True
            ),
        )

        self.assertFalse(result["recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertEqual(
            result["recommendation_certificate"]["comparison"][
                "eligible_options"
            ],
            [],
        )

    def test_large_margin_requirement_remains_underdetermined(self) -> None:
        result = _provide(
            production_live=True,
            allow_white_favor=True,
            minimum_margin=100_000_000,
        )

        self.assertFalse(result["recommendation_ready"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertIsNone(result["recommended_outcome"])
        self.assertIsNone(result["action_literal"])

    def test_missing_dominance_is_a_typed_blocker(self) -> None:
        projection, session, budget, model = _complete(production_live=True)
        result = provide_raiktor_three_way_exit_recommendation(
            projection,
            session,
            None,
            budget,
            model,
            _terminal_control(projection, production_live=True),
        )

        self.assertIn("measured_power_dominance_unavailable", result["blockers"])
        self.assertFalse(result["recommendation_ready"])
        self.assertFalse(result["action_ready"])

    def test_cross_frame_dominance_is_rejected(self) -> None:
        projection, session, budget, model = _complete(production_live=True)
        power = _dominance(projection)
        power["frame"]["date_raw"] += 24

        with self.assertRaisesRegex(
            ThreeWayExitRecommendationError, "crossed paused frames"
        ):
            provide_raiktor_three_way_exit_recommendation(
                projection,
                session,
                power,
                budget,
                model,
                _terminal_control(projection, production_live=True),
            )

    def test_missing_terminal_control_fails_closed(self) -> None:
        projection, session, budget, model = _complete(production_live=True)

        result = provide_raiktor_three_way_exit_recommendation(
            projection,
            session,
            _dominance(projection),
            budget,
            model,
        )

        self.assertEqual(
            result["blockers"], ["opponent_terminal_control_unavailable"]
        )
        self.assertFalse(result["recommendation_ready"])
        self.assertFalse(result["action_ready"])

    def test_cross_frame_terminal_control_is_rejected(self) -> None:
        projection, session, budget, model = _complete(production_live=True)
        terminal_control = _terminal_control(
            projection, production_live=True
        )
        terminal_control["frame"]["date_raw"] += 24

        with self.assertRaisesRegex(
            ThreeWayExitRecommendationError,
            "terminal-control inputs crossed paused frames",
        ):
            provide_raiktor_three_way_exit_recommendation(
                projection,
                session,
                _dominance(projection),
                budget,
                model,
                terminal_control,
            )


if __name__ == "__main__":
    unittest.main()
