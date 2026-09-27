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


def _result_with_release_preview() -> dict[str, object]:
    result = _result()
    value = result["player_prisoner_collection"]
    value["schema_version"] = 2
    value["prisoners"][0]["unconditional_release_preview"] = {
        "private_build": True, "read_only": True, "advertised": False,
        "action_surface_present": False, "status": "available",
        "snapshot_id": "native:5", "public_revision": 5,
        "native_revision": 5, "date_raw": 100,
        "definition": {"canonical_key": "release_from_prison_interaction"},
        "payload_shape": "two_role_all_release_options_off",
        "roles": {"actor_character_id": 31853,
                  "recipient_character_id": 34250},
        "unconditional_prisoner_release": True, "can_send": True,
        "costs": {"raw_scale": 100_000,
                  "entries": [{"resource_key": str(index), "raw": 0}
                              for index in range(10)]},
        "acceptance": {"kind": "auto_accept", "auto_accept": True,
                       "would_accept_now": True},
        "readiness": {"same_frame_ready": True},
    }
    return result


def test_private_prisoner_collection_carries_native_unconditional_release() -> None:
    result = _result_with_release_preview()
    value = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    preview = value["player_prisoner_collection"]["prisoners"][0]["unconditional_release_preview"]
    assert preview["can_send"] is True
    assert preview["unconditional_prisoner_release"] is True


def test_private_release_preview_rejects_wrong_prisoner_binding() -> None:
    result = _result_with_release_preview()
    preview = result["player_prisoner_collection"]["prisoners"][0]["unconditional_release_preview"]
    preview["roles"]["recipient_character_id"] = 44484
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4)


def test_private_prisoner_lineage_is_same_frame_value_input() -> None:
    result = _result_with_release_preview()
    value = result["player_prisoner_collection"]
    value.update({"schema_version": 3, "played_house_id": 12,
                  "played_dynasty_id": 30})
    row = value["prisoners"][0]
    row.update({"house_id": 12, "dynasty_id": 30,
                "same_house": True, "same_dynasty": True})
    observed = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    assert observed["player_prisoner_collection"]["prisoners"][0]["same_dynasty"] is True

    row["same_dynasty"] = False
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4)


def test_private_prisoner_lineage_preserves_legitimate_absence() -> None:
    result = _result_with_release_preview()
    value = result["player_prisoner_collection"]
    value.update({"schema_version": 3, "played_house_id": None,
                  "played_dynasty_id": None})
    value["prisoners"][0].update({
        "house_id": None, "dynasty_id": None,
        "same_house": False, "same_dynasty": False,
    })
    query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)


def _result_with_ransom_quote() -> dict[str, object]:
    result = _result_with_release_preview()
    value = result["player_prisoner_collection"]
    value.update({"schema_version": 4, "played_house_id": 12,
                  "played_dynasty_id": 30})
    row = value["prisoners"][0]
    row.update({"house_id": 45, "dynasty_id": 45,
                "same_house": False, "same_dynasty": False,
                "ransom_quote_preview": {
                    "private_build": True, "read_only": True,
                    "advertised": False, "action_surface_present": False,
                    "status": "available", "unavailable_reason": None,
                    "snapshot_id": "native:5", "public_revision": 5,
                    "native_revision": 5, "proof_epoch": 2,
                    "date_raw": 100, "definition_key": "ransom_interaction",
                    "jailer_character_id": 31853, "payer_character_id": 44484,
                    "prisoner_character_id": 34250,
                    "selected_option": "gold", "can_send": True,
                    "quoted_gold_raw": 2_500_000, "raw_scale": 100_000,
                    "recipient_acceptance_raw": 100_000,
                    "recipient_answer_status_raw": 0,
                    "would_accept_now": True,
                    "amount_is_acceptance_time_quote": False,
                }})
    return result


def test_private_ransom_quote_requires_same_prisoner_payer_and_option() -> None:
    result = _result_with_ransom_quote()
    observed = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    quote = observed["player_prisoner_collection"]["prisoners"][0]["ransom_quote_preview"]
    assert quote["quoted_gold_raw"] == 2_500_000
    assert quote["payer_character_id"] == 44484

    quote["prisoner_character_id"] = 47028
    with pytest.raises(BridgeUnavailableError):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4)


def test_private_ransom_quote_keeps_refused_or_unavailable_distinct() -> None:
    result = _result_with_ransom_quote()
    quote = result["player_prisoner_collection"]["prisoners"][0]["ransom_quote_preview"]
    quote.update({"recipient_answer_status_raw": 2,
                  "would_accept_now": False})
    observed = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    assert observed["player_prisoner_collection"]["prisoners"][0]["ransom_quote_preview"]["would_accept_now"] is False
    quote.clear()
    quote.update({"private_build": True, "read_only": True,
                  "advertised": False, "action_surface_present": False,
                  "status": "unavailable", "unavailable_reason": "option_unavailable"})
    observed = query_player_prisoner_collection_private_v1(
        _Driver(result), expected_revision=4)
    assert observed["player_prisoner_collection"]["prisoners"][0]["ransom_quote_preview"]["status"] == "unavailable"


def test_private_ransom_ordinal_queries_one_bound_second_prisoner() -> None:
    result = _result_with_ransom_quote()
    value = result["player_prisoner_collection"]
    first = value["prisoners"][0]
    second = deepcopy(first)
    second["source_ordinal"] = 1
    second["prisoner_character_id"] = 47028
    second["unconditional_release_preview"]["roles"]["recipient_character_id"] = 47028
    second["ransom_quote_preview"]["prisoner_character_id"] = 47028
    first["ransom_quote_preview"] = {
        "private_build": True, "read_only": True, "advertised": False,
        "action_surface_present": False, "status": "unavailable",
        "unavailable_reason": "not_evaluated",
    }
    value.update({"total_count": 2, "returned_count": 2, "prisoners": [first, second]})
    result["step"] += "-ransom-ordinal-1"
    driver = _Driver(result)
    observed = query_player_prisoner_collection_private_v1(
        driver, expected_revision=4, ransom_ordinal=1,
    )
    assert driver.endpoint.request["step"] == result["step"]
    assert observed["player_prisoner_collection"]["prisoners"][1]["ransom_quote_preview"]["quoted_gold_raw"] == 2_500_000
    second["ransom_quote_preview"] = deepcopy(first["ransom_quote_preview"])
    with pytest.raises(BridgeUnavailableError, match="wrong prisoner ordinal"):
        query_player_prisoner_collection_private_v1(
            _Driver(result), expected_revision=4, ransom_ordinal=1,
        )


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
