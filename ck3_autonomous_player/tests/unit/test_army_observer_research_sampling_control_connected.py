"""Real integrated Driver/MCP sampling controls over synthetic transport frames."""
from __future__ import annotations
import asyncio
import copy
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from xar_autoplayer.bridge import army_observer_research_sampling_control as control
from test_army_profile_cache_regression import make_scenario
from test_native_bridge_driver import _army, _hello, _snapshot, _war
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004


def need(ok, reason):
    if not ok:
        raise AssertionError(reason)


def row(example):
    # Fixed complete wire examples; no replacement native state machine.
    examples = {
        "enabled": dict(installed=True, available=True, capture_enabled=True, busy=False,
            clear_completed=False, epoch=6, active_captures=0, retained_records=0,
            qualified_records=0, status="enabled", readiness="awaiting_sample"),
        "inflight": dict(installed=True, available=True, capture_enabled=True, busy=True,
            clear_completed=False, epoch=6, active_captures=1, retained_records=2,
            qualified_records=1, status="enabled", readiness="inflight"),
        "disabled": dict(installed=True, available=True, capture_enabled=False, busy=False,
            clear_completed=True, epoch=7, active_captures=0, retained_records=0,
            qualified_records=0, status="disabled", readiness="off"),
        "busy": dict(installed=True, available=True, capture_enabled=False, busy=True,
            clear_completed=False, epoch=7, active_captures=1, retained_records=2,
            qualified_records=1, status="busy", readiness="off"),
        "unavailable-retained": dict(installed=False, available=True, capture_enabled=True, busy=False,
            clear_completed=False, epoch=9, active_captures=0, retained_records=2,
            qualified_records=1, status="unavailable", readiness="unavailable"),
    }
    return copy.deepcopy(examples[example])


def packet(step, states, accepted):
    return dict(step=step, accepted=accepted, status="completed" if accepted else "incomplete",
                army_observer_research_sampling_v1=states)


