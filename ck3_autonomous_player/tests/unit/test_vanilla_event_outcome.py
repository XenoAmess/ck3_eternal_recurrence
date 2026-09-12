from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.native_auto_run import (  # noqa: E402
    _registered_event_material_postcondition_issue,
)
from xar_autoplayer.bridge.driver import CallbackGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.vanilla_events.outcome import (  # noqa: E402
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    query_vanilla_event_knowledge_v1,
)


def _decision(
    *, event_key: str = "tgp_travel_events.0030", native_index: int = 1
) -> dict[str, object]:
    knowledge = query_vanilla_event_knowledge_v1(event_key)
    analysis = knowledge.get("analysis")
    profile = (
        analysis.get("selected_choice_effect_profile")
        if isinstance(analysis, dict)
        else None
    )
    return {
        "status": "recommended",
        "event_definition_key": event_key,
        "selected_option_number": native_index + 1,
        "selected_native_option_index": native_index,
        "choice_effect_profile": profile,
    }


def _expectation(stress_points: int = 42) -> dict[str, object]:
    value = plan_registered_event_material_postcondition_v1(
        _decision(),
        {"character_id": 27181, "alive": True, "stress_points": stress_points},
        snapshot_id="native:19",
        revision=33,
    )
    assert isinstance(value, dict)
    return value


def _selection(
    before: int,
    after: int,
    *,
    starting_character_id: int = 27181,
    ending_character_id: int = 27181,
) -> dict[str, object]:
    return {
        "postcondition_verified": True,
        "starting_snapshot_id": "native:19",
        "starting_revision": 33,
        "starting_played_character_stress": {
            "status": "available",
            "character_id": starting_character_id,
            "stress_points": before,
        },
        "ending_played_character_stress": {
            "status": "available",
            "character_id": ending_character_id,
            "stress_points": after,
        },
    }


def _gold_selection(before: int, after: int) -> dict[str, object]:
    return {
        "postcondition_verified": True,
        "starting_snapshot_id": "native:19",
        "starting_revision": 33,
        "starting_played_character_gold": {
            "status": "available",
            "character_id": 27181,
            "gold_raw": before,
            "scale": 100_000,
        },
        "ending_played_character_gold": {
            "status": "available",
            "character_id": 27181,
            "gold_raw": after,
            "scale": 100_000,
        },
    }


