"""Quiet-query cadence and durable consumption; every Native/OS boundary is synthetic."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge import ordinary_sway_quiet_observation_v1 as quiet
from xar_autoplayer.bridge.ordinary_sway_service_v1 import INPUT, STATE_FILE, project_ordinary_sway_input_v1
from xar_autoplayer.bridge.player_mercenary_context import STEP as MARKET_QUERY
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP as QUERY
from xar_autoplayer.ordinary_sway_schedule_v1 import plan_ordinary_sway_schedule_v1
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger

ACTOR, TARGET, INSTANCE, DATE = 7, 9, 134217986, 53288448


def seed(path):
    resolved = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": ACTOR, "target_character_id": TARGET,
        "action_id": "original-once", "post_native_revision": 5,
        "post_date_raw": DATE, "next_turn_consumed": True,
        "native_receipt": {
            "schema": "active-scheme-sway-formal-private-v1", "stage": "applied",
            "postcondition_verified": True, "action_id": "original-once",
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": 8,
            "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256,
        },
    }
    (path / LEDGER_FILE).write_text(json.dumps({"schema": SCHEMA, "pending": None, "resolved": resolved}), encoding="utf-8")


class SourceDriver:
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    def __init__(self, path):
        self.state_dir = path
        self.frame = {
            "snapshot_id": "quiet:7", "paused": True, "map_ready": True,
            "revision": 17, "native_revision": 7, "date_raw": DATE,
            "episode_run_id": "synthetic-original", "episode_character_id": ACTOR,
            "episode_identity_pending": False, "one_life_terminal_reason": None,
            "played_character": {"character_id": ACTOR, "alive": True},
            "active_context": {"active_event": None, "pending_character_interaction": None},
            "player_armies": [{"army_id": 10, "in_combat": False, "retreating": False}],
            "diagnostics": {"bridge_pid": 111, "connection_generation": 2},
        }
        self.calls = []
        self.value = 0
        self.terminal = self.fail = False

    def take_snapshot_without_native_command_history(self):
        self.calls.append("snapshot")
        return deepcopy(self.frame)

    def take_snapshot(self):
        return self.take_snapshot_without_native_command_history()

    def capabilities(self):
        return {"bridge_capabilities": []}

    def query_active_scheme_sway_completion_private_v1(self, **arguments):
        self.calls.append("completion")
        if arguments["expected_revision"] != self.frame["revision"]:
            raise ValueError("public revision required")
        if self.fail:
            raise BridgeUnavailableError("synthetic readonly failure")
        return {
            "schema": "xar.ck3.sway_completion.v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": 8,
            "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"], "date_raw": self.frame["date_raw"],
            "instance_source_observed": True, "instance_present": True,
            "storage_slot_reused": False, "exact_instance_join_ready": True,
            "owner_matches_actor": not self.terminal, "owner_cleared": self.terminal,
            "native_owner_raw": 0xFFFFFFFF if self.terminal else ACTOR,
            "native_status_observed": True, "native_status_raw": int(self.terminal),
            "native_status_key": "terminated_unattributed" if self.terminal else "continue",
            "native_terminal_state_observed": self.terminal,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def query_active_scheme_sway_outcome_opinion_private_v1(self, **arguments):
        self.calls.append("opinion")
        if arguments["expected_revision"] != self.frame["revision"]:
            raise ValueError("public revision required")
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"], "date_raw": self.frame["date_raw"],
            "target_opinion_of_actor": self.value,
            "scheme_sway_opinion": {"observed": True, "present": self.value != 0,
                                    "value": self.value if self.value != 0 else None},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        }


def planned(driver):
    frame = driver.frame
    return {
        "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "planning_source_frame": {
            "status": "complete", "actor_character_id": ACTOR,
            "episode_run_id": frame["episode_run_id"], "date_raw": frame["date_raw"],
            "bridge_pid": 111, "connection_generation": 2,
        },
        "plan": {"selected_step": QUERY, "phase": "native_war_army_strength_query"},
        INPUT: project_ordinary_sway_input_v1(frame, None),
    }


def executed(plan):
    return {"status": "executed", "selected_step": plan["plan"]["selected_step"],
            "plan": plan["plan"], "result": {"army_strengths": [], "status": "available"}}


def service(driver):
    value = object.__new__(GameplayBridgeService)
    value.driver = driver
    value._auto_camera_worker = SimpleNamespace(schedule=lambda _: {"status": "synthetic-no-presentation"})
    return value


def market_plan(driver):
    value = planned(driver)
    value["planning_source_frame"] = GameplayBridgeService._observed_planning_source_frame(driver.frame)
    value["plan"] = {"selected_step": MARKET_QUERY, "phase": "native_war_mercenary_query"}
    return value


def market_result(driver):
    frame = driver.frame
    return {
        "step": MARKET_QUERY, "status": "completed", "accepted": True, "read_only": True,
        "query_sequence": 1, "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "mercenary_query_source_frame_v1": observed_frame(frame),
        "player_mercenary_context": {
            "schema": "ck3_12004_player_mercenary_context_v1",
            "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
            "actor_character_id": ACTOR, "date_raw": frame["date_raw"], "capture_epoch": 1,
            "read_only": True, "native_hire_mode": 1, "available": True,
            "unavailable_reason": None, "rows": [],
        },
    }


class MarketDriver(SourceDriver):
    """Synthetic paused endpoint; no Native, Game or network connection."""
    def __init__(self, path):
        super().__init__(path)
        self.frame["diagnostics"]["hello"] = {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        }

    def execute_step(self, step, *, expected_revision=None):
        if step != MARKET_QUERY or expected_revision != self.frame["revision"]:
            raise AssertionError("only the original same-frame market read is executable")
        self.calls.append("original-market-query")
        return market_result(self)


class QuietObservationTests(unittest.TestCase):
    def test_market_full_auto_original_execution_then_named_gain_terminal_and_later_consumption(self):
        with tempfile.TemporaryDirectory(prefix="sway-market-") as temp:
            path = Path(temp)
            seed(path)
            driver = MarketDriver(path)
            cues = []
            # Only the planner input and Native endpoint are synthetic. The
            # original Service executor, before_submit and following consumers run.
            with patch.object(GameplayBridgeService, "_plan_turn_internal", lambda _: market_plan(driver)):
                first = service(driver).auto_turn(before_submit=lambda cue: cues.append(cue))
                self.assertEqual(cues[0]["plan"]["selected_step"], MARKET_QUERY)
                self.assertLess(driver.calls.index("original-market-query"), driver.calls.index("completion"))
                self.assertEqual(first["result"], market_result(driver))
                optional = first["ordinary_sway_optional"]
                self.assertEqual(optional["schedule_window"], "after_completed_ordinary_mercenary_query")
                self.assertFalse(optional["submit_attempted"])
                self.assertEqual(optional["new_game_days"], 0)
                self.assertFalse(read_sway_ledger(path)["resolved"]["material_intervention"]["next_turn_consumed"])
                for days, opinion, terminal in ((0, 0, False), (30, 25, False), (30, 25, True), (0, 25, True)):
                    driver.frame["date_raw"] += days * 24
                    driver.frame["revision"] += 1
                    driver.frame["native_revision"] += 1
                    driver.frame["snapshot_id"] = "market:" + str(driver.frame["native_revision"])
                    driver.value, driver.terminal = opinion, terminal
                    returned = service(driver).auto_turn()
                    self.assertEqual(returned["selected_step"], MARKET_QUERY)
                    if days == 30 and not terminal:
                        material = read_sway_ledger(path)["resolved"]["material_intervention"]
                        self.assertTrue(material["incremental_named_gain_observed"])
                        self.assertFalse(material["next_turn_consumed"])
                end = read_sway_ledger(path)["resolved"]["terminal_intervention"]
                self.assertTrue(end["instance_terminal_outcome_observed"])
                self.assertFalse(end["terminal_cause_observed"])
                self.assertTrue(end["next_turn_consumed"])
                gain_witness = read_sway_ledger(path)["resolved"]["first_named_gain_intervention"]
                self.assertTrue(gain_witness["incremental_named_gain_observed"])
                self.assertTrue(gain_witness["next_turn_consumed"])
                self.assertEqual(gain_witness["source_date_raw"], DATE + 30 * 24)
                self.assertEqual(gain_witness["baseline_source_date_raw"], DATE)
                self.assertEqual(driver.calls.count("original-market-query"), 5)
                self.assertEqual(driver.calls.count("completion"), 3)
                self.assertEqual(driver.frame["date_raw"], DATE + 60 * 24)

    def test_market_incomplete_envelope_foreign_frame_and_bad_native_context_preserve_original(self):
        with tempfile.TemporaryDirectory(prefix="sway-market-") as temp:
            path = Path(temp)
            seed(path)
            changes = (
                ("ack_only", lambda plan, result, frame: result.update(status="pending")),
                ("world_action", lambda plan, result, frame: result.update(read_only=False)),
                ("sequence_bool", lambda plan, result, frame: result.update(query_sequence=True)),
                ("other_phase", lambda plan, result, frame: plan["plan"].update(phase="native_war_mercenary_finance_query")),
                ("old_capture", lambda plan, result, frame: result["mercenary_query_source_frame_v1"].update(native_revision=6)),
                ("old_connection", lambda plan, result, frame: frame["diagnostics"].update(connection_generation=3)),
                ("wrong_actor", lambda plan, result, frame: result["player_mercenary_context"].update(actor_character_id=99)),
                ("wrong_build", lambda plan, result, frame: result["player_mercenary_context"].update(executable_sha256="0" * 64)),
                ("missing_native_rows", lambda plan, result, frame: result["player_mercenary_context"].pop("rows")),
                ("new_battle", lambda plan, result, frame: frame["player_armies"][0].update(in_combat=True)),
            )
            for name, change in changes:
                with self.subTest(name=name):
                    driver = MarketDriver(path)
                    plan, result = market_plan(driver), market_result(driver)
                    change(plan, result, driver.frame)
                    outcome = {"status": "executed", "selected_step": MARKET_QUERY, "result": result}
                    returned = quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome)
                    self.assertIs(returned, outcome)
                    self.assertNotIn("completion", driver.calls)
                    self.assertFalse((path / STATE_FILE).exists())

    def test_full_auto_original_query_first_monthly_durable_gain_terminal_and_later_consume(self):
        with tempfile.TemporaryDirectory(prefix="sway-quiet-") as temp:
            path = Path(temp)
            seed(path)
            driver = SourceDriver(path)

            def ordinary_plan(_):
                return planned(driver)

            def ordinary_execute(_, plan, **kwargs):
                driver.calls.append("original-war-query")
                driver.frame["revision"] += 1
                driver.frame["native_revision"] += 1
                driver.frame["snapshot_id"] = "quiet:" + str(driver.frame["native_revision"])
                return executed(plan)

            with patch.object(GameplayBridgeService, "_plan_turn_internal", ordinary_plan), \
                 patch.object(GameplayBridgeService, "_execute_planned_turn", ordinary_execute):
                first = service(driver).auto_turn()
                self.assertLess(driver.calls.index("original-war-query"), driver.calls.index("completion"))
                self.assertEqual(first["selected_step"], QUERY)
                self.assertEqual(first["ordinary_sway_optional"]["job"], "observe_applied")
                self.assertFalse(first["ordinary_sway_optional"]["submit_attempted"])
                baseline = read_sway_ledger(path)["resolved"]["material_intervention"]
                self.assertFalse(baseline["next_turn_consumed"])
                driver.calls.clear()
                # A newly constructed Service must retain the persisted monthly cadence.
                second = service(driver).auto_turn()
                self.assertNotIn("completion", driver.calls)
                self.assertTrue(second["sway_following_turn"]["material_intervention"]["next_turn_consumed"])
                driver.frame["date_raw"] += 30 * 24
                driver.value = 25
                gain = service(driver).auto_turn()
                material = read_sway_ledger(path)["resolved"]["material_intervention"]
                self.assertTrue(material["incremental_named_gain_observed"])
                self.assertFalse(material["next_turn_consumed"])
                self.assertEqual(gain["selected_step"], QUERY)
                driver.frame["date_raw"] += 30 * 24
                driver.terminal = True
                terminal = service(driver).auto_turn()
                end = read_sway_ledger(path)["resolved"]["terminal_intervention"]
                self.assertTrue(end["instance_terminal_outcome_observed"])
                self.assertFalse(end["terminal_cause_observed"])
                self.assertFalse(end["next_turn_consumed"])
                driver.calls.clear()
                after = service(driver).auto_turn()
                self.assertNotIn("completion", driver.calls)
                self.assertTrue(after["sway_following_turn"]["terminal_intervention"]["next_turn_consumed"])
                self.assertEqual(driver.frame["date_raw"], DATE + 60 * 24)

    def test_pending_empty_terminal_and_foreign_never_start_or_reconcile_in_quiet_mode(self):
        frame = SourceDriver(Path("unused")).frame
        for ledger in ({"pending": None, "resolved": None},
                       {"pending": {"actor_character_id": ACTOR}, "resolved": None},
                       {"resolved": {"status": "applied", "postcondition_verified": True,
                                     "actor_character_id": 88, "target_character_id": TARGET}},
                       {"resolved": {"status": "applied", "postcondition_verified": True,
                                     "actor_character_id": ACTOR, "target_character_id": TARGET,
                                     "terminal_intervention": {"instance_terminal_outcome_observed": True}}}):
            with self.subTest(ledger=ledger):
                job = plan_ordinary_sway_schedule_v1(frame, selected_step=QUERY,
                                                     ledger=ledger, active_observation_only=True)
                self.assertIsNone(job["job"])

    def test_empty_pending_or_disabled_observer_never_takes_native_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="sway-quiet-") as temp:
            path = Path(temp)
            driver = SourceDriver(path)
            plan = planned(driver)
            outcome = executed(plan)
            self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            seed(path)
            ledger = read_sway_ledger(path)
            ledger["pending"] = {"actor_character_id": ACTOR, "target_character_id": TARGET}
            (path / LEDGER_FILE).write_text(json.dumps(ledger), encoding="utf-8")
            self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            seed(path)
            driver.allow_private_active_scheme_sway_completion_query = False
            driver.allow_private_active_scheme_sway_outcome_opinion_query = False
            self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            self.assertFalse(driver.calls)

    def test_critical_or_changed_postframe_skips_reads_and_preserves_original_result(self):
        with tempfile.TemporaryDirectory(prefix="sway-quiet-") as temp:
            path = Path(temp)
            seed(path)
            driver = SourceDriver(path)
            original = deepcopy(driver.frame)
            for update in ({"paused": False}, {"episode_identity_pending": True},
                           {"player_armies": [{"in_combat": True, "retreating": False}]},
                           {"player_armies": [{"in_combat": False, "retreating": True}]},
                           {"top_exclusive_modal_choice_hint": {"status": "present"}},
                           {"active_context": {"active_event": {"instance_id": 1}, "pending_character_interaction": None}},
                           {"played_character": {"character_id": 88, "alive": True}},
                           {"diagnostics": {"bridge_pid": 112, "connection_generation": 2}},
                           {"date_raw": DATE + 24}, {"episode_run_id": "another-episode"}):
                with self.subTest(update=update):
                    driver.frame = deepcopy(original)
                    plan = planned(driver)
                    outcome = executed(plan)
                    driver.frame.update(update)
                    returned = quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome)
                    self.assertIs(returned, outcome)
                    self.assertNotIn("completion", driver.calls)
                    self.assertFalse((path / STATE_FILE).exists())

    def test_other_war_phases_actions_and_existing_optional_do_no_extra_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="sway-quiet-") as temp:
            path = Path(temp)
            seed(path)
            driver = SourceDriver(path)
            for phase, step in (("native_war_siege_continuation_native_army_query", QUERY),
                                ("native_war_battle_control", "retreat-army-10"),
                                ("native_war_route_contact_horizon_progress", "advance-route-contact-horizon-v1"),
                                ("native_war_stationary_objective_hold_sentinel", "life-advance")):
                plan = planned(driver)
                plan["plan"].update(phase=phase, selected_step=step)
                outcome = executed(plan)
                self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            plan = planned(driver)
            outcome = {**executed(plan), "ordinary_sway_optional": {"job": "observe_applied"}}
            self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            outcome = executed(plan)
            outcome["result"]["status"] = "unavailable"
            self.assertIs(quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome), outcome)
            self.assertFalse(driver.calls)

    def test_failure_retains_completed_query_and_cadence_does_not_retry_same_day(self):
        with tempfile.TemporaryDirectory(prefix="sway-quiet-") as temp:
            path = Path(temp)
            seed(path)
            driver = SourceDriver(path)
            driver.fail = True
            plan = planned(driver)
            outcome = executed(plan)
            first = quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome)
            self.assertEqual(first["result"], outcome["result"])
            self.assertEqual(first["ordinary_sway_optional"]["result"]["status"], "query_failed")
            self.assertEqual(driver.calls.count("completion"), 1)
            driver.calls.clear()
            second = quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome)
            self.assertIs(second, outcome)
            self.assertFalse(driver.calls)
            # Even an optional storage failure cannot invalidate the war result.
            with patch.object(quiet, "_inputs", side_effect=OSError("synthetic disk read")):
                third = quiet.observe_sway_after_quiet_query_v1(service(driver), plan, outcome)
            self.assertEqual(third["result"], outcome["result"])
            self.assertFalse(third["ordinary_sway_optional"]["request_retried"])


if __name__ == "__main__":
    unittest.main()
