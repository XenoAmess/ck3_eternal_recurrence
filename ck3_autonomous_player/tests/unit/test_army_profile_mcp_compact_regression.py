"""Offline profile/compact regressions through real Driver, Service and MCP.

Only the endpoint and the automatic planner's choice are synthetic. None of
these cases connect to CK3 or establish live native acceptance.
"""

from __future__ import annotations

import asyncio
import copy
import json
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from test_native_bridge_driver import FakeEndpoint, _army, _army_strength, _hello, _snapshot
from xar_autoplayer.bridge.army_strengths_mcp_result import (
    build_army_auto_turn_mcp_result,
    build_army_strengths_mcp_result,
)
from xar_autoplayer.bridge.army_strengths_profile_contract import (
    ARMY_OBSERVED_PHASE_COVERAGE_KEY,
    ARMY_STRENGTHS_PROFILE_KEY,
    OBSERVED_HISTORY_FULL_PROFILE,
    OBSERVED_PHASE_KEYS,
    ORDINARY_CORE_PROFILE,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


@contextmanager
def _registered_army_server(*, full_failure: str | None = None):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
        episode_projection="native_campaign",
    )
    endpoint.publish(_hello("game.state.snapshot", "game.command.query-army-strengths-v1"))
    endpoint.publish(_snapshot(
        40,
        played_character={"character_id": 707, "alive": True},
        active_wars=[],
        player_armies=[_army(81), _army(82)],
    ))
    before = driver.take_internal_semantic_snapshot()
    requests = []

    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        assert frame["step"] == QUERY_ARMY_STRENGTHS_STEP
        profile = frame[ARMY_STRENGTHS_PROFILE_KEY]
        requests.append(copy.deepcopy(frame))
        envelope = {
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"],
        }
        if profile == OBSERVED_HISTORY_FULL_PROFILE and full_failure == "rejected":
            endpoint.publish({**envelope, "ok": False,
                              "error": "synthetic full profile unsupported"})
            return
        delivered_profile = (
            ORDINARY_CORE_PROFILE if full_failure == "mismatch" else profile
        )
        rows = [
            _army_strength(81, "player", [], current=0, maximum=10, base_power_raw=0),
            _army_strength(82, "player", [], status="unavailable"),
        ]
        if delivered_profile == OBSERVED_HISTORY_FULL_PROFILE:
            for row in rows:
                row.update({key: None for key in OBSERVED_PHASE_KEYS})
        endpoint.publish({
            **envelope, "ok": True,
            "result": {
                "step": QUERY_ARMY_STRENGTHS_STEP, "accepted": True,
                "status": "partial", "query_sequence": 7, "army_strengths": rows,
                ARMY_STRENGTHS_PROFILE_KEY: delivered_profile,
                ARMY_OBSERVED_PHASE_COVERAGE_KEY: (
                    "not_requested" if delivered_profile == ORDINARY_CORE_PROFILE
                    else "exported_retained"
                ),
            },
        })

    endpoint.send_hook = answer
    try:
        yield create_server(driver), driver, before, requests
    finally:
        driver.close()


def _compact_summary(response, *, auto=False):
    assert response.is_error is False
    assert len(response.content) == 1
    assert response.content[0].type == "text"
    structured = response.structured_content
    assert isinstance(structured, dict)
    assert json.loads(response.content[0].text) == structured
    encoded = response.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8")
    assert len(encoded) < 4096
    for key in OBSERVED_PHASE_KEYS:
        assert key.encode("utf-8") not in encoded
    assert b"actual_army_observed_phase_consumption_12004" not in encoded
    assert b"army_strengths\"" not in encoded
    assert structured["result_location"] == "compact_mcp_summary"
    return structured["result"] if auto else structured


def _assert_observed_values(summary, before, army_ids, profile, coverage):
    assert summary[ARMY_STRENGTHS_PROFILE_KEY] == profile
    assert summary[ARMY_OBSERVED_PHASE_COVERAGE_KEY] == coverage
    assert summary["accepted"] is True
    assert summary["status"] == "partial"
    assert summary["query_sequence"] == 7
    assert summary["army_ids"] == army_ids
    assert summary["source"]["revision"] == before["revision"]
    assert summary["source"]["native_revision"] == before["native_revision"]
    assert [row["army_id"] for row in summary["armies"]] == army_ids
    by_id = {row["army_id"]: row for row in summary["armies"]}
    assert by_id[81]["status"] == "available"
    assert by_id[81]["current_soldiers"] == 0
    assert by_id[81]["ai_base_power_raw"] == 0
    assert by_id[81]["unavailable_reason"] is None
    assert by_id[82]["status"] == "unavailable"
    assert by_id[82]["current_soldiers"] is None
    assert by_id[82]["ai_base_power_raw"] is None
    assert by_id[82]["unavailable_reason"] == "regiment_generation_mismatch"


