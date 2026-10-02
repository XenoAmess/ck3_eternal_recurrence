"""No-launch Stage5 Start holds, single-submit pending and material recovery."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.activity_feast_stage5_start_formal_consumer import (
    assess_feast_start_private_v1, consume_feast_start_private_v1,
    consume_feast_start_following_turn, read_feast_start_ledger,
    reconcile_feast_start_private_v1, reconcile_feast_lifecycle_private_v1,
)
from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_SCHEMA, POST_SCHEMA, START_STEP,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003


def inputs() -> dict[str, object]:
    return {
        "schema": INPUT_SCHEMA, "snapshot_revision": 3,
        "queried_revision": 5, "queried_snapshot_id": "native:3",
        "date_raw": 53219928, "actor_character_id": 29829,
        "activity_key": "activity_feast", "selected_option_key": "feast_type_generic",
        "planning_stage": 5, "final_can_start": True,
        "native_guest_route_qualified": False,
        "guest_join_status": "guest_source_unavailable",
        "selected_nonhost_count": None,
        "positive_join_count": None,
        "timely_positive_join_count": None,
        "arrival_time_observed": False,
        "resources": {
            key: {"resource_index": i, "configured_cost_raw": 1_000_000 if i == 0 else 0}
            for i, key in enumerate(("gold", "treasury", "piety", "barter_goods"))
        },
        "balances": {
            "gold": {"available": True, "raw": 120_000_000},
            "treasury": {"available": False, "raw": None},
            "piety": {"available": False, "raw": None},
            "barter_goods": {"available": False, "raw": None},
        },
        "hosted_activities": [],
    }


def guest() -> dict[str, object]:
    return {"status": "observed", "arrival_time_observed": True,
            "same_frame": True, "snapshot_revision": 3, "date_raw": 53219928,
            "actor_character_id": 29829, "timely_positive_join_count": 1}


def budget() -> dict[str, object]:
    return {"reserved_raw": dict.fromkeys(
                ("gold", "treasury", "piety", "barter_goods"), 0),
            "peaceful_spend_allowed": True, "gold_floor_raw": 20_000_000,
            "active_war_count": 0, "war_cash_reserve_raw": None}


class Driver:
    allow_private_activity_feast_stage5_start_action = True
    allow_private_activity_feast_stage5_start_query = True

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.endpoint = self
        self.state = self
        self.sent: list[dict[str, object]] = []
        self.fail_submit = False
        self.fail_post = False
        self.native_revision = 3
        self.date_raw = 53219928
        self.actor_character_id = 29829
        self.native_build_12002 = False
        self.post = {
            "schema": POST_SCHEMA, "snapshot_revision": 4,
            "date_raw": 53219928, "actor_character_id": 29829,
            "balances": {
                **inputs()["balances"],
                "gold": {"available": True, "raw": 119_000_000},
            },
            "hosted_activities": [{
                "activity_id": 77, "activity_type_key": "activity_feast",
                "host_character_id": 29829,
            }],
            "read_only": True, "advertised": False,
        }
        self.after_submit = False

    def take_snapshot(self) -> dict[str, object]:
        revision = self.native_revision + 1 if self.after_submit else self.native_revision
        snapshot = {"snapshot_id": f"native:{revision}",
                "revision": 6 if self.after_submit else 5,
                "native_revision": revision, "date_raw": self.date_raw,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": self.actor_character_id, "alive": True}}
        if self.native_build_12002:
            snapshot["diagnostics"] = {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }}
        return snapshot

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["life-advance"], "bridge_capabilities": []}

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        step = self.sent[-1]["step"]
        if step == START_STEP:
            if self.fail_submit:
                raise BridgeUnavailableError("submit timeout")
            self.after_submit = True
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True,
                    "result": {"step": step, "accepted": True,
                               "status": "pending", "private_build": True,
                               "read_only": False, "advertised": False,
                               "backend_id": "native-headless",
                               "activity_feast_stage5_start": {
                                   "schema": "activity-feast-stage5-start-private-action-v1",
                                   "submitted": True, "native_status": "submitted_pending",
                                   "precondition": inputs()}}}
        if self.fail_post:
            raise BridgeUnavailableError("post unavailable")
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": step, "accepted": True,
                           "status": "available", "private_build": True,
                           "read_only": True, "advertised": False,
                           "backend_id": "native-headless",
                           "activity_feast_hosted_post": self.post}}


class FeastStartConsumerTest(unittest.TestCase):
    def test_actual_cached_pre_start_snapshot_waits_once_before_independent_post(self) -> None:
        class CachedPostDriver(Driver):
            # Execute the production wait method. Only its local publication
            # condition is fixture-owned; no native process or pipe is used.
            wait_for_change = NativeHeadlessGameplayDriver.wait_for_change
            command_timeout_seconds = 10.0

            def __init__(self, state_dir: Path) -> None:
                super().__init__(state_dir)
                self.published_after_start = False
                self.waits = []
                self.native_revision = 18
                self.actor_character_id = 31853
                self.date_raw = 53328600

            def capabilities(self):
                return {**super().capabilities(), "snapshot": True}

            def take_snapshot(self):
                submitted = self.after_submit
                self.after_submit = submitted and self.published_after_start
                try:
                    value = super().take_snapshot()
                finally:
                    self.after_submit = submitted
                value["revision"] = 3 if self.published_after_start else 2
                value["diagnostics"] = {"hello": {
                    "expected_ck3_version": CK3_12003.game_version,
                    "expected_ck3_sha256": CK3_12003.executable_sha256,
                }}
                return value

            def wait_for_public_change(self, after_revision, timeout_seconds):
                self.waits.append((after_revision, timeout_seconds))
                self.published_after_start = True

            def wait_for_command_result(self, request_id, timeout_seconds):
                if (self.sent[-1]["step"] != START_STEP
                        and self.sent[-1]["expected_revision"] != 19):
                    return {"type": "command_result", "protocol_version": 1,
                            "request_id": request_id, "ok": False,
                            "error": "nonwar private snapshot revision is stale or malformed"}
                return super().wait_for_command_result(request_id, timeout_seconds)

        # Actual paused .3 attempt03 material values: Commit native18, cached
        # frame stays18 after ACK; independent published frame19 has -100gold
        # and full hosted activity587202561. Immediate old post was stale.
        with TemporaryDirectory() as temp:
            driver = CachedPostDriver(Path(temp))
            qualified = inputs()
            qualified.update({"native_guest_route_qualified": True,
                              "snapshot_revision": 18, "queried_revision": 2,
                              "queried_snapshot_id": "native:18",
                              "date_raw": 53328600, "actor_character_id": 31853})
            qualified["resources"]["gold"]["configured_cost_raw"] = 10_000_000
            qualified["balances"]["gold"]["raw"] = 62_305_241
            qualified["balances"]["piety"] = {"available": True, "raw": 85_985_500}
            driver.post.update({"snapshot_revision": 19, "date_raw": 53328600,
                                "actor_character_id": 31853})
            driver.post["balances"] = deepcopy(qualified["balances"])
            driver.post["balances"]["gold"]["raw"] = 52_305_241
            driver.post["hosted_activities"] = [{
                "activity_id": 587202561, "host_character_id": 31853,
                "activity_type_key": "activity_feast", "terminal_flags_observed": True,
                "native_completed": False, "native_invalidated": False,
            }]
            actual_guest = {**guest(), "snapshot_revision": 18,
                            "date_raw": 53328600, "actor_character_id": 31853}
            result = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=actual_guest, budget=budget())
            self.assertEqual(result["status"], "applied")
            self.assertTrue(result["postcondition_verified"])
            self.assertEqual(result["activity_id"], 587202561)
            self.assertEqual(result["lifecycle"]["outcome"]["status"], "ongoing")
            self.assertEqual(driver.waits, [(2, 10.0)])
            self.assertEqual([row["step"] for row in driver.sent],
                             [START_STEP, "query-activity-feast-hosted-post-v1-private"])
            self.assertEqual(driver.sent[1]["expected_revision"], 19)
            self.assertIsNone(read_feast_start_ledger(Path(temp))["pending"])

    def test_unknown_guest_or_balance_holds_without_native_submit(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            result = consume_feast_start_private_v1(
                driver, inputs=inputs(), guest=guest(), budget=budget())
            self.assertEqual(result["reason"], "native_guest_route_unqualified")
            self.assertEqual(driver.sent, [])
            illegal = inputs()
            illegal["final_can_start"] = False
            self.assertEqual(assess_feast_start_private_v1(
                illegal, guest=guest(), budget=budget())["status"],
                "not_actionable")
            qualified = inputs()
            qualified["native_guest_route_qualified"] = True
            qualified["balances"]["gold"] = {"available": False, "raw": None}
            result = assess_feast_start_private_v1(
                qualified, guest=guest(), budget=budget())
            self.assertEqual(result["reason"], "gold_balance_unobserved")
            self.assertEqual(result["status"], "missing_input")

    def test_exact_hosted_id_and_debit_resolve_only_after_read(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            qualified = inputs()
            qualified["native_guest_route_qualified"] = True
            result = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=guest(), budget=budget())
            self.assertEqual(result["status"], "applied")
            self.assertTrue(result["postcondition_verified"])
            self.assertEqual([row["step"] for row in driver.sent],
                             [START_STEP, "query-activity-feast-hosted-post-v1-private"])
            self.assertEqual(driver.sent[0]["reserve_gold_raw"], 20_000_000)
            self.assertIsNone(read_feast_start_ledger(driver.state_dir)["pending"])
            following = driver.take_snapshot()
            following["native_revision"] = 5
            self.assertIsNone(consume_feast_start_following_turn(
                driver.state_dir, following))
            following["date_raw"] += 1
            self.assertTrue(consume_feast_start_following_turn(
                driver.state_dir, following)["next_turn_consumed"])
            self.assertIsNone(consume_feast_start_following_turn(
                driver.state_dir, following))

    def test_resolved_restore_reads_exact_hosted_id_without_resubmit(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            qualified = inputs()
            qualified["native_guest_route_qualified"] = True
            first = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=guest(), budget=budget())
            self.assertEqual(first["activity_id"], 77)
            restored = consume_feast_start_private_v1(driver, inputs={})
            self.assertEqual(restored["status"], "already_applied")
            self.assertTrue(restored["restored_activity_observed"])
            driver.post["hosted_activities"][0]["activity_id"] = 78
            missing = consume_feast_start_private_v1(driver, inputs={})
            self.assertEqual(missing["status"], "resolved_activity_unobserved")
            self.assertFalse(missing["postcondition_verified"])
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_new_pid_lower_revision_resolves_material_pending_without_submit(self) -> None:
        with TemporaryDirectory() as temp:
            old_driver = Driver(Path(temp))
            old_driver.native_revision = 9
            old_driver.fail_post = True
            qualified = inputs()
            qualified.update({"native_guest_route_qualified": True,
                              "snapshot_revision": 9, "queried_snapshot_id": "native:9"})
            old_guest = {**guest(), "snapshot_revision": 9}
            first = consume_feast_start_private_v1(
                old_driver, inputs=qualified, guest=old_guest, budget=budget())
            self.assertEqual(first["status"], "pending_post_read_red")
            self.assertEqual(read_feast_start_ledger(Path(temp))["pending"]["native_revision"], 9)
            fresh_driver = Driver(Path(temp))
            fresh_driver.post["snapshot_revision"] = 3
            recovered = consume_feast_start_private_v1(fresh_driver, inputs={})
            self.assertEqual(recovered["status"], "applied")
            self.assertTrue(recovered["postcondition_verified"])
            self.assertEqual(recovered["activity_id"], 77)
            self.assertEqual(sum(row["step"] == START_STEP for row in old_driver.sent), 1)
            self.assertEqual(sum(row["step"] == START_STEP for row in fresh_driver.sent), 0)


class FeastLifecycleConsumerTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture = ROOT / "native_bridge/research/fixtures/ck3_12002_feast_hosted_post_wire.json"
        self.native_posts = json.loads(fixture.read_text(encoding="utf-8"))

    def start(self, state_dir: Path) -> Driver:
        driver = Driver(state_dir)
        driver.post = deepcopy(self.native_posts[0])
        driver.post.update({"snapshot_revision": 4, "date_raw": driver.date_raw})
        qualified = inputs()
        qualified["native_guest_route_qualified"] = True
        qualified["balances"] = deepcopy(driver.post["balances"])
        qualified["balances"]["gold"]["raw"] += 1_000_000
        result = consume_feast_start_private_v1(
            driver, inputs=qualified, guest=guest(), budget=budget())
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["activity_id"], 0x01000012)
        self.assertEqual(result["lifecycle"]["outcome"]["status"], "ongoing")
        return driver

    def later(self, driver: Driver, native_case: int) -> None:
        driver.post = deepcopy(self.native_posts[native_case])
        driver.date_raw = driver.post["date_raw"]
        driver.native_revision = driver.post["snapshot_revision"] - 1

    def counter_trace(self) -> list[dict[str, object]]:
        fixture = ROOT / "native_bridge/research/fixtures/ck3_12002_feast_outcome_values_wire.json"
        return json.loads(fixture.read_text(encoding="utf-8"))

    def start_with_counter_baseline(
        self, state_dir: Path, baseline_post: dict[str, object],
    ) -> Driver:
        driver = Driver(state_dir)
        driver.post = deepcopy(baseline_post)
        driver.native_build_12002 = True
        driver.date_raw = driver.post["date_raw"]
        driver.actor_character_id = driver.post["actor_character_id"]
        driver.native_revision = driver.post["snapshot_revision"] - 1
        fixture = ROOT / "native_bridge/research/fixtures/ck3_12002_feast_outcome_values_wire_baseline.json"
        qualified = json.loads(fixture.read_text(encoding="utf-8"))
        qualified.update({
            "native_guest_route_qualified": True,
            "actor_character_id": driver.actor_character_id,
            "date_raw": driver.date_raw,
            "snapshot_revision": driver.native_revision,
            "queried_snapshot_id": f"native:{driver.native_revision}",
            "queried_revision": 5,
            "balances": deepcopy(driver.post["balances"]),
            "outcome_values": deepcopy(driver.post["outcome_values"]),
        })
        qualified["balances"]["gold"]["raw"] += 1_000_000
        matching_guest = {**guest(), "actor_character_id": driver.actor_character_id,
                          "date_raw": driver.date_raw,
                          "snapshot_revision": driver.native_revision}
        result = consume_feast_start_private_v1(
            driver, inputs=qualified, guest=matching_guest,
            budget={**budget(), "gold_floor_raw": 0})
        self.assertEqual(result["status"], "applied")
        return driver

    def set_counter_post(self, driver: Driver, post: dict[str, object]) -> None:
        driver.post = deepcopy(post)
        driver.date_raw = driver.post["date_raw"]
        driver.native_revision = driver.post["snapshot_revision"] - 1

    def test_actual_native_counter_trace_measures_changes_without_attributing_payoff(self) -> None:
        before, after, _ = self.counter_trace()[:3]
        with TemporaryDirectory() as temp:
            driver = self.start_with_counter_baseline(Path(temp), before)
            self.set_counter_post(driver, after)
            result = reconcile_feast_lifecycle_private_v1(driver)
            self.assertEqual(result["lifecycle_status"], "completed")
            value = result["value_observation"]
            self.assertEqual(value["status"], "observed_counters")
            self.assertEqual(value["counter_changes"], {
                "prestige_raw": 10_000_000, "stress_points": -20,
                "reveler_xp_raw": 500_000,
            })
            self.assertEqual(value["reveler_presence_transition"], {"before": True, "after": True})
            self.assertTrue(value["post_terminal_counters_observed"])
            self.assertFalse(value["benefit_verified"])
            self.assertFalse(value["counter_changes_attributed_to_feast"])
            self.assertEqual(value["counter_native_provenance"]["exact_ck3_build"], "1.20.0.2")
            self.assertEqual(value["counter_native_provenance"]["exe_sha256"], CK3_12002.executable_sha256)
            queries = len(driver.sent)
            recorded = reconcile_feast_lifecycle_private_v1(driver)
            self.assertEqual(recorded["status"], "lifecycle_terminal_recorded")
            self.assertEqual(len(driver.sent), queries)

    def test_terminal_identity_survives_missing_counters_until_one_restored_counter_read(self) -> None:
        before, after, _, released = self.counter_trace()
        with TemporaryDirectory() as temp:
            driver = self.start_with_counter_baseline(Path(temp), before)
            self.set_counter_post(driver, after)
            driver.post.pop("outcome_values")
            first = reconcile_feast_lifecycle_private_v1(driver)
            self.assertEqual(first["lifecycle_status"], "completed")
            self.assertFalse(first["value_observation"]["post_terminal_counters_observed"])
            cold = Driver(Path(temp))
            cold.native_build_12002 = True
            cold.post = deepcopy(released)
            cold.post["snapshot_revision"] = 3
            cold.date_raw = cold.post["date_raw"]
            cold.actor_character_id = cold.post["actor_character_id"]
            cold.native_revision = 3
            cold.fail_post = True
            unreadable = reconcile_feast_lifecycle_private_v1(cold)
            self.assertEqual(unreadable["lifecycle_status"], "completed")
            self.assertEqual(unreadable["counter_read_status"], "post_read_red")
            cold.fail_post = False
            result = reconcile_feast_lifecycle_private_v1(cold)
            self.assertEqual(result["lifecycle_status"], "completed")
            self.assertEqual(result["observation"]["latest_identity_observation"]["status"], "unknown")
            self.assertEqual(result["observation"]["outcome"]["snapshot_revision"], after["snapshot_revision"])
            self.assertEqual(result["value_observation"]["counter_snapshot_revision"], 3)
            self.assertEqual(result["value_observation"]["counter_changes"]["prestige_raw"],
                             released["outcome_values"]["prestige_raw"] - before["outcome_values"]["prestige_raw"])
            queries = len(cold.sent)
            reconcile_feast_lifecycle_private_v1(cold)
            self.assertEqual(len(cold.sent), queries)
            self.assertFalse(any(row["step"] == START_STEP for row in cold.sent))

    def test_observed_reveler_absence_keeps_xp_delta_unavailable(self) -> None:
        _, after, absent = self.counter_trace()[:3]
        with TemporaryDirectory() as temp:
            driver = self.start_with_counter_baseline(Path(temp), absent)
            self.set_counter_post(driver, after)
            result = reconcile_feast_lifecycle_private_v1(driver)
            value = result["value_observation"]
            self.assertEqual(value["pre_start_outcome_values"]["reveler_present"], False)
            self.assertIsNone(value["pre_start_outcome_values"]["reveler_xp_raw"])
            self.assertEqual(value["reveler_presence_transition"], {"before": False, "after": True})
            self.assertIsNone(value["counter_changes"]["reveler_xp_raw"])
            self.assertNotIn("reveler_points", value["outcome_values"])
            self.assertFalse(value["benefit_verified"])

    def test_no_tracking_performs_no_native_query(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            self.assertEqual(reconcile_feast_lifecycle_private_v1(driver)["status"],
                             "no_tracking")
            self.assertEqual(driver.sent, [])

    def test_ongoing_id_survives_following_turn_and_cold_restore(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 0)
            self.assertTrue(consume_feast_start_following_turn(
                driver.state_dir, driver.take_snapshot())["next_turn_consumed"])
            cold = Driver(Path(temp))
            cold.post = deepcopy(driver.post)
            cold.date_raw = cold.post["date_raw"]
            cold.native_revision = cold.post["snapshot_revision"]
            result = reconcile_feast_lifecycle_private_v1(cold)
            self.assertEqual(result["lifecycle_status"], "ongoing")
            self.assertFalse(result["lifecycle_terminal_observed"])
            self.assertFalse(result["lifecycle_completed"])
            self.assertTrue(read_feast_start_ledger(Path(temp))["resolved"]["next_turn_consumed"])
            self.assertEqual([row["step"] for row in cold.sent],
                             ["query-activity-feast-hosted-post-v1-private"])

    def test_completion_retains_actual_balances_without_claiming_benefit(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 1)
            driver.post["balances"]["gold"]["raw"] += 2_000_000
            driver.post["balances"]["piety"]["raw"] += 1_000_000
            result = reconcile_feast_lifecycle_private_v1(driver)
            self.assertEqual(result["lifecycle_status"], "completed")
            self.assertTrue(result["lifecycle_terminal_observed"])
            self.assertTrue(result["lifecycle_completed"])
            value = result["value_observation"]
            self.assertEqual(value["resource_changes_raw"], {
                "gold": 2_000_000, "piety": 1_000_000,
                "treasury": None, "barter_goods": None,
            })
            self.assertEqual(value["status"], "unobserved")
            self.assertFalse(value["benefit_verified"])
            self.assertFalse(value["resource_changes_attributed_to_feast"])
            self.assertIsNone(value["opinion_change_raw"])
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_missing_identity_and_reused_slot_do_not_become_terminal(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 1)
            row = deepcopy(driver.post["hosted_activities"][0])
            for replacement in ([], [{**row, "activity_id": 0x02000012}],
                                [{**row, "host_character_id": 38822}],
                                [{**row, "activity_type_key": "activity_hunt"}]):
                with self.subTest(rows=replacement):
                    driver.post["hosted_activities"] = replacement
                    result = reconcile_feast_lifecycle_private_v1(driver)
                    self.assertEqual(result["lifecycle_status"], "unknown")
                    self.assertFalse(result["lifecycle_terminal_observed"])
                    self.assertIsNone(result["lifecycle_completed"])
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_invalidation_and_overlapping_native_flags_remain_distinct(self) -> None:
        for completed in (False, True):
            with self.subTest(completed=completed), TemporaryDirectory() as temp:
                driver = self.start(Path(temp))
                self.later(driver, 2)
                driver.post["hosted_activities"][0]["native_completed"] = completed
                result = reconcile_feast_lifecycle_private_v1(driver)
                self.assertEqual(result["lifecycle_status"],
                                 "completed_and_invalidated" if completed else "invalidated")
                self.assertEqual(result["lifecycle_completed"], completed)
                self.assertTrue(result["lifecycle_invalidated"])
                self.assertFalse(result["value_observation"]["benefit_verified"])

    def test_recorded_completion_survives_release_without_query_or_resubmit(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 1)
            reconcile_feast_lifecycle_private_v1(driver)
            cold = Driver(Path(temp))
            cold.date_raw = driver.date_raw + 1
            cold.post["hosted_activities"] = []
            cold.fail_post = True
            result = reconcile_feast_lifecycle_private_v1(cold)
            self.assertEqual(result["status"], "lifecycle_terminal_recorded")
            self.assertEqual(result["lifecycle_status"], "completed")
            self.assertEqual(result["observation"]["outcome"]["snapshot_revision"], 12)
            restored = consume_feast_start_private_v1(cold, inputs={})
            self.assertEqual(restored["status"], "already_applied")
            self.assertEqual(restored["lifecycle_observation"]["lifecycle_status"], "completed")
            self.assertFalse(restored["restored_activity_observed"])
            self.assertEqual(cold.sent, [])

    def test_service_plan_consumes_real_lifecycle_helper_without_changing_action(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 1)
            plan = {"policy": "fixture-existing-plan", "phase": "life",
                    "selected_step": "life-advance", "reason": "existing plan"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=plan):
                queries_before = len(driver.sent)
                default = GameplayBridgeService(driver).plan_turn()
                self.assertNotIn("activity_feast_lifecycle_observation", default["plan"])
                self.assertEqual(len(driver.sent), queries_before)
                driver.allow_private_activity_feast_lifecycle_observation = True
                result = GameplayBridgeService(driver).plan_turn()
            self.assertEqual(result["plan"]["selected_step"], "life-advance")
            self.assertEqual(result["plan"]["activity_feast_lifecycle_observation"]["lifecycle_status"],
                             "completed")
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_nonwar_formal_caller_tracks_terminal_and_consumes_following_turn_once(self) -> None:
        with TemporaryDirectory() as temp:
            driver = self.start(Path(temp))
            self.later(driver, 1)
            plan = {"policy": "fixture-existing-nonwar", "phase": "life",
                    "selected_step": "life-advance", "reason": "existing plan"}
            service = GameplayBridgeService(driver)
            with patch("xar_autoplayer.strategy.choose_nonwar_turn_v1", side_effect=lambda *_, **__: deepcopy(plan)):
                queries_before = len(driver.sent)
                default = service.plan_nonwar_turn()
                self.assertNotIn("activity_feast_lifecycle_observation", default["plan"])
                self.assertEqual(len(driver.sent), queries_before)
                driver.allow_private_activity_feast_lifecycle_observation = True
                with patch.object(service, "_execute_planned_turn", side_effect=lambda planned, **_: planned):
                    first = service.auto_nonwar_turn()
                second = service.plan_nonwar_turn()
            self.assertEqual(first["plan"]["selected_step"], "life-advance")
            self.assertEqual(first["plan"]["activity_feast_lifecycle_observation"]["lifecycle_status"],
                             "completed")
            self.assertTrue(first["plan"]["activity_feast_start_following_turn"]["next_turn_consumed"])
            self.assertNotIn("activity_feast_start_following_turn", second["plan"])
            self.assertEqual(second["plan"]["activity_feast_lifecycle_observation"]["status"],
                             "lifecycle_terminal_recorded")
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_nonwar_pending_reconciles_material_before_existing_early_return(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            driver.fail_submit = True
            qualified = inputs()
            qualified["native_guest_route_qualified"] = True
            initial = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=guest(), budget=budget())
            self.assertEqual(initial["status"], "submission_unresolved")
            driver.fail_submit = False
            driver.after_submit = True
            driver.allow_private_activity_feast_lifecycle_observation = True
            plan = {"policy": "fixture-natural-modal", "phase": "event",
                    "selected_step": "choose-event-option:fixture", "reason": "existing event"}
            with patch("xar_autoplayer.strategy.choose_nonwar_turn_v1", return_value=plan):
                observed = GameplayBridgeService(driver).plan_nonwar_turn()
            self.assertEqual(observed["plan"]["selected_step"], "choose-event-option:fixture")
            self.assertTrue(observed["plan"]["activity_feast_lifecycle_observation"]["start_postcondition_verified"])
            ledger = read_feast_start_ledger(Path(temp))
            self.assertIsNone(ledger["pending"])
            self.assertEqual(ledger["resolved"]["activity_id"], 77)
            self.assertFalse(ledger["resolved"]["next_turn_consumed"])
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)

    def test_timeout_or_ambiguous_post_never_retries_start(self) -> None:
        with TemporaryDirectory() as temp:
            driver = Driver(Path(temp))
            qualified = inputs()
            qualified["native_guest_route_qualified"] = True
            driver.fail_submit = True
            first = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=guest(), budget=budget())
            self.assertEqual(first["status"], "submission_unresolved")
            driver.fail_submit = False
            driver.post = deepcopy(driver.post)
            driver.post["hosted_activities"] = []
            driver.post["snapshot_revision"] = 3
            driver.post["balances"]["gold"]["raw"] = 120_000_000
            second = consume_feast_start_private_v1(
                driver, inputs=qualified, guest=guest(), budget=budget())
            self.assertEqual(second["status"], "pending_post_unresolved")
            self.assertEqual(sum(row["step"] == START_STEP for row in driver.sent), 1)
            driver.after_submit = True
            driver.post["snapshot_revision"] = 4
            driver.post["hosted_activities"] = [{
                "activity_id": 77, "activity_type_key": "activity_feast",
                "host_character_id": 29829}]
            driver.post["balances"]["gold"]["raw"] = 119_000_000
            recovered = reconcile_feast_start_private_v1(driver)
            self.assertEqual(recovered["status"], "applied")


if __name__ == "__main__":
    unittest.main()