class VanillaEventMaterialOutcomeTests(unittest.TestCase):
    def test_supported_choice_plans_same_frame_stress_expectation(self) -> None:
        expected = _expectation()

        self.assertEqual(expected["status"], "ready")
        self.assertEqual(expected["metric"], "played_character.stress_points")
        self.assertEqual(expected["expected_relation"], "non_increasing")
        self.assertEqual(expected["character_id"], 27181)
        self.assertEqual(expected["starting_value"], 42)

    def test_missing_structured_effect_profile_is_not_planned(self) -> None:
        decision = _decision()
        decision["choice_effect_profile"] = None

        self.assertIsNone(
            plan_registered_event_material_postcondition_v1(
                decision,
                {"character_id": 27181, "stress_points": 42},
                snapshot_id="native:19",
                revision=33,
            )
        )

    def test_missing_stress_is_typed_unavailable_and_unknown_event_is_ignored(
        self,
    ) -> None:
        unavailable = plan_registered_event_material_postcondition_v1(
            _decision(),
            {"character_id": 27181, "alive": True},
            snapshot_id="native:19",
            revision=33,
        )
        unsupported = plan_registered_event_material_postcondition_v1(
            _decision(event_key="other.0001"),
            {"character_id": 27181, "alive": True, "stress_points": 42},
            snapshot_id="native:19",
            revision=33,
        )

        self.assertEqual(unavailable["status"], "unavailable")
        self.assertEqual(
            unavailable["unavailable_reason"],
            "same_frame_player_stress_unavailable",
        )
        self.assertIsNone(unsupported)

    def test_decrease_is_material_and_zero_floor_is_not(self) -> None:
        changed = evaluate_registered_event_material_postcondition_v1(
            _expectation(), _selection(42, 27)
        )
        floor = evaluate_registered_event_material_postcondition_v1(
            _expectation(0), _selection(0, 0)
        )

        self.assertEqual(changed["status"], "verified_change")
        self.assertEqual(changed["delta"], -15)
        self.assertTrue(changed["relation_satisfied"])
        self.assertTrue(changed["material_change_observed"])
        self.assertEqual(floor["status"], "verified_no_change")
        self.assertTrue(floor["relation_satisfied"])
        self.assertFalse(floor["material_change_observed"])

    def test_increase_and_character_drift_fail(self) -> None:
        increased = evaluate_registered_event_material_postcondition_v1(
            _expectation(), _selection(42, 43)
        )
        drifted = evaluate_registered_event_material_postcondition_v1(
            _expectation(), _selection(42, 27, ending_character_id=27182)
        )

        self.assertEqual(increased["status"], "failed")
        self.assertEqual(increased["unavailable_reason"], "stress_increased")
        self.assertEqual(drifted["status"], "failed")
        self.assertEqual(
            drifted["unavailable_reason"],
            "same_character_snapshot_binding_mismatch",
        )

    def test_trait_gold_gain_is_planned_and_requires_a_strict_increase(
        self,
    ) -> None:
        expected = plan_registered_event_material_postcondition_v1(
            _decision(event_key="trait_specific.8001"),
            {"character_id": 27181, "alive": True},
            played_character_gold={"raw": 35_000_000, "scale": 100_000},
            snapshot_id="native:19",
            revision=33,
        )
        assert isinstance(expected, dict)

        increased = evaluate_registered_event_material_postcondition_v1(
            expected, _gold_selection(35_000_000, 50_000_000)
        )
        unchanged = evaluate_registered_event_material_postcondition_v1(
            expected, _gold_selection(35_000_000, 35_000_000)
        )
        decreased = evaluate_registered_event_material_postcondition_v1(
            expected, _gold_selection(35_000_000, 34_000_000)
        )

        self.assertEqual(expected["status"], "ready")
        self.assertEqual(expected["metric"], "played_character_gold.raw")
        self.assertEqual(expected["starting_value"], 35_000_000)
        self.assertEqual(increased["status"], "verified_change")
        self.assertEqual(increased["delta"], 15_000_000)
        self.assertTrue(increased["relation_satisfied"])
        self.assertEqual(unchanged["status"], "failed")
        self.assertEqual(unchanged["unavailable_reason"], "gold_not_increased")
        self.assertEqual(decreased["status"], "failed")
        self.assertEqual(decreased["unavailable_reason"], "gold_not_increased")

    def test_trait_gold_missing_snapshot_value_is_typed_unavailable(self) -> None:
        expected = plan_registered_event_material_postcondition_v1(
            _decision(event_key="trait_specific.8001"),
            {"character_id": 27181, "alive": True},
            snapshot_id="native:19",
            revision=33,
        )

        self.assertEqual(expected["status"], "unavailable")
        self.assertEqual(
            expected["unavailable_reason"],
            "same_frame_player_gold_unavailable",
        )

    def test_ready_expectation_preserves_failed_or_missing_result_as_runner_issue(
        self,
    ) -> None:
        expectation = _expectation()
        plan = {"event_material_postcondition": expectation}
        failed = evaluate_registered_event_material_postcondition_v1(
            expectation, _selection(42, 43)
        )

        self.assertEqual(
            _registered_event_material_postcondition_issue(
                plan, {"event_material_postcondition": failed}
            ),
            "failed",
        )
        self.assertEqual(
            _registered_event_material_postcondition_issue(plan, {}),
            "unavailable",
        )
        self.assertIsNone(
            _registered_event_material_postcondition_issue(
                {"event_material_postcondition": {"status": "unavailable"}},
                {},
            )
        )

    def test_service_attaches_evaluated_material_result(self) -> None:
        expectation = _expectation()
        snapshot = {
            "snapshot_id": "native:19",
            "revision": 33,
            "active_event": {
                "instance_id": 91,
                "option_count": 2,
                "options": [
                    {"option_number": 1, "enabled": True},
                    {"option_number": 2, "enabled": True},
                ],
            },
        }
        driver = CallbackGameplayDriver(
            backend_id="fixture",
            snapshot=lambda: snapshot,
            execute=lambda _step, _revision: {
                "accepted": True,
                "event_selection": _selection(42, 27),
            },
            action_steps=("select-event-option-2",),
        )
        service = GameplayBridgeService(driver)
        planned = {
            "snapshot_id": "native:19",
            "revision": 33,
            "plan": {
                "phase": "active_event_registry_choice",
                "selected_step": "select-event-option-2",
                "active_event": {"instance_id": 91},
                "event_material_postcondition": expectation,
            },
        }

        with mock.patch.object(service, "plan_turn", return_value=planned):
            outcome = service.auto_turn()

        self.assertEqual(outcome["status"], "executed")
        self.assertEqual(
            outcome["result"]["event_material_postcondition"]["status"],
            "verified_change",
        )


if __name__ == "__main__":
    unittest.main()
