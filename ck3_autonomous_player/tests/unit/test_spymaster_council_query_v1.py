"""Offline consumption of native-emitted Spymaster Council read fixtures.

Positive packets come from the production provider/projector/codec transport
fixture with distinct diplomacy, stewardship and intrigue values. Negative
cases mutate those packets explicitly. Frontend revisions are synthetic and
different from the preserved native revisions. No live game or pipe is used.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    build_assign_councillor_request_v1,
)
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    CHANCELLOR_POSITION_KEY,
    SPYMASTER_POSITION_KEY,
    STEWARD_POSITION_KEY,
    build_council_composition_candidates_request_v1,
)
from xar_autoplayer.bridge.council_private_transport_v1 import (
    PRIVATE_GATES_STEP,
    PRIVATE_QUERY_STEP,
    query_council_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import require_exact_native_build
from xar_autoplayer.private_council_formal_consumer_v1 import select_council_candidate_v1
from test_chancellor_council_query_v1 import _MailboxDriver


FIXTURES = PROJECT_ROOT / "tests/fixtures/council_spymaster_readonly"
QUERY_NAMES = {
    PRIVATE_QUERY_STEP: "spymaster_status_available.json",
    PRIVATE_GATES_STEP: "spymaster_status_gates.json",
}
TOOLS = {
    PRIVATE_QUERY_STEP: "ck3_query_council_composition_candidates_private_v1",
    PRIVATE_GATES_STEP: "ck3_query_council_final_gates_private_v1",
}


def _result(query_step: str) -> dict[str, object]:
    raw = json.loads((FIXTURES / QUERY_NAMES[query_step]).read_text(encoding="utf-8"))
    return raw["result"]


def _candidates(result: dict[str, object], query_step: str) -> dict[str, object]:
    if query_step == PRIVATE_GATES_STEP:
        return result["council_final_gates"]["council_composition_candidates"]
    return result["council_composition_candidates"]


class _SpymasterMailbox(_MailboxDriver):
    def __init__(self, result: dict[str, object], query_step: str):
        super().__init__([result])
        payload = _candidates(result, query_step)
        frame = payload["snapshot"]
        native = frame["native_revision"]
        public = native + 100
        self.snapshot = {
            "snapshot_id": f"native:{public}", "revision": public,
            "native_revision": native, "date_raw": frame["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": payload["owner_character_id"], "alive": True},
        }
        exact = payload["exact_build"]
        self.native_build = require_exact_native_build(exact["game_version"], exact["executable_sha256"])

    def take_snapshot(self) -> dict[str, object]:
        return {**self.take_internal_semantic_snapshot(), "diagnostics": {"hello": {
            "expected_ck3_version": self.native_build.game_version,
            "expected_ck3_sha256": self.native_build.executable_sha256,
        }}}


def _query(driver: _SpymasterMailbox, query_step: str) -> dict[str, object]:
    return query_council_private_v1(
        driver, expected_revision=driver.snapshot["revision"],
        position_key=SPYMASTER_POSITION_KEY, query_step=query_step,
        expected_game_version=driver.native_build.game_version,
        expected_executable_sha256=driver.native_build.executable_sha256,
    )


def test_spymaster_read_is_explicit_and_public_steward_default_is_preserved() -> None:
    fields = {
        "expected_snapshot_id": "native:13", "public_revision": 13,
        "native_revision": 13, "date_raw": 53175816, "owner_character_id": 16777217,
    }
    assert build_council_composition_candidates_request_v1(**fields)["position_key"] == STEWARD_POSITION_KEY
    for role, flags in (
        (SPYMASTER_POSITION_KEY, {}),
        (SPYMASTER_POSITION_KEY, {"allow_chancellor_read_only": True}),
        (CHANCELLOR_POSITION_KEY, {"allow_spymaster_read_only": True}),
    ):
        with pytest.raises(ValueError, match="explicitly opted-in"):
            build_council_composition_candidates_request_v1(**fields, position_key=role, **flags)
    request = build_council_composition_candidates_request_v1(
        **fields, position_key=SPYMASTER_POSITION_KEY, allow_spymaster_read_only=True,
    )
    assert request["position_key"] == SPYMASTER_POSITION_KEY


@pytest.mark.parametrize("query_step", [PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP])
def test_production_native_spymaster_packets_publish_intrigue_and_bind_native_frame(query_step: str) -> None:
    driver = _SpymasterMailbox(_result(query_step), query_step)
    result = _query(driver, query_step)
    payload = result["council_composition_candidates"]
    assert result["read_only"] is True
    assert payload["position"]["position_key"] == SPYMASTER_POSITION_KEY
    assert payload["position"]["incumbent_main_skill"] == {"key": "intrigue", "value": 17}
    assert sorted(row["main_skill"]["value"] for row in payload["candidates"]) == [13, 23]
    assert all(row["main_skill"]["key"] == "intrigue" for row in payload["candidates"])
    assert driver.sent[0]["position_key"] == SPYMASTER_POSITION_KEY
    assert driver.sent[0]["expected_revision"] == driver.snapshot["native_revision"]
    assert driver.sent[0]["expected_revision"] != driver.snapshot["revision"]
    assert result["queried_revision"] == driver.snapshot["revision"]
    assert payload["snapshot"]["public_revision"] == driver.snapshot["native_revision"]
    if query_step == PRIVATE_GATES_STEP:
        gates = result["council_final_gates"]
        assert gates["candidate_count"] == len(payload["candidates"]) == len(gates["rows"])
        assert [(row["character_id"], row["native_collection_ordinal"]) for row in gates["rows"]] == [
            (row["character_id"], row["native_collection_ordinal"]) for row in payload["candidates"]
        ]
    assert driver.results == []


@pytest.mark.parametrize("wrong_skill", ["stewardship", "diplomacy"])
@pytest.mark.parametrize("field", ["incumbent", "candidate"])
def test_spymaster_rejects_another_roles_effective_skill(wrong_skill: str, field: str) -> None:
    result = _result(PRIVATE_QUERY_STEP)
    payload = _candidates(result, PRIVATE_QUERY_STEP)
    skill = (payload["position"]["incumbent_main_skill"] if field == "incumbent"
             else payload["candidates"][0]["main_skill"])
    skill["key"] = wrong_skill
    driver = _SpymasterMailbox(result, PRIVATE_QUERY_STEP)
    with pytest.raises(BridgeUnavailableError, match="incumbent_main_skill is invalid|main_skill.key must be intrigue"):
        _query(driver, PRIVATE_QUERY_STEP)


@pytest.mark.parametrize("query_step", [PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP])
@pytest.mark.parametrize("wrong_role", [STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY])
def test_same_frame_other_role_cannot_satisfy_spymaster_request(query_step: str, wrong_role: str) -> None:
    result = _result(query_step)
    _candidates(result, query_step)["position"]["position_key"] = wrong_role
    driver = _SpymasterMailbox(result, query_step)
    with pytest.raises(BridgeUnavailableError, match="requested position"):
        _query(driver, query_step)


def test_missing_spymaster_skill_is_not_an_available_observation() -> None:
    result = _result(PRIVATE_QUERY_STEP)
    del _candidates(result, PRIVATE_QUERY_STEP)["candidates"][0]["main_skill"]
    driver = _SpymasterMailbox(result, PRIVATE_QUERY_STEP)
    with pytest.raises(BridgeUnavailableError, match="exactly the v1 fields"):
        _query(driver, PRIVATE_QUERY_STEP)


def test_readonly_spymaster_does_not_enter_assignment_or_formal_steward_policy() -> None:
    driver = _SpymasterMailbox(_result(PRIVATE_GATES_STEP), PRIVATE_GATES_STEP)
    query = _query(driver, PRIVATE_GATES_STEP)
    payload = query["council_composition_candidates"]
    with pytest.raises(ValueError, match="complete paused frame"):
        build_assign_councillor_request_v1(
            payload, candidate_character_id=payload["candidates"][0]["character_id"],
            request_id="readonly-spymaster-fixture",
        )
    with pytest.raises(ValueError, match="requested position"):
        select_council_candidate_v1(query)
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == PRIVATE_GATES_STEP


@pytest.mark.parametrize("query_step", [PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP])
def test_existing_mcp_query_schema_routes_the_production_spymaster_payload(query_step: str) -> None:
    from mcp import Client

    driver = _SpymasterMailbox(_result(query_step), query_step)

    async def exercise() -> None:
        async with Client(create_server(driver)) as client:
            tools = await client.list_tools()
            tool = next(item for item in tools.tools if item.name == TOOLS[query_step])
            schema = tool.model_dump(mode="json", by_alias=True)["inputSchema"]
            assert schema["properties"]["position_key"]["default"] == STEWARD_POSITION_KEY
            assert schema["properties"]["position_key"]["type"] == "string"
            assert "expected_revision" in schema["required"]
            assert "position_key" not in schema["required"]
            assert "ck3_assign_councillor_private_v1" not in {item.name for item in tools.tools}
            response = await client.call_tool(TOOLS[query_step], {
                "expected_revision": driver.snapshot["revision"], "position_key": SPYMASTER_POSITION_KEY,
            })
            assert response.is_error is False
            payload = response.structured_content["council_composition_candidates"]
            assert payload["position"]["position_key"] == SPYMASTER_POSITION_KEY
            assert payload["position"]["incumbent_main_skill"] == {"key": "intrigue", "value": 17}

    asyncio.run(exercise())
    assert driver.sent[0]["position_key"] == SPYMASTER_POSITION_KEY
    assert driver.sent[0]["expected_revision"] == driver.snapshot["native_revision"]
    assert driver.results == []
