from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    FOCUS_QUERY_STEP,
    parse_player_lifestyle_focus_private_v1,
    query_player_lifestyle_focus_private_v1,
)


def _frame() -> dict[str, object]:
    return {
        "paused": True,
        "snapshot_id": "native:3",
        "native_revision": 3,
        "date_raw": 53368176,
        "played_character_id": 36403,
        "episode_run_id": "native-36403-2b4b233056bd",
    }


def _response() -> dict[str, object]:
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": "focus-read-1", "ok": True,
        "result": {
            "step": FOCUS_QUERY_STEP,
            "private_build": True, "advertised": False,
            "read_only": True, "policy_scoped": True,
            "snapshot_id": "native:3",
            "episode_run_id": "native-36403-2b4b233056bd",
            "status": "observed_native_legal",
            "target_key": "stewardship_wealth_focus",
            "target_lifestyle_key": "stewardship_lifestyle",
            "native_legal": True,
            "scanned_database_rows": 23,
            "target_lifestyle_progress": {
                "presence": "present", "source": "exact_native_getters",
                "xp_total_raw": 0, "xp_within_level_raw": 0,
                "xp_per_level": 1000, "unspent_perk_points": 0,
                "used_perk_points": 0,
            },
        },
    }


def _parse(response: dict[str, object], after: dict[str, object] | None = None) -> dict[str, object]:
    return parse_player_lifestyle_focus_private_v1(
        response, expected_request_id="focus-read-1",
        source_frame=_frame(), independent_after_frame=after or _frame(),
    )


class _Driver:
    allow_private_lifestyle_formal_trial = True
    command_timeout_seconds = 1.0

    def __init__(self) -> None:
        self.endpoint = self
        self.state = self
        self.last_request: dict[str, object] | None = None
        self.snapshots = 0

    def take_snapshot(self) -> dict[str, object]:
        self.snapshots += 1
        return {
            "paused": True, "map_ready": True,
            "snapshot_id": "native:3", "native_revision": 3,
            "revision": 4, "date_raw": 53368176,
            "episode_run_id": "native-36403-2b4b233056bd",
            "played_character": {"character_id": 36403},
        }

    def send(self, request: dict[str, object]) -> None:
        self.last_request = request

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        assert self.last_request is not None
        response = _response()
        response["request_id"] = request_id
        return response


class FocusPrivateObservationTests(unittest.TestCase):
    def test_private_query_binds_native_not_public_revision(self) -> None:
        driver = _Driver()
        parsed = query_player_lifestyle_focus_private_v1(driver, expected_revision=4)
        self.assertEqual(parsed["status"], "observed")
        self.assertEqual(driver.last_request["expected_revision"], 3)
        self.assertEqual(driver.last_request["expected_snapshot_id"], "native:3")
        self.assertEqual(driver.snapshots, 2)

    def test_private_query_disabled_does_not_send(self) -> None:
        driver = _Driver()
        driver.allow_private_lifestyle_formal_trial = False
        self.assertEqual(query_player_lifestyle_focus_private_v1(driver)["status"], "trial_off")
        self.assertIsNone(driver.last_request)

    def test_stale_public_revision_does_not_send(self) -> None:
        driver = _Driver()
        self.assertEqual(
            query_player_lifestyle_focus_private_v1(driver, expected_revision=3)["status"],
            "paused_frame_unavailable",
        )
        self.assertIsNone(driver.last_request)

    def test_exact_getter_zero_is_observed_not_inferred(self) -> None:
        parsed = _parse(_response())
        self.assertEqual(parsed["status"], "observed")
        self.assertIs(parsed["native_legal"], True)
        self.assertEqual(parsed["target_lifestyle_progress"]["xp_total_raw"], 0)

    def test_native_illegal_is_typed(self) -> None:
        response = _response()
        response["result"]["status"] = "observed_native_illegal"
        response["result"]["native_legal"] = False
        parsed = _parse(response)
        self.assertEqual(parsed["status"], "observed")
        self.assertIs(parsed["native_legal"], False)

    def test_unavailable_target_progress_does_not_gain_zero(self) -> None:
        response = _response()
        response["result"]["target_lifestyle_progress"] = {
            "presence": "unavailable", "reason": "target_native_getters_unavailable",
        }
        parsed = _parse(response)
        self.assertEqual(parsed["status"], "target_progress_unavailable")
        self.assertNotIn("target_lifestyle_progress", parsed)

    def test_unavailable_with_numeric_value_is_red(self) -> None:
        response = _response()
        response["result"]["target_lifestyle_progress"] = {
            "presence": "unavailable", "reason": "target_native_getters_unavailable",
            "xp_total_raw": 0,
        }
        self.assertEqual(_parse(response)["status"], "red")

    def test_missing_or_null_values_are_red(self) -> None:
        for value in (None, False, "0"):
            with self.subTest(value=value):
                response = _response()
                response["result"]["target_lifestyle_progress"]["xp_total_raw"] = value
                self.assertEqual(_parse(response)["status"], "red")

    def test_private_binding_or_native_error_is_red(self) -> None:
        response = _response()
        response["result"]["advertised"] = True
        self.assertEqual(_parse(response)["status"], "red")
        response = _response()
        response["ok"] = False
        response["error"] = "native_read_failed"
        self.assertEqual(_parse(response)["status"], "red")

    def test_frame_drift_is_red(self) -> None:
        after = _frame()
        after["native_revision"] = 4
        self.assertEqual(_parse(_response(), after)["status"], "red")

    def test_native_unavailable_does_not_claim_legality(self) -> None:
        response = _response()
        response["result"]["status"] = "unavailable_database"
        del response["result"]["native_legal"]
        del response["result"]["target_lifestyle_progress"]
        parsed = _parse(response)
        self.assertEqual(parsed["status"], "red")
        self.assertEqual(parsed["native_status"], "unavailable_database")


if __name__ == "__main__":
    unittest.main()