def test_connected_control_contract_focus(tmp_path):
    army = make_scenario(tmp_path / "driver", projection="native_campaign")
    requests, replies = [], []
    try:
        army.endpoint.publish({**_hello("game.state.snapshot", control.ARMY_CAPABILITY),
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256})
        first, second = _army(82), _army(81)
        army.endpoint.publish(_snapshot(40, played_character={"character_id":707,"alive":True},
            player_armies=[first,second], active_wars=[_war(45,allied_armies=[second]),
                                                     _war(46,allied_armies=[second])]))
        army.before = army.driver.take_internal_semantic_snapshot()
        original_answer = army.endpoint.send_hook

        def answer(frame):
            if frame.get("type") != "execute_step" or frame.get("step") not in {
                control.ENABLE_STEP, control.DISABLE_STEP, control.QUERY_STEP,
            }:
                return original_answer(frame)
            requests.append(copy.deepcopy(frame))
            need(bool(replies), "unexpected control retry or implicit capture control")
            reply = replies.pop(0)
            if reply == "timeout":
                return
            army.endpoint.publish(dict(type="command_result", protocol_version=1,
                request_id=frame["request_id"], ok=True, result=copy.deepcopy(reply)))

        army.endpoint.send_hook = answer
        driver = army.driver
        revision = army.before["revision"]
        army.query()  # Current ordinary cache proves invalidation behavior.
        before = copy.deepcopy(driver._army_strength_query)
        need(before is not None, "real normal Army cache absent")
        server = create_server(driver)
        setter = "ck3_set_army_observer_research_sampling_v1"
        query = "ck3_query_army_observer_research_sampling_v1"
        names = {tool.name for tool in asyncio.run(server.list_tools())}
        need({setter,query} <= names, "new registered controls absent")

        # Strict MCP bool/family rejects precede transport and keep cache.
        for arguments in [dict(enabled=1,observer_family="all",expected_revision=revision),
                          dict(enabled=True,observer_family="guessed",expected_revision=revision)]:
            with pytest.raises(ToolError):
                asyncio.run(server.call_tool(setter,arguments))
        need(requests == [] and driver._army_strength_query == before, "bad public input dispatched or changed cache")
        with pytest.raises(PreSubmissionRevisionMismatchError):
            driver.query_army_observer_research_sampling_v1(observer_family="all",expected_revision=revision+1)
        need(requests == [], "stale source dispatched")

        # A query can truthfully expose unavailable retained state; accepted
        # query does not certify install or sample readiness, nor clear it.
        states = {name:row("enabled") for name in control.FAMILIES}
        states["regular_core"] = row("unavailable-retained")
        replies.append(packet(control.QUERY_STEP,states,True))
        result = asyncio.run(server.call_tool(query,dict(observer_family="all",expected_revision=revision)))
        need(result.is_error is False and result.structured_content[control.STATE_KEY] == states,
             "registered query changed real unavailable/retained fields")
        need(driver._army_strength_query == before, "read-only query invalidated current Army cache")
        need(requests[-1]["observer_family"] == "all" and requests[-1]["expected_revision"] == army.before["native_revision"],
             "family/native revision not sent by real Driver primitive")

        # Enable while the observer is already enabled/inflight is an
        # accepted control, not a completed entry/return sample.
        replies.append(packet(control.ENABLE_STEP,{"regular_core":row("inflight")},True))
        enabled = asyncio.run(server.call_tool(setter,dict(enabled=True,observer_family="regular_core",expected_revision=revision)))
        need(enabled.is_error is False and enabled.structured_content["accepted"] is True and
             enabled.structured_content[control.STATE_KEY]["regular_core"]["readiness"] == "inflight",
             "enabled/inflight was falsely promoted to retained readiness")
        need(driver._army_strength_query is None, "successful set retained stale Army cache")

        # A pending disable is returned once, history ok=false, no retry.
        army.query()
        replies.append(packet(control.DISABLE_STEP,{"regular_core":row("busy")},False))
        pending = asyncio.run(server.call_tool(setter,dict(enabled=False,observer_family="regular_core",expected_revision=revision)))
        need(pending.is_error is False and pending.structured_content["accepted"] is False and
             pending.structured_content["status"] == "incomplete", "busy disable manufactured completion")
        need(driver._army_strength_query is None and driver._command_history[-1]["ok"] is False,
             "pending set kept stale cache or wrong history")

        # Malformed wire counters are rejected once after send and do not
        # manufacture state or retain the previous Army cache.
        army.query()
        malformed = packet(control.ENABLE_STEP,{"regular_core":row("enabled")},True)
        malformed[control.STATE_KEY]["regular_core"]["epoch"] = True
        replies.append(malformed)
        sent = len(requests)
        with pytest.raises(BridgeUnavailableError):
            driver.set_army_observer_research_sampling_v1(True,observer_family="regular_core",expected_revision=revision)
        need(len(requests)==sent+1 and driver._army_strength_query is None, "malformed control retried or retained cache")

        # A timeout after sending the real primitive leaves an unknown set
        # outcome; no second action, and old cache must be discarded.
        army.query()
        replies.append("timeout")
        sent = len(requests)
        with pytest.raises(BridgeUnavailableError):
            driver.set_army_observer_research_sampling_v1(True,observer_family="regular_core",expected_revision=revision)
        need(len(requests)==sent+1 and driver._army_strength_query is None,
             "unknown set result retried or reused stale cache")
        need(replies == [], "planned single control replies not consumed exactly once")

        # Schema-level negative branches use the same strict consumer.
        valid = {**packet(control.QUERY_STEP,{"regular_core":row("enabled")},True),"backend_id":"native-headless"}
        mutations = [
            lambda x:x.update(status=[]),
            lambda x:x[control.STATE_KEY].update(unselected=row("enabled")),
            lambda x:x[control.STATE_KEY]["regular_core"].update(qualified_records=1),
            lambda x:x[control.STATE_KEY]["regular_core"].update(readiness="retained_observation"),
            lambda x:x.update(accepted=False,status="incomplete"),
            lambda x:x[control.STATE_KEY]["regular_core"].update(active_captures=1),
        ]
        for change in mutations:
            bad = copy.deepcopy(valid);change(bad)
            with pytest.raises(ValueError):
                control.normalize_result(bad,expected_step=control.QUERY_STEP,observer_family="regular_core")
    finally:
        army.driver.close()
