"""Exactly two native-contract cases for caller-conditioned phase events.

Numbers and identities are synthetic fixtures. The independently calculated
expectations do not come from production helpers. These tests never call CK3.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.siege_current_phase_event import (
    CurrentPhaseEventState,
    PhaseEvent,
    PhaseEventStep,
    apply_current_phase_event,
    main,
    stock_phase_event_rules,
)


class CurrentPhaseEventTests(unittest.TestCase):
    def test_selected_starvation_new_level_dynamic_totals_no_post_reclamp(self) -> None:
        state = CurrentPhaseEventState(
            current_work_raw=1000000,
            phase_counter=17,
            breach_level=0,
            starvation_level=1,
            disease_level=0,
            desertion_count=0,
            stalemate_count=0,
        )
        step = PhaseEventStep(
            can_advance=True,
            normal_prepared_work_raw=1050000,
            total_apply_raw=5000000,
            phase_due=True,
            selected_event=PhaseEvent.STARVATION,
            total_event_raw=6000000,
            total_post_raw=1500000,
        )
        actual = apply_current_phase_event(state, step, rules=stock_phase_event_rules())
        # NEW level2 chooses supplied15%; 60*0.15=9 work, 10.5+9=19.5.
        # T_post15 only compares; it must not rewrite work from19.5 to15.
        self.assertEqual(actual["status"], "conditional_event_applied")
        self.assertEqual(actual["normal_applied_work_raw"], 1050000)
        self.assertEqual(actual["state_after_level_increment"]["starvation_level"], 2)
        self.assertEqual(actual["state_after_level_increment"]["current_work_raw"], 1050000)
        self.assertEqual(actual["state_after_level_increment"]["phase_counter"], 18)
        self.assertEqual(actual["event_bonus_raw"], 900000)
        self.assertEqual(actual["work_after_raw"], 1950000)
        self.assertEqual(actual["state_after"]["current_work_raw"], 1950000)
        self.assertEqual(actual["state_after"]["starvation_level"], 2)
        self.assertEqual(actual["state_after"]["phase_counter"], 0)
        self.assertEqual(actual["total_post_raw"], 1500000)
        self.assertTrue(actual["completion"])
        self.assertFalse(actual["post_total_reclamped_work"])
        self.assertEqual(actual["selected_event"], 1)
        self.assertEqual(actual["selection_origin"], "explicit_caller_selected")
        self.assertEqual(actual["rules_origin"], "conditional_installed_stock_12003_not_runtime_effective")
        self.assertFalse(actual["actual_selected_event_claimed"])
        self.assertFalse(actual["complete_transition"])
        self.assertIsNone(actual["completion_date_prediction"])
        self.assertEqual(state.starvation_level, 1)

    def test_due_unknown_file_cli_does_not_substitute_prepared_breach_cache(self) -> None:
        # This FullSiege ID is fixture-only; P472's real cached baseline is empty.
        value = {
            "input_origin": "synthetic_offline_fixture_not_current_P472",
            "holding_row": {
                "province_id": 472,
                "holding_title_id": 1359,
                "siege_observable": True,
                "active_siege": {
                    "siege_id": 603001,
                    "current_work": {"raw": 1000000, "scale": 100000},
                    "phase_counter": 17,
                    "phase_event_state": {
                        "breach_level": 0,
                        "starvation_level": 1,
                        "disease_level": 0,
                        "desertion_count": 0,
                        "stalemate_count": 0,
                    },
                    "prepared_selected_phase_event_enum": 0,
                },
            },
            "step": {
                "can_advance": True,
                "normal_prepared_work_raw": 1050000,
                "total_apply_raw": 5000000,
                "phase_due": True,
                "selected_event": None,
                "total_event_raw": None,
                "total_post_raw": 5000000,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "conditional-input.json"
            output_path = Path(directory) / "conditional-output.json"
            input_path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(main([str(input_path), "--output", str(output_path)]), 0)
            rendered = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(len(rendered["steps"]), 1)
        self.assertEqual(rendered["prepared_selected_phase_event_enum"], 0)
        self.assertEqual(rendered["prepared_selection_interpretation"], "last_prepare_cache_not_implicit_future_draw")
        actual = rendered["steps"][0]
        self.assertEqual(actual["status"], "event_pending")
        self.assertEqual(actual["first_input_gap"], "caller_selected_event")
        self.assertEqual(actual["normal_applied_work_raw"], 1050000)
        self.assertEqual(actual["state_after_normal"]["phase_counter"], 18)
        self.assertEqual(actual["state_after_normal"]["breach_level"], 0)
        self.assertIsNone(actual["state_after"])
        self.assertIsNone(actual["completion"])
        self.assertNotIn("selected_event", actual)
        self.assertFalse(actual["event_applied"])
        self.assertFalse(actual["actual_selected_event_claimed"])
        self.assertEqual(actual["selection_origin"], "unknown")
        self.assertEqual(actual["rules_origin"], "unknown")
        self.assertIsNone(actual["completion_date_prediction"])


if __name__ == "__main__":
    unittest.main()
