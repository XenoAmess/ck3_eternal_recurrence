from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.combat_core import DrawState, TrialRandomStreams, TrialResult
from xar_autoplayer.simulation.phase_event_evaluator import PhaseEventEvaluationError
from xar_autoplayer.simulation.phase_event_feedback import (
    PhaseEventFeedbackInput,
    PhaseEventFeedbackResearchKernel,
)


def _commander_context() -> dict[str, object]:
    fixture = Path(__file__).with_name(
        "test_combat_phase_inputs_v3_production_contract.py"
    )
    spec = importlib.util.spec_from_file_location("_xar_phase_v3_builder", fixture)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload, scope = module._production_payload()
    normalized = module._normalize(payload, scope)
    return next(
        context
        for context in normalized["phase_event_inputs"]["evaluation_contexts"]
        if context["phase_roles"] == ["commander"]
    )


class PhaseEventFeedbackKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = _commander_context()
        cls.day0 = (-cls.context["root_character_id"]) % 5

    def test_positive_effect_refreshes_next_due_day_then_empty_consumes_selection(self) -> None:
        # Salt 21 selects wounded (12/1016) and then the 1000-weight
        # commander_none on this pinned production-shaped context.
        initial = PhaseEventFeedbackInput(
            self.context,
            role="commander",
            start_day_index=self.day0,
            effect_draws_by_day={
                self.day0: {"commander_wounded": (0, 0)},
            },
        )
        kernel = PhaseEventFeedbackResearchKernel()
        result = kernel.project_trial(
            initial, selection_state=DrawState(0, 21), horizon_days=6
        )
        first, last = result.days[0], result.days[-1]
        self.assertEqual(first["selected_candidate_key"], "commander_wounded")
        self.assertEqual(first["executable_event_key"], "commander_wounded")
        self.assertNotEqual(first["before_state_sha256"], first["after_state_sha256"])
        self.assertEqual(last["selected_candidate_key"], "commander_none")
        self.assertIsNone(last["executable_event_key"])
        self.assertEqual(last["before_state_sha256"], last["after_state_sha256"])
        self.assertEqual(first["after_state_sha256"], last["before_state_sha256"])
        self.assertEqual(result.final_state["root"]["wounded_rank_raw"], 100_000)
        self.assertEqual(dict(first["weights_source_order"])["commander_killed"], 0)
        self.assertEqual(dict(last["weights_source_order"])["commander_killed"], 2)
        self.assertEqual(result.selection_state.counter, 2)
        self.assertTrue(all(not day["due"] for day in result.days[1:-1]))
        self.assertFalse(result.planner_usable)
        self.assertFalse(result.active_attack_allowed)
        self.assertFalse(kernel.manifest.fidelity_gate)

    def test_missing_selected_effect_tape_fails_before_fake_feedback(self) -> None:
        initial = PhaseEventFeedbackInput(
            self.context,
            role="commander",
            start_day_index=self.day0,
            effect_draws_by_day={},
        )
        with self.assertRaisesRegex(PhaseEventEvaluationError, "missing effect draw tape"):
            PhaseEventFeedbackResearchKernel().project_trial(
                initial, selection_state=DrawState(0, 21), horizon_days=1
            )

    def test_battle_transition_protocol_remains_no_resolution(self) -> None:
        initial = PhaseEventFeedbackInput(
            self.context,
            role="commander",
            start_day_index=self.day0,
            effect_draws_by_day={
                self.day0: {"commander_wounded": (0, 0)},
            },
        )
        outcome = PhaseEventFeedbackResearchKernel().simulate_trial(
            initial,
            streams=TrialRandomStreams(DrawState(0, 0), DrawState(0, 21)),
            horizon_days=6,
        )
        self.assertIs(outcome.result, TrialResult.NO_RESOLUTION)
        self.assertEqual((outcome.player_hard_loss_raw, outcome.enemy_hard_loss_raw), (0, 0))


if __name__ == "__main__":
    unittest.main()
