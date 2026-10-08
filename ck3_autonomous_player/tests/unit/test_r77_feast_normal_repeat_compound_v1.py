"""Root FIRST0: normal Service repeat, wartime budget and durable no-resend.

Authored, not run by the source owner. Native frames/reads, the ordinary baseline
and the physical Commit are fixture seams; this gives no new native/live credit.
"""
from copy import deepcopy
import json
from unittest.mock import patch

from xar_autoplayer import activity_feast_stage5_start_formal_consumer as consumer
from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_SCHEMA, POST_SCHEMA, RESOURCE_KEYS, START_STEP, POST_STEP,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.activity_feast_ordinary_v1 import OPEN_STEP
from xar_autoplayer.environment import write_json_atomic


class FeastDriver:
    allow_private_activity_feast_stage5_start_action = True
    allow_private_activity_feast_stage5_start_query = True
    allow_private_activity_feast_lifecycle_observation = True
    nonwar_only = False

    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.command_timeout_seconds = 1
        self.frame = {
            "backend_id": "native-headless", "snapshot_id": "native:40",
            "revision": 41, "native_revision": 40, "date_raw": 53288544,
            "paused": True, "map_ready": True, "played_character": {
                "character_id": 29829, "alive": True},
            "exact_ck3_build": "1.20.0.4",
            "ck3_executable_sha256": CK3_12004.executable_sha256,
            "active_wars": [{"war_id": 100663329}],
            "active_event": None, "pending_character_interaction": None,
            "one_life_terminal": False, "one_life_terminal_reason": None,
            "episode_projection": "native_campaign", "history": [],
            "native_command_history": [], "player_armies": [],
            "episode_run_id": "r77-feast-normal-repeat-compound",
            "episode_character_id": 29829,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256}},
        }
        self.gold = 150_000_000
        self.cost = 10_000_000
        self.activity_id = None
        self.post_visible = False
        self.completed = False
        self.can_start = True
        self.commits = []
        self.root_reads = []
        self.planning_stage = None
        self.configuration_requests = []
        self.endpoint = self
        self.state = self

    def query_activity_planner_diag_private_v1(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        return {"planner_status": "planner_absent" if self.planning_stage is None else "observed",
                "planning_stage": self.planning_stage,
                "host_view_activity_key": None if self.planning_stage is None else "activity_feast",
                "date_raw": self.frame["date_raw"]}

    def query_activity_feast_hosted_post_private_v1(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        return self.post()

    def send(self, request):
        self.configuration_requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        request = self.configuration_requests[-1]
        assert request["request_id"] == request_id
        assert request["expected_revision"] == self.frame["native_revision"]
        step = request["step"]
        base = {"snapshot_revision": self.frame["native_revision"],
                "date_raw": self.frame["date_raw"], "actor_character_id": 29829}
        option = {"activity_key": "activity_feast", "selected_option_key": "feast_type_generic"}
        if step == OPEN_STEP:
            assert self.planning_stage is None
            self.planning_stage = 1
            key, read_only = "activity_feast_planner_open", False
            native = {**base, "schema": "activity-feast-planner-open-private-v1",
                      "open_status": "opened", "native_dispatch_invoked": True,
                      "selected_feast_verified": True, "widget_attached": True,
                      "widget_visible": True, "planning_stage": 1,
                      "configured_cost_state": "unknown", "final_can_start_state": "unknown",
                      "raw_pointer_fields_persisted": False}
        elif step == "query-activity-stage1-option-v1-private":
            assert self.planning_stage == 1
            key, read_only = "activity_stage1_option", True
            native = {**base, **option, "schema": "activity-stage1-option-private-read-v1",
                      "planning_stage": 1, "selected_option_shown": True,
                      "selected_option_valid": True, "can_progress_stage1": True,
                      "generic_feast_confirm_ready": True, "read_only": True,
                      "raw_pointer_fields_persisted": False}
        elif step == "confirm-activity-feast-stage1-v1-private":
            assert self.planning_stage == 1
            self.planning_stage = 2
            key, read_only = "activity_stage1_confirm", False
            native = {**base, **option, "schema": "activity-stage1-confirm-private-v1",
                      "expected_option_key": "feast_type_generic", "precondition_status": "observed",
                      "selected_option_shown": True, "selected_option_valid": True,
                      "can_progress_stage1": True, "generic_feast_confirm_ready": True,
                      "status": "stage_two_verified", "submitted": True, "stage_two_visible": True,
                      "selected_option_retained": True, "planning_stage_after": 2,
                      "gold_before_raw": self.gold, "gold_after_raw": self.gold,
                      "snapshot_unchanged": True, "activity_start_state": "not_started_immediate",
                      "next_turn_verified": False, "raw_pointer_fields_persisted": False,
                      "advertised": False}
        elif step == "query-activity-feast-stage2-option-v1-private":
            assert self.planning_stage == 2
            key, read_only = "activity_stage2_option", True
            native = {**base, **option, "schema": "activity-stage2-option-private-read-v1",
                      "planning_stage": 2, "generic_feast_selected": True, "read_only": True,
                      "raw_pointer_fields_persisted": False, "advertised": False}
        elif step == "query-activity-feast-stage2-location-v1-private":
            assert self.planning_stage == 2 and request["candidate_province_ids"] == [137]
            key, read_only = "activity_stage2_location", True
            native = {**base, **option, "schema": "activity-stage2-location-private-read-v1",
                      "planning_stage": 2, "configuration_rows": [
                          {"index": 0, "phase_kind": 0, "province_id": 0, "is_active": True},
                          {"index": 1, "phase_kind": 0, "province_id": 0, "is_active": False}],
                      "active_row_index": 0, "activity_single_location_flag": True,
                      "previous_planning_stage": 1, "candidates": [{"province_id": 137, "can_select": True}],
                      "can_progress_stage2": False, "read_only": True,
                      "raw_pointer_fields_persisted": False, "advertised": False}
        elif step == "select-activity-feast-stage2-destination-v1-private":
            assert self.planning_stage == 2 and request["province_id"] == 137
            self.planning_stage = 5
            key, read_only = "activity_stage2_destination_select", False
            native = {**base, **option, "schema": "activity-stage2-destination-private-action-v1",
                      "selected_province_id": 137, "status": "verified_stage_five", "submitted": True,
                      "needs_recovery": False, "stage_five_visible": True, "rows_filled": True,
                      "selected_option_retained": True, "gold_unchanged": True, "frame_unchanged": True,
                      "no_activity_started": True, "planning_stage_before": 2, "planning_stage_after": 5,
                      "configuration_province_ids_before": [0, 0],
                      "configuration_province_ids_after": [137, 137],
                      "player_gold_before_raw": self.gold, "player_gold_after_raw": self.gold,
                      "read_only": False, "advertised": False}
        else:
            raise AssertionError(step)
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": {
                    "step": step, "accepted": True, "status": "available",
                    "private_build": True, "read_only": read_only, "advertised": False,
                    key: native, "backend_id": "native-headless"}}

    def take_snapshot(self):
        return deepcopy(self.frame)

    take_internal_semantic_snapshot = take_snapshot

    def capabilities(self):
        return {"backend_id": "native-headless",
                "action_steps": ["life-advance", "save-checkpoint"],
                "bridge_capabilities": []}

    def query_activity_feast_stage5_start_inputs_private_v1(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        if not self.can_start or self.planning_stage != 5:
            raise BridgeUnavailableError("fixture native final CanStart unavailable")
        return {
            "schema": INPUT_SCHEMA, "snapshot_revision": self.frame["native_revision"],
            "queried_revision": expected_revision,
            "queried_snapshot_id": self.frame["snapshot_id"],
            "post_snapshot_id": self.frame["snapshot_id"],
            "date_raw": self.frame["date_raw"], "actor_character_id": 29829,
            "activity_key": "activity_feast", "selected_option_key": "feast_type_generic",
            "planning_stage": 5, "scale": 100000, "normal_refresh_sequence": 2,
            "final_can_start": True, "native_guest_route_qualified": True,
            "guest_join_status": "observed", "arrival_time_observed": True,
            "selected_nonhost_count": 1, "positive_join_count": 1,
            "timely_positive_join_count": 1,
            "resources": {key: {"resource_index": index,
                "configured_cost_raw": self.cost if key == "gold" else 0}
                for index, key in enumerate(RESOURCE_KEYS)},
            "balances": self.balances(), "hosted_activities": [],
            "outcome_values": self.values(), "read_only": True, "advertised": False,
            "exact_ck3_build": "1.20.0.4",
            "exe_sha256": CK3_12004.executable_sha256,
        }

    def balances(self):
        return {key: {"available": key == "gold",
                      "raw": self.gold if key == "gold" else None}
                for key in RESOURCE_KEYS}

    def values(self):
        return {"prestige_raw": 300_000_000 + (1_000_000 if self.completed else 0),
                "stress_points": 3, "reveler_present": False, "reveler_xp_raw": None}

    def post(self):
        return {
            "schema": POST_SCHEMA, "snapshot_revision": self.frame["native_revision"],
            "date_raw": self.frame["date_raw"], "actor_character_id": 29829,
            "balances": self.balances(), "hosted_activities": (
                [{"activity_id": self.activity_id, "host_character_id": 29829,
                  "activity_type_key": "activity_feast", "terminal_flags_observed": True,
                  "native_completed": self.completed, "native_invalidated": False}]
                if self.post_visible else []),
            "outcome_values": self.values(), "read_only": True, "advertised": False,
            "exact_ck3_build": "1.20.0.4", "exe_sha256": CK3_12004.executable_sha256,
            "queried_snapshot_id": self.frame["snapshot_id"],
        }

    def commit(self, *, inputs, reserve_raw):
        assert reserve_raw["gold"] == 21_800_000
        self.commits.append(deepcopy(inputs))
        self.activity_id = 83886200
        self.gold -= self.cost
        self.can_start = False
        self.planning_stage = None
        self.frame.update(revision=42, native_revision=41, snapshot_id="native:41")
        return {"source_snapshot_id": "native:40", "submitted": True,
                "status": "submitted_pending", "postcondition_verified": False}

    def execute_step(self, step, *, expected_revision=None, **kwargs):
        assert expected_revision == self.frame["revision"]
        assert step == "life-advance"
        self.frame["date_raw"] += 24
        self.frame["native_revision"] += 1
        self.frame["revision"] += 1
        self.frame["snapshot_id"] = f"native:{self.frame['native_revision']}"
        return {"step": step, "accepted": True, "status": "advanced"}


class FeastService(GameplayBridgeService):
    def snapshot(self, *, include_native_command_history=False):
        return self.driver.take_snapshot()

    def execute_step(self, step, *, expected_revision=None, **kwargs):
        return self.driver.execute_step(step, expected_revision=expected_revision, **kwargs)

    def _prepare_succession_transition_v1(self, snapshot, available, **kwargs):
        return snapshot

    def query_campaign_root_context_v1(self, *, expected_revision):
        assert expected_revision == self.driver.frame["revision"]
        self.driver.root_reads.append(expected_revision)
        return {"campaign_root_context": {
            "player_character_id": 29829,
            "capital_province_id": 137,
            "snapshot_revision": self.driver.frame["native_revision"],
            "date_raw": self.driver.frame["date_raw"],
            "player_max_monthly_gold_maintenance_v1": {
                "status": "available", "value": {"raw": 100000, "scale": 100000}}}}


def test_normal_repeat_history_pending_war_budget_terminal_and_following(tmp_path):
    # A complete old receipt is retained byte-for-byte as a JSON value; its
    # old provenance is never relabeled as a current4 observation.
    previous = {"status": "applied", "postcondition_verified": True,
                "actor_character_id": 29829,
                "activity_id": 83886111, "date_raw": 53220624,
                "next_turn_consumed": True,
                "source_pending": {"intent_id": "retained-r76", "native_ack": {
                    "exact_ck3_build": "1.20.0.3", "old_payload": {"keep": [1, 2, 3]}}},
                "lifecycle": {"terminal_observed": True, "outcome": {
                    "status": "completed", "native_completed": True,
                    "native_invalidated": False, "exact_ck3_build": "1.20.0.3",
                    "date_raw": 53222952},
                    "value_observation": {"post_terminal_counters_observed": True}}}
    initial = {"schema": consumer.LEDGER_SCHEMA, "pending": None, "resolved": previous}
    write_json_atomic(tmp_path / consumer.LEDGER_FILE, initial)
    driver = FeastDriver(tmp_path)
    service = FeastService(driver)
    baseline = {"policy": "ordinary-baseline-fixture", "selected_step": "life-advance",
                "phase": "life_advance"}
    with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
            patch.object(consumer, "submit_activity_feast_stage5_start_private_v1",
                         side_effect=lambda active, **args: active.commit(**args)), \
            patch.object(consumer, "query_activity_feast_hosted_post_private_v1",
                         side_effect=lambda active, **args: active.post()):
        # Default recovery is preserved before the normal strategy selects a
        # fresh legal opportunity. It does not alter the retained receipt.
        recovered = consumer.consume_feast_start_private_v1(driver, inputs={})
        assert recovered["status"] == "already_applied"
        assert json.loads((tmp_path / consumer.LEDGER_FILE).read_text()) == initial
        plan = service.plan_turn()["plan"]
        assert plan["selected_step"] == OPEN_STEP
        assert plan["activity_feast_opportunity"]["province_id"] == 137
        assert driver.configuration_requests == []
        configured = service.auto_turn()
        assert configured["selected_step"] == OPEN_STEP
        assert configured["result"]["status"] == "configured_stage_five"
        assert driver.planning_stage == 5 and driver.commits == []
        assert [row["step"] for row in driver.configuration_requests] == [
            OPEN_STEP, "query-activity-stage1-option-v1-private",
            "confirm-activity-feast-stage1-v1-private",
            "query-activity-feast-stage2-option-v1-private",
            "query-activity-feast-stage2-location-v1-private",
            "select-activity-feast-stage2-destination-v1-private"]
        assert json.loads((tmp_path / consumer.LEDGER_FILE).read_text()) == initial
        plan = service.plan_turn()["plan"]
        assert plan["selected_step"] == START_STEP
        assert plan["activity_feast_opportunity"]["new_attempt"] is True
        assert plan["activity_feast_opportunity"]["budget"]["war_cash_reserve_raw"] == 1_800_000
        assert driver.commits == []
        started = service.auto_turn()
        assert started["selected_step"] == START_STEP
        assert started["status"] == "pending"
        ledger = consumer.read_feast_start_ledger(tmp_path)
        assert ledger["history"] == [previous]
        assert ledger["resolved"] is None and ledger["pending"]["new_attempt"] is True
        assert len(driver.commits) == 1 and driver.root_reads
        pending = service.auto_turn()
        assert pending["selected_step"] == POST_STEP
        assert pending["result"]["postcondition_verified"] is False
        assert len(driver.commits) == 1
        driver.post_visible = True
        material = service.auto_turn()
        assert material["plan"]["activity_feast_lifecycle_observation"]["lifecycle_terminal_observed"] is False
        ledger = consumer.read_feast_start_ledger(tmp_path)
        assert ledger["pending"] is None
        assert ledger["resolved"]["activity_id"] == driver.activity_id
        assert ledger["history"] == [previous] and len(driver.commits) == 1
        advanced = service.auto_turn()
        assert advanced["selected_step"] == "life-advance"
        assert consumer.read_feast_start_ledger(tmp_path)["resolved"]["next_turn_consumed"] is True
        driver.completed = True
        terminal = service.plan_turn()["plan"]["activity_feast_lifecycle_observation"]
        assert terminal["lifecycle_terminal_observed"] is True
        ledger = consumer.read_feast_start_ledger(tmp_path)
        assert ledger["resolved"]["lifecycle"]["value_observation"]["benefit_verified"] is False
        assert ledger["history"] == [previous] and len(driver.commits) == 1
