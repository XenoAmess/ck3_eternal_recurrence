"""Require fresh compiled whole packets; exercise SDK, filming and JSON consumers.

The protocol hello/endpoint are synthetic. Trait rows and failure observations
must come from the real native mailbox/reader/serializer fixture, never an
authored replacement of its addon. No game process or game effect is used.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))

from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_observations import (
    MilestoneBinding, json_value, project_observation,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_pilgrimage_traits import normalize_player_pilgrimage_traits_v1
from xar_autoplayer.bridge.version_identity import CK3_12004


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError("whole native JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError("native JSON keys must be strings")
        result[key] = item
    return result


class Endpoint:
    pipe_name = r"\\.\pipe\pilgrimage-trait-offline-synthetic"

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.on_frame: Callable[[dict[str, object]], None] | None = None
        self.requests: list[dict[str, object]] = []

    def start(self, on_frame: Callable[[dict[str, object]], None],
              on_disconnect: Callable[[], None]) -> None:
        self.on_frame = on_frame

    def publish(self, value: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(deepcopy(value))

    def send(self, frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        assert frame.get("step") == "query-player-religion-context-v1"
        self.requests.append(deepcopy(frame))
        reply = deepcopy(self.packet)
        # Only the test transport correlation token is bound to the real SDK
        # request. The complete compiled native result is retained unchanged.
        reply["request_id"] = frame["request_id"]
        self.publish(reply)

    def close(self) -> None:
        pass


async def consume(packet_value: object, index: int) -> None:
    from mcp import Client

    packet = object_value(packet_value)
    original = deepcopy(packet)
    result = object_value(packet["result"])
    context = object_value(result["player_religion_context"])
    assert result["game_version"] == CK3_12004.game_version
    assert result["executable_sha256"] == CK3_12004.executable_sha256
    assert result["step"] == "query-player-religion-context-v1"
    expected = normalize_player_pilgrimage_traits_v1(result["player_pilgrimage_traits"],
                                                   current_context=context)
    assert expected is not None and expected["available"] == (index < 3)
    endpoint = Endpoint(packet)
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    try:
        setattr(driver, "allow_private_player_religion_context_query", True)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 4242, "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "connection_generation": 1, "ck3_build_match": True,
            "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
            "capabilities": ["game.state.snapshot", "game.command.query-player-religion-context-v1"]})
        revision = result["snapshot_revision"]
        assert type(revision) is int
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:" + str(revision), "revision": revision,
            "state": {"phase": "map_hud", "date": "synthetic-native-fixture", "date_raw": context["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "played_character": {
                    "character_id": context["played_character_id"], "alive": True},
                "player_armies": [], "active_wars": []}})
        before = driver.take_snapshot()
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert tools["ck3_query_player_religion_context_v1"].annotations.read_only_hint
            response = await client.call_tool("ck3_query_player_religion_context_v1",
                                              {"expected_revision": before["revision"]})
            assert not response.is_error
            actual = object_value(response.structured_content)
        assert actual["player_pilgrimage_traits"] == expected
        after = driver.take_snapshot()
        diagnostics = object_value(before["diagnostics"])
        actor = context["played_character_id"]
        pid = diagnostics["bridge_pid"]
        generation = diagnostics["connection_generation"]
        episode = before.get("episode_run_id")
        assert type(actor) is int and type(pid) is int and type(generation) is int
        assert episode is None or isinstance(episode, str)
        binding: MilestoneBinding = {"run_id": "synthetic-trait-pipeline", "machine_id": "synthetic",
            "actor_character_id": actor, "bridge_pid": pid, "connection_generation": generation,
            "episode_run_id": episode}
        metrics = project_observation(binding, before, actual, after)
        assert metrics["source_frame_bound"]
        # Retain the actual first-run failure path: a protocol fixture without
        # qualified hello fields or with a mismatched episode cannot acquire
        # collector credit, even when the native addon itself is valid.
        missing_hello = deepcopy(before)
        missing_diagnostics = object_value(missing_hello["diagnostics"])
        incomplete_hello = object_value(missing_diagnostics["hello"])
        for key in ("connection_generation", "ck3_build_match", "game_adapter_id"):
            incomplete_hello.pop(key, None)
        missing_diagnostics["hello"] = incomplete_hello
        missing_hello["diagnostics"] = missing_diagnostics
        assert not project_observation(binding, missing_hello, actual, after)["source_frame_bound"]
        wrong_episode = deepcopy(binding)
        wrong_episode["episode_run_id"] = None if episode is not None else "different-synthetic-episode"
        assert not project_observation(wrong_episode, before, actual, after)["source_frame_bound"]
        assert metrics["trait_experience"]["observed"] == expected["available"]
        assert metrics["trait_experience"]["raw"] == expected
        assert json_value(json.loads(json.dumps(metrics))) == json_value(metrics)
        assert len(endpoint.requests) == 1 and packet == original
        request = endpoint.requests[0]
        assert request["expected_revision"] == revision
        assert request["expected_snapshot_revision"] == revision
        assert "character_id" not in request
    finally:
        driver.close()


async def verify(path: Path) -> None:
    original = path.read_bytes()
    doc = object_value(json.loads(original.decode("utf-8-sig")))
    provenance = object_value(doc["fixture_provenance"])
    assert provenance["kind"] == "synthetic_native_world_and_callbacks"
    assert provenance["producer"] == "production_owner_execute_and_whole_serializer"
    cases = doc["pilgrimage_trait_cases"]
    assert isinstance(cases, list) and len(cases) == 8
    for index, packet in enumerate(cases):
        await consume(packet, index)
    assert path.read_bytes() == original
    print("Eight compiled native trait packets -> actual registered MCP SDK -> filming -> JSON: PASS; 0 skipped")


def main() -> int:
    import asyncio
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-fixture", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(verify(args.native_fixture))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
