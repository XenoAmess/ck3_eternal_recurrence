"""Closed 8890 DTOs; chooser/outer frame/dispatch are explicit synthetic seams."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from test_construction_formal_private_consumer import Driver
from xar_autoplayer import construction_formal_consumer as consumer
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.driver import BridgeUnavailableError, CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004


FIXTURE = json.loads((Path(__file__).parent / "fixtures" /
                      "construction8890_closed_query_v1.json").read_text(encoding="utf-8"))


def inputs():
    source = FIXTURE["planning_source_frame"]
    snapshot = {key: source[key] for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
    snapshot.update(paused=True, map_ready=True, active_event=None,
                    pending_character_interaction=None, active_wars=[], player_armies=[],
                    played_character={"character_id": source["actor_character_id"], "alive": True},
                    played_character_gold={"raw": 9602663, "scale": 100000},
                    diagnostics={"hello": {"expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256}})
    plan = {"policy": "one-life-turn-v1", "phase": "native_war_discovery_cooldown",
            "selected_step": "life-advance", "reason": "synthetic ordinary clock admission",
            "player_risk_context": deepcopy(FIXTURE["player_risk_context"])}
    return snapshot, {"snapshot_id": snapshot["snapshot_id"],
                      "revision": snapshot["revision"], "plan": plan}


def run_consumer(tmp_path, query):
    snapshot, planned = inputs()
    driver = Driver(tmp_path)
    driver.snapshot = snapshot
    with patch.object(consumer, "same_frame_construction_scope_v1", return_value={
            "status": "admitted", "government_key": "feudal_government"}), \
            patch.object(transport, "query_construction_private", return_value=query):
        return consumer.plan_construction_private(driver, planned, snapshot, [], {"life-advance"})


def test_actual_cost_unavailable_dto_retains_ordinary_action_and_risk(tmp_path):
    query = deepcopy(FIXTURE["construction_private_query"])
    result = run_consumer(tmp_path, query)["plan"]
    assert result["selected_step"] == "life-advance"
    assert result["phase"] == "native_war_discovery_cooldown"
    assert result["reason"] == "synthetic ordinary clock admission"
    assert result["construction_private_query"] == query
    assert result["player_risk_context"] == FIXTURE["player_risk_context"]
    assert result["construction_spending_deferred_v1"]["business_submission"] is False
    assert not (tmp_path / consumer._LEDGER).exists()


@pytest.mark.parametrize("section,key,value", [
    ("source_frame", "actor_character_id", 999),
    ("source_frame", "native_revision", 1785),
    ("source_frame", "date_raw", 53228616),
    ("source_frame", "episode_run_id", "foreign"),
    ("source_frame", "revision", 1788),
    ("source_frame", "snapshot_id", "native:1787"),
    ("ending_frame", "revision", 1788),
    ("ending_frame", "snapshot_id", "native:1787"),
    ("ending_frame", "episode_run_id", "foreign"),
    ("ending_frame", "revision", None),
    ("source_frame", "actor_character_id", None),
    ("source_frame", "native_revision", None),
    ("source_frame", "date_raw", None),
    ("source_frame", "episode_run_id", None),
    ("source_frame", "revision", None),
    ("source_frame", "snapshot_id", None),
    ("ending_frame", "snapshot_id", None),
    ("ending_frame", "episode_run_id", None),
])
def test_missing_or_changed_query_binding_stays_red(tmp_path, section, key, value):
    query = deepcopy(FIXTURE["construction_private_query"])
    if value is None:
        del query[section][key]
    else:
        query[section][key] = value
    plan = run_consumer(tmp_path, query)["plan"]
    assert plan["selected_step"] is None
    assert plan["construction_private_query"] == query
    assert "construction_spending_deferred_v1" not in plan


def test_real_transport_preserves_native_cost_red_and_frame_guard(tmp_path):
    driver = Driver(tmp_path)
    driver.snapshot, _ = inputs()
    native = deepcopy(FIXTURE["construction_private_query"]["native_result"])
    def response(request_id, timeout):
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": native}
    driver.wait_for_command_result = response
    query = transport.query_construction_private(driver,
        expected_revision=driver.snapshot["revision"])
    assert query["status"] == "source_red"
    assert query["native_result"] == native
    assert query["source_frame"] == FIXTURE["construction_private_query"]["source_frame"]
    assert query["ending_frame"] == FIXTURE["construction_private_query"]["ending_frame"]
    assert [row["step"] for row in driver.requests] == [transport.QUERY_NATIVE]
    with pytest.raises(BridgeUnavailableError):
        transport.query_construction_private(driver,
            expected_revision=driver.snapshot["revision"] + 1)
    assert len(driver.requests) == 1


@pytest.mark.parametrize("changed", [False, True])
def test_service_auto_ordinary_dispatch_not_construction_with_closed_red(tmp_path, changed):
    snapshot, planned = inputs()
    calls, displayed = [], []
    driver = CallbackGameplayDriver(backend_id="native-headless",
        snapshot=lambda: deepcopy(snapshot),
        execute=lambda step, revision: calls.append((step, revision)) or {"accepted": True},
        action_steps=("life-advance",))
    driver.state_dir = tmp_path
    driver.allow_private_construction_formal_trial = True
    query = deepcopy(FIXTURE["construction_private_query"])
    if changed:
        query["ending_frame"]["revision"] += 1
    with patch("xar_autoplayer.bridge.service.choose_one_life_turn",
               return_value=planned["plan"]), \
            patch("xar_autoplayer.ordinary_player_risk_context_v1.build_ordinary_player_risk_context_v1",
                  return_value=deepcopy(FIXTURE["player_risk_context"])), \
            patch.object(consumer, "same_frame_construction_scope_v1", return_value={
                "status": "admitted", "government_key": "feudal_government"}), \
            patch.object(transport, "query_construction_private", return_value=query):
        result = GameplayBridgeService(driver).auto_turn(
            before_submit=lambda item: displayed.append(item))
    if changed:
        assert result["status"] == "blocked"
        assert not calls and not displayed
        return
    assert result["status"] == "executed"
    assert result["selected_step"] == "life-advance"
    assert calls == [("life-advance", snapshot["revision"])]
    assert len(displayed) == 1
    assert displayed[0]["plan"]["construction_private_query"] == query
    assert displayed[0]["plan"]["player_risk_context"] == FIXTURE["player_risk_context"]
    assert not (tmp_path / consumer._LEDGER).exists()


def test_missing_optional_durable_state_or_root_channel_defers_only_spend(tmp_path):
    snapshot, planned = inputs()
    driver = Driver(tmp_path)
    driver.state_dir = None
    assert consumer.plan_construction_private(driver, planned, snapshot, [], set())[
        "plan"]["selected_step"] == "life-advance"
    driver.state_dir = tmp_path
    with patch.object(consumer, "same_frame_construction_scope_v1",
                      return_value={"status": "root_query_needed"}):
        result = consumer.plan_construction_private(driver, planned, snapshot, [], set())
    assert result["plan"]["selected_step"] == "life-advance"
    assert not driver.requests


def test_unresolved_prior_action_and_query_exceptions_keep_their_guards(tmp_path):
    snapshot, planned = inputs()
    driver = Driver(tmp_path)
    consumer.write_construction_ledger(tmp_path, {
        "schema": "xar.ck3.construction_formal_pending_v1",
        "pending": {"episode_run_id": "foreign"}, "applied": None})
    result = consumer.plan_construction_private(driver, planned, snapshot, [], set())
    assert result["plan"]["selected_step"] is None
    assert "another episode" in result["plan"]["reason"]
    assert not driver.requests
    consumer.write_construction_ledger(tmp_path, {
        "schema": "xar.ck3.construction_formal_pending_v1", "pending": None, "applied": None})
    with patch.object(consumer, "same_frame_construction_scope_v1", return_value={
            "status": "admitted", "government_key": "feudal_government"}), \
            patch.object(transport, "query_construction_private",
                         side_effect=BridgeUnavailableError("query frame changed")):
        with pytest.raises(BridgeUnavailableError, match="query frame changed"):
            consumer.plan_construction_private(driver, planned, snapshot, [], set())
