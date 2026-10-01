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
