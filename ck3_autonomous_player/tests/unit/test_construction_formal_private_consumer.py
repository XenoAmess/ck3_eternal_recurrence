from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.driver import BridgeUnavailableError, StepPostconditionError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, SUBMIT_STEP, plan_construction_private, read_construction_ledger,
)


def frame(revision: int = 3, *, episode: str = "native-29829-e1") -> dict[str, object]:
    return {"paused": True, "map_ready": True, "snapshot_id": f"native:{revision}",
            "revision": revision, "native_revision": revision,
            "date_raw": 53_178_312, "episode_run_id": episode,
            "played_character": {"character_id": 29829, "alive": True},
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": []}


def root(revision: int = 3) -> list[dict[str, object]]:
    return [{"command": "query-campaign-root-context-v1", "ok": True,
             "result": {"campaign_root_context": {"status": "available",
                 "snapshot_revision": revision, "date_raw": 53_178_312,
                 "player_character_id": 29829, "government": {
                     "key": "feudal_government", "flags": ["government_is_feudal"]}}}}]


def world(revision: int = 3, *, active: bool = False) -> dict[str, object]:
    return {"status": "source_available", "snapshot_revision": revision,
            "date_raw": 53_178_312, "player_character_id": 29829,
            "native_final_legality_evaluated": True, "native_cost_evaluated": True,
            "checks_truncated": False, "player_gold_raw": 50_000_000,
            "legal_samples": [{"barony_title_id": 2103, "province_id": 2635,
                               "building_type_id": 24, "slot_index": 1,
                               "native_cost_observed": True,
                               "cost_raw_native": [15_000_000] + [0] * 9}],
            "active_constructions": [{"barony_title_id": 2103,
                "province_id": 2635, "active": active,
                "building_type_id": 24 if active else None,
                "slot_index": 1 if active else None,
                "initiator_character_id": 29829 if active else None}]}


class Driver:
    def __init__(self, directory: Path):
        self.state_dir = directory
        self.snapshot = frame()
        self.endpoint = self
        self.state = self
        self.command_timeout_seconds = 2.0
        self.requests: list[dict[str, object]] = []
        self.recorded = []
        self.timeout_action = False
        self.active_construction = False
        self.unknown_gold = False
        self.r753_truncated_samples = False

    def take_snapshot(self):
        return {**self.snapshot, "native_command_history": [
            {"command": step, "ok": True, "result": result}
            for step, result in self.recorded]}

    def capabilities(self):
        return {"action_steps": ["life-advance", "query-campaign-root-context-v1"],
                "bridge_capabilities": []}

    def send(self, request):
        self.requests.append(request)

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        if self.timeout_action and request["step"] == transport.ACTION_NATIVE:
            return None
        revision = request["expected_revision"]
        if request["step"] == transport.QUERY_NATIVE:
            result = {"step": transport.QUERY_NATIVE, "accepted": True,
                "private_probe": {"advertised": False,
                    "snapshot_revision": revision, "proof_epoch": revision,
                    "date_raw": 53_178_312,
                    "player_world_building_sources": {
                        **world(revision, active=revision >= 4 or self.active_construction),
                        **({"player_gold_raw": None} if self.unknown_gold else {}),
                        **({
                            "checks_truncated": True,
                            "final_legality_checks": 512,
                            "player_gold_raw": 50_035_659,
                            "legal_samples": [
                                {"barony_title_id": 2103, "province_id": 2635,
                                 "building_type_id": building, "slot_index": slot,
                                 "native_cost_observed": True,
                                 "cost_raw_native": [cost] + [0] * 9}
                                for building, cost in ((12, 40_000_000),
                                                       (24, 15_000_000))
                                for slot in (1, 2, 3)
                            ],
                        } if self.r753_truncated_samples else {}),
                    }}}
        else:
            result = {"step": transport.ACTION_NATIVE, "accepted": True,
                "private_probe": {"private_action": {
                    "status": "pending_receipt", "applied": False,
                    "advertised": False, "production_native_path": True,
                    "validator_calls": 1, "materialize_calls": 1, "receiver_calls": 1,
                    "receiver_command_sequence": 1, "proof_epoch": revision,
                    "actor_character_id": 29829, "barony_title_id": 2103,
                    "province_id": 2635, "building_type_id": 24,
                    "slot_index": 1, "stock_gold_cost_raw": 15_000_000,
                    "gold_before_raw": 50_000_000}}}
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": result}

    def _record_command(self, step, *, ok, result):
        self.recorded.append((step, result))


class ConstructionFormalConsumerTests(unittest.TestCase):
    def test_r753_truncated_scan_keeps_six_native_legal_cost_samples(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r753_truncated_samples = True
            query = transport.query_construction_private(driver, expected_revision=3)
            self.assertEqual(query["status"], "selected")
            self.assertTrue(query["world"]["checks_truncated"])
            self.assertEqual(query["world"]["final_legality_checks"], 512)
            self.assertEqual(len(query["world"]["legal_samples"]), 6)
            self.assertEqual(query["candidate"]["building_type_id"], 24)
            self.assertEqual(query["candidate"]["slot_index"], 1)
            self.assertEqual(query["candidate"]["stock_gold_cost_raw"], 15_000_000)
            self.assertEqual(query["candidate"]["gold_before_raw"], 50_035_659)

    def test_unknown_gold_is_red_not_no_legal_building(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.unknown_gold = True
            query = transport.query_construction_private(driver, expected_revision=3)
            self.assertEqual(query["status"], "source_red")

    def test_formal_service_selects_private_step_without_advertising(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.allow_private_construction_formal_trial = True
            driver.recorded.extend([(row["command"], row["result"]) for row in root()])
            service = GameplayBridgeService(driver)
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": "life-advance", "phase": "peacetime"}):
                planned = service.plan_turn()
            self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
            self.assertNotIn(SUBMIT_STEP, driver.capabilities()["action_steps"])
            with mock.patch.object(service, "plan_turn", return_value=planned), \
                 mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                outcome = service.auto_turn()
            self.assertEqual(outcome["selected_step"], SUBMIT_STEP)
            self.assertEqual(outcome["result"]["status"], "submitted_verification_pending")

    def test_scope_before_private_query_and_non_advertised_choice(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            planned = {"plan": {"selected_step": "life-advance"}, "revision": 3}
            root_plan = plan_construction_private(driver, planned, frame(), [],
                                                  {"query-campaign-root-context-v1"})
            self.assertEqual(root_plan["plan"]["selected_step"],
                             "query-campaign-root-context-v1")
            self.assertEqual(driver.requests, [])
            selected = plan_construction_private(driver, planned, frame(), root(), set())
            self.assertEqual(selected["plan"]["selected_step"], SUBMIT_STEP)
            self.assertEqual(driver.requests[0]["step"], transport.QUERY_NATIVE)
            self.assertNotIn("advertised", selected["plan"])

    def test_submit_receipt_next_turn_and_no_second_submit(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                chosen = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=chosen, expected_revision=3)
                self.assertEqual(pending["status"], "submitted_verification_pending")
                self.assertEqual(read_construction_ledger(driver.state_dir)["pending"], pending)
                with self.assertRaises(BridgeUnavailableError):
                    transport.submit_construction_private(driver, query=chosen,
                                                          expected_revision=3)
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 4}
                driver.snapshot = frame(4)
                receipt_plan = plan_construction_private(driver, planned, frame(4),
                                                        [], set())
                self.assertEqual(receipt_plan["plan"]["selected_step"], RECEIPT_STEP)
                receipt = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                self.assertTrue(receipt["postcondition_verified"])
                self.assertIsNone(read_construction_ledger(driver.state_dir)["pending"])
                consumed = plan_construction_private(driver, planned, frame(4), [], set())
                self.assertEqual(consumed["plan"]["selected_step"], "life-advance")
                self.assertEqual(consumed["plan"]["construction_receipt_consumed"], receipt)
                driver.allow_private_construction_formal_trial = True
                service = GameplayBridgeService(driver)
                with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                                return_value={"selected_step": "life-advance"}), \
                     mock.patch("xar_autoplayer.bridge.service.construction_process_identity",
                                return_value=(123, "t1")):
                    following = service.plan_turn()
                self.assertEqual(following["plan"]["construction_receipt_consumed"], receipt)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)

    def test_lost_ack_stays_pending_across_cold_process_and_requires_material(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.timeout_action = True
            with mock.patch.object(transport, "_identity", side_effect=[
                    (123, "t1"), (124, "t2"), (124, "t2")]):
                chosen = transport.query_construction_private(driver, expected_revision=3)
                with self.assertRaises(StepPostconditionError):
                    transport.submit_construction_private(driver, query=chosen,
                                                          expected_revision=3)
                pending = read_construction_ledger(driver.state_dir)["pending"]
                self.assertEqual(pending["status"], "action_state_unknown")
                driver.snapshot = frame(1)
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 1}
                cold_plan = plan_construction_private(driver, planned, frame(1), [], set())
                self.assertEqual(cold_plan["plan"]["selected_step"], RECEIPT_STEP)
                with self.assertRaises(BridgeUnavailableError):
                    transport.query_construction_receipt(
                        driver, pending=pending, expected_revision=1)
                self.assertEqual(read_construction_ledger(driver.state_dir)["pending"], pending)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)

    def test_cold_restore_material_receipt_on_new_process_epoch(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", side_effect=[
                    (123, "t1"), (124, "t2"), (124, "t2")]):
                chosen = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(driver, query=chosen,
                                                                expected_revision=3)
                driver.snapshot = frame(1)
                driver.active_construction = True
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 1}
                next_plan = plan_construction_private(driver, planned, frame(1), [], set())
                self.assertEqual(next_plan["plan"]["selected_step"], RECEIPT_STEP)
                receipt = transport.query_construction_receipt(driver, pending=pending,
                                                               expected_revision=1)
                self.assertEqual(receipt["post_proof_epoch"], 1)
                self.assertTrue(receipt["postcondition_verified"])

    def test_restoring_older_checkpoint_clears_stale_applied_only_after_material_read(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", side_effect=[
                    (123, "t1"), (123, "t1"), (124, "t2"), (124, "t2")]):
                chosen = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(driver, query=chosen,
                                                                expected_revision=3)
                driver.snapshot = frame(4)
                receipt = transport.query_construction_receipt(driver, pending=pending,
                                                               expected_revision=4)
                self.assertEqual(receipt["status"], "applied")
                driver.snapshot = frame(1)
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 1}
                cold_plan = plan_construction_private(driver, planned, frame(1), [], set())
                self.assertEqual(cold_plan["plan"]["selected_step"], RECEIPT_STEP)
                restored = transport.query_construction_receipt(driver, pending=receipt,
                                                                expected_revision=1)
                self.assertEqual(restored["status"], "restored_before_action")
                self.assertIsNone(read_construction_ledger(driver.state_dir)["applied"])
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)


if __name__ == "__main__":
    unittest.main()
