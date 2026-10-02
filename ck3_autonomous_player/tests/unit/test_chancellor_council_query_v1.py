"""Synthetic offline role fixtures for the two private Council read queries.

Existing native serializer fixtures supply the DTO shape. Chancellor role,
skill and current build metadata are explicit synthetic substitutions, not
paused game evidence. No test opens a pipe, controls CK3 or writes a ledger.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    build_assign_councillor_request_v1,
)
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    CHANCELLOR_POSITION_KEY,
    STEWARD_POSITION_KEY,
    build_council_composition_candidates_request_v1,
    normalize_council_composition_candidates_v1,
)
from xar_autoplayer.bridge.council_private_transport_v1 import (
    PRIVATE_GATES_STEP,
    PRIVATE_QUERY_STEP,
    PRIVATE_STATUS_STEP,
    query_council_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.private_council_formal_consumer_v1 import select_council_candidate_v1


FIXTURES = PROJECT_ROOT / "tests/fixtures/native_12002/governance"
PAYLOAD_KEYS = (
    "snapshot", "owner_character_id", "position",
    "candidate_collection_complete", "candidates", "readiness",
)


def _wire(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _terminal(position_key: str, query_step: str = PRIVATE_QUERY_STEP) -> dict[str, object]:
    result = _wire("council-private-query-available.json")["result"]
    payload = result["council_composition_candidates"]
    payload["exact_build"] = {
        "game_version": CK3_12003.game_version,
        "executable_sha256": CK3_12003.executable_sha256,
    }
    skill_key = "diplomacy" if position_key == CHANCELLOR_POSITION_KEY else "stewardship"
    payload["position"]["position_key"] = position_key
    payload["position"]["incumbent_main_skill"]["key"] = skill_key
    for candidate in payload["candidates"]:
        candidate["main_skill"]["key"] = skill_key
    if query_step == PRIVATE_GATES_STEP:
        gates = _wire("council-gates.json")["result"]["council_final_gates"]
        gates["council_composition_candidates"] = payload
        result["step"] = PRIVATE_GATES_STEP
        result["council_final_gates"] = gates
        del result["council_composition_candidates"]
    return result


def _payload(position_key: str) -> dict[str, object]:
    value = _terminal(position_key)["council_composition_candidates"]
    return {key: value[key] for key in PAYLOAD_KEYS}


def _request(**extra: object) -> dict[str, object]:
    return build_council_composition_candidates_request_v1(
        expected_snapshot_id="native:13", public_revision=13,
        native_revision=13, date_raw=53175816, owner_character_id=16777217,
        **extra,
    )


def _normalize(payload: dict[str, object], **extra: object) -> dict[str, object]:
    return normalize_council_composition_candidates_v1(
        payload, expected_snapshot_id="native:13", expected_public_revision=13,
        expected_native_revision=13, expected_date_raw=53175816,
        expected_owner_character_id=16777217, **extra,
    )


class _MailboxDriver:
    allow_private_council_query = True
    allow_private_council_action = False
    query_council_composition_candidates_private_v1 = (
        NativeHeadlessGameplayDriver.query_council_composition_candidates_private_v1
    )
    query_council_final_gates_private_v1 = (
        NativeHeadlessGameplayDriver.query_council_final_gates_private_v1
    )

    def __init__(self, results: list[dict[str, object]]):
        payload = _payload(STEWARD_POSITION_KEY)
        self.snapshot = {
            "snapshot_id": "native:31", "revision": 31, "native_revision": 13,
            "date_raw": payload["snapshot"]["date_raw"], "paused": True,
            "map_ready": True,
            "played_character": {"character_id": payload["owner_character_id"], "alive": True},
        }
        self.results = copy.deepcopy(results)
        self.sent: list[dict[str, object]] = []
        self.endpoint = SimpleNamespace(send=self.sent.append)
        self.state = SimpleNamespace(wait_for_command_result=self._response)
        self.command_timeout_seconds = 1.0

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def take_snapshot(self) -> dict[str, object]:
        return {**self.take_internal_semantic_snapshot(), "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }}}

    def _response(self, request_id: str, timeout: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True, "result": self.results.pop(0),
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1, "backend_id": "native-headless", "source": "named-pipe",
            "snapshot": True, "wait_for_change": False, "action_steps": [], "bridge_capabilities": [],
        }


def test_public_builder_and_default_consumer_remain_steward_only() -> None:
    assert _request()["position_key"] == STEWARD_POSITION_KEY
    assert _normalize(_payload(STEWARD_POSITION_KEY))["position"]["position_key"] == STEWARD_POSITION_KEY
    with pytest.raises(ValueError, match="explicitly opted-in"):
        _request(position_key=CHANCELLOR_POSITION_KEY)
    with pytest.raises(ValueError, match="requested position"):
        _normalize(_payload(CHANCELLOR_POSITION_KEY))


def test_private_chancellor_request_and_role_specific_skill_are_explicit() -> None:
    request = _request(position_key=CHANCELLOR_POSITION_KEY, allow_chancellor_read_only=True)
    assert request["position_key"] == CHANCELLOR_POSITION_KEY
    normalized = _normalize(_payload(CHANCELLOR_POSITION_KEY), expected_position_key=request["position_key"])
    assert normalized["position"]["incumbent_main_skill"]["key"] == "diplomacy"
    assert all(row["main_skill"]["key"] == "diplomacy" for row in normalized["candidates"])
    with pytest.raises(ValueError, match="position_key must"):
        _request(position_key="councillor_marshal", allow_chancellor_read_only=True)


@pytest.mark.parametrize("position_key", [STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY])
@pytest.mark.parametrize("field", ["incumbent", "candidate"])
def test_wrong_role_skill_cannot_become_available(position_key: str, field: str) -> None:
    payload = _payload(position_key)
    wrong_skill = "stewardship" if position_key == CHANCELLOR_POSITION_KEY else "diplomacy"
    skill = (payload["position"]["incumbent_main_skill"] if field == "incumbent"
             else payload["candidates"][0]["main_skill"])
    skill["key"] = wrong_skill
    with pytest.raises(ValueError, match="incumbent_main_skill is invalid|main_skill.key must"):
        _normalize(payload, expected_position_key=position_key)


@pytest.mark.parametrize("query_step", [PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP])
def test_private_mailbox_preserves_requested_role_while_polling(query_step: str) -> None:
    pending = _wire("council-private-query-pending.json")["result"]
    pending["step"] = query_step
    driver = _MailboxDriver([pending, _terminal(CHANCELLOR_POSITION_KEY, query_step)])
    result = query_council_private_v1(
        driver, expected_revision=31, position_key=CHANCELLOR_POSITION_KEY,
        query_step=query_step, expected_game_version=CK3_12003.game_version,
        expected_executable_sha256=CK3_12003.executable_sha256,
    )
    assert result["read_only"] is True
    assert result["council_composition_candidates"]["position"]["position_key"] == CHANCELLOR_POSITION_KEY
    assert [request["step"] for request in driver.sent] == [query_step, PRIVATE_STATUS_STEP]
    assert driver.sent[0]["position_key"] == CHANCELLOR_POSITION_KEY
    assert driver.sent[0]["expected_revision"] == 13
    assert "position_key" not in driver.sent[1]
    assert "expected_revision" not in driver.sent[1]
    assert driver.results == []


@pytest.mark.parametrize("query_step", [PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP])
def test_old_steward_response_cannot_satisfy_chancellor_request(query_step: str) -> None:
    driver = _MailboxDriver([_terminal(STEWARD_POSITION_KEY, query_step)])
    with pytest.raises(BridgeUnavailableError, match="requested position"):
        query_council_private_v1(
            driver, expected_revision=31, position_key=CHANCELLOR_POSITION_KEY,
            query_step=query_step, expected_game_version=CK3_12003.game_version,
            expected_executable_sha256=CK3_12003.executable_sha256,
        )


def test_chancellor_typed_occupied_request_preserves_default_vacancy_policy() -> None:
    observation = _normalize(_payload(CHANCELLOR_POSITION_KEY), expected_position_key=CHANCELLOR_POSITION_KEY)
    request = build_assign_councillor_request_v1(
        observation, candidate_character_id=observation["candidates"][0]["character_id"],
        request_id="offline-chancellor-occupied",
    )
    assert request.position_key == CHANCELLOR_POSITION_KEY
    assert request.expected_has_incumbent is True
    terminal = _terminal(CHANCELLOR_POSITION_KEY, PRIVATE_GATES_STEP)
    query = {**terminal, "council_composition_candidates": observation}
    occupied = select_council_candidate_v1(query, position_key=CHANCELLOR_POSITION_KEY)
    assert occupied["outcome"] == "NO_CHANGE"
    assert occupied["reason_code"] == "occupied_chancellor_outside_action_coverage"
    # This is a constructed offline vacancy, not a paused appointment outcome.
    observation["position"].update({"incumbent_character_id": None,
        "incumbent_main_skill": None, "vacant": True, "action_route": "assign"})
    for row in observation["candidates"]:
        row["action_route"] = "assign"
    decision = select_council_candidate_v1(query, position_key=CHANCELLOR_POSITION_KEY)
    assert decision["outcome"] == "ASSIGN_REQUIRED"
    request = build_assign_councillor_request_v1(
        observation, candidate_character_id=decision["selected_candidate"]["character_id"],
        request_id="offline-chancellor-vacancy",
    )
    assert request.position_key == CHANCELLOR_POSITION_KEY
    assert request.expected_has_incumbent is False
    observation["position"]["position_key"] = "councillor_spymaster"
    with pytest.raises(ValueError, match="complete paused frame"):
        build_assign_councillor_request_v1(observation,
            candidate_character_id=request.candidate_character_id, request_id="unsupported-role")


@pytest.mark.parametrize("query_step,tool_name", [
    (PRIVATE_QUERY_STEP, "ck3_query_council_composition_candidates_private_v1"),
    (PRIVATE_GATES_STEP, "ck3_query_council_final_gates_private_v1"),
])
def test_existing_mcp_tools_route_explicit_chancellor_and_default_steward(
    query_step: str, tool_name: str,
) -> None:
    from mcp import Client

    driver = _MailboxDriver([
        _terminal(CHANCELLOR_POSITION_KEY, query_step),
        _terminal(STEWARD_POSITION_KEY, query_step),
    ])

    async def exercise() -> None:
        async with Client(create_server(driver)) as client:
            chancellor = await client.call_tool(tool_name, {
                "expected_revision": 31, "position_key": CHANCELLOR_POSITION_KEY,
            })
            assert chancellor.is_error is False
            assert chancellor.structured_content["council_composition_candidates"]["position"]["position_key"] == CHANCELLOR_POSITION_KEY
            steward = await client.call_tool(tool_name, {"expected_revision": 31})
            assert steward.is_error is False
            assert steward.structured_content["council_composition_candidates"]["position"]["position_key"] == STEWARD_POSITION_KEY

    asyncio.run(exercise())
    assert [request["position_key"] for request in driver.sent] == [CHANCELLOR_POSITION_KEY, STEWARD_POSITION_KEY]
    assert driver.results == []
