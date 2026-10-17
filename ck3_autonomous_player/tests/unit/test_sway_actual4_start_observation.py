"""Portable public-source adoption of the P49 .4 serializer composition.

Native envelopes and OS boundaries are synthetic. The planner, transports,
formal ledger, lifecycle observer and following consumer are production code.
"""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import types
import unittest

from test_ordinary_sway_service_v1 import (
    ACTOR, ClosedShapeDriver, overlay_for, service,
)

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools"))
from g2_saved_campaign.sway_start_typed_classifier_v1 import (
    classify_ordinary_sway_start_applied_v1,
)
from xar_autoplayer.bridge import active_scheme_sway_private_transport as query_transport
from xar_autoplayer.bridge import active_scheme_sway_formal_private_transport as action_transport
from xar_autoplayer.sway_formal_consumer import (
    _resolved_instance_identity, read_sway_ledger,
)


class ActualSerializerShapeDriver(ClosedShapeDriver):
    """Real .4 serializer fields with in-memory request/reply values."""

    def __init__(self, path):
        super().__init__(path)
        self.sent = {}
        self.native_wires = []
        self.wrong_after_instance = False
        self.endpoint = types.SimpleNamespace(send=self.send)
        self.state = types.SimpleNamespace(wait_for_command_result=self.wait_result)

    def send(self, request):
        if self.in_planning:
            raise ValueError("Native transport invoked under planning lock")
        self.sent[request["request_id"]] = copy.deepcopy(request)

    def wait_result(self, request_id, timeout_seconds):
        request = self.sent.pop(request_id)
        step = request["step"]
        self.capture += 1
        if step.startswith(query_transport.STEP_PREFIX):
            self.queries += 1
            value = {
                "schema": query_transport.SCHEMA,
                "snapshot_revision": self.native_revision,
                "capture_epoch": self.capture, "container_generation": 1,
                "date_raw": self.date, "actor_character_id": ACTOR,
                "target_character_id": self.target,
                "target_opinion_of_actor": self.opinion,
                "active_scheme_count": int(self.active),
                "matching_sway_active": self.active,
                "native_complete_can_send": not self.active,
                "native_legal_now": not self.active,
                "native_failure_classification": "" if not self.active else "native_complete_validator_rejected",
                "active_sway_instances": ([{
                    "scheme_instance_id": 16777234 if self.wrong_after_instance else 16777233,
                    "scheme_instance_generation": 1, "target_character_id": self.target,
                    "progress": 0, "progress_goal": 100,
                    "is_exposed": False, "is_frozen": False,
                }] if self.active else []),
            }
            envelope = {
                "step": step, "accepted": True, "status": "available",
                "private_build": True, "read_only": True, "advertised": False,
                "active_scheme_sway": value, "backend_id": "native-headless",
            }
        else:
            value = {"schema": action_transport.SCHEMA, "action_id": request["action_id"]}
            if step.startswith(action_transport.SUBMIT_PREFIX):
                self.submits += 1
                self.active = True
                self.action_id = request["action_id"]
                value.update(
                    stage="submitted_verification_pending",
                    actor_character_id=ACTOR, target_character_id=self.target,
                    pre_capture_epoch=self.capture, pre_container_generation=1,
                    pre_date_raw=self.date, submit_call_count=1, receipt_pending=True,
                )
            elif step.startswith(action_transport.RECEIPT_PREFIX):
                self.receipts += 1
                value.update(
                    stage="applied", post_capture_epoch=self.capture,
                    post_container_generation=1, post_date_raw=self.date,
                    scheme_instance_id=16777233, scheme_instance_generation=1,
                    postcondition_verified=True,
                )
                # Actual .4 receipt serializer has no actor/target fields.
            else:
                raise ValueError("unhandled synthetic transport step: " + step)
            envelope = {
                "step": step, "accepted": True, "status": value["stage"],
                "private_build": True, "advertised": False,
                "active_scheme_sway_formal": value, "backend_id": "native-headless",
            }
        frame = {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True, "result": envelope,
        }
        self.native_wires.append({"request": request, "response": copy.deepcopy(frame)})
        return frame

    def query_active_scheme_sway_target_private_v1(self, **kwargs):
        return query_transport.query_active_scheme_sway_target_private_v1(self, **kwargs)

    def submit_active_scheme_sway_private_v1(self, **kwargs):
        return action_transport.submit_active_scheme_sway_private_v1(self, **kwargs)

    def query_active_scheme_sway_receipt_private_v1(self, **kwargs):
        return action_transport.query_active_scheme_sway_receipt_private_v1(self, **kwargs)


