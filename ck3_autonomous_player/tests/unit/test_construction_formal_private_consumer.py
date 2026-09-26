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
    RECEIPT_STEP, ROOT_QUERY_STEP, SUBMIT_STEP,
    plan_construction_private, read_construction_ledger,
    write_construction_ledger,
)


def frame(revision: int = 3, *, episode: str = "native-29829-e1",
          public_revision: int | None = None) -> dict[str, object]:
    return {"paused": True, "map_ready": True, "snapshot_id": f"native:{revision}",
            "revision": revision if public_revision is None else public_revision,
            "native_revision": revision,
            "date_raw": 53_178_312, "episode_run_id": episode,
            "played_character": {"character_id": 29829, "alive": True},
            "played_character_gold": {"raw": 50_000_000, "scale": 100_000},
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": []}


def root(revision: int = 3) -> list[dict[str, object]]:
    return [{"command": "query-campaign-root-context-v1", "ok": True,
             "result": {"campaign_root_context": {"status": "available",
                 "snapshot_revision": revision, "date_raw": 53_178_312,
                 "player_character_id": 29829,
                 "player_monthly_gold_income": {"raw": 1_000_000, "scale": 100_000},
                 "government": {
                     "key": "feudal_government", "flags": ["government_is_feudal"]}}}}]


def world(revision: int = 3, *, active: bool = False) -> dict[str, object]:
    return {"status": "source_available", "snapshot_revision": revision,
            "date_raw": 53_178_312, "player_character_id": 29829,
            "native_final_legality_evaluated": True, "native_cost_evaluated": True,
            "checks_truncated": False, "positive_income_coverage_complete": True,
            "player_gold_raw": 35_000_000 if active else 50_000_000,
            "legal_samples": [{"barony_title_id": 2103, "province_id": 2635,
                               "building_type_id": 24, "slot_index": 1,
                               "building_key": "common_tradeport_01",
                               "native_cost_observed": True,
                               "cost_raw_native": [15_000_000] + [0] * 9}],
            "active_constructions": [{"barony_title_id": 2103,
                "province_id": 2635, "active": active,
                "building_type_id": 24 if active else None,
                "slot_index": 1 if active else None,
                "initiator_character_id": 29829 if active else None}],
            "completed_buildings_observed": True,
            "completed_buildings": []}


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
        self.completed_construction = False
        self.completed_source_unavailable = False
        self.unknown_gold = False
        self.r753_truncated_samples = False
        self.r0080_material_without_cost = False
        self.second_building_available = False
        self.no_positive_building = False
        self.r0227_material_without_completion = False
        self.positive_coverage_incomplete = False
        self.gold_override = None

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
        query_epoch = (
            4662 if self.r753_truncated_samples and revision == 3
            else 4682 if self.r753_truncated_samples and revision == 4
            else 7474 if self.r0080_material_without_cost and revision == 3
            else 7616 if self.r0080_material_without_cost and revision == 4
            else revision * 10
        )
        if request["step"] == transport.QUERY_NATIVE:
            source = world(revision, active=(revision >= 4 or self.active_construction)
                           and not self.completed_construction)
            source["date_raw"] = self.snapshot["date_raw"]
            if self.no_positive_building:
                source["legal_samples"][0]["building_key"] = "military_camps_01"
            if self.positive_coverage_incomplete:
                source["positive_income_coverage_complete"] = False
                source["checks_truncated"] = True
            if self.completed_construction:
                source["completed_buildings"] = [{
                    "barony_title_id": 2103, "province_id": 2635,
                    "building_type_id": 24, "slot_index": 1}]
            if self.completed_source_unavailable:
                source["completed_buildings_observed"] = False
                source["completed_buildings"] = None
            if self.r0227_material_without_completion:
                post = revision >= 4 or self.active_construction
                source["player_gold_raw"] = 24_490_601 if post else 34_490_601
                source["completed_buildings_observed"] = False
                source["completed_buildings"] = None
                source["active_constructions"] = [{
                    "barony_title_id": 2174, "province_id": 2629,
                    "active": post, "building_type_id": 628 if post else None,
                    "slot_index": 1 if post else None,
                    "initiator_character_id": 29829 if post else None}]
                source["legal_samples"] = [] if post else [{
                    "barony_title_id": 2174, "province_id": 2629,
                    "building_type_id": 628, "slot_index": 1,
                    "building_key": "hill_farms_01",
                    "native_cost_observed": True,
                    "cost_raw_native": [10_000_000] + [0] * 9}]
            if self.gold_override is not None:
                source["player_gold_raw"] = self.gold_override
            if self.second_building_available and revision >= 5:
                source["date_raw"] = self.snapshot["date_raw"]
                source["player_gold_raw"] = 25_000_000 if revision >= 6 else 35_000_000
                second_sample = {
                    "barony_title_id": 2200, "province_id": 2700,
                    "building_type_id": 30, "slot_index": 2,
                    "building_key": "orchards_01",
                    "native_cost_observed": True,
                    "cost_raw_native": [10_000_000] + [0] * 9,
                }
                source["legal_samples"] = [] if revision >= 6 else [second_sample]
                source["active_constructions"].append({
                    "barony_title_id": 2200, "province_id": 2700,
                    "active": revision >= 6,
                    "building_type_id": 30 if revision >= 6 else None,
                    "slot_index": 2 if revision >= 6 else None,
                    "initiator_character_id": 29829 if revision >= 6 else None,
                })
            result = {"step": transport.QUERY_NATIVE, "accepted": True,
                "private_probe": {"advertised": False,
                    "snapshot_revision": revision, "proof_epoch": query_epoch,
                    "date_raw": self.snapshot["date_raw"],
                    "player_world_building_sources": {
                        **source,
                        **({
                            "checks_truncated": True,
                            "final_legality_checks": 512,
                            "player_gold_raw": (35_035_659 if revision >= 4
                                                else 50_035_659),
                            "legal_samples": [
                                {"barony_title_id": 2103, "province_id": 2635,
                                 "building_type_id": building, "slot_index": slot,
                                 "building_key": ("farm_estates_01" if building == 12
                                                  else "common_tradeport_01"),
                                 "native_cost_observed": True,
                                 "cost_raw_native": [cost] + [0] * 9}
                                for building, cost in ((12, 40_000_000),
                                                       (24, 15_000_000))
                                for slot in (1, 2, 3)
                            ],
                        } if (self.r753_truncated_samples or
                              (self.r0080_material_without_cost and revision == 3))
                           else {}),
                        **({
                            "checks_truncated": True,
                            "final_legality_checks": 512,
                            "native_cost_evaluated": False,
                            "native_cost_checks": 0,
                            "player_gold_raw": 35_035_659,
                            "legal_samples": [],
                        } if self.r0080_material_without_cost and revision == 4
                           else {}),
                        **({"player_gold_raw": None} if self.unknown_gold else {}),
                    }}}
        else:
            second = self.second_building_available and revision >= 5
            result = {"step": transport.ACTION_NATIVE, "accepted": True,
                "private_probe": {"private_action": {
                    "status": "pending_receipt", "applied": False,
                    "advertised": False, "production_native_path": True,
                    "validator_calls": 1, "materialize_calls": 1, "receiver_calls": 1,
                    "receiver_command_sequence": 1,
                    "proof_epoch": (4664 if self.r753_truncated_samples
                                    else 7476 if self.r0080_material_without_cost
                                    else query_epoch + 2),
                    "actor_character_id": 29829,
                    "barony_title_id": (2174 if self.r0227_material_without_completion
                                        else 2200 if second else 2103),
                    "province_id": (2629 if self.r0227_material_without_completion
                                    else 2700 if second else 2635),
                    "building_type_id": (628 if self.r0227_material_without_completion
                                         else 30 if second else 24),
                    "slot_index": 2 if second else 1,
                    "stock_gold_cost_raw": (10_000_000 if
                                            self.r0227_material_without_completion
                                            or second else 15_000_000),
                    "gold_before_raw": (
                        34_490_601 if self.r0227_material_without_completion else
                        35_000_000 if second else
                        50_035_659 if (self.r753_truncated_samples or
                                       self.r0080_material_without_cost)
                        else 50_000_000
                    )}}}
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": result}

    def _record_command(self, step, *, ok, result):
        self.recorded.append((step, result))


class ConstructionFormalConsumerTests(unittest.TestCase):
    def test_unavailable_completed_observer_keeps_prewar_legality_and_start_source(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.completed_source_unavailable = True
            planned = {"plan": {"selected_step": "query-declarable-wars"},
                       "revision": 3}
            selected = plan_construction_private(
                driver, planned, frame(), root(), set(),
                prewar_arbitration=True)
            self.assertEqual(selected["plan"]["selected_step"], SUBMIT_STEP)
            world_source = selected["plan"]["construction_private_query"]["world"]
            self.assertIs(world_source["completed_buildings_observed"], False)
            self.assertIsNone(world_source["completed_buildings"])
            receipt = transport.query_construction_private(
                driver, expected_revision=3, material_receipt=True)
            self.assertEqual(receipt["status"], "material_source")
            self.assertIsNone(receipt["world"]["completed_buildings"])

    def test_r0227_active_tuple_and_exact_spend_apply_start_receipt_only(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r0227_material_without_completion = True
            with mock.patch.object(transport, "_identity", return_value=(146040, "c4")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                self.assertEqual(selected["candidate"], {
                    "barony_title_id": 2174, "province_id": 2629,
                    "building_type_id": 628, "slot_index": 1,
                    "stock_gold_cost_raw": 10_000_000,
                    "gold_before_raw": 34_490_601,
                    "building_key": "hill_farms_01",
                    "authored_monthly_income_hundredths": 35})
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                driver.snapshot["played_character_gold"]["raw"] = 24_490_601
                material = transport.query_construction_private(
                    driver, expected_revision=4, material_receipt=True)
                self.assertEqual(material["status"], "material_source")
                self.assertIs(material["world"]["completed_buildings_observed"], False)
                self.assertIsNone(material["world"]["completed_buildings"])
                self.assertEqual(material["world"]["player_gold_raw"], 24_490_601)
                receipt = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
            self.assertEqual(receipt["status"], "applied")
            self.assertTrue(receipt["postcondition_verified"])
            self.assertEqual(receipt["completion_status"], "in_progress")
            self.assertIsNone(receipt["completion_observed_date_raw"])
            self.assertIsNone(receipt["observed_player_monthly_income_delta_raw"])
            self.assertEqual(receipt["post_player_gold_raw"], 24_490_601)
            self.assertIsNone(read_construction_ledger(driver.state_dir)["pending"])
            self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                 for row in driver.requests), 1)

    def test_r0227_cold_restore_reads_active_and_spend_without_resubmitting(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r0227_material_without_completion = True
            with mock.patch.object(transport, "_identity", return_value=(146040, "c4")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
            restored = Driver(Path(location))
            restored.r0227_material_without_completion = True
            restored.active_construction = True
            restored.snapshot = frame(1)
            restored.snapshot["played_character_gold"]["raw"] = 24_490_601
            with mock.patch.object(transport, "_identity", return_value=(146041, "c5")):
                receipt = transport.query_construction_receipt(
                    restored, pending=pending, expected_revision=1)
            self.assertEqual(receipt["completion_status"], "in_progress")
            self.assertEqual(receipt["post_player_gold_raw"], 24_490_601)
            self.assertIsNone(read_construction_ledger(restored.state_dir)["pending"])
            self.assertFalse(any(row["step"] == transport.ACTION_NATIVE
                                 for row in restored.requests))

    def test_r0227_same_day_active_without_spend_keeps_pending(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r0227_material_without_completion = True
            with mock.patch.object(transport, "_identity", return_value=(146040, "c4")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                driver.gold_override = 34_490_601
                with self.assertRaisesRegex(BridgeUnavailableError,
                                             "gold spend not verified"):
                    transport.query_construction_receipt(
                        driver, pending=pending, expected_revision=4)
            self.assertEqual(read_construction_ledger(driver.state_dir)["pending"],
                             pending)

    def test_prewar_query_step_consumes_positive_building_before_war_query(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            baseline = {"plan": {"policy": "one-life-turn-v1",
                                  "selected_step": "query-declarable-wars"},
                        "revision": 3}
            self.assertEqual(plan_construction_private(
                driver, baseline, frame(), root(), set()), baseline)
            selected = plan_construction_private(
                driver, baseline, frame(), root(), set(),
                prewar_arbitration=True)
            plan = selected["plan"]
            self.assertEqual(plan["selected_step"], SUBMIT_STEP)
            self.assertEqual(plan["construction_private_query"]["status"], "selected")
            budget = plan["construction_prewar_arbitration"]
            self.assertEqual(budget["status"], "selected_positive_budgeted_building")
            self.assertEqual(budget["original_selected_step"], "query-declarable-wars")
            self.assertEqual(budget["observed_player_gold_raw"], 50_000_000)
            self.assertEqual(budget["construction_gold_cost_raw"], 15_000_000)
            self.assertEqual(budget["construction_minimum_gold_reserve_raw"],
                             transport.RESERVE_RAW)
            self.assertEqual(budget["gold_after_construction_raw"], 35_000_000)
            self.assertEqual(budget["authored_monthly_income_hundredths"], 35)
            self.assertIsNone(budget["war_future_gold_cost_raw"])
            self.assertIsNone(budget["additional_shared_gold_commitment_raw"])
            self.assertFalse(any(row["step"] == transport.ACTION_NATIVE
                                 for row in driver.requests))

    def test_prewar_typed_declaration_observes_budget_and_preserves_war_if_empty(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            war_step = "declare-war-123-4-0"
            baseline = {"plan": {"policy": "one-life-turn-v1",
                                  "selected_step": war_step}, "revision": 3}
            driver.no_positive_building = True
            result = plan_construction_private(
                driver, baseline, frame(), root(), set(),
                prewar_arbitration=True)
            self.assertEqual(result["plan"]["selected_step"], war_step)
            self.assertEqual(result["plan"]["construction_prewar_arbitration"]["status"],
                             "no_positive_budgeted_building")
            driver.no_positive_building = False
            driver.gold_override = 50_000_000
            mismatched_cash = frame()
            mismatched_cash["played_character_gold"]["raw"] = 49_000_000
            result = plan_construction_private(
                driver, baseline, mismatched_cash, root(), set(),
                prewar_arbitration=True)
            self.assertEqual(result["plan"]["selected_step"], war_step)
            self.assertEqual(result["plan"]["construction_prewar_arbitration"]["status"],
                             "same_frame_cash_or_positive_value_unavailable")
            driver.gold_override = 30_000_000
            low_cash = frame()
            low_cash["played_character_gold"]["raw"] = 30_000_000
            result = plan_construction_private(
                driver, baseline, low_cash, root(), set(),
                prewar_arbitration=True)
            self.assertEqual(result["plan"]["selected_step"], war_step)
            self.assertEqual(result["plan"]["construction_prewar_arbitration"]["status"],
                             "no_positive_budgeted_building")

    def test_uncovered_positive_definitions_preserve_red_instead_of_advancing(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.no_positive_building = True
            driver.positive_coverage_incomplete = True
            query = transport.query_construction_private(driver, expected_revision=3)
            self.assertEqual(query["status"], "evidence_insufficient")
            self.assertEqual(query["reason"],
                             "positive_income_candidate_coverage_incomplete")
            baseline = {"plan": {"selected_step": "life-advance"}, "revision": 3}
            normal = plan_construction_private(driver, baseline, frame(), root(), set())
            self.assertIsNone(normal["plan"]["selected_step"])
            self.assertEqual(normal["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")
            war_step = "declare-war-123-4-0"
            prewar = {"plan": {"selected_step": war_step}, "revision": 3}
            result = plan_construction_private(driver, prewar, frame(), root(), set(),
                                               prewar_arbitration=True)
            self.assertIsNone(result["plan"]["selected_step"])
            self.assertEqual(result["plan"]["construction_prewar_arbitration"]["status"],
                             "positive_income_coverage_incomplete")

    def test_prewar_scope_query_and_unrelated_step_do_not_submit(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            baseline = {"plan": {"policy": "one-life-turn-v1",
                                  "selected_step": "declare-war-123-4-0"},
                        "revision": 3}
            query = plan_construction_private(
                driver, baseline, frame(), [], {ROOT_QUERY_STEP},
                prewar_arbitration=True)
            self.assertEqual(query["plan"]["selected_step"], ROOT_QUERY_STEP)
            self.assertEqual(query["plan"]["construction_prewar_arbitration"]["status"],
                             "root_query_needed")
            unavailable = plan_construction_private(
                driver, baseline, frame(), [], set(), prewar_arbitration=True)
            self.assertEqual(unavailable["plan"]["selected_step"],
                             "declare-war-123-4-0")
            unrelated = {"plan": {"selected_step": "query-army"}, "revision": 3}
            self.assertEqual(plan_construction_private(
                driver, unrelated, frame(), root(), set(),
                prewar_arbitration=True), unrelated)
            self.assertFalse(driver.requests)

    def test_prewar_pending_action_requires_receipt_before_competing_spend(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            pending = {"episode_run_id": frame()["episode_run_id"],
                       "source_bridge_pid": 123,
                       "source_bridge_creation_date": "t1",
                       "pre_native_revision": 3}
            write_construction_ledger(driver.state_dir, {
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": pending, "applied": None})
            baseline = {"plan": {"selected_step": "query-declarable-wars"},
                        "revision": 3}
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                waiting = plan_construction_private(
                    driver, baseline, frame(), root(), set(),
                    prewar_arbitration=True)
                self.assertIsNone(waiting["plan"]["selected_step"])
                self.assertEqual(waiting["plan"]["construction_prewar_arbitration"]["status"],
                                 "pending_action_needs_later_receipt")
                later = plan_construction_private(
                    driver, baseline, frame(4), root(4), set(),
                    prewar_arbitration=True)
                self.assertEqual(later["plan"]["selected_step"], RECEIPT_STEP)
            self.assertFalse(driver.requests)

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
            self.assertEqual(query["candidate"]["building_key"],
                             "common_tradeport_01")
            self.assertEqual(query["candidate"]["authored_monthly_income_hundredths"],
                             35)

    def test_affordable_positive_income_beats_cheapest_and_unknown(self):
        source = world()
        source["legal_samples"] = [
            {**source["legal_samples"][0], "building_type_id": 30,
             "building_key": "military_camps_01", "cost_raw_native":
             [8_000_000] + [0] * 9},
            {**source["legal_samples"][0], "building_type_id": 24,
             "building_key": "common_tradeport_01"},
            {**source["legal_samples"][0], "building_type_id": 12,
             "building_key": "farm_estates_01", "cost_raw_native":
             [20_000_000] + [0] * 9},
        ]
        selected = transport._candidate(source)
        self.assertEqual(selected["building_type_id"], 12)
        self.assertEqual(selected["authored_monthly_income_hundredths"], 70)
        source["legal_samples"][2]["building_key"] = "unknown_01"
        self.assertEqual(transport._candidate(source)["building_type_id"], 24)
        source["legal_samples"][1]["building_key"] = "unknown_02"
        self.assertIsNone(transport._candidate(source))

    def test_r753_query_ack_material_epochs_are_independent(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r753_truncated_samples = True
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                query = transport.query_construction_private(driver, expected_revision=3)
                self.assertEqual(query["proof_epoch"], 4662)
                pending = transport.submit_construction_private(
                    driver, query=query, expected_revision=3,
                )
                self.assertEqual(pending["status"], "submitted_verification_pending")
                self.assertEqual(pending["pre_proof_epoch"], 4664)
                self.assertEqual(read_construction_ledger(driver.state_dir)["pending"], pending)
                driver.snapshot = frame(4)
                receipt = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4,
                )
                self.assertEqual(receipt["post_proof_epoch"], 4682)
                self.assertTrue(receipt["postcondition_verified"])

    def test_r0080_active_build_receipt_needs_no_new_cost_sample(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r0080_material_without_cost = True
            with mock.patch.object(transport, "_identity", return_value=(33820, "r0080")):
                selected = transport.query_construction_private(
                    driver, expected_revision=3)
                self.assertEqual(selected["status"], "selected")
                self.assertEqual(selected["candidate"]["gold_before_raw"], 50_035_659)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                self.assertEqual(pending["pre_proof_epoch"], 7476)
                driver.snapshot = frame(4)
                old_candidate_query = transport.query_construction_private(
                    driver, expected_revision=4)
                self.assertEqual(old_candidate_query["status"], "source_red")
                native_world = old_candidate_query["native_result"]["private_probe"][
                    "player_world_building_sources"]
                self.assertEqual(native_world["status"], "source_available")
                self.assertFalse(native_world["native_cost_evaluated"])
                self.assertEqual(native_world["legal_samples"], [])
                self.assertTrue(native_world["active_constructions"][0]["active"])
                material = transport.query_construction_private(
                    driver, expected_revision=4, material_receipt=True)
                self.assertEqual(material["status"], "material_source")
                self.assertEqual(material["proof_epoch"], 7616)
                receipt = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                self.assertEqual(receipt["status"], "applied")
                self.assertTrue(receipt["postcondition_verified"])
                self.assertEqual(receipt["action_request_id"],
                                 pending["action_request_id"])
                self.assertEqual(receipt["post_player_gold_raw"], 35_035_659)
                self.assertEqual(read_construction_ledger(driver.state_dir)["applied"],
                                 receipt)
                self.assertIsNone(read_construction_ledger(driver.state_dir)["pending"])
                self.assertEqual(
                    sum(request["step"] == transport.ACTION_NATIVE
                        for request in driver.requests), 1)

    def test_r0080_material_mode_still_rejects_unknown_gold(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.r0080_material_without_cost = True
            driver.snapshot = frame(4)
            driver.unknown_gold = True
            query = transport.query_construction_private(
                driver, expected_revision=4, material_receipt=True)
            self.assertEqual(query["status"], "source_red")
            self.assertIsNone(query["native_result"]["private_probe"][
                "player_world_building_sources"]["player_gold_raw"])

    def test_unknown_gold_is_red_not_no_legal_building(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.unknown_gold = True
            query = transport.query_construction_private(driver, expected_revision=3)
            self.assertEqual(query["status"], "source_red")
            self.assertTrue(query["native_query_request_id"].startswith("construction-read-"))
            self.assertEqual(query["source_frame"]["snapshot_id"], "native:3")
            self.assertEqual(query["ending_frame"]["snapshot_id"], "native:3")

    def test_r0066_failed_material_source_retains_native_result_and_pending(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot = frame(9, episode="native-29829-ee172aa720db",
                                    public_revision=10)
            driver.snapshot["date_raw"] = 53_178_528
            pending = {
                "status": "submitted_verification_pending",
                "action_request_id": "construction-submit-a138bf862f7e4684a5ab2e1dcf57a0fa",
                "episode_run_id": "native-29829-ee172aa720db",
                "actor_character_id": 29829,
                "pre_native_revision": 3,
                "pre_date_raw": 53_178_312,
                "source_bridge_pid": 69072,
                "source_bridge_creation_date": "20260921215424.447443+000",
            }
            write_construction_ledger(driver.state_dir, {
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": pending, "applied": None,
            })
            # Synthetic failure payload: R0066 lost the actual native result.
            native_result = {"step": transport.QUERY_NATIVE,
                             "private_probe": {"player_world_building_sources": {
                                 "status": "unavailable", "failure": "fixture_only"}}}
            source_frame = {"snapshot_id": "native:9", "revision": 10,
                            "native_revision": 9, "date_raw": 53_178_528,
                            "episode_run_id": pending["episode_run_id"],
                            "actor_character_id": 29829}
            ending_frame = {"snapshot_id": "native:9", "revision": 10,
                            "episode_run_id": pending["episode_run_id"]}
            with mock.patch.object(driver, "_record_command",
                                   wraps=driver._record_command) as record, \
                 mock.patch.object(transport, "_identity", return_value=(
                    69072, "20260921215424.447443+000")), \
                 mock.patch.object(transport, "query_construction_private",
                                   return_value={"status": "source_red",
                                                 "native_query_request_id":
                                                     "construction-read-fixture-r0066",
                                                 "native_result": native_result,
                                                 "source_frame": source_frame,
                                                 "ending_frame": ending_frame}):
                with self.assertRaisesRegex(BridgeUnavailableError,
                                            "construction material source unavailable"):
                    transport.query_construction_receipt(
                        driver, pending=pending, expected_revision=10,
                    )
            self.assertEqual(read_construction_ledger(driver.state_dir)["pending"],
                             pending)
            self.assertEqual(driver.requests, [])
            step, failure = driver.recorded[-1]
            self.assertEqual(step, RECEIPT_STEP)
            self.assertEqual(failure["status"], "receipt_source_unavailable")
            self.assertEqual(failure["action_request_id"],
                             pending["action_request_id"])
            self.assertIs(record.call_args.kwargs["ok"], False)
            self.assertEqual(failure["stage"],
                             "construction_receipt_native_source_query")
            self.assertEqual(failure["native_query_status"], "source_red")
            self.assertEqual(failure["native_query_request_id"],
                             "construction-read-fixture-r0066")
            self.assertEqual(failure["native_result"], native_result)
            self.assertEqual(failure["source_frame"], source_frame)
            self.assertEqual(failure["ending_frame"], ending_frame)

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

    def test_service_preserves_incomplete_construction_red_after_family_chance(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.allow_private_construction_formal_trial = True
            driver.allow_private_family_marriage_formal_trial = True
            driver.no_positive_building = True
            driver.positive_coverage_incomplete = True
            driver.recorded.extend([(row["command"], row["result"]) for row in root()])
            service = GameplayBridgeService(driver)
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": "life-advance",
                                          "phase": "peacetime"}), \
                 mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private",
                            side_effect=lambda _driver, planned, _snapshot, **_kwargs:
                                planned) as family:
                planned = service.plan_turn()
            family.assert_called_once()
            self.assertIsNone(planned["plan"]["selected_step"])
            self.assertEqual(planned["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")
            self.assertIn("coverage incomplete", planned["plan"]["reason"])
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": "life-advance",
                                          "phase": "peacetime"}), \
                 mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private",
                            side_effect=lambda _driver, planned, _snapshot, **_kwargs:
                                {**planned, "plan": {**planned["plan"],
                                    "selected_step": "private-family-submit"}}):
                family_selected = service.plan_turn()
            self.assertEqual(family_selected["plan"]["selected_step"],
                             "private-family-submit")

    def test_service_prewar_incomplete_construction_blocks_war_after_family_chance(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.allow_private_construction_formal_trial = True
            driver.allow_private_family_marriage_formal_trial = True
            driver.no_positive_building = True
            driver.positive_coverage_incomplete = True
            driver.recorded.extend([(row["command"], row["result"]) for row in root()])
            service = GameplayBridgeService(driver)
            war_step = "query-declarable-wars"
            driver.capabilities = lambda: {
                "action_steps": ["life-advance", "query-campaign-root-context-v1",
                                 war_step], "bridge_capabilities": []}
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": war_step,
                                          "phase": "peacetime"}), \
                 mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private",
                            side_effect=lambda _driver, planned, _snapshot, **_kwargs:
                                planned) as family:
                planned = service.plan_turn()
            family.assert_called_once()
            self.assertIsNone(planned["plan"]["selected_step"])
            self.assertIn("construction_prewar_arbitration", planned["plan"], planned)
            self.assertEqual(planned["plan"]["construction_prewar_arbitration"]
                             ["original_selected_step"], war_step)
            self.assertEqual(planned["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")

    def test_r0060_public_revision_after_native_root_query_reaches_construction(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.allow_private_construction_formal_trial = True
            # R0060's real root query bound native:3 / public revision 4.
            driver.snapshot = frame(3, public_revision=4)
            driver.recorded.extend([(row["command"], row["result"]) for row in root(3)])
            service = GameplayBridgeService(driver)
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": "life-advance", "phase": "peacetime"}):
                planned = service.plan_turn()
            self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
            self.assertEqual(driver.requests[0]["step"], transport.QUERY_NATIVE)
            self.assertNotIn(SUBMIT_STEP, driver.capabilities()["action_steps"])

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

    def test_later_day_reopens_a_distinct_affordable_construction(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                first = transport.query_construction_private(driver, expected_revision=3)
                first_pending = transport.submit_construction_private(
                    driver, query=first, expected_revision=3)
                driver.snapshot = frame(4)
                receipt = transport.query_construction_receipt(
                    driver, pending=first_pending, expected_revision=4)
                same_frame = {"plan": {"selected_step": "life-advance"}, "revision": 4}
                before_queries = len(driver.requests)
                consumed = plan_construction_private(
                    driver, same_frame, frame(4), root(4), set())
                self.assertEqual(consumed["plan"]["selected_step"], "life-advance")
                self.assertEqual(len(driver.requests), before_queries)

                later = frame(5)
                later["date_raw"] += 24
                driver.snapshot = later
                driver.second_building_available = True
                later_root = root(5)
                later_root[0]["result"]["campaign_root_context"]["date_raw"] = later["date_raw"]
                later_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"}, "revision": 5},
                    later, later_root, set())
                self.assertEqual(later_plan["plan"]["selected_step"], SUBMIT_STEP)
                self.assertEqual(later_plan["plan"]["construction_receipt_consumed"], receipt)
                self.assertEqual(later_plan["plan"]["construction_private_query"]["candidate"]["province_id"], 2700)
                second_pending = transport.submit_construction_private(
                    driver, query=later_plan["plan"]["construction_private_query"],
                    expected_revision=5)
                self.assertNotEqual(second_pending["action_request_id"],
                                    first_pending["action_request_id"])
                self.assertEqual(read_construction_ledger(driver.state_dir)["pending"],
                                 second_pending)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 2)
                later_material = frame(6)
                later_material["date_raw"] += 48
                driver.snapshot = later_material
                second_receipt = transport.query_construction_receipt(
                    driver, pending=second_pending, expected_revision=6)
                self.assertEqual(second_receipt["candidate"]["province_id"], 2700)
                self.assertEqual(second_receipt["post_player_gold_raw"], 25_000_000)
                self.assertTrue(second_receipt["postcondition_verified"])
                self.assertIsNone(read_construction_ledger(driver.state_dir)["pending"])

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
                self.assertEqual(receipt["post_proof_epoch"], 10)
                self.assertTrue(receipt["postcondition_verified"])

    def test_completed_slot_is_consumed_on_monthly_formal_watch(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                driver._record_command("query-campaign-root-context-v1", ok=True,
                                       result=root(3)[0]["result"])
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                self.assertEqual(pending["pre_player_monthly_gold_income_raw"], 1_000_000)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                self.assertEqual(start["completion_status"], "in_progress")
                later = frame(5)
                later["date_raw"] += 31
                driver.snapshot = later
                driver.completed_construction = True
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 5}
                need_income = plan_construction_private(
                    driver, planned, later, [], {"query-campaign-root-context-v1"})
                self.assertEqual(need_income["plan"]["selected_step"],
                                 "query-campaign-root-context-v1")
                later_root = root(5)[0]
                later_root["result"]["campaign_root_context"]["date_raw"] = later["date_raw"]
                later_root["result"]["campaign_root_context"][
                    "player_monthly_gold_income"]["raw"] = 1_050_000
                driver._record_command("query-campaign-root-context-v1", ok=True,
                                       result=later_root["result"])
                watch = plan_construction_private(
                    driver, planned, later, [later_root], {"query-campaign-root-context-v1"})
                self.assertEqual(watch["plan"]["selected_step"], RECEIPT_STEP)
                done = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(done["status"], "applied")
                self.assertEqual(done["completion_status"], "completed")
                self.assertEqual(done["completion_observed_date_raw"], later["date_raw"])
                self.assertEqual(done["observed_player_monthly_income_delta_raw"], 50_000)
                self.assertEqual(done["start_receipt"]["completion_status"], "in_progress")
                self.assertEqual(read_construction_ledger(driver.state_dir)["applied"], done)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)

    def test_cold_restore_after_completion_reads_built_slot(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", side_effect=[
                    (123, "t1"), (123, "t1"), (124, "t2"), (124, "t2")]):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                later = frame(5)
                later["date_raw"] += 31
                driver.snapshot = later
                driver.completed_construction = True
                planned = {"plan": {"selected_step": "life-advance"}, "revision": 5}
                cold = plan_construction_private(driver, planned, later, [], set())
                self.assertEqual(cold["plan"]["selected_step"], RECEIPT_STEP)
                done = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(done["completion_status"], "completed")
                self.assertEqual(done["post_bridge_pid"], 124)
                self.assertIsNone(read_construction_ledger(driver.state_dir)["pending"])

    def test_monthly_watch_keeps_active_start_proof_and_defers_next_read(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                later = frame(5)
                later["date_raw"] += 31
                driver.snapshot = later
                still_active = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(still_active["completion_status"], "in_progress")
                self.assertEqual(still_active["start_receipt"]["post_proof_epoch"],
                                 start["post_proof_epoch"])
                next_day = frame(6)
                next_day["date_raw"] += 32
                plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 6}, next_day, [], set())
                self.assertNotEqual(plan["plan"]["selected_step"], RECEIPT_STEP)

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

    def test_unobserved_completed_slots_cannot_prove_rollback_after_restore(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", side_effect=[
                    (123, "t1"), (123, "t1"), (124, "t2")]):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                receipt = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                driver.snapshot = frame(1)
                driver.completed_construction = True
                driver.completed_source_unavailable = True
                with self.assertRaisesRegex(BridgeUnavailableError,
                                             "material not yet observed"):
                    transport.query_construction_receipt(
                        driver, pending=receipt, expected_revision=1)
            self.assertEqual(read_construction_ledger(driver.state_dir)["applied"],
                             receipt)


if __name__ == "__main__":
    unittest.main()
