from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_construction_province_income_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, StepPostconditionError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
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
                "initiator_character_id": 29829 if active else None,
                "native_province_monthly_income_observed": True,
                "native_province_monthly_income_raw": 2_468_000}],
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
        self.province_income_after_completion_raw = None
        self.province_income_unavailable = False

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
                if self.province_income_after_completion_raw is not None:
                    source["active_constructions"][0][
                        "native_province_monthly_income_raw"] = (
                            self.province_income_after_completion_raw)
            if self.province_income_unavailable:
                source["active_constructions"][0][
                    "native_province_monthly_income_observed"] = False
                source["active_constructions"][0][
                    "native_province_monthly_income_raw"] = None
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
                    "initiator_character_id": 29829 if post else None,
                    "native_remaining_work_raw": 87_000_000 if post else None,
                    "native_progress_divisor_raw": 120_000 if post else None}]
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
    def test_blocked_war_plan_still_observes_same_frame_m5_building(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.allow_private_m5_joint_collector = True
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.snapshot["player_armies"] = [{"army_id": 791}]
            baseline = {"plan": {"selected_step": None,
                                 "reason": "war forecast inputs blocked"},
                        "revision": 3}
            observed = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())["plan"]
            self.assertIsNone(observed["selected_step"])
            self.assertEqual(observed["reason"], "war forecast inputs blocked")
            self.assertEqual(observed["construction_wartime_observation"]
                             ["native_source_status"], "selected")
            self.assertFalse(observed["construction_wartime_observation"]
                             ["formal_action_ready"])
            repeated = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())["plan"]
            self.assertEqual(repeated["construction_wartime_observation"],
                             observed["construction_wartime_observation"])
            self.assertEqual([row["step"] for row in driver.requests],
                             [transport.QUERY_NATIVE])
            driver.allow_private_m5_joint_collector = False
            without_m5 = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())["plan"]
            self.assertNotIn("construction_wartime_observation", without_m5)
            self.assertEqual(len(driver.requests), 1)

    def test_wartime_construction_observes_native_choice_without_spend(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.snapshot["player_armies"] = [{"army_id": 791}]
            baseline = {"plan": {"selected_step": "query-army-strengths-v1"},
                        "revision": 3}
            first = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())
            plan = first["plan"]
            observation = plan["construction_wartime_observation"]
            self.assertEqual(plan["selected_step"], "query-army-strengths-v1")
            self.assertEqual(observation["status"], "observed")
            self.assertEqual(observation["native_source_status"], "selected")
            self.assertEqual(observation["candidate"]["stock_gold_cost_raw"],
                             15_000_000)
            self.assertEqual(observation["candidate"]
                             ["authored_monthly_income_hundredths"], 35)
            self.assertEqual(observation["observed_active_war_count"], 1)
            self.assertEqual(observation["observed_player_army_count"], 1)
            self.assertIsNone(observation["war_future_gold_cost_raw"])
            self.assertIsNone(observation["existing_shared_gold_commitment_raw"])
            self.assertEqual(observation["joint_budget_affordability"],
                             "unassessed")
            self.assertEqual(observation["native_proof_epoch"], 30)
            self.assertTrue(observation["native_query_request_id"].startswith(
                "construction-read-"))
            self.assertFalse(observation["formal_action_ready"])
            self.assertEqual([row["step"] for row in driver.requests],
                             [transport.QUERY_NATIVE])
            again = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())
            self.assertEqual(again["plan"]["construction_wartime_observation"],
                             observation)
            self.assertEqual(len(driver.requests), 1)
            with self.assertRaisesRegex(BridgeUnavailableError,
                                         "stable admitted paused actor frame"):
                transport.query_construction_private(driver, expected_revision=3)

    def test_wartime_one_shot_can_include_source_world_without_spend(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.snapshot["player_armies"] = [{"army_id": 83886367}]
            observation = transport.query_construction_wartime_observation_private(
                driver, expected_revision=3, include_world=True)
            self.assertEqual(observation["status"], "observed")
            self.assertEqual(observation["world"]["player_gold_raw"],
                             observation["observed_player_gold_raw"])
            self.assertTrue(observation["world"]["legal_samples"])
            self.assertEqual([row["step"] for row in driver.requests],
                             [transport.QUERY_NATIVE])

    def test_wartime_construction_cash_mismatch_is_read_only_red(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.gold_override = 49_000_000
            baseline = {"plan": {"selected_step": "query-army-strengths-v1"},
                        "revision": 3}
            observation = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())[
                    "plan"]["construction_wartime_observation"]
            self.assertEqual(observation["status"], "source_red")
            self.assertEqual(observation["reason"], "same_frame_cash_mismatch")
            self.assertIsNone(observation["candidate"])
            self.assertFalse(observation["formal_action_ready"])
            self.assertFalse(any(row["step"] == transport.ACTION_NATIVE
                                 for row in driver.requests))

    def test_wartime_construction_rejects_actor_mismatch_after_native_query(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            source = transport.query_construction_private(
                driver, expected_revision=3, wartime_observation=True)
            source["source_frame"]["actor_character_id"] = 99999
            with mock.patch.object(transport, "query_construction_private",
                                   return_value=source):
                observation = transport.query_construction_wartime_observation_private(
                    driver, expected_revision=3)
            self.assertEqual(observation["status"], "source_red")
            self.assertEqual(observation["reason"], "same_frame_binding_mismatch")
            self.assertIsNone(observation["candidate"])
            self.assertFalse(observation["formal_action_ready"])

    def test_wartime_native_validation_red_keeps_diagnostic(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.unknown_gold = True
            observation = transport.query_construction_wartime_observation_private(
                driver, expected_revision=3)
            self.assertEqual(observation["status"], "source_red")
            self.assertEqual(observation["reason"],
                             "native_construction_source_validation_failed")
            self.assertEqual(observation["native_source_status"], "source_red")
            raw = json.loads(Path(observation["raw_artifact_path"])
                             .read_text(encoding="utf-8"))
            self.assertIsNone(raw["native_result"]["private_probe"]
                              ["player_world_building_sources"]["player_gold_raw"])
            self.assertEqual(observation["raw_artifact_sha256"],
                             transport.sha256_file(Path(observation["raw_artifact_path"])))
            self.assertEqual(observation["native_validation_diagnostic"]
                             ["world_status"], "source_available")
            self.assertNotIn("native_result", observation)
            self.assertEqual(observation["ending_frame"]["snapshot_id"],
                             "native:3")
            self.assertIsNone(observation["candidate"])

    def test_wartime_native_red_compacts_large_result_but_keeps_raw_artifact(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.unknown_gold = True
            source = transport.query_construction_private(
                driver, expected_revision=3, wartime_observation=True)
            native = source["native_result"]["private_probe"]
            native["player_world_building_sources"]["holdings"] = [
                {"marker": "large-raw-only", "index": index}
                for index in range(4096)]
            with mock.patch.object(transport, "query_construction_private",
                                   return_value=source):
                observation = transport.query_construction_wartime_observation_private(
                    driver, expected_revision=3)
            compact = json.dumps(observation)
            self.assertLess(len(compact), 4000)
            self.assertNotIn("large-raw-only", compact)
            self.assertEqual(observation["reason"],
                             "native_construction_source_validation_failed")
            raw = json.loads(Path(observation["raw_artifact_path"])
                             .read_text(encoding="utf-8"))
            self.assertEqual(len(raw["native_result"]["private_probe"]
                                 ["player_world_building_sources"]["holdings"]), 4096)

    def test_wartime_no_candidate_and_incomplete_coverage_stay_distinct(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.no_positive_building = True
            baseline = {"plan": {"selected_step": "query-army-strengths-v1"},
                        "revision": 3}
            complete = plan_construction_private(
                driver, baseline, driver.snapshot, [], set())[
                    "plan"]["construction_wartime_observation"]
            self.assertEqual(complete["status"], "observed")
            self.assertEqual(complete["native_source_status"],
                             "no_legal_budgeted_building")
            self.assertIsNone(complete["candidate"])
            driver.positive_coverage_incomplete = True
            driver.snapshot = frame(4)
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.snapshot["date_raw"] = 53_178_336
            driver.snapshot["played_character_gold"]["raw"] = 35_000_000
            incomplete = plan_construction_private(
                driver, {**baseline, "revision": 4}, driver.snapshot, [], set())[
                    "plan"]["construction_wartime_observation"]
            self.assertEqual(incomplete["status"], "observed")
            self.assertEqual(incomplete["native_source_status"],
                             "evidence_insufficient")
            self.assertIsNone(incomplete["candidate"])
            self.assertIs(incomplete["positive_income_coverage_complete"], False)

    def test_formal_service_retains_war_step_with_read_only_building_observation(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.allow_private_construction_formal_trial = True
            driver.capabilities = lambda: {
                "action_steps": ["query-army-strengths-v1"],
                "bridge_capabilities": []}
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value={"selected_step": "query-army-strengths-v1",
                                          "phase": "wartime"}):
                planned = GameplayBridgeService(driver).plan_turn()["plan"]
            self.assertEqual(planned["selected_step"], "query-army-strengths-v1")
            self.assertEqual(planned["construction_wartime_observation"]
                             ["native_source_status"], "selected")
            self.assertFalse(planned["construction_wartime_observation"]
                             ["formal_action_ready"])
            self.assertEqual([row["step"] for row in driver.requests],
                             [transport.QUERY_NATIVE])

    def test_private_province_aggregate_binds_completed_row_to_paused_frame(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            driver.completed_construction = True
            result = _ck3_query_construction_province_income_private_v1(
                mock.Mock(driver=driver), expected_revision=3,
                barony_title_id=2103, province_id=2635)
            self.assertEqual(result["status"], "observed")
            self.assertEqual(result["native_province_monthly_income_raw"], 2_468_000)
            self.assertEqual(result["source_frame"]["snapshot_id"], "native:3")
            self.assertEqual(result["source_frame"]["actor_character_id"], 29829)
            self.assertEqual(driver.requests[-1]["step"], transport.QUERY_NATIVE)

    def test_formal_receipt_retains_target_province_aggregate_through_completion_and_cold_read(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                before = pending["pre_province_income_observation"]
                self.assertEqual(before["native_province_monthly_income_raw"],
                                 2_468_000)
                self.assertEqual(before["snapshot_id"], "native:3")
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                self.assertEqual(start["completion_status"], "in_progress")
                self.assertIsNone(start["observed_province_monthly_income_delta_raw"])

                later = frame(5)
                later["date_raw"] += 31 * 24
                driver.snapshot = later
                driver.completed_construction = True
                driver.province_income_after_completion_raw = 2_504_000
                completed = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(completed["completion_status"], "completed")
                self.assertEqual(completed["construction_province_income_observation"], {
                    "status": "observed", "barony_title_id": 2103,
                    "province_id": 2635, "snapshot_id": "native:5",
                    "native_revision": 5, "date_raw": later["date_raw"],
                    "native_province_monthly_income_raw": 2_504_000,
                })
                self.assertEqual(completed[
                    "observed_province_monthly_income_delta_raw"], 36_000)
                self.assertEqual(read_construction_ledger(driver.state_dir)
                                 ["applied"]["observed_province_monthly_income_delta_raw"],
                                 36_000)

            driver.snapshot = frame(1)
            driver.snapshot["date_raw"] = later["date_raw"]
            driver.province_income_unavailable = True
            with mock.patch.object(transport, "_identity", return_value=(124, "t2")):
                cold = transport.query_construction_receipt(
                    driver, pending=completed, expected_revision=1)
            self.assertEqual(cold["construction_province_income_observation"],
                             completed["construction_province_income_observation"])
            self.assertEqual(cold["observed_province_monthly_income_delta_raw"],
                             36_000)
            self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                 for row in driver.requests), 1)

    def test_first_completion_with_unreadable_province_income_keeps_delta_unknown(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=root(3)[0]["result"])
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)

                later = frame(5)
                later["date_raw"] += 31 * 24
                driver.snapshot = later
                driver.completed_construction = True
                driver.province_income_unavailable = True
                later_root = root(5)[0]["result"]
                later_root["campaign_root_context"]["date_raw"] = later["date_raw"]
                later_root["campaign_root_context"][
                    "player_monthly_gold_income"]["raw"] = 1_050_000
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=later_root)
                completed = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)

                self.assertEqual(completed["completion_status"], "completed")
                self.assertEqual(completed["construction_province_income_observation"]
                                 ["status"], "unavailable")
                self.assertIsNone(completed["observed_province_monthly_income_delta_raw"])
                self.assertEqual(completed["observed_player_monthly_income_delta_raw"],
                                 50_000)
                self.assertEqual(completed["completion_observed_date_raw"],
                                 later["date_raw"])

                next_day = frame(6)
                next_day["date_raw"] = later["date_raw"] + 24
                driver.snapshot = next_day
                not_due = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 6}, next_day, [], set())
                self.assertNotEqual(not_due["plan"]["selected_step"], RECEIPT_STEP)

                later_month = frame(7)
                later_month["date_raw"] = later["date_raw"] + 30 * 24
                driver.snapshot = later_month
                due = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 7}, later_month, [], set())
                self.assertEqual(due["plan"]["selected_step"], RECEIPT_STEP)
                driver.province_income_unavailable = False
                driver.province_income_after_completion_raw = 2_504_000
                refreshed = transport.query_construction_receipt(
                    driver, pending=completed, expected_revision=7)
                self.assertEqual(refreshed["observed_province_monthly_income_delta_raw"],
                                 36_000)
                self.assertEqual(refreshed["completion_observed_date_raw"],
                                 later["date_raw"])

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
            self.assertEqual(receipt["construction_progress_observation"], {
                "status": "observed", "snapshot_id": "native:4",
                "native_revision": 4, "date_raw": frame(4)["date_raw"],
                "native_remaining_work_raw": 87_000_000,
                "native_progress_divisor_raw": 120_000,
            })
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
            self.assertEqual(read_construction_ledger(restored.state_dir)["applied"]
                             ["construction_progress_observation"]["status"], "observed")
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

    def test_uncovered_positive_definitions_preserve_evidence_and_selected_step(self):
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
            self.assertEqual(normal["plan"]["selected_step"], "life-advance")
            self.assertEqual(normal["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")
            war_step = "declare-war-123-4-0"
            prewar = {"plan": {"selected_step": war_step}, "revision": 3}
            result = plan_construction_private(driver, prewar, frame(), root(), set(),
                                               prewar_arbitration=True)
            self.assertEqual(result["plan"]["selected_step"], war_step)
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

    def test_service_preserves_normal_step_with_incomplete_construction_after_family_chance(self):
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
            self.assertEqual(planned["plan"]["selected_step"], "life-advance")
            self.assertEqual(planned["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")
            self.assertEqual(planned["plan"]["phase"], "peacetime")
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

    def test_service_prewar_incomplete_construction_keeps_war_after_family_chance(self):
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
            self.assertEqual(planned["plan"]["selected_step"], war_step)
            self.assertIn("construction_prewar_arbitration", planned["plan"], planned)
            self.assertEqual(planned["plan"]["construction_prewar_arbitration"]
                             ["original_selected_step"], war_step)
            self.assertEqual(planned["plan"]["construction_private_query"]["status"],
                             "evidence_insufficient")

    def test_incomplete_construction_world_preserves_and_executes_normal_advance(self):
        class OrdinaryAdvanceDriver(Driver):
            def __init__(self, directory):
                super().__init__(directory)
                self.ordinary_executions = []

            def execute_step(self, step, *, expected_revision):
                if step != "life-advance" or expected_revision != self.snapshot["revision"]:
                    raise AssertionError("expected the retained ordinary advance")
                self.ordinary_executions.append((step, expected_revision))
                self.snapshot.update(
                    revision=expected_revision + 1,
                    native_revision=self.snapshot["native_revision"] + 1,
                    date_raw=self.snapshot["date_raw"] + 24,
                )
                self.snapshot["snapshot_id"] = f"native:{self.snapshot['native_revision']}"
                return {"step": step, "days_advanced": 1}

        with TemporaryDirectory() as location:
            directory = Path(location)
            driver = OrdinaryAdvanceDriver(directory)
            driver.allow_private_construction_formal_trial = True
            driver.no_positive_building = True
            driver.positive_coverage_incomplete = True
            driver.snapshot["diagnostics"] = {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }}
            driver.snapshot["active_wars"] = [{"war_id": 16777231}]
            driver.snapshot["player_armies"] = [{"army_id": 218104048}]
            driver.recorded.extend([(row["command"], row["result"]) for row in root()])
            write_construction_ledger(directory, read_construction_ledger(directory))
            ledger_path = directory / "construction-formal-pending-v1.json"
            ledger_before = ledger_path.read_bytes()
            date_before = driver.snapshot["date_raw"]
            # The entering plan is an ordinary clock after movement was deferred;
            # this fixture does not replace it with the unselected army move.
            baseline = {"selected_step": "life-advance", "phase": "peacetime",
                        "reason": "ordinary advance after projected contact deferred movement"}
            with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",
                            return_value=baseline):
                outcome = GameplayBridgeService(driver).auto_turn()

            self.assertEqual(outcome["status"], "executed")
            self.assertEqual(outcome["selected_step"], baseline["selected_step"])
            for field in ("selected_step", "phase", "reason"):
                self.assertEqual(outcome["plan"][field], baseline[field])
            query = outcome["plan"]["construction_private_query"]
            self.assertEqual(query["status"], "evidence_insufficient")
            self.assertEqual(query["reason"], "positive_income_candidate_coverage_incomplete")
            self.assertEqual(query["exact_ck3_build"], CK3_12004.game_version)
            self.assertEqual(query["exe_sha256"], CK3_12004.executable_sha256)
            self.assertIsNone(query.get("candidate"))
            self.assertIs(query["world"]["positive_income_coverage_complete"], False)
            self.assertIs(query["world"]["checks_truncated"], True)
            self.assertEqual(query["world"]["legal_samples"][0]["building_key"],
                             "military_camps_01")
            self.assertEqual([row["step"] for row in driver.requests],
                             [transport.QUERY_NATIVE])
            self.assertEqual(driver.ordinary_executions, [("life-advance", 3)])
            self.assertEqual(driver.snapshot["date_raw"], date_before + 24)
            self.assertEqual(ledger_path.read_bytes(), ledger_before)

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
                self.assertEqual(receipt["construction_progress_observation"]
                                 ["status"], "unavailable")
                self.assertIsNone(receipt["construction_progress_observation"]
                                  ["native_progress_divisor_raw"])
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
                # The first building remains active. A second receipt must
                # retain its completion and income follow-up across restarts.
                ledger = read_construction_ledger(driver.state_dir)
                self.assertEqual(ledger["applied"], second_receipt)
                self.assertEqual(ledger["applied_prior"], [receipt])

            cold_frame = frame(7)
            cold_frame["date_raw"] += 48
            driver.snapshot = cold_frame
            with mock.patch.object(transport, "_identity", return_value=(124, "t2")):
                cold_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"}, "revision": 7},
                    cold_frame, [], set())
                self.assertEqual(cold_plan["plan"]["selected_step"], RECEIPT_STEP)
                self.assertEqual(cold_plan["plan"]["construction_pending_action"]
                                 ["action_request_id"], receipt["action_request_id"])
                first_cold = transport.query_construction_receipt(
                    driver, pending=receipt, expected_revision=7)
                self.assertEqual(first_cold["candidate"]["province_id"], 2635)
                self.assertEqual(read_construction_ledger(driver.state_dir)
                                 ["applied_prior"][0], first_cold)
                second_cold_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"}, "revision": 7},
                    cold_frame, [], set())
                self.assertEqual(second_cold_plan["plan"]["selected_step"], RECEIPT_STEP)
                self.assertEqual(second_cold_plan["plan"]["construction_pending_action"]
                                 ["action_request_id"], second_receipt["action_request_id"])
                second_cold = transport.query_construction_receipt(
                    driver, pending=second_receipt, expected_revision=7)
                self.assertEqual(second_cold["candidate"]["province_id"], 2700)
                self.assertEqual(read_construction_ledger(driver.state_dir)
                                 ["applied"], second_cold)

                due_frame = frame(8)
                due_frame["date_raw"] = cold_frame["date_raw"] + 30 * 24
                driver.snapshot = due_frame
                first_watch_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"}, "revision": 8},
                    due_frame, [], set())
                self.assertEqual(first_watch_plan["plan"]["selected_step"], RECEIPT_STEP)
                self.assertEqual(first_watch_plan["plan"]["construction_pending_action"]
                                 ["action_request_id"], receipt["action_request_id"])
                first_watch = transport.query_construction_receipt(
                    driver, pending=first_cold, expected_revision=8)
                self.assertEqual(first_watch["completion_status"], "in_progress")
                second_watch_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"}, "revision": 8},
                    due_frame, [], set())
                self.assertEqual(second_watch_plan["plan"]["selected_step"], RECEIPT_STEP)
                self.assertEqual(second_watch_plan["plan"]["construction_pending_action"]
                                 ["action_request_id"], second_receipt["action_request_id"])

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
                later["date_raw"] += 31 * 24
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
                self.assertEqual(done["construction_progress_observation"]["status"],
                                 "not_active")
                self.assertIsNone(done["construction_progress_observation"]
                                  ["native_remaining_work_raw"])
                self.assertEqual(done["completion_observed_date_raw"], later["date_raw"])
                self.assertEqual(done["observed_player_monthly_income_delta_raw"], 50_000)
                self.assertEqual(done["start_receipt"]["completion_status"], "in_progress")
                self.assertEqual(read_construction_ledger(driver.state_dir)["applied"], done)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)

    def test_due_completion_receipt_is_consumed_during_war_turn(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=root(3)[0]["result"])
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                later = frame(5)
                later["date_raw"] += 30 * 24
                later["active_wars"] = [{"war_id": 48}]
                driver.snapshot = later
                driver.completed_construction = True
                war_step = "query-army-strengths-v1"
                planned = {"plan": {"selected_step": war_step}, "revision": 5}
                modal = {**later, "active_event": {"instance_id": 9}}
                event_plan = {"plan": {"selected_step": "select-event-option-1"},
                              "revision": 5}
                self.assertEqual(plan_construction_private(
                    driver, event_plan, modal, [], {ROOT_QUERY_STEP}), event_plan)
                need_income = plan_construction_private(
                    driver, planned, later, [], {ROOT_QUERY_STEP})
                self.assertEqual(need_income["plan"]["selected_step"], ROOT_QUERY_STEP)
                later_root = root(5)[0]
                later_root["result"]["campaign_root_context"]["date_raw"] = later["date_raw"]
                later_root["result"]["campaign_root_context"][
                    "player_monthly_gold_income"]["raw"] = 1_050_000
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=later_root["result"])
                watch = plan_construction_private(
                    driver, planned, later, [later_root], {ROOT_QUERY_STEP})
                self.assertEqual(watch["plan"]["selected_step"], RECEIPT_STEP)
                completed = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(completed["completion_status"], "completed")
                self.assertEqual(completed["observed_player_monthly_income_delta_raw"], 50_000)
                after = plan_construction_private(
                    driver, planned, later, [later_root], {ROOT_QUERY_STEP})
                self.assertEqual(after["plan"]["selected_step"], war_step)
                self.assertEqual(after["plan"]["construction_receipt_consumed"], completed)
                with self.assertRaises(BridgeUnavailableError):
                    transport.query_construction_private(
                        driver, expected_revision=5)
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
                later["date_raw"] += 31 * 24
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

    def test_cold_war_restore_rechecks_existing_construction_before_monthly_watch(self):
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
            later["date_raw"] += 9 * 24
            later["active_wars"] = [{"war_id": 48}]
            later["player_armies"] = [{"army_id": 16777237}]
            driver.snapshot = later
            war_step = "query-army-strengths-v1"
            with mock.patch.object(transport, "_identity", return_value=(124, "t2")):
                plan = plan_construction_private(
                    driver, {"plan": {"selected_step": war_step}, "revision": 5},
                    later, [], set())
                self.assertEqual(plan["plan"]["selected_step"], RECEIPT_STEP)
                cold = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
            self.assertEqual(cold["completion_status"], "in_progress")
            self.assertEqual(cold["post_bridge_pid"], 124)
            self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                 for row in driver.requests), 1)

    def test_cold_completion_without_root_income_is_followed_up_same_day(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=root(3)[0]["result"])
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
            later = frame(5)
            later["date_raw"] += 31 * 24
            driver.snapshot = later
            driver.completed_construction = True
            planned = {"plan": {"selected_step": "life-advance"}, "revision": 5}
            with mock.patch.object(transport, "_identity", return_value=(124, "t2")):
                cold = plan_construction_private(driver, planned, later, [], set())
                self.assertEqual(cold["plan"]["selected_step"], RECEIPT_STEP)
                completed = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(completed["completion_status"], "completed")
                self.assertIsNone(completed["observed_player_monthly_gold_income_raw"])
                self.assertIsNone(completed["observed_player_monthly_income_delta_raw"])

                need_income = plan_construction_private(
                    driver, planned, later, [], {ROOT_QUERY_STEP})
                self.assertEqual(need_income["plan"]["selected_step"], ROOT_QUERY_STEP)
                later_root = root(5)[0]
                later_root["result"]["campaign_root_context"]["date_raw"] = later["date_raw"]
                later_root["result"]["campaign_root_context"][
                    "player_monthly_gold_income"]["raw"] = 1_050_000
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=later_root["result"])
                followup = plan_construction_private(
                    driver, planned, later, [later_root], {ROOT_QUERY_STEP})
                self.assertEqual(followup["plan"]["selected_step"], RECEIPT_STEP)
                income = transport.query_construction_receipt(
                    driver, pending=completed, expected_revision=5)
                self.assertEqual(income["completion_observed_date_raw"], later["date_raw"])
                self.assertEqual(income["observed_player_monthly_gold_income_raw"], 1_050_000)
                self.assertEqual(income["observed_player_monthly_income_delta_raw"], 50_000)
                self.assertEqual(sum(row["step"] == transport.ACTION_NATIVE
                                     for row in driver.requests), 1)

    def test_cold_completed_recheck_preserves_prior_actual_income(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=root(3)[0]["result"])
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
                completed_frame = frame(5)
                completed_frame["date_raw"] += 31 * 24
                driver.snapshot = completed_frame
                driver.completed_construction = True
                completed_root = root(5)[0]["result"]
                completed_root["campaign_root_context"]["date_raw"] = completed_frame["date_raw"]
                completed_root["campaign_root_context"][
                    "player_monthly_gold_income"]["raw"] = 1_050_000
                driver._record_command(ROOT_QUERY_STEP, ok=True, result=completed_root)
                complete = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(complete["observed_player_monthly_income_delta_raw"], 50_000)

            restored_frame = frame(1)
            restored_frame["date_raw"] = completed_frame["date_raw"]
            driver.snapshot = restored_frame
            with mock.patch.object(transport, "_identity", return_value=(124, "t2")):
                cold = transport.query_construction_receipt(
                    driver, pending=complete, expected_revision=1)
            self.assertEqual(cold["completion_status"], "completed")
            self.assertEqual(cold["completion_observed_date_raw"], completed_frame["date_raw"])
            self.assertEqual(cold["observed_player_monthly_gold_income_raw"], 1_050_000)
            self.assertEqual(cold["observed_player_monthly_income_delta_raw"], 50_000)
            self.assertEqual(cold["income_observed_date_raw"], completed_frame["date_raw"])

    def test_cold_material_rechecks_keep_the_original_monthly_watch_due_date(self):
        with TemporaryDirectory() as location:
            driver = Driver(Path(location))
            with mock.patch.object(transport, "_identity", return_value=(123, "t1")):
                selected = transport.query_construction_private(driver, expected_revision=3)
                pending = transport.submit_construction_private(
                    driver, query=selected, expected_revision=3)
                driver.snapshot = frame(4)
                start = transport.query_construction_receipt(
                    driver, pending=pending, expected_revision=4)
            start_date = start["completion_last_check_date_raw"]

            for revision, elapsed, identity in (
                    (5, 10 * 24, (124, "t2")),
                    (6, 20 * 24, (125, "t3"))):
                later = frame(revision)
                later["date_raw"] = start_date + elapsed
                driver.snapshot = later
                with mock.patch.object(transport, "_identity", return_value=identity):
                    cold = transport.query_construction_receipt(
                        driver, pending=start, expected_revision=revision)
                self.assertEqual(cold["completion_status"], "in_progress")
                self.assertEqual(cold["post_date_raw"], later["date_raw"])
                self.assertEqual(cold["completion_last_check_date_raw"], start_date)
                start = cold

            due = frame(7)
            due["date_raw"] = start_date + 30 * 24
            driver.snapshot = due
            with mock.patch.object(transport, "_identity", return_value=(126, "t4")):
                plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 7}, due, [], set())
                self.assertEqual(plan["plan"]["selected_step"], RECEIPT_STEP)
                watched = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=7)
            self.assertEqual(watched["completion_last_check_date_raw"], due["date_raw"])

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
                # R0240 watched after only nine game days: raw dates advance
                # by 24 per day, not by one. That read consumed a formal turn.
                premature = frame(5)
                premature["date_raw"] += 9 * 24
                driver.snapshot = premature
                premature_plan = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 5}, premature, [], set())
                self.assertNotEqual(premature_plan["plan"]["selected_step"],
                                    RECEIPT_STEP)
                with self.assertRaisesRegex(BridgeUnavailableError,
                                            "later monthly frame"):
                    transport.query_construction_receipt(
                        driver, pending=start, expected_revision=5)
                later = frame(5)
                later["date_raw"] += 30 * 24
                driver.snapshot = later
                at_boundary = plan_construction_private(
                    driver, {"plan": {"selected_step": "life-advance"},
                             "revision": 5}, later, [], set())
                self.assertEqual(at_boundary["plan"]["selected_step"], RECEIPT_STEP)
                still_active = transport.query_construction_receipt(
                    driver, pending=start, expected_revision=5)
                self.assertEqual(still_active["completion_status"], "in_progress")
                self.assertEqual(still_active["start_receipt"]["post_proof_epoch"],
                                 start["post_proof_epoch"])
                next_day = frame(6)
                next_day["date_raw"] += 31 * 24
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