def classify(body, driver):
    frame = body["planning_source_frame"]
    return classify_ordinary_sway_start_applied_v1(
        body,
        initial_frame={"actor_character_id": ACTOR, "episode_run_id": frame["episode_run_id"]},
        game_pid=frame["bridge_pid"],
    )


class PublicActual4StartAdoption(unittest.TestCase):
    def test_full_planner_real_transports_retained_identity_and_following(self):
        with tempfile.TemporaryDirectory(prefix="sway-public-actual4-") as temp:
            driver = ActualSerializerShapeDriver(Path(temp))
            ordinary = service(driver)
            first = ordinary.auto_turn(before_submit=overlay_for(driver))
            self.assertEqual(first["selected_step"], "ordinary-sway-opportunity-v1")
            raw_receipt = copy.deepcopy(first["result"]["native_receipt"])
            self.assertNotIn("actor_character_id", raw_receipt)
            self.assertNotIn("target_character_id", raw_receipt)
            identity = _resolved_instance_identity(first["result"])
            self.assertEqual((identity["actor_character_id"], identity["target_character_id"]),
                             (ACTOR, driver.target))
            self.assertEqual(first["result"]["native_receipt"], raw_receipt)
            credit = classify(first, driver)
            self.assertEqual(credit["category"], "sway_start_applied_primitive")
            self.assertFalse(credit["sway_terminal_observed"])
            self.assertFalse(credit["sway_material_benefit_verified"])
            second = ordinary.auto_turn(before_submit=overlay_for(driver))
            self.assertEqual(second["selected_step"], "life-advance")
            retained = read_sway_ledger(driver.state_dir)["resolved"]
            self.assertTrue(retained["next_turn_consumed"])
            self.assertTrue(retained["latest_instance_observation"]["tracked_instance_active"])
            self.assertEqual(retained["native_receipt"], raw_receipt)
            self.assertEqual(retained["applied_instance_observation"]["scheme_instance_id"], 16777233)
            # A new Service instance reopens the retained ledger; this is file
            # persistence only, not a CK3 cold restore or runtime claim.
            reopened = service(driver)
            reopened.auto_turn()
            self.assertEqual((driver.submits, driver.receipts, driver.completions), (1, 1, 1))

    def test_other_independent_instance_retains_pending_without_repeat_start(self):
        with tempfile.TemporaryDirectory(prefix="sway-public-mismatch-") as temp:
            driver = ActualSerializerShapeDriver(Path(temp))
            driver.wrong_after_instance = True
            ordinary = service(driver)
            result = ordinary.auto_turn()
            optional = result["ordinary_sway_optional"]["result"]
            self.assertEqual(optional["status"], "postcondition_pending")
            self.assertFalse(optional["postcondition_verified"])
            retained = read_sway_ledger(driver.state_dir)
            self.assertIsNotNone(retained["pending"])
            self.assertIsNone(retained["resolved"])
            self.assertEqual(driver.submits, 1)
            # Existing cadence waits before the read-only pending recovery.
            ordinary.auto_turn()
            self.assertEqual(driver.submits, 1)

    def test_public_credit_rejects_identity_drift_without_changing_original(self):
        with tempfile.TemporaryDirectory(prefix="sway-public-credit-") as temp:
            driver = ActualSerializerShapeDriver(Path(temp))
            body = service(driver).auto_turn()
            before = copy.deepcopy(body)
            for path, value in (
                (("result", "applied_instance_observation", "scheme_instance_generation"), 2),
                (("result", "native_receipt", "exe_sha256"), "0" * 64),
                (("planning_source_frame", "bridge_pid"), True),
            ):
                mutated = copy.deepcopy(body)
                cursor = mutated
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = value
                with self.subTest(path=path), self.assertRaises(ValueError):
                    classify(mutated, driver)
            self.assertEqual(body, before)
            self.assertEqual(driver.submits, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
