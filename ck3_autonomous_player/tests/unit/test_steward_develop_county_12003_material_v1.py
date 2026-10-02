"""Offline SDK consumption of native-emitted .3 Develop County material DTOs.

Positive files are copied unchanged from the production native fixture. The
real native query method and service consume a fake primitive response; no
game, named pipe or UI is contacted. Only frontend revisions are synthetic.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.steward_develop_county_contract import (
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY,
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP,
)
from xar_autoplayer.bridge.version_identity import CK3_12003


FIXTURES = PROJECT_ROOT / "tests/fixtures/steward_develop_county_12003_material"
TOOL = "ck3_query_steward_develop_county_candidates_v1"
STEP = QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP
WIRE_NAMES = ["develop_material_available.json", "develop_material_blocked.json"]


def _native_result(name: str) -> dict[str, object]:
    packet = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return packet["result"]


class _NativeMaterialDriver:
    """Use the existing production query method with an offline native result."""

    _execute_steward_develop_county_candidates_v1_query = (
        NativeHeadlessGameplayDriver._execute_steward_develop_county_candidates_v1_query
    )

    def __init__(self, result: dict[str, object]):
        self.result = copy.deepcopy(result)
        frame = result["steward_develop_county_candidates"]
        native_revision = frame["snapshot_revision"]
        public_revision = native_revision + 100
        self.snapshot = {
            "format_version": 1,
            "snapshot_id": f"material-fixture:{public_revision}",
            "revision": public_revision,
            "native_revision": native_revision,
            "date_raw": frame["observed_date_raw"],
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": frame["player_character_id"], "alive": True},
            "episode_run_id": "offline-develop-material-fixture",
            "backend_id": "native-headless",
            "diagnostics": {
                "connection_generation": 1,
                "hello": {
                    "expected_ck3_version": CK3_12003.game_version,
                    "expected_ck3_sha256": CK3_12003.executable_sha256,
                },
            },
        }
        self.primitive_calls: list[dict[str, object]] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1, "backend_id": "native-headless", "source": "offline-native-wire-fixture",
            "snapshot": True, "wait_for_change": False,
            "action_steps": [STEP],
            "bridge_capabilities": [QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY],
        }

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def _execute_primitive_step(
        self, step: str, *, expected_revision: int,
        required_capability: str,
    ) -> dict[str, object]:
        assert step == STEP
        assert expected_revision == self.snapshot["revision"]
        assert required_capability == QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY
        self.primitive_calls.append({
            "step": step, "expected_revision": expected_revision,
            "required_capability": required_capability,
        })
        return copy.deepcopy(self.result)

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        assert step == STEP
        return self._execute_steward_develop_county_candidates_v1_query(
            expected_revision=expected_revision,
        )


@pytest.mark.parametrize("wire_name", WIRE_NAMES)
def test_official_sdk_consumes_production_material_wire_with_distinct_revisions(wire_name: str) -> None:
    from mcp import Client

    native = _native_result(wire_name)
    frame = native["steward_develop_county_candidates"]
    driver = _NativeMaterialDriver(native)

    async def exercise() -> None:
        async with Client(create_server(driver)) as client:
            listed = await client.list_tools()
            tool = next(item for item in listed.tools if item.name == TOOL)
            schema = tool.model_dump(mode="json", by_alias=True)["inputSchema"]
            assert set(schema["properties"]) == {"expected_revision"}
            assert schema["properties"]["expected_revision"]["type"] == "integer"
            assert schema["required"] == ["expected_revision"]
            assert schema["additionalProperties"] is False

            reply = await client.call_tool(TOOL, {"expected_revision": driver.snapshot["revision"]})
            assert reply.is_error is False
            result = reply.structured_content
            observed = result["steward_develop_county_candidates"]
            assert observed["player_character_id"] == frame["player_character_id"]
            assert observed["steward_character_id"] == frame["steward_character_id"]
            assert observed["task_key"] == "task_develop_county"
            assert observed["provenance"]["game_version"] == CK3_12003.game_version
            assert observed["provenance"]["executable_sha256"].upper() == CK3_12003.executable_sha256
            assert observed["readiness"] is True
            assert observed["shown"] is frame["shown"]
            assert observed["valid"] is frame["valid"]
            assert observed == frame
            assert observed["candidate_collection_scope"] == "player_realm"
            assert observed["candidate_collection_complete"] is True
            assert result["source"]["revision"] == driver.snapshot["revision"]
            assert result["source"]["native_revision"] == frame["snapshot_revision"]
            assert result["source"]["revision"] != result["source"]["native_revision"]
            assert result["binding"]["expected_revision"] == driver.snapshot["revision"]

    asyncio.run(exercise())
    assert len(driver.primitive_calls) == 1


def test_query_only_material_uses_existing_action_consumer_rejection() -> None:
    native = _native_result("develop_material_available.json")
    frame = native["steward_develop_county_candidates"]
    driver = _NativeMaterialDriver(native)
    row = next(row for row in frame["candidates"] if row["native_target_valid"])

    with pytest.raises(BridgeUnavailableError, match="same-frame native candidate"):
        GameplayBridgeService(driver).change_steward_develop_county_task_v1(
            frame["steward_character_id"], "task_develop_county",
            row["county_title_id"], expected_revision=driver.snapshot["revision"],
            replace_existing_task=True,
        )

    assert [call["step"] for call in driver.primitive_calls] == [STEP]