@pytest.mark.parametrize("route", ["direct", "execute", "auto"])
def test_army_strengths_core_registered_routes_keep_scope_and_compact_metadata(route):
    with _registered_army_server() as (server, driver, before, requests):
        if route == "direct":
            response = asyncio.run(server.call_tool("ck3_query_army_strengths", {
                "army_ids": [82, 81], "expected_revision": before["revision"],
            }))
            expected_ids = [82, 81]
        elif route == "execute":
            response = asyncio.run(server.call_tool("ck3_execute_step", {
                "step": QUERY_ARMY_STRENGTHS_STEP,
                "expected_revision": before["revision"],
            }))
            expected_ids = [81, 82]
        else:
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value={
                "selected_step": QUERY_ARMY_STRENGTHS_STEP,
                "phase": "synthetic_army_query",
            }) as planner:
                response = asyncio.run(server.call_tool("ck3_auto_turn", {}))
                planner.assert_called_once()
            assert response.structured_content["status"] == "executed"
            assert response.structured_content["selected_step"] == QUERY_ARMY_STRENGTHS_STEP
            expected_ids = [81, 82]
        summary = _compact_summary(response, auto=route == "auto")
        _assert_observed_values(summary, before, expected_ids,
                                ORDINARY_CORE_PROFILE, "not_requested")
        assert [request[ARMY_STRENGTHS_PROFILE_KEY] for request in requests] == [
            ORDINARY_CORE_PROFILE
        ]
        cached = driver.take_internal_semantic_snapshot()
        assert len(cached["army_strengths"]) == 2
        assert cached[ARMY_STRENGTHS_PROFILE_KEY] == ORDINARY_CORE_PROFILE
        assert cached[ARMY_OBSERVED_PHASE_COVERAGE_KEY] == "not_requested"
        for row in cached["army_strengths"]:
            assert not set(OBSERVED_PHASE_KEYS).intersection(row)


def test_army_strengths_explicit_full_keeps_null_observations_in_service_and_compact_metadata():
    with _registered_army_server() as (server, driver, before, requests):
        # Spy on the real builder's input without replacing Service, Driver or
        # the builder's behavior. Ordinary snapshots deliberately require core.
        with patch("xar_autoplayer.bridge.mcp_server.build_army_strengths_mcp_result",
                   wraps=build_army_strengths_mcp_result) as builder:
            response = asyncio.run(server.call_tool("ck3_query_army_strengths", {
                "army_ids": [81, 82], "expected_revision": before["revision"],
                "profile": OBSERVED_HISTORY_FULL_PROFILE,
            }))
            builder.assert_called_once()
            full_payload = builder.call_args.args[0]
        _assert_observed_values(_compact_summary(response), before, [81, 82],
                                OBSERVED_HISTORY_FULL_PROFILE, "exported_retained")
        assert [request[ARMY_STRENGTHS_PROFILE_KEY] for request in requests] == [
            OBSERVED_HISTORY_FULL_PROFILE
        ]
        assert len(full_payload["army_strengths"]) == 2
        assert full_payload[ARMY_STRENGTHS_PROFILE_KEY] == OBSERVED_HISTORY_FULL_PROFILE
        assert full_payload[ARMY_OBSERVED_PHASE_COVERAGE_KEY] == "exported_retained"
        for row in full_payload["army_strengths"]:
            for key in OBSERVED_PHASE_KEYS:
                assert key in row
                assert row[key] is None
        assert driver.take_internal_semantic_snapshot()["army_strengths"] == []


@pytest.mark.parametrize("failure, message", [
    ("rejected", "synthetic full profile unsupported"),
    ("mismatch", "profile disagrees with request"),
])
def test_army_strengths_full_failure_is_visible_without_core_retry(failure, message):
    with _registered_army_server(full_failure=failure) as (server, driver, before, requests):
        with pytest.raises(ToolError, match=message):
            asyncio.run(server.call_tool("ck3_query_army_strengths", {
                "army_ids": [81], "expected_revision": before["revision"],
                "profile": OBSERVED_HISTORY_FULL_PROFILE,
            }))
        assert [request[ARMY_STRENGTHS_PROFILE_KEY] for request in requests] == [
            OBSERVED_HISTORY_FULL_PROFILE
        ]
        assert driver.take_internal_semantic_snapshot().get("army_strengths") in (None, [])


@pytest.mark.parametrize("auto", [False, True])
def test_army_strengths_actual_compact_builders_do_not_export_large_projected_journals(auto):
    # Exercise the real builders with a large in-memory Service projection;
    # this fixture is not a native journal/schema validation claim.
    marker = "synthetic-observed-journal-only-" * 4096
    payload = {
        "accepted": True, "status": "available", "query_sequence": 7,
        ARMY_STRENGTHS_PROFILE_KEY: OBSERVED_HISTORY_FULL_PROFILE,
        ARMY_OBSERVED_PHASE_COVERAGE_KEY: "exported_retained",
        "army_ids": [81], "source": {"revision": 40, "native_revision": 40},
        "army_strengths": [{**_army_strength(81, "player", [], current=0),
                            **{key: None for key in OBSERVED_PHASE_KEYS}}],
        "actual_army_observed_phase_consumption_12004": [{"journal": marker}],
    }
    original = copy.deepcopy(payload)
    if auto:
        response = build_army_auto_turn_mcp_result({
            "status": "executed", "selected_step": QUERY_ARMY_STRENGTHS_STEP,
            "plan": {"selected_step": QUERY_ARMY_STRENGTHS_STEP,
                     "phase": "synthetic_army_query", "journal": marker},
            "result": payload,
        })
    else:
        response = build_army_strengths_mcp_result(payload)
    summary = _compact_summary(response, auto=auto)
    assert summary[ARMY_STRENGTHS_PROFILE_KEY] == OBSERVED_HISTORY_FULL_PROFILE
    assert summary[ARMY_OBSERVED_PHASE_COVERAGE_KEY] == "exported_retained"
    assert summary["armies"][0]["current_soldiers"] == 0
    assert "synthetic-observed-journal-only" not in response.model_dump_json()
    assert payload == original
