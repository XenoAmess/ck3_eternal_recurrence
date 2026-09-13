from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    OFFER_WHITE_PEACE_CAPABILITY,
    SURRENDER_WAR_CAPABILITY,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (  # noqa: E402
    PROVIDER_SCHEMA,
    ThreeWayExitActionGateError,
    provide_raiktor_three_way_exit_action_gate,
)
from test_raiktor_three_way_exit_recommendation import _provide  # noqa: E402
from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    _snapshot,
)


def _capabilities(*actions: str) -> dict[str, object]:
    return {
        "action_steps": list(actions),
        "bridge_capabilities": [
            OFFER_WHITE_PEACE_CAPABILITY,
            SURRENDER_WAR_CAPABILITY,
        ],
    }


class RaiktorThreeWayExitActionGateTests(unittest.TestCase):
    def test_exact_continue_plan_is_authorized_once(self) -> None:
        recommendation = _provide(production_live=True)
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation,
            _snapshot(),
            _capabilities("resume-map"),
        )

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "authorized")
        self.assertTrue(result["action_ready"])
        self.assertEqual(result["action_literal"], "resume-map")
        action = result["authorization"]["action"]
        self.assertEqual(action["expected_revision"], 91)
        self.assertTrue(action["single_action_only"])
        self.assertIsNone(action["required_capability"])
        self.assertFalse(result["postcondition_verified"])

    def test_exact_white_peace_requires_typed_capability(self) -> None:
        recommendation = _provide(
            production_live=True, allow_white_favor=True
        )
        action = "offer-white-peace-50331699"
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation,
            _snapshot(),
            _capabilities(action),
        )

        self.assertTrue(result["action_ready"])
        self.assertEqual(result["action_literal"], action)
        self.assertEqual(
            result["authorization"]["action"]["required_capability"],
            OFFER_WHITE_PEACE_CAPABILITY,
        )

        capabilities = _capabilities(action)
        capabilities["bridge_capabilities"].remove(
            OFFER_WHITE_PEACE_CAPABILITY
        )
        blocked = provide_raiktor_three_way_exit_action_gate(
            recommendation, _snapshot(), capabilities
        )
        self.assertFalse(blocked["action_ready"])
        self.assertIn(
            "recommended_action_capability_not_advertised",
            blocked["blockers"],
        )

    def test_exact_surrender_maps_to_typed_capability(self) -> None:
        recommendation = _provide(
            production_live=True, opponent_penalty=100_000_000
        )
        action = "surrender-war-50331699"
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation,
            _snapshot(),
            _capabilities(action),
        )

        self.assertTrue(result["action_ready"])
        self.assertEqual(
            result["authorization"]["action"]["required_capability"],
            SURRENDER_WAR_CAPABILITY,
        )

    def test_static_recommendation_does_not_authorize_action(self) -> None:
        recommendation = _provide(production_live=False)
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation, _snapshot(), _capabilities("resume-map")
        )

        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertIn(
            "production_recommendation_not_ready", result["blockers"]
        )

    def test_current_snapshot_must_match_recommendation_frame(self) -> None:
        recommendation = _provide(production_live=True)
        snapshot = _snapshot()
        snapshot["date_raw"] += 24
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation, snapshot, _capabilities("resume-map")
        )

        self.assertFalse(result["action_ready"])
        self.assertIn("action_frame_date_mismatch", result["blockers"])

    def test_missing_action_step_remains_blocked(self) -> None:
        recommendation = _provide(production_live=True)
        result = provide_raiktor_three_way_exit_action_gate(
            recommendation, _snapshot(), _capabilities()
        )

        self.assertFalse(result["action_ready"])
        self.assertIn(
            "recommended_action_step_not_advertised", result["blockers"]
        )

    def test_tampered_recommendation_hash_is_rejected(self) -> None:
        recommendation = deepcopy(_provide(production_live=True))
        recommendation["recommendation_certificate"]["comparison"][
            "winning_margin_raw"
        ] += 1

        with self.assertRaisesRegex(
            ThreeWayExitActionGateError, "hash drifted"
        ):
            provide_raiktor_three_way_exit_action_gate(
                recommendation, _snapshot(), _capabilities("resume-map")
            )


if __name__ == "__main__":
    unittest.main()
