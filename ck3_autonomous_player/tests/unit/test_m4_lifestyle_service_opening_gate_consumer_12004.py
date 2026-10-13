"""New ordinary-Service opening gate consumption, without old LIFE matrices."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from test_lifestyle_formal_private_consumer import _Driver, _game_frame, _scope_root
from xar_autoplayer.bridge import service as service_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    FOCUS_SUBMIT_STEP, RECEIPT_STEP, STATE_QUERY_STEP,
    query_player_lifestyle_receipt_private_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


ROOT_QUERY = "query-campaign-root-context-v1"


class _OpeningDriver(_Driver):
    """Reuse only protocol fixtures; no existing test case is executed."""

    def __init__(self, *, existing_focus):
        super().__init__()
        self.require_initial_lifestyle_focus_before_date_advance = True
        self.initial_lifestyle_focus_gate_stage = "await_submit"
        self.state.stock_focus_present = existing_focus
        self.state.formal_focus_absent = not existing_focus
        self.state.zero_points = True
        self.history.extend(_scope_root())
        self.executed = []
        self.checkpoints = []
        self.requests = []
        native_result = self.state.wait_for_command_result

        def current_frame_result(request_id, timeout):
            response = native_result(request_id, timeout)
            life = response["result"].get("snapshot")
            if isinstance(life, dict):
                revision = self.state.last["expected_revision"]
                life.update(snapshot_id=f"native:{revision}", public_revision=revision,
                            native_revision=revision, proof_epoch=revision)
                if self.state.stock_focus_present and life["current_focus"]["presence"] == "present":
                    life["current_focus"]["key"] = self.state.selected_focus_key
            return response

        self.state.wait_for_command_result = current_frame_result

    def capabilities(self):
        value = super().capabilities()
        value["action_steps"].append("save-checkpoint")
        return value

    def send(self, request):
        self.requests.append(deepcopy(request))
        super().send(request)

    def execute_step(self, step, *, expected_revision=None):
        assert expected_revision == self.frame["revision"]
        self.executed.append(step)
        if step == ROOT_QUERY:
            result = deepcopy(_scope_root()[0]["result"])
            result.update(step=step, accepted=True)
            result["campaign_root_context"]["snapshot_revision"] = self.frame["native_revision"]
            self._record_command(step, ok=True, result=result)
            return result
        if step == "save-checkpoint":
            checkpoint = {
                "status": "saved", "strategy": "native-autosave-command-v1",
                "name": "xar_checkpoint.ck3",
                "date_raw": self.frame["date_raw"],
                "snapshot_id": self.frame["snapshot_id"],
                "episode_run_id": self.frame["episode_run_id"],
                "path": "fixture/xar_checkpoint.ck3", "size": 1,
                "sha256": "a" * 64,
            }
            result = {"step": step, "accepted": True, "checkpoint": checkpoint,
                      "materialization": {"available": True}}
            self.checkpoints.append(result)
            self._record_command(step, ok=True, result=result)
            return result
        raise AssertionError(f"unexpected game step: {step}")

    def query_player_lifestyle_receipt_private_v1(self, *, pending, expected_revision):
        return query_player_lifestyle_receipt_private_v1(
            self, pending=pending, expected_revision=expected_revision,
        )

    def publish_later_focus_frame(self):
        self.frame = _game_frame(4)
        self.state.stock_focus_present = True
        self.state.formal_focus_absent = False


class OpeningLifestyleServiceConsumer12004Test(unittest.TestCase):
    def test_cold_service_rehydrates_pending_focus_before_existing_focus(self):
        driver = _OpeningDriver(existing_focus=False)
        submitted = GameplayBridgeService(driver).auto_turn()
        action_id = submitted["result"]["action_request_id"]
        self.assertEqual(submitted["selected_step"], FOCUS_SUBMIT_STEP)

        driver.publish_later_focus_frame()
        driver.initial_lifestyle_focus_gate_stage = "await_submit"
        restored_service = GameplayBridgeService(driver)
        restored = restored_service.plan_turn()["plan"]
        self.assertEqual(restored["selected_step"], RECEIPT_STEP)
        self.assertNotIn("initial_lifestyle_focus_existing", restored)
        self.assertEqual(restored["lifestyle_pending_action"]["action_request_id"], action_id)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_receipt")
        self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(sum(row["step"] == FOCUS_SUBMIT_STEP for row in driver.requests), 1)

    def test_stale_existing_focus_proof_keeps_opening_gate_closed(self):
        driver = _OpeningDriver(existing_focus=True)
        service = GameplayBridgeService(driver)
        execute = service._execute_planned_turn

        def stale_source(planned, **kwargs):
            outcome = execute(planned, **kwargs)
            source = outcome["plan"]["initial_lifestyle_focus_existing"]["source_frame"]
            source["revision"] += 1
            return outcome

        with patch.object(service, "_execute_planned_turn", side_effect=stale_source):
            with self.assertRaisesRegex(BridgeUnavailableError, "existing opening focus proof"):
                service.auto_turn()
        self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_submit")
        self.assertEqual(driver.executed, [ROOT_QUERY])

    def test_existing_focus_consumption_releases_gate_to_full_ordinary_planner(self):
        driver = _OpeningDriver(existing_focus=True)
        service = GameplayBridgeService(driver)
        opening = service.auto_turn()
        self.assertEqual(opening["selected_step"], ROOT_QUERY)
        self.assertEqual(opening["plan"]["initial_lifestyle_focus_existing"]["status"],
                         "verified_existing")
        self.assertFalse(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "complete")
        self.assertNotIn(FOCUS_SUBMIT_STEP, [row["command"] for row in driver.history])
        with patch.object(service_module, "choose_one_life_turn",
                          wraps=service_module.choose_one_life_turn) as full_planner:
            resumed = service.plan_turn()
        full_planner.assert_called_once()
        self.assertFalse(resumed["plan"].get("phase", "").startswith("initial_lifestyle"))
        self.assertEqual(driver.frame["date_raw"], _game_frame()["date_raw"])

    def test_focus_ack_waits_for_independent_receipt_and_following_consumption(self):
        self._exercise_focus_gate(external_checkpoint=False)

    def test_external_checkpoint_skips_only_duplicate_save_and_keeps_shared_consumer(self):
        self._exercise_focus_gate(external_checkpoint=True)

    def _exercise_focus_gate(self, *, external_checkpoint):
        driver = _OpeningDriver(existing_focus=False)
        service = GameplayBridgeService(driver)
        if external_checkpoint:
            service._initial_lifestyle_focus_external_checkpoint_v1 = True
        submitted = service.auto_turn()
        self.assertEqual(submitted["selected_step"], FOCUS_SUBMIT_STEP)
        self.assertEqual(submitted["result"]["status"], "submitted_verification_pending")
        action_id = submitted["result"]["action_request_id"]
        self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_receipt")
        same_frame = service.plan_turn()
        self.assertNotEqual(same_frame["plan"]["selected_step"], "life-advance")
        self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)

        driver.publish_later_focus_frame()
        receipt = service.auto_turn()
        self.assertEqual(receipt["selected_step"], RECEIPT_STEP)
        self.assertEqual(receipt["result"]["action_request_id"], action_id)
        self.assertTrue(receipt["result"]["postcondition_verified"])
        self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_consumption")

        if external_checkpoint:
            self.assertEqual(driver.checkpoints, [])
            with patch.object(service_module, "choose_one_life_turn",
                              wraps=service_module.choose_one_life_turn) as premature_full:
                service.plan_turn()
            premature_full.assert_not_called()
            self.assertTrue(driver.require_initial_lifestyle_focus_before_date_advance)
            saved = service.save_checkpoint(expected_revision=driver.frame["revision"])
            self.assertTrue(saved["materialization"]["available"])
        self.assertEqual(len(driver.checkpoints), 1)

        with patch.object(service_module, "choose_one_life_turn",
                          wraps=service_module.choose_one_life_turn) as full_planner:
            consumed = service.plan_turn()
        self.assertEqual(consumed["plan"]["lifestyle_receipt_consumed"]["action_request_id"],
                         action_id)
        self.assertFalse(driver.require_initial_lifestyle_focus_before_date_advance)
        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "complete")
        full_planner.assert_called_once()
        self.assertEqual(driver.executed.count("save-checkpoint"), 1)
        self.assertEqual(driver.frame["date_raw"], _game_frame()["date_raw"])
        self.assertEqual(sum(row["command"] == FOCUS_SUBMIT_STEP
                             and row["result"]["status"] == "submitted_verification_pending"
                             for row in driver.history), 1)
        receipt_index = next(index for index, row in enumerate(driver.requests)
                             if row["step"] == RECEIPT_STEP)
        self.assertIn(STATE_QUERY_STEP, [row["step"]
                                      for row in driver.requests[receipt_index + 1:]])


if __name__ == "__main__":
    unittest.main()
