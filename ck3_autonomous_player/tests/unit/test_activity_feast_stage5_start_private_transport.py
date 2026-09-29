"""No-launch contract for the default-off feast Start input/post reads."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_SCHEMA, INPUT_STEP, POST_SCHEMA, POST_STEP,
    query_activity_feast_hosted_post_private_v1,
    query_activity_feast_stage5_start_inputs_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:3", "revision": 5, "native_revision": 3,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "episode_run_id": "native-29829-test", "episode_character_id": 29829,
    }


def common_payload(schema: str) -> dict[str, object]:
    return {
        "schema": schema, "snapshot_revision": 3,
        "date_raw": 53219928, "actor_character_id": 29829,
        "balances": {
            "gold": {"available": True, "raw": 120_644_281},
            "treasury": {"available": False, "raw": None},
            "piety": {"available": True, "raw": 50_000_000},
            "barter_goods": {"available": False, "raw": None},
        },
        "hosted_activities": [
            {"activity_id": 17, "host_character_id": 29829,
             "activity_type_key": "activity_hunt"},
        ],
        "read_only": True, "advertised": False,
    }


def inputs_payload() -> dict[str, object]:
    return {
        **common_payload(INPUT_SCHEMA),
        "activity_key": "activity_feast",
        "selected_option_key": "feast_type_generic",
        "planning_stage": 5, "scale": 100000,
        "normal_refresh_sequence": 1, "final_can_start": True,
        "resources": {
            "gold": {"resource_index": 0, "configured_cost_raw": 1_000_000},
            "treasury": {"resource_index": 1, "configured_cost_raw": 0},
            "piety": {"resource_index": 2, "configured_cost_raw": 0},
            "barter_goods": {"resource_index": 3, "configured_cost_raw": 0},
        },
        "native_guest_route_qualified": False,
        "guest_join_status": "guest_source_unavailable",
        "selected_nonhost_count": None,
        "positive_join_count": None,
        "timely_positive_join_count": None,
        "arrival_time_observed": False,
    }


class Driver:
    allow_private_activity_feast_stage5_start_query = True

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.sent: list[dict[str, object]] = []
        self.after = snapshot()
        self.ok = True
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        step = self.sent[-1]["step"]
        key = ("activity_feast_stage5_start_inputs" if step == INPUT_STEP
               else "activity_feast_hosted_post")
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": self.ok,
            "error": "native_activity_start_red:frame_changed" if not self.ok else None,
            "result": {
                "step": step, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, key: self.payload,
                "backend_id": "native-headless",
            } if self.ok else None,
        }


class ActivityFeastStage5StartReadTest(unittest.TestCase):
    def test_inputs_are_bound_and_unknown_guest_remains_false(self) -> None:
        driver = Driver(inputs_payload())
        result = query_activity_feast_stage5_start_inputs_private_v1(
            driver, expected_revision=5)
        self.assertEqual(driver.sent[0], {
            "type": "execute_step", "protocol_version": 1,
            "request_id": driver.sent[0]["request_id"],
            "step": INPUT_STEP, "expected_revision": 3,
            "expected_date_raw": 53219928,
            "expected_actor_character_id": 29829,
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
            "expected_planning_stage": 5,
        })
        self.assertIs(result["native_guest_route_qualified"], False)
        self.assertEqual(result["resources"]["gold"]["configured_cost_raw"],
                         1_000_000)
        observed = inputs_payload()
        observed.update({
            "guest_join_status": "observed", "selected_nonhost_count": 2,
            "positive_join_count": 1, "timely_positive_join_count": 1,
            "arrival_time_observed": True,
        })
        self.assertEqual(query_activity_feast_stage5_start_inputs_private_v1(
            Driver(observed), expected_revision=5)["timely_positive_join_count"], 1)
        driver.payload["resources"]["gold"]["configured_cost_raw"] = 0
        self.assertEqual(result["resources"]["gold"]["configured_cost_raw"],
                         1_000_000)

    def test_independent_hosted_post_and_red(self) -> None:
        post = common_payload(POST_SCHEMA)
        post["hosted_activities"].append({
            "activity_id": 18, "host_character_id": 29829,
            "activity_type_key": "activity_feast",
        })
        driver = Driver(post)
        result = query_activity_feast_hosted_post_private_v1(
            driver, expected_revision=5)
        self.assertEqual(driver.sent[0]["step"], POST_STEP)
        self.assertNotIn("expected_planning_stage", driver.sent[0])
        self.assertEqual(result["hosted_activities"][-1]["activity_id"], 18)
        driver = Driver(post)
        driver.ok = False
        with self.assertRaisesRegex(BridgeUnavailableError, "frame_changed"):
            query_activity_feast_hosted_post_private_v1(
                driver, expected_revision=5)

    def test_missing_cost_or_crossed_frame_and_default_off(self) -> None:
        bad = inputs_payload()
        bad["resources"]["piety"]["configured_cost_raw"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "cost row"):
            query_activity_feast_stage5_start_inputs_private_v1(
                Driver(bad), expected_revision=5)
        bad = inputs_payload()
        bad["guest_join_status"] = "observed"
        bad["selected_nonhost_count"] = 1
        bad["positive_join_count"] = 0
        bad["timely_positive_join_count"] = 1
        bad["arrival_time_observed"] = True
        with self.assertRaisesRegex(BridgeUnavailableError, "guest counts"):
            query_activity_feast_stage5_start_inputs_private_v1(
                Driver(bad), expected_revision=5)
        driver = Driver(inputs_payload())
        driver.after["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            query_activity_feast_stage5_start_inputs_private_v1(
                driver, expected_revision=5)
        driver = Driver(inputs_payload())
        driver.allow_private_activity_feast_stage5_start_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_stage5_start_inputs_private_v1(
                driver, expected_revision=5)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
