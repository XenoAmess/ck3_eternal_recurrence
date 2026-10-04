"""Contract-derived finite vectors for the independent current-Siege module.

All nonempty Siege IDs and tick/event operands here are synthetic fixtures.
Expected integer values are literals derived from the sealed .3 native contract,
not from production helpers. No SDK, pipe, native callback, or game is invoked.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.siege_current_tick import (
    adapt_current_siege_condition,
    ceil_fixed_nonnegative,
    fixed_mul,
    main,
    ordinary_daily_work_from_terms,
    phase_length_from_terms,
    run_current_siege_tick,
)


def _phase_terms(actor: int = -10000, breach: int = 0) -> dict[str, int]:
    return {
        "breach_adjust_raw": breach,
        "siege_phase_time_modifier_raw": actor,
        "siege_cached_phase_time_modifier_raw": 0,
        "province_phase_time_modifier_raw": 0,
    }


def _holding(current: int = 1000000, total: int = 5000000) -> dict:
    return {
        "province_id": 472,
        "holding_title_id": 1359,
        "siege_observable": True,
        "active_siege": {
            "siege_id": 603001,
            "current_work": {"raw": current, "scale": 100000},
            "total_work": {"raw": total, "scale": 100000},
            "days_left": 80,
            "assault_in_progress": False,
        },
    }


def _operands(**changes) -> dict:
    operands = {
        "siege_id": 603001,
        "province_id": 472,
        "internal_besieging_army_id": 501001,
        "actual_siege_commander_id": 34867,
        "native_can_advance": True,
        "ordinary_daily_work_raw": 50000,
        "phase_counter": 5,
        "phase_terms": _phase_terms(),
    }
    operands.update(changes)
    return operands


def _run(holding: dict | None = None, operands: dict | None = None) -> dict:
    return run_current_siege_tick(adapt_current_siege_condition(
        holding if holding is not None else _holding(),
        tick_operands=operands if operands is not None else _operands(),
        snapshot_revision=64,
        observed_date_raw=53251272,
    ))


class CurrentSiegeTickTests(unittest.TestCase):
    def test_signed_stepwise_multiplication_and_final_daily_clamp(self) -> None:
        self.assertEqual(fixed_mul(-150001, 50000), -75000)
        self.assertEqual(fixed_mul(150001, -50000), -75000)
        self.assertEqual(fixed_mul(111111, 123457), 137174)
        self.assertEqual(ordinary_daily_work_from_terms(
            army_progress_raw=11111,
            maa_progress_raw=0,
            excess_strength_progress_raw=0,
            conditional_additive_raw=0,
            daily_multiplier_raw=123457,
            fort_factor_raw=70000,
        ), 96021)
        for army, fort in ((-100000, 100000), (-110000, 100000), (0, 10000)):
            with self.subTest(army=army, fort=fort):
                self.assertEqual(ordinary_daily_work_from_terms(
                    army_progress_raw=army,
                    maa_progress_raw=0,
                    excess_strength_progress_raw=0,
                    conditional_additive_raw=0,
                    daily_multiplier_raw=100000,
                    fort_factor_raw=fort,
                ), 50000)

    def test_phase_aggregate_once_add_before_multiply_clamp_and_ceil(self) -> None:
        vectors = (
            (0, 0, 100000, 2000000, 20),
            (-10000, 0, 90000, 1800000, 18),
            (-10000, -10000, 80000, 1600000, 16),
            (-10001, 0, 89999, 1799980, 18),
            (1, 0, 100001, 2000020, 21),
            (-100001, 0, 0, 0, 0),
        )
        for actor, breach, factor, length, threshold in vectors:
            with self.subTest(actor=actor, breach=breach):
                actual = phase_length_from_terms(_phase_terms(actor, breach))
                self.assertEqual(actual["status"], "available")
                self.assertEqual(actual["phase_factor_raw"], factor)
                self.assertEqual(actual["phase_length_raw"], length)
                self.assertEqual(actual["phase_threshold"], threshold)
                self.assertEqual(ceil_fixed_nonnegative(length), threshold)
        incomplete = _phase_terms()
        del incomplete["siege_cached_phase_time_modifier_raw"]
        actual = phase_length_from_terms(incomplete)
        self.assertEqual(actual["status"], "unavailable")
        self.assertIsNone(actual["phase_length_raw"])

    def test_cached_p472_no_current_siege_cannot_create_tick(self) -> None:
        condition = adapt_current_siege_condition({
            "province_id": 472,
            "holding_title_id": 1359,
            "siege_observable": True,
            "active_siege": None,
        }, snapshot_revision=64, observed_date_raw=53251272,
            commander_phase_observation={
                "character_id": 34867,
                "siege_phase_time_modifier_raw": -10000,
            })
        actual = run_current_siege_tick(condition)
        self.assertEqual(actual["status"], "not_applicable")
        self.assertEqual(actual["reason"], "no_current_siege")
        self.assertIsNone(actual["observed_frame"].get("siege_id"))
        self.assertNotIn("bound_current_besieger", actual)
        self.assertNotIn("projected_work_raw", actual)
        self.assertNotIn("breach_level", actual)
        self.assertIsNone(actual["completion_date_prediction"])

    def test_unobserved_siege_is_unavailable_not_observed_absent(self) -> None:
        actual = _run({
            "province_id": 472,
            "holding_title_id": 1359,
            "siege_observable": None,
            "active_siege": None,
        })
        self.assertEqual(actual["status"], "unavailable")
        self.assertEqual(actual["missing_inputs"], ["holding_row.siege_observable"])
        self.assertNotEqual(actual.get("reason"), "no_current_siege")
        self.assertNotIn("projected_work_raw", actual)

    def test_current_eta_does_not_set_tick_or_completion_deadline(self) -> None:
        for eta in (1, 999, None):
            with self.subTest(eta=eta):
                holding = _holding()
                holding["active_siege"]["days_left"] = eta
                actual = _run(holding)
                self.assertEqual(actual["status"], "projected")
                self.assertEqual(actual["observed_native_eta_days"], eta)
                self.assertEqual(actual["eta_interpretation"], "current_native_estimate_only")
                self.assertEqual(actual["projected_work_raw"], 1050000)
                self.assertEqual(actual["projected_phase_counter"], 6)
                self.assertIsNone(actual["completion_date_prediction"])
                self.assertFalse(actual["actual_next_draw_claimed"])
                self.assertFalse(actual["complete_transition"])

    def test_same_active_siege_native_fields_map_without_supplied_operands(self) -> None:
        holding = _holding()
        holding["active_siege"].update(
            ordinary_daily_progress={"raw": 96021, "scale": 100000},
            current_phase_length={"raw": 1799980, "scale": 100000},
            prepared_phase_length={"raw": 2000000, "scale": 100000},
            phase_counter=16,
            can_advance=True,
            besieging_army_id=83886367,
            assault_in_progress=None,
        )
        actual = run_current_siege_tick(adapt_current_siege_condition(
            holding, snapshot_revision=64, observed_date_raw=53251272,
        ))
        self.assertEqual(actual["operand_origin"], "observed_active_siege_native_fields")
        self.assertEqual(actual["status"], "projected")
        self.assertEqual(actual["ordinary_daily_work_raw"], 96021)
        self.assertEqual(actual["current_phase_length_raw"], 1799980)
        self.assertEqual(actual["observed_prepared_phase_length"]["raw"], 2000000)
        self.assertEqual(actual["phase_threshold"], 18)
        self.assertFalse(actual["phase_due"])
        self.assertEqual(actual["projected_work_raw"], 1096021)
        self.assertEqual(actual["projected_phase_counter"], 17)
        self.assertEqual(actual["bound_current_besieger"]["besieging_army_id"], 83886367)
        self.assertIsNone(actual["observed_assault_in_progress"])
        holding["active_siege"].update(
            current_phase_length={"raw": 0, "scale": 100000},
            phase_counter=0,
            can_advance=False,
        )
        blocked = run_current_siege_tick(adapt_current_siege_condition(holding))
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["projected_work_raw"], 1000000)
        self.assertEqual(blocked["projected_phase_counter"], 0)
        holding["active_siege"]["can_advance"] = True
        zero_length = run_current_siege_tick(adapt_current_siege_condition(holding))
        self.assertEqual(zero_length["status"], "event_pending")
        self.assertEqual(zero_length["current_phase_length_raw"], 0)
        self.assertEqual(zero_length["phase_threshold"], 0)
        self.assertEqual(zero_length["phase_counter_before"], 0)

    def test_missing_native_inputs_stay_gaps_without_cached_or_history_fill(self) -> None:
        for field in ("ordinary_daily_progress", "current_phase_length", "phase_counter", "can_advance"):
            with self.subTest(field=field):
                holding = _holding()
                holding["active_siege"].update(
                    ordinary_daily_progress={"raw": 50000, "scale": 100000},
                    current_phase_length={"raw": 1800000, "scale": 100000},
                    prepared_phase_length={"raw": 2000000, "scale": 100000},
                    phase_counter=5,
                    can_advance=True,
                )
                holding["active_siege"][field] = None
                actual = run_current_siege_tick(adapt_current_siege_condition(
                    holding,
                    commander_phase_observation={
                        "character_id": 34867,
                        "siege_phase_time_modifier_raw": -10000,
                    },
                ))
                self.assertEqual(actual["status"], "unavailable")
                self.assertIn("active_siege." + field, actual["missing_inputs"])
                self.assertNotIn("normal_applied_work_raw", actual)
                self.assertIsNone(actual["completion_date_prediction"])
        holding["active_siege"]["can_advance"] = True
        separate = run_current_siege_tick(adapt_current_siege_condition(holding, tick_operands={}))
        self.assertEqual(separate["operand_origin"], "explicit_caller_supplied")
        self.assertEqual(separate["status"], "unavailable")
        self.assertEqual(separate["missing_inputs"], ["native_can_advance"])

    def test_actor_change_keeps_counter_and_same_normal_daily_work(self) -> None:
        before = _run(operands=_operands(phase_counter=17, phase_terms=_phase_terms(0)))
        after = _run(operands=_operands(phase_counter=17, phase_terms=_phase_terms(-10000)))
        self.assertEqual(before["phase_counter_before"], 17)
        self.assertEqual(after["phase_counter_before"], 17)
        self.assertEqual(before["phase_threshold"], 20)
        self.assertEqual(after["phase_threshold"], 18)
        self.assertFalse(before["phase_due"])
        self.assertTrue(after["phase_due"])
        self.assertEqual(before["ordinary_daily_work_raw"], 50000)
        self.assertEqual(after["ordinary_daily_work_raw"], 50000)
        self.assertEqual(before["normal_applied_work_raw"], 1050000)
        self.assertEqual(after["normal_applied_work_raw"], 1050000)
        self.assertEqual(after["status"], "event_pending")
        self.assertIsNone(after["projected_work_raw"])
        self.assertIsNone(after["projected_phase_counter"])
        self.assertNotIn("conditional_supplied_event", after)

    def test_normal_completion_clamps_and_skips_due_starvation(self) -> None:
        operands = _operands(
            phase_counter=17,
            ordinary_daily_work_raw=100000,
            selected_event_raw=1,
            starvation_level=0,
            event_total_work_raw=1000000,
        )
        actual = _run(_holding(990000, 1000000), operands)
        self.assertTrue(actual["phase_due"])
        self.assertEqual(actual["prepared_next_work_raw"], 1090000)
        self.assertEqual(actual["projected_work_raw"], 1000000)
        self.assertTrue(actual["normal_completion"])
        self.assertTrue(actual["event_skipped_due_to_normal_completion"])
        self.assertEqual(actual["projected_phase_counter"], 18)
        self.assertNotIn("conditional_supplied_event", actual)
        self.assertEqual(operands["starvation_level"], 0)

    def test_blocked_keeps_work_counter_and_stops_active_assault(self) -> None:
        holding = _holding()
        holding["active_siege"]["assault_in_progress"] = True
        actual = _run(holding, _operands(native_can_advance=False, phase_counter=17))
        self.assertEqual(actual["status"], "blocked")
        self.assertEqual(actual["projected_work_raw"], 1000000)
        self.assertEqual(actual["projected_phase_counter"], 17)
        self.assertFalse(actual["normal_work_applied"])
        self.assertTrue(actual["native_stops_active_assault"])

    def test_selected_starvation_uses_new_level_after_D_and_event_cap(self) -> None:
        actual = _run(_holding(1000000, 30000000), _operands(
            phase_counter=17,
            ordinary_daily_work_raw=69433,
            selected_event_raw=1,
            starvation_level=0,
            event_total_work_raw=30000000,
        ))
        self.assertEqual(actual["normal_applied_work_raw"], 1069433)
        self.assertEqual(actual["conditional_supplied_event"]["new_level"], 1)
        self.assertEqual(actual["conditional_supplied_event"]["extra_work_raw"], 1500000)
        self.assertEqual(actual["projected_work_raw"], 2569433)
        self.assertEqual(actual["projected_phase_counter"], 0)
        capped = _run(_holding(850000, 1000000), _operands(
            phase_counter=17,
            ordinary_daily_work_raw=100000,
            selected_event_raw=1,
            starvation_level=1,
            event_total_work_raw=1000000,
        ))
        self.assertEqual(capped["conditional_supplied_event"]["new_level"], 2)
        self.assertEqual(capped["conditional_supplied_event"]["extra_work_raw"], 150000)
        self.assertEqual(capped["projected_work_raw"], 1000000)
        self.assertEqual(capped["actual_post_event_completion"], "unknown_dynamic_total_not_replayed")

    def test_other_selected_events_keep_prepared_D_and_future_effects_separate(self) -> None:
        vectors = (
            (0, {"breach_level": 0}, 1050000, "next_breach_adjust_raw", -10000),
            (0, {"breach_level": 1}, 1050000, "next_breach_adjust_raw", -30000),
            (2, {"disease_level": 0}, 1050000, "future_daily_multiplier_addition_raw", 10000),
            (2, {"disease_level": 1}, 1050000, "future_daily_multiplier_addition_raw", 20000),
            (3, {"event_total_work_raw": 1300000}, 1300000, "extra_work_raw", 500000),
            (4, {}, 1050000, "extra_work_raw", 0),
        )
        for enum, event_inputs, work, detail, expected in vectors:
            with self.subTest(enum=enum, inputs=event_inputs):
                actual = _run(operands=_operands(phase_counter=17, selected_event_raw=enum, **event_inputs))
                self.assertEqual(actual["normal_applied_work_raw"], 1050000)
                self.assertEqual(actual["ordinary_daily_work_raw"], 50000)
                self.assertEqual(actual["projected_work_raw"], work)
                self.assertEqual(actual["projected_phase_counter"], 0)
                self.assertEqual(actual["conditional_supplied_event"][detail], expected)
                self.assertEqual(actual["conditional_supplied_event"]["selection_origin"], "explicit_caller_supplied")
                self.assertFalse(actual["actual_next_draw_claimed"])

    def test_file_only_cli_preserves_no_current_siege_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "baseline.json"
            output_path = Path(directory) / "projection.json"
            input_path.write_text(json.dumps({
                "holding_row": {
                    "province_id": 472,
                    "holding_title_id": 1359,
                    "siege_observable": True,
                    "active_siege": None,
                },
                "snapshot_revision": 64,
                "observed_date_raw": 53251272,
            }), encoding="utf-8")
            self.assertEqual(main([str(input_path), "--output", str(output_path)]), 0)
            actual = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(actual["reason"], "no_current_siege")
            self.assertEqual(actual["observed_frame"]["province_id"], 472)
            self.assertEqual(actual["observed_frame"]["holding_title_id"], 1359)
            self.assertIsNone(actual["observed_frame"].get("siege_id"))
            self.assertIsNone(actual["completion_date_prediction"])


if __name__ == "__main__":
    unittest.main()
