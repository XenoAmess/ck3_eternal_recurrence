from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_exit_utility_evaluator import (
    PROVIDER_SCHEMA,
    ExitUtilityEvaluationError,
    evaluate_raiktor_immediate_exit_utilities,
)
from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (
    provide_raiktor_exit_utility_model,
)
from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    provide_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (
    provide_raiktor_white_peace_narrow_projection,
)
from test_raiktor_white_peace_narrow_projection_provider import (
    _options_query,
    _snapshot,
    _terms_query,
)


def _inputs() -> tuple[dict[str, object], ...]:
    terms = _terms_query()
    projection = provide_raiktor_white_peace_narrow_projection(
        _snapshot(), _options_query(), terms
    )
    return (
        projection,
        terms["raiktor_surrender_aggregate_session"],
        provide_raiktor_owner_budget_profile(None),
        provide_raiktor_exit_utility_model(),
    )


class RaiktorExitUtilityEvaluatorTests(unittest.TestCase):
    def test_scores_both_immediate_exits_without_authorizing_action(
        self,
    ) -> None:
        result = evaluate_raiktor_immediate_exit_utilities(*_inputs())

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertTrue(result["utility_evaluation_ready"])
        self.assertFalse(result["production_live_inputs"])
        self.assertFalse(result["full_three_way_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])

        certificate = result["evaluation_certificate"]
        white = certificate["options"]["white_peace"]
        surrender = certificate["options"]["surrender"]
        self.assertEqual(white["base_utility_raw"], -11_525_000)
        self.assertEqual(white["uncertainty_penalty_raw"], 17_500_000)
        self.assertEqual(white["utility_raw"], -29_025_000)
        self.assertEqual(
            white["hard_budget_breaches"],
            ["white_peace_favor_hook_budget_breached"],
        )
        self.assertEqual(white["execution_blockers"], [])
        self.assertFalse(white["eligible"])
        self.assertEqual(surrender["base_utility_raw"], -52_225_000)
        self.assertEqual(
            surrender["uncertainty_penalty_raw"], 22_500_000
        )
        self.assertEqual(surrender["utility_raw"], -74_725_000)
        self.assertEqual(surrender["execution_blockers"], [])
        self.assertTrue(surrender["eligible"])
        self.assertEqual(
            certificate["comparison"]["preferred_immediate_exit"],
            "surrender",
        )

    def test_unavailable_white_peace_is_scored_but_not_eligible(self) -> None:
        terms = _terms_query()
        projection = provide_raiktor_white_peace_narrow_projection(
            _snapshot(), _options_query(available=False), terms
        )
        result = evaluate_raiktor_immediate_exit_utilities(
            projection,
            terms["raiktor_surrender_aggregate_session"],
            provide_raiktor_owner_budget_profile(None),
            provide_raiktor_exit_utility_model(),
        )

        self.assertTrue(result["utility_evaluation_ready"])
        options = result["evaluation_certificate"]["options"]
        self.assertEqual(options["white_peace"]["utility_raw"], -29_025_000)
        self.assertEqual(
            options["white_peace"]["execution_blockers"],
            ["white_peace_native_execution_unavailable"],
        )
        self.assertFalse(options["white_peace"]["eligible"])
        self.assertTrue(options["surrender"]["eligible"])

    def test_unavailable_surrender_is_scored_but_not_eligible(self) -> None:
        terms = _terms_query()
        projection = provide_raiktor_white_peace_narrow_projection(
            _snapshot(),
            _options_query(surrender_available=False),
            terms,
        )
        result = evaluate_raiktor_immediate_exit_utilities(
            projection,
            terms["raiktor_surrender_aggregate_session"],
            provide_raiktor_owner_budget_profile(None),
            provide_raiktor_exit_utility_model(),
        )

        options = result["evaluation_certificate"]["options"]
        self.assertEqual(options["surrender"]["utility_raw"], -74_725_000)
        self.assertEqual(
            options["surrender"]["execution_blockers"],
            ["surrender_native_execution_unavailable"],
        )
        self.assertFalse(options["surrender"]["eligible"])
        self.assertEqual(
            result["evaluation_certificate"]["comparison"]["status"],
            "pairwise_underdetermined",
        )

    def test_projection_cannot_bind_a_different_surrender_aggregate(
        self,
    ) -> None:
        projection, session, budget, model = _inputs()
        projection = deepcopy(projection)
        projection["white_peace_observation"][
            "evaluated_surrender_terms_sha256"
        ] = "F" * 64

        with self.assertRaisesRegex(
            ExitUtilityEvaluationError,
            "surrender aggregate hashes differ",
        ):
            evaluate_raiktor_immediate_exit_utilities(
                projection, session, budget, model
            )

    def test_model_must_bind_the_loaded_budget_profile(self) -> None:
        projection, session, budget, model = _inputs()
        model = deepcopy(model)
        model["exit_utility_model"]["budget_profile_binding"][
            "profile_source_sha256"
        ] = "F" * 64

        with self.assertRaisesRegex(
            ExitUtilityEvaluationError,
            "model and budget profile bindings differ",
        ):
            evaluate_raiktor_immediate_exit_utilities(
                projection, session, budget, model
            )

    def test_missing_inputs_remain_typed_blockers(self) -> None:
        result = evaluate_raiktor_immediate_exit_utilities(
            None, None, None, None
        )

        self.assertFalse(result["utility_evaluation_ready"])
        self.assertEqual(
            result["blockers"],
            [
                "white_peace_narrow_projection_unavailable",
                "surrender_session_unavailable",
                "strategy_budget_profile_unavailable",
                "strategy_utility_model_unavailable",
            ],
        )
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])


if __name__ == "__main__":
    unittest.main()
