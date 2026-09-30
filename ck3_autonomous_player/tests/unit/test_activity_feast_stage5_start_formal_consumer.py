"""No-launch Stage5 Start holds, single-submit pending and material recovery."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.activity_feast_stage5_start_formal_consumer import (
    assess_feast_start_private_v1, consume_feast_start_private_v1,
    consume_feast_start_following_turn, read_feast_start_ledger,
    reconcile_feast_start_private_v1,
)
from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_SCHEMA, POST_SCHEMA, START_STEP,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError


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
        return {"snapshot_id": f"native:{revision}",
                "revision": 6 if self.after_submit else 5,
                "native_revision": revision, "date_raw": 53219928,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": 29829, "alive": True}}

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
