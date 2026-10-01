"""R724 production auto_turn regression for a rejected read-only root query."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.campaign_root_context_contract import (  # noqa: E402
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    _NativeCommandRejectedError,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.succession_transition_contract import (  # noqa: E402
    freeze_succession_expectation_v1,
)


_REJECTION = "campaign-root snapshot changed or is not ready"
_R11_REJECTION = "application-main typed query failed or its snapshot changed"


def _root_frame(revision: int, native_revision: int) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{native_revision}",
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": 53_192_712,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "episode_character_id": 29_829,
        "episode_run_id": "r724-same-campaign",
        "one_life_terminal": False,
        "one_life_terminal_reason": None,
        "active_event": None,
        "pending_character_interaction": None,
        "active_wars": [{"war_id": 33_554_473, "score": -41}],
        "player_armies": [{"army_id": 50_331_653, "province_id": 5615}],
        "native_command_history": [],
        "diagnostics": {"bridge_pid": 4242, "connection_generation": 3},
    }


class _RejectedRootDriver:
    def __init__(
        self, *, drift: str | None = None, second_reject: bool = False,
        rejection: str = _REJECTION,
    ):
        self.current = _root_frame(500, 30)
        self.drift = drift
        self.second_reject = second_reject
        self.calls: list[tuple[str, int | None]] = []
        self.wait_count = 0
        self.first_error = _NativeCommandRejectedError(rejection)

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.current)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.calls.append((step, expected_revision))
        if len(self.calls) == 1:
            self.current["native_command_history"].append(
                {
                    "index": 1,
                    "command": step,
                    "ok": False,
                    "error": f"_NativeCommandRejectedError: {self.first_error}",
                }
            )
            raise self.first_error
        if self.second_reject:
            raise _NativeCommandRejectedError(self.first_error.native_error)
        return {
            "step": step,
            "accepted": True,
            "status": "available",
            "queried_revision": expected_revision,
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        self.wait_count += 1
        if after_revision != 500 or timeout_seconds != 1.5:
            raise AssertionError("root retry crossed its one-frame wait bound")
        self.current["revision"] = 501
        self.current["native_revision"] = 31
        self.current["snapshot_id"] = "native:31"
        if self.drift == "date":
            self.current["date_raw"] += 1
        elif self.drift == "event":
            self.current["active_event"] = {"instance_id": 1}
        elif self.drift == "pending":
            self.current["pending_character_interaction"] = {"instance_id": 2}
        elif self.drift == "actor":
            self.current["played_character"]["character_id"] = 7
        elif self.drift == "typed_action":
            self.current["native_command_history"].append(
                {"index": 2, "command": "move-army-1-to-2", "ok": True}
            )
        elif self.drift == "not_ready":
            self.current["map_ready"] = False
        elif self.drift == "no_new_native_frame":
            self.current["native_revision"] = 30
        return self.take_snapshot()


class _RejectedSuccessionRootDriver(_RejectedRootDriver):
    """Real 1.20 material with synthetic revisions and R11's native rejection.

    The existing paused Council fixture supplies the full root DTO. Rebinding
    only its snapshot identity/revisions exercises the service's production
    root, bundle and succession-freeze code without claiming another live read.
    """

    def __init__(self, **options):
        super().__init__(rejection=_R11_REJECTION, **options)
        fixture = ROOT / "tests/fixtures/private_council_formal12002_actual.json"
        data = json.loads(fixture.read_text(encoding="utf-8-sig"))
        self.current.update(copy.deepcopy(data["current_snapshot"]))
        self.current.update(revision=500, native_revision=30, snapshot_id="native:30")
        self.current["backend_id"] = "native-headless"
        self.current["history"] = []
        self.root_result = copy.deepcopy(data["current_root"])
        for key in ("scope", "build", "source", "binding"):
            self.root_result.pop(key)
        provenance = self.root_result["campaign_root_context"]["provenance"]
        self.current["diagnostics"]["hello"] = {
            "expected_ck3_version": provenance["game_version"],
            "expected_ck3_sha256": provenance["executable_sha256"],
        }
        self.retained_revisions = []

    take_internal_semantic_snapshot = _RejectedRootDriver.take_snapshot

    def capabilities(self):
        return {
            "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, "life-advance"],
            "bridge_capabilities": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY],
        }

    def execute_step(self, step, *, expected_revision=None):
        if step != QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP:
            raise AssertionError("succession query fixture must not submit an action")
        super().execute_step(step, expected_revision=expected_revision)
        result = copy.deepcopy(self.root_result)
        result["snapshot_revision"] = self.current["native_revision"]
        result["campaign_root_context"]["snapshot_revision"] = self.current["native_revision"]
        result.update(
            queried_snapshot_id=self.current["snapshot_id"],
            queried_revision=self.current["revision"],
            queried_native_revision=self.current["native_revision"],
        )
        self.current["native_command_history"].append({
            "index": len(self.current["native_command_history"]) + 1,
            "command": step, "ok": True, "result": copy.deepcopy(result),
        })
        return result

    def retain_succession_expectation_v1(self, turn_bundle, *, expected_revision):
        if turn_bundle["binding"]["revision"] != expected_revision:
            raise AssertionError("succession fixture received an old bundle revision")
        self.current["succession_expectation"] = freeze_succession_expectation_v1(
            turn_bundle, episode_run_id=self.current["episode_run_id"],
            episode_character_id=self.current["episode_character_id"],
        )
        self.retained_revisions.append(expected_revision)

    def reconcile_retained_succession_transition_v1(self, *args, **kwargs):
        raise AssertionError("the living R11 actor must not reconcile a successor")


class R724CampaignRootReadRetryTests(unittest.TestCase):
    def _service(self, driver: _RejectedRootDriver) -> GameplayBridgeService:
        service = GameplayBridgeService(driver)
        service.plan_turn = mock.Mock(return_value={
            "snapshot_id": "native:30",
            "revision": 500,
            "plan": {
                "phase": "native_campaign_root_context",
                "selected_step": QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            },
        })
        return service

    def test_one_rejected_read_retries_on_fresh_paused_revision(self) -> None:
        driver = _RejectedRootDriver()
        outcome = self._service(driver).auto_turn()

        self.assertEqual(outcome["status"], "executed")
        self.assertEqual(
            driver.calls,
            [(QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 500),
             (QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 501)],
        )
        self.assertEqual(driver.wait_count, 1)
        retry = outcome["read_only_query_retry"]
        self.assertEqual(retry["old_native_revision"], 30)
        self.assertEqual(retry["fresh_native_revision"], 31)
        self.assertEqual(retry["failed_history_index"], 1)
        self.assertIn(_REJECTION, retry["rejection"])

    def test_r11_selected_root_query_uses_existing_bounded_retry(self) -> None:
        driver = _RejectedRootDriver(rejection=_R11_REJECTION)
        outcome = self._service(driver).auto_turn()
        self.assertEqual(driver.calls, [
            (QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 500),
            (QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 501),
        ])
        self.assertEqual(driver.wait_count, 1)
        self.assertIn(_R11_REJECTION, outcome["read_only_query_retry"]["rejection"])

    def test_r11_nonwar_preparation_retries_real_bundle_then_retains_fresh_binding(self) -> None:
        driver = _RejectedSuccessionRootDriver()
        service = GameplayBridgeService(driver)
        planned = service.plan_nonwar_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(planned["revision"], 501)
        self.assertEqual(driver.calls, [
            (QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 500),
            (QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, 501),
        ])
        self.assertEqual(driver.wait_count, 1)
        self.assertEqual(driver.retained_revisions, [501])
        self.assertEqual(driver.current["succession_expectation"]["binding"]["native_revision"], 31)
        retry = planned["plan"]["read_only_query_retry"]
        self.assertEqual((retry["old_revision"], retry["fresh_revision"]), (500, 501))
        self.assertIn(_R11_REJECTION, retry["rejection"])
        self.assertIs(driver.current["native_command_history"][0]["ok"], False)
        self.assertNotIn("starting_snapshot", retry)
        # A second plan consumes the fresh expectation and cannot repeat the read.
        service.plan_nonwar_turn()
        self.assertEqual(len(driver.calls), 2)

    def test_r11_nonwar_preparation_second_rejection_preserves_first_error(self) -> None:
        driver = _RejectedSuccessionRootDriver(second_reject=True)
        with self.assertRaises(_NativeCommandRejectedError) as observed:
            GameplayBridgeService(driver).plan_nonwar_turn()
        self.assertIs(observed.exception, driver.first_error)
        self.assertEqual(len(driver.calls), 2)
        self.assertEqual(driver.wait_count, 1)
        self.assertEqual(driver.retained_revisions, [])
        self.assertIn(_R11_REJECTION, observed.exception.read_only_query_retry["second_error"])

    def test_r11_nonwar_preparation_changed_date_does_not_retry_or_retain(self) -> None:
        driver = _RejectedSuccessionRootDriver(drift="date")
        with self.assertRaises(_NativeCommandRejectedError) as observed:
            GameplayBridgeService(driver).plan_nonwar_turn()
        self.assertIs(observed.exception, driver.first_error)
        self.assertEqual(len(driver.calls), 1)
        self.assertEqual(driver.wait_count, 1)
        self.assertEqual(driver.retained_revisions, [])

    def test_drift_or_typed_action_retains_original_rejection(self) -> None:
        for drift in (
            "date", "event", "pending", "actor", "typed_action",
            "not_ready", "no_new_native_frame",
        ):
            with self.subTest(drift=drift):
                driver = _RejectedRootDriver(drift=drift)
                with self.assertRaises(_NativeCommandRejectedError) as observed:
                    self._service(driver).auto_turn()
                self.assertIs(observed.exception, driver.first_error)
                self.assertEqual(len(driver.calls), 1)
                self.assertEqual(driver.wait_count, 1)

    def test_second_rejection_retains_first_error_and_retry_evidence(self) -> None:
        driver = _RejectedRootDriver(second_reject=True)
        with self.assertRaises(_NativeCommandRejectedError) as observed:
            self._service(driver).auto_turn()
        self.assertIs(observed.exception, driver.first_error)
        self.assertEqual(len(driver.calls), 2)
        self.assertIn(
            _REJECTION, observed.exception.read_only_query_retry["second_error"]
        )

    def test_initial_root_snapshot_failure_keeps_selected_step(self) -> None:
        driver = _RejectedRootDriver()
        service = self._service(driver)
        with mock.patch.object(
            driver, "take_snapshot",
            side_effect=BridgeUnavailableError("root snapshot temporarily unavailable"),
        ):
            with self.assertRaises(BridgeUnavailableError) as observed:
                service.auto_turn()
        self.assertEqual(
            observed.exception.selected_step,
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
        )
        self.assertEqual(driver.calls, [])


if __name__ == "__main__":
    unittest.main()
