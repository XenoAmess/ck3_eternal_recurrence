"""Focused contract checks for the private paused prisoner collection route."""

from __future__ import annotations

from copy import deepcopy
import asyncio

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.player_prisoner_collection_private_transport import (
    query_player_prisoner_collection_private_v1,
)


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def send(self, value: dict[str, object]) -> None:
        self.request = value


class _State:
    def __init__(self, endpoint: _Endpoint, value: dict[str, object]) -> None:
        self.endpoint = endpoint
        self.value = value

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        assert timeout > 0
        assert self.endpoint.request is not None
        assert self.endpoint.request["request_id"] == request_id
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": self.value}


class _Driver:
    allow_private_prisoner_collection_query = True

    def __init__(self, result: dict[str, object]) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint, result)
        self.snapshot = {
            "snapshot_id": "paused-1", "revision": 4, "native_revision": 5,
            "date_raw": 100, "paused": True, "map_ready": True,
            "played_character": {"character_id": 31853, "alive": True},
        }
        self.drift_after_first = False
        self.snapshot_reads = 0

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_reads += 1
        result = deepcopy(self.snapshot)
        if self.drift_after_first and self.snapshot_reads > 1:
            result["date_raw"] += 1
        return result


def _result() -> dict[str, object]:
    return {
        "step": "query-player-prisoner-collection-private-v1",
        "accepted": True, "status": "available", "query_sequence": 1,
        "observation_revision": 2, "snapshot_revision": 5,
        "player_prisoner_collection": {
            "schema": "player-prisoner-collection-private-v1",
            "schema_version": 1, "snapshot_revision": 5,
            "status": "available", "unavailable_reason": None,
            "date_raw": 100, "played_character_id": 31853,
            "total_count": 1, "returned_count": 1,
            "collection_complete": True,
            "prisoners": [{"source_ordinal": 0,
                           "prisoner_character_id": 34250,
                           "collection_owner_character_id": 31853,
                           "jailer_character_id": 31853,
                           "custody_relation_verified": True}],
        },
        "private_build": True, "read_only": True,
        "advertised": False, "backend_id": "native-headless",
    }


def test_private_prisoner_collection_valid_paused_result() -> None:
    driver = _Driver(_result())
    value = query_player_prisoner_collection_private_v1(
        driver, expected_revision=4)
    assert value["player_prisoner_collection"]["prisoners"][0]["prisoner_character_id"] == 34250
    assert driver.endpoint.request["expected_revision"] == 5


def test_private_prisoner_collection_rejects_unpaired_owner() -> None:
    result = _result()
    result["player_prisoner_collection"]["prisoners"][0]["collection_owner_character_id"] = 99
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4)


def test_private_prisoner_collection_rejects_reverse_jailer_mismatch() -> None:
    result = _result()
    result["player_prisoner_collection"]["prisoners"][0]["jailer_character_id"] = 99
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4)


def test_private_prisoner_collection_requires_opt_in() -> None:
    driver = _Driver(_result())
    driver.allow_private_prisoner_collection_query = False
    with pytest.raises(UnsupportedStepError):
        query_player_prisoner_collection_private_v1(
            driver, expected_revision=4)


def test_private_prisoner_collection_rejects_frame_drift() -> None:
    driver = _Driver(_result())
    driver.drift_after_first = True
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            driver, expected_revision=4)


def test_private_prisoner_collection_preserves_typed_unavailable() -> None:
    result = _result()
    result["status"] = "unavailable"
    result["player_prisoner_collection"].update({
        "status": "unavailable", "unavailable_reason": "collection_truncated",
        "date_raw": None, "played_character_id": None,
        "total_count": None, "returned_count": None,
        "collection_complete": False, "prisoners": [],
    })
    value = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    assert value["status"] == "unavailable"


def test_mcp_registers_read_only_tool_only_for_private_opt_in() -> None:
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server

    class McpDriver:
        allow_private_prisoner_collection_query = False

        def query_player_prisoner_collection_private_v1(
            self, *, expected_revision: int,
        ) -> dict[str, object]:
            return {"expected_revision": expected_revision, "status": "unavailable"}

    async def check() -> None:
        driver = McpDriver()
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            assert "ck3_query_player_prisoner_collection_private_v1" not in names
        driver.allow_private_prisoner_collection_query = True
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            tool = tools["ck3_query_player_prisoner_collection_private_v1"]
            assert tool.annotations.read_only_hint is True
            result = await client.call_tool(
                tool.name, {"expected_revision": 5})
            assert result.is_error is False
            assert result.structured_content["expected_revision"] == 5

    asyncio.run(check())
