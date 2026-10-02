"""Focused new consumer chain using preserved 1.20.0.2 production SDK DTOs."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from xar_autoplayer.private_council_formal_consumer_v1 import (
    LEDGER_FILENAME, RECEIPT_STEP, SUBMIT_STEP, plan_council_private,
    read_council_ledger, read_council_receipt_private, submit_council_private,
)
from xar_autoplayer.bridge.council_assign_councillor_action_contract import build_assign_councillor_request_v1
from test_council_assign_councillor_action_v1 import _ack, _receipt

FIXTURE = Path(__file__).parents[1] / "fixtures" / "private_council_formal12002_actual.json"


class ActualCouncilDriver:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.allow_private_council_action = True
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.phase = "pre"
        self.query_calls = 0
        self.submit_calls = 0
        self.receipt_calls = 0
        self.root_calls = 0
        self.request_id = None

    def take_internal_semantic_snapshot(self):
        key = {"pre": "pre_snapshot", "post": "receipt_snapshot", "current": "current_snapshot"}[self.phase]
        return copy.deepcopy(self.data[key])

    take_snapshot = take_internal_semantic_snapshot

    def query_council_final_gates_private_v1(self, *, expected_revision):
        self.query_calls += 1
        assert expected_revision == self.take_snapshot()["revision"]
        return copy.deepcopy(self.data["positive_query" if self.phase == "pre" else "current_query"])

    def submit_council_assign_private_v1(self, *, query, candidate_character_id, expected_revision, action_request_id):
        self.submit_calls += 1
        assert self.phase == "pre"
        assert query == self.data["positive_query"]
        assert candidate_character_id == 33433
        assert expected_revision == self.take_snapshot()["revision"]
        self.request_id = action_request_id
        value = copy.deepcopy(self.data["pending"])
        # Native protocol echoes the request chosen by the caller. Rebind only
        # that correlation token; every observed native ACK field is retained.
        value["action_request_id"] = action_request_id
        value["council_assign_councillor_ack"]["action_request_id"] = action_request_id
        value["request"]["request_id"] = action_request_id
        return value

    def query_council_assign_receipt_private_v1(self, *, pending, expected_revision):
        self.receipt_calls += 1
        assert self.phase == "post"
        assert expected_revision == self.take_snapshot()["revision"]
        assert pending["council_assign_councillor_ack"]["action_request_id"] == self.request_id
        value = copy.deepcopy(self.data["receipt"])
        value["council_assign_councillor_receipt"]["action_request_id"] = self.request_id
        return value

    def execute_step(self, step, *, expected_revision):
        self.root_calls += 1
        assert step == "query-campaign-root-context-v1"
        assert expected_revision == self.take_snapshot()["revision"]
        return copy.deepcopy(self.data["receipt_root" if self.phase == "post" else "current_root"])


def plan(driver):
    snapshot = driver.take_snapshot()
    return plan_council_private(driver,
        {"revision": snapshot["revision"], "snapshot_id": snapshot["snapshot_id"],
         "plan": {"policy": "nonwar-dispatch", "selected_step": None}},
        snapshot, [], set())


def test_real_positive_query_once_pending_independent_receipt_and_next_consumption(tmp_path):
    driver = ActualCouncilDriver(tmp_path)
    planned = plan(driver)
    choice = planned["plan"]
    assert choice["selected_step"] == SUBMIT_STEP
    assert choice["council_decision"]["native_candidate_count"] == 13
    assert choice["council_decision"]["legal_candidate_count"] == 10
    assert choice["council_decision"]["selected_candidate"]["character_id"] == 33433
    assert choice["council_decision"]["skill_gain"] == 4
    pending = submit_council_private(driver, plan=choice, expected_revision=planned["revision"])
    assert pending["stage"] == "receipt_pending"
    assert driver.submit_calls == 1
    assert read_council_ledger(tmp_path)["applied"] is None
    waiting = plan(driver)["plan"]
    assert waiting["selected_step"] is None
    assert waiting["council_pending_action"] == pending
    assert driver.query_calls == 1
    with pytest.raises(ValueError, match="unresolved assignment"):
        submit_council_private(driver, plan=choice, expected_revision=planned["revision"])
    assert driver.submit_calls == 1
    # Only this independent, preserved later SDK frame changes the fixture.
    driver.phase = "post"
    ready = plan(driver)["plan"]
    assert ready["selected_step"] == RECEIPT_STEP
    applied = read_council_receipt_private(driver, pending=ready["council_pending_action"],
        expected_revision=driver.take_snapshot()["revision"])
    assert applied["status"] == "applied"
    assert applied["independent_position"]["incumbent_character_id"] == 33433
    assert applied["independent_position"]["task_key"] == "task_collect_taxes"
    assert applied["next_turn_consumed"] is False
    assert read_council_ledger(tmp_path)["pending"] is None
    # R10 is an actual new-process paused observation. Its native revision
    # restarts at one; holder/task must be re-read rather than trusted cached.
    driver.phase = "current"
    following = plan(driver)["plan"]
    assert following["council_observation_consumed"] is True
    assert following["council_decision"]["outcome"] == "NO_CHANGE"
    assert following["council_receipt_consumed"]["next_turn_consumed"] is True
    assert following["council_receipt_consumed"]["next_turn_native_revision"] == 1
    assert read_council_ledger(tmp_path)["applied"]["next_turn_consumed"] is True
    assert (driver.submit_calls, driver.receipt_calls, driver.root_calls) == (1, 1, 2)


def test_current_actual_incumbent_not_outperformed_and_off_sends_nothing(tmp_path):
    driver = ActualCouncilDriver(tmp_path)
    driver.phase = "current"
    driver.allow_private_council_action = False
    disabled = plan(driver)
    assert disabled["plan"]["selected_step"] is None
    assert driver.query_calls == 0
    assert not (tmp_path / LEDGER_FILENAME).exists()
    driver.allow_private_council_action = True
    observed = plan(driver)["plan"]
    assert observed["council_observation_consumed"] is True
    assert observed["council_decision"]["outcome"] == "NO_CHANGE"
    assert observed["council_decision"]["incumbent_character_id"] == 33433
    assert observed["council_decision"]["incumbent_main_skill"]["value"] == 15
    assert observed["council_decision"]["skill_gain"] == -4
    assert observed["selected_step"] is None
    assert driver.submit_calls == 0


class OfflineChancellorDriver(ActualCouncilDriver):
    """Constructed role/post-state fixture on the preserved Steward DTO shape.

    The original actual Steward packets are unchanged. Chancellor states,
    ACK and post material here are offline data, never live result evidence.
    """

    def __init__(self, state_dir, *, candidate_character_id=909, diplomacy=7):
        super().__init__(state_dir)
        self.phase = "vacant"
        self.candidate_character_id = candidate_character_id
        self.diplomacy = diplomacy
        self.role_queries = []
        self.native_ack = None
        self.steward_improvement = False
        self.last_queried_role = None

    def take_internal_semantic_snapshot(self):
        value = copy.deepcopy(self.data["current_snapshot"])
        revision = 2 if self.phase == "occupied" else 1
        value.update({"snapshot_id": f"native:{revision}", "revision": revision,
                      "native_revision": revision})
        if self.phase == "cold":
            value["date_raw"] += 24
        return value

    take_snapshot = take_internal_semantic_snapshot

    def query_council_final_gates_private_v1(self, *, expected_revision, **arguments):
        role = arguments.get("position_key", "councillor_steward")
        self.role_queries.append(role)
        self.last_queried_role = role
        self.query_calls += 1
        snapshot = self.take_snapshot()
        assert expected_revision == snapshot["revision"]
        value = copy.deepcopy(self.data["current_query"])
        payload = value["council_composition_candidates"]
        payload["snapshot"].update({"snapshot_id": snapshot["snapshot_id"],
            "public_revision": snapshot["native_revision"], "native_revision": snapshot["native_revision"],
            "date_raw": snapshot["date_raw"]})
        if role == "councillor_chancellor":
            vacant = self.phase == "vacant"
            payload["position"].update({"position_key": role,
                "incumbent_character_id": None if vacant else self.candidate_character_id,
                "incumbent_main_skill": None if vacant else {"key": "diplomacy", "value": self.diplomacy},
                "vacant": vacant, "action_route": "assign" if vacant else "replace"})
            candidate = copy.deepcopy(payload["candidates"][0])
            candidate.update({"character_id": self.candidate_character_id if vacant else self.candidate_character_id + 1,
                "native_collection_ordinal": 0, "main_skill": {"key": "diplomacy", "value": self.diplomacy},
                "action_route": "assign" if vacant else "replace"})
            payload["candidates"] = [candidate]
            gates = value["council_final_gates"]
            gate = copy.deepcopy(gates["rows"][0])
            gate.update({"character_id": candidate["character_id"], "native_collection_ordinal": 0,
                "final_gate_available": True, "candidate_already_councillor": False,
                "candidate_is_guest": False, "pending_character_interaction": False,
                "incumbent_fireability_evaluated": not vacant, "incumbent_can_be_fired": not vacant})
            gates.update({"candidate_count": 1, "rows": [gate]})
        elif self.steward_improvement:
            candidate = copy.deepcopy(payload["candidates"][0])
            candidate.update({"character_id": 1910, "native_collection_ordinal": 0,
                "main_skill": {"key": "stewardship", "value": payload["position"]["incumbent_main_skill"]["value"] + 1}})
            payload["candidates"] = [candidate]
            gate = copy.deepcopy(value["council_final_gates"]["rows"][0])
            gate.update({"character_id": candidate["character_id"], "native_collection_ordinal": 0,
                "final_gate_available": True, "candidate_already_councillor": False, "candidate_is_guest": False,
                "pending_character_interaction": False, "incumbent_fireability_evaluated": True, "incumbent_can_be_fired": True})
            value["council_final_gates"].update({"candidate_count": 1, "rows": [gate]})
        return value

    def execute_step(self, step, *, expected_revision):
        assert step == "query-campaign-root-context-v1"
        assert expected_revision == self.take_snapshot()["revision"]
        self.root_calls += 1
        value = copy.deepcopy(self.data["current_root"])
        root = value["campaign_root_context"]
        snapshot = self.take_snapshot()
        root.update({"snapshot_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"]})
        row = next(row for row in root["council"]["positions"] if row["position_key"] == "councillor_chancellor")
        row["incumbent_character_id"] = None if self.phase == "vacant" else self.candidate_character_id
        if self.phase == "vacant":
            row.update({"task_key": None, "task_type": None, "frozen": None, "target": None, "progress": None})
        return value

    def submit_council_assign_private_v1(self, *, query, candidate_character_id, expected_revision, action_request_id):
        role = query["council_composition_candidates"]["position"]["position_key"]
        assert self.last_queried_role == role
        if role == "councillor_chancellor":
            assert self.phase == "vacant"
            assert candidate_character_id == self.candidate_character_id
        else:
            assert self.steward_improvement and role == "councillor_steward"
        assert expected_revision == self.take_snapshot()["revision"]
        self.submit_calls += 1
        request = build_assign_councillor_request_v1(query["council_composition_candidates"],
            candidate_character_id=candidate_character_id, request_id=action_request_id)
        self.native_ack = _ack(request)
        return {"council_assign_councillor_ack": copy.deepcopy(self.native_ack),
                "action_request_id": action_request_id, "request": request.as_wire_fields()}

    def query_council_assign_receipt_private_v1(self, *, pending, expected_revision):
        assert self.phase == "occupied"
        assert pending["council_assign_councillor_ack"] == self.native_ack
        assert expected_revision == self.take_snapshot()["revision"]
        self.receipt_calls += 1
        receipt = _receipt(self.native_ack)
        snapshot = self.take_snapshot()
        receipt.update({"post_snapshot_id": snapshot["snapshot_id"],
            "post_public_revision": snapshot["revision"], "post_native_revision": snapshot["native_revision"],
            "post_date_raw": snapshot["date_raw"]})
        return {"council_assign_councillor_receipt": receipt}


@pytest.mark.parametrize("candidate_character_id,diplomacy", [(909, 7), (1210, 12)])
def test_chancellor_vacancy_preserves_old_steward_and_consumes_own_next_and_cold(tmp_path, candidate_character_id, diplomacy):
    driver = OfflineChancellorDriver(tmp_path, candidate_character_id=candidate_character_id, diplomacy=diplomacy)
    # The existing latest-applied schema retains its original Steward identity.
    old = {"status": "applied", "episode_run_id": driver.take_snapshot()["episode_run_id"],
        "candidate_character_id": 33433, "action_ack": copy.deepcopy(driver.data["pending"]),
        "receipt": copy.deepcopy(driver.data["receipt"]), "next_turn_consumed": False}
    (tmp_path / LEDGER_FILENAME).write_text(json.dumps({"schema": "xar.ck3.private-council-formal/v1",
        "pending": None, "applied": old}), encoding="utf-8")
    planned = plan(driver)
    choice = planned["plan"]
    assert choice["council_receipt_consumed"]["next_turn_consumed"] is True
    assert choice["council_receipt_consumed"]["next_turn_position"]["position_key"] == "councillor_steward"
    assert choice["council_decision"]["position_key"] == "councillor_chancellor"
    assert choice["council_decision"]["selected_candidate"]["character_id"] == candidate_character_id
    assert choice["council_decision"]["selected_candidate"]["main_skill"]["value"] == diplomacy
    pending = submit_council_private(driver, plan=choice, expected_revision=planned["revision"])
    assert plan(driver)["plan"]["council_pending_action"] == pending
    assert driver.submit_calls == 1
    driver.phase = "occupied"
    ready = plan(driver)["plan"]
    assert ready["selected_step"] == RECEIPT_STEP
    applied = read_council_receipt_private(driver, pending=ready["council_pending_action"], expected_revision=2)
    assert applied["independent_position"]["position_key"] == "councillor_chancellor"
    assert applied["independent_position"]["task_key"] == "task_foreign_affairs"
    assert applied["next_turn_consumed"] is False
    following = plan(driver)["plan"]
    assert following["council_receipt_consumed"]["next_turn_consumed"] is True
    assert following["council_receipt_consumed"]["next_turn_position"]["position_key"] == "councillor_chancellor"
    assert driver.submit_calls == 1
    # A new driver/process uses the same ledger with a reset native revision.
    cold = OfflineChancellorDriver(tmp_path, candidate_character_id=candidate_character_id, diplomacy=diplomacy)
    cold.phase = "cold"
    recovered = plan(cold)["plan"]
    assert recovered["council_receipt_consumed"]["next_turn_consumed"] is True
    assert recovered["council_receipt_consumed"]["next_turn_native_revision"] == 1
    assert recovered["council_receipt_consumed"]["next_turn_position"]["incumbent_character_id"] == candidate_character_id
    assert cold.role_queries == ["councillor_chancellor", "councillor_steward"]
    assert cold.submit_calls == 0
    assert set(read_council_ledger(tmp_path)) == {"schema", "pending", "applied"}


def test_applied_chancellor_read_does_not_overwrite_a_new_steward_submit_quote(tmp_path):
    driver = OfflineChancellorDriver(tmp_path)
    query = driver.query_council_final_gates_private_v1(expected_revision=1, position_key="councillor_chancellor")
    request = build_assign_councillor_request_v1(query["council_composition_candidates"],
        candidate_character_id=driver.candidate_character_id, request_id="offline-applied-chancellor")
    applied = {"status": "applied", "episode_run_id": driver.take_snapshot()["episode_run_id"],
        "candidate_character_id": driver.candidate_character_id,
        "action_ack": {"council_assign_councillor_ack": _ack(request)}, "receipt": {}, "next_turn_consumed": False}
    (tmp_path / LEDGER_FILENAME).write_text(json.dumps({"schema": "xar.ck3.private-council-formal/v1",
        "pending": None, "applied": applied}), encoding="utf-8")
    driver.phase = "cold"
    driver.steward_improvement = True
    planned = plan(driver)
    assert planned["plan"]["council_receipt_consumed"]["next_turn_consumed"] is True
    assert planned["plan"]["council_decision"]["position_key"] == "councillor_steward"
    assert planned["plan"]["council_decision"]["outcome"] == "REPLACE_REQUIRED"
    pending = submit_council_private(driver, plan=planned["plan"], expected_revision=planned["revision"])
    assert pending["action_ack"]["council_assign_councillor_ack"]["position_key"] == "councillor_steward"
    assert driver.submit_calls == 1
