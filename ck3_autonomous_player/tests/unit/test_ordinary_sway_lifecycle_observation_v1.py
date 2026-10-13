"""New connected ordinary Service observation; synthetic normalized native inputs."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.ordinary_sway_lifecycle_observation_v1 import observe_resolved_sway_lifecycle_v1
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger


ACTOR, TARGET, INSTANCE = 29829, 34333, 134217986
DATE = 53288448


def seed(state_dir: Path):
    resolved = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": ACTOR, "target_character_id": TARGET,
        "action_id": "ordinary-sway", "post_native_revision": 5,
        "post_date_raw": DATE, "next_turn_consumed": True,
        "following_native_revision": 6, "following_date_raw": DATE,
        "native_receipt": {
            "schema": "active-scheme-sway-formal-private-v1", "stage": "applied",
            "postcondition_verified": True, "action_id": "ordinary-sway",
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": 8,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
        },
    }
    (state_dir / LEDGER_FILE).write_text(json.dumps({
        "schema": SCHEMA, "pending": None, "resolved": resolved,
    }), encoding="utf-8")
    return resolved


class SourceDriver:
    allow_private_active_scheme_sway_completion_query = True
    allow_private_active_scheme_sway_outcome_opinion_query = True

    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.frame = {
            "snapshot_id": "ordinary-frame", "paused": True, "map_ready": True,
            "revision": 17, "native_revision": 7, "date_raw": DATE,
            "played_character": {"character_id": ACTOR, "alive": True},
        }
        self.calls = []
        self.terminal = False
        self.fail = False

    def take_snapshot_without_native_command_history(self):
        return deepcopy(self.frame)

    def take_snapshot(self):
        return self.take_snapshot_without_native_command_history()

    def capabilities(self):
        return {"bridge_capabilities": []}

    def query_active_scheme_sway_completion_private_v1(self, **arguments):
        self.calls.append(("completion", arguments))
        if self.fail:
            raise BridgeUnavailableError("current copied source unavailable")
        return {
            "schema": "xar.ck3.sway_completion.v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "scheme_instance_id": INSTANCE, "scheme_instance_generation": 8,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"], "date_raw": DATE,
            "instance_source_observed": True, "instance_present": True,
            "storage_slot_reused": False, "exact_instance_join_ready": True,
            "owner_matches_actor": not self.terminal, "owner_cleared": self.terminal,
            "native_owner_raw": 0xFFFFFFFF if self.terminal else ACTOR,
            "native_status_observed": True, "native_status_raw": int(self.terminal),
            "native_status_key": "terminated_unattributed" if self.terminal else "continue",
            "native_terminal_state_observed": self.terminal,
            "terminal_cause_observed": False, "terminal_cause": "unknown",
        }

    def query_active_scheme_sway_outcome_opinion_private_v1(self, **arguments):
        self.calls.append(("opinion", arguments))
        return {
            "schema": "xar.ck3.sway-outcome-opinion-v1", "available": True,
            "actor_character_id": ACTOR, "target_character_id": TARGET,
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "snapshot_revision": self.frame["native_revision"], "date_raw": DATE,
            "target_opinion_of_actor": 27,
            "scheme_sway_opinion": {"observed": True, "present": True, "value": 25},
            "sway_blocker_opinion": {"observed": True, "present": False, "value": None},
            "instance_terminal_outcome_observed": False, "cancel_outcome_observed": False,
        }

    def execute_step(self, step, *, expected_revision):
        self.calls.append((step, expected_revision))
        assert expected_revision == self.frame["revision"]
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        return {"status": "completed", "step": step}


def test_ordinary_observation_stages_then_consumes_without_target_runner(tmp_path):
    seed(tmp_path)
    driver = SourceDriver(tmp_path)
    def ordinary_plan(service):
        driver.calls.append(("full-planner", driver.frame["revision"]))
        return {"revision": driver.frame["revision"], "plan": {"selected_step": "pause-map"}}
    with patch.object(GameplayBridgeService, "_plan_turn_internal", ordinary_plan):
        service = GameplayBridgeService(driver)
        first = service.auto_turn()
        assert [name for name, _ in driver.calls] == ["completion", "opinion", "full-planner", "pause-map"]
        assert first["sway_following_turn"]["material_intervention"]["next_turn_consumed"]
        assert not read_sway_ledger(tmp_path)["resolved"]["terminal_intervention"]["instance_terminal_outcome_observed"]
        assert driver.calls[0][1]["expected_revision"] == 17  # public, not native7
        driver.terminal = True
        terminal = GameplayBridgeService(driver).auto_turn()
        observed = terminal["sway_following_turn"]["terminal_intervention"]
        assert observed["next_turn_consumed"] and observed["instance_terminal_outcome_observed"]
        assert not observed["terminal_cause_observed"] and observed["terminal_cause"] == "unknown"
        assert "sway_following_turn" not in GameplayBridgeService(driver).auto_turn()
        assert read_sway_ledger(tmp_path)["pending"] is None


def test_ordinary_observation_skips_other_actor_and_preserves_full_planner_after_read_failure(tmp_path):
    seed(tmp_path)
    driver = SourceDriver(tmp_path)
    service = GameplayBridgeService(driver)
    original = deepcopy(driver.frame)
    for update in ({"paused": False}, {"map_ready": False},
                   {"one_life_terminal_reason": "played_character_changed"},
                   {"played_character": {"character_id": 999, "alive": True}},
                   {"played_character": {"character_id": ACTOR, "alive": False}}):
        driver.frame = {**original, **update}
        assert observe_resolved_sway_lifecycle_v1(service) is None
    assert not driver.calls
    driver.frame = original
    driver.fail = True
    with patch.object(service, "_plan_turn_internal", return_value={
        "revision": original["revision"], "plan": {"selected_step": "pause-map"},
    }):
        planned = service.plan_turn()
    assert planned["plan"]["selected_step"] == "pause-map"
    assert planned["sway_lifecycle_observation"]["status"] == "query_failed"
    assert planned["sway_lifecycle_observation"]["request_retried"] is False
    assert [name for name, _ in driver.calls] == ["completion"]
