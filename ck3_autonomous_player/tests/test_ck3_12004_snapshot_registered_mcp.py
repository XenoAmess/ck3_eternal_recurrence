"""Consume compiled whole Snapshot bytes through the real registered MCP tool.

FIRST source only until Root runs the native producer and this consumer.
Only packet I/O is offline: Driver, protocol normalization, Service, registered
ck3_take_snapshot and MCP 2.0 result conversion are the production code.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys


TOOL = "ck3_take_snapshot"
# Assertions from full-snapshot-first/EXPECTED.json, never a transport payload.
EXPECTED_STATE = {
    "date_raw": 45000000,
    "speed": 5,
    "paused": True,
    "local_player_id": 0,
    "map_ready": True,
    "played_character": {
        "character_id": 29829,
        "alive": True,
        "stress_points": 7,
        "betrothed_id": 29831,
        "primary_spouse_id": 29830,
        "spouse_ids": [29830],
    },
    "played_character_gold": {"raw": -1234567, "scale": 100000},
    "played_character_prestige": {"raw": 2345678, "scale": 100000},
    "played_character_piety": {"raw": -3456789, "scale": 100000},
    "one_life_settlement": None,
    "active_event": {"instance_id": 77, "option_count": 2, "option_indexes": [1, 2]},
    "pending_character_interaction": {
        "instance_id": 16777216,
        "sender_character_id": 29830,
        "auto_accept_notification": False,
    },
    "active_wars": [],
    "player_armies": [],
    "last_checkpoint_submission": None,
    "history": [],
}
# The registered tool exposes the planner-facing event contract produced by
# normalize_active_event(), not the raw bridge event's option_indexes field.
# Keep the native assertion above separate so neither representation can hide
# a change to the compiled whole state_snapshot supplied to the Driver.
EXPECTED_REGISTERED_STATE = {
    **EXPECTED_STATE,
    "active_event": {
        "source": "native",
        "instance_id": 77,
        "option_count": 2,
        "title": None,
        "options": [
            {"index": 0, "option_number": 1, "label": None, "enabled": True},
            {"index": 1, "option_number": 2, "label": None, "enabled": True},
        ],
    },
}


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AssertionError(f"native producer output must be an object: {path}")
    return value


def check_subset(observed: object, expected: object, scope: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            raise AssertionError(f"{scope} must remain an object")
        for key, value in expected.items():
            if key not in observed:
                raise AssertionError(f"{scope}.{key} is missing")
            check_subset(observed[key], value, f"{scope}.{key}")
    elif type(observed) is not type(expected) or observed != expected:
        raise AssertionError(f"{scope} changed: expected {expected!r}, observed {observed!r}")


class WholeSnapshotEndpoint:
    """Fixture replacement for named-pipe I/O, with no replacement Service data."""

    def __init__(self, whole_wire: dict, exported_identity: dict) -> None:
        self.whole_wire = whole_wire
        self.identity = exported_identity
        self.requests: list[dict] = []
        self.on_frame = None
        self.closed = False

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        # Metadata uses the compiled producer's exact .4 export. State and
        # revision are supplied only by its original state_snapshot object.
        on_frame({
            "protocol_version": 1,
            "type": "hello",
            "pid": 12004,
            "connection_generation": 1,
            "capabilities": ["game.state.snapshot"],
            "game_adapter_status": "ready",
            "game_adapter_id": self.identity["adapter_id"],
            "expected_ck3_version": self.identity["game_version"],
            "expected_ck3_sha256": self.identity["executable_sha256"],
        })
        on_frame(self.whole_wire)

    def send(self, request: dict) -> None:
        if (request.get("type") != "ping"
                or request.get("protocol_version") != 1
                or not isinstance(request.get("request_id"), str)
                or self.requests):
            raise AssertionError("registered snapshot must consume the published frame without native commands")
        self.requests.append(deepcopy(request))
        self.on_frame({
            "protocol_version": 1, "type": "pong", "request_id": request["request_id"],
        })

    def close(self) -> None:
        self.closed = True


async def consume_registered_snapshot(wire_path: Path, source_root: Path) -> dict:
    sys.path.insert(0, str(source_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12004

    whole_wire = read_object(wire_path)
    identity_path = wire_path.with_name("snapshot-foundation-result.json")
    identity = read_object(identity_path)
    negative_path = wire_path.with_name("snapshot-foundation-missing-settlement-core.json")
    negative_wire = read_object(negative_path)
    if (whole_wire.get("type") != "state_snapshot"
            or whole_wire.get("protocol_version") != 1
            or whole_wire.get("snapshot_id") != "native:1"
            or type(whole_wire.get("revision")) is not int
            or whole_wire["revision"] != 1):
        raise AssertionError("input must be the compiled positive whole state_snapshot")
    check_subset(whole_wire.get("state"), EXPECTED_STATE, "native.state")
    if (identity.get("game_version") != CK3_12004.game_version
            or identity.get("executable_sha256", "").upper() != CK3_12004.executable_sha256
            or identity.get("adapter_id") != "ck3-1.20.0.4-msvc-x64"
            or str(identity.get("steam_build_id")) != "25734779"
            or identity.get("complete_read") is not True
            or identity.get("native_rva_invocations") != 0
            or identity.get("scope") != "offline_owned_memory"):
        raise AssertionError("compiled producer did not export the actual4 offline foundation identity")
    # Missing settlement is a separate producer scope. It is deliberately
    # never ingested into the full-Snapshot Driver below.
    negative_core = negative_wire.get("result")
    if (negative_wire.get("type") != "command_result"
            or negative_wire.get("protocol_version") != 1
            or negative_wire.get("ok") is not True
            or not isinstance(negative_core, dict)
            or negative_core.get("schema") != "ck3_12004_core_frame_v1"
            or negative_core.get("complete_snapshot") is not False
            or negative_core.get("core_available") is not True
            or negative_core.get("application_main_observed") is not False
            or negative_core.get("played_character_id") != 29829
            or negative_core.get("game_version") != identity["game_version"]
            or negative_core.get("executable_sha256", "").upper() != identity["executable_sha256"].upper()
            or identity.get("missing_settlement_full_read") is not False
            or identity.get("independent_core_available") is not True
            or identity.get("standalone_core_complete_snapshot") is not False):
        raise AssertionError("missing-settlement partial core was promoted or lost its independent prefix")

    endpoint = WholeSnapshotEndpoint(whole_wire, identity)
    driver = NativeHeadlessGameplayDriver(
        pipe_name=r"\\.\pipe\xar_12004_snapshot_offline_fixture",
        endpoint=endpoint,
        command_timeout_seconds=1.0,
        state_dir=None,
        save_dir=None,
        episode_projection="native_campaign",
    )
    try:
        raw = driver.state.raw_transport_snapshot()
        if raw["semantic_packet_accepted"] is not True or raw["native_packet"] != whole_wire:
            raise AssertionError("production protocol ingest changed or rejected the compiled whole frame")
        server = create_server(driver)
        # MCPServer.call_tool reaches the real SDK2 ToolManager with result
        # conversion enabled and the actual registered Service entry.
        result = await server.call_tool(TOOL, {"include_native_command_history": False})
        if result.is_error:
            raise AssertionError(f"registered Snapshot query failed: {result.content}")
        observed = result.structured_content
        if not isinstance(observed, dict):
            raise AssertionError("registered Snapshot did not return structured data")
        check_subset(observed, EXPECTED_REGISTERED_STATE, "registered.snapshot")
        if (observed.get("snapshot_id") != whole_wire["snapshot_id"]
                or observed.get("native_revision") != whole_wire["revision"]):
            raise AssertionError("registered Snapshot lost the native producer revision/identity")
        hello = observed.get("diagnostics", {}).get("hello", {})
        if (hello.get("expected_ck3_version") != identity["game_version"]
                or hello.get("expected_ck3_sha256") != identity["executable_sha256"]
                or hello.get("game_adapter_id") != identity["adapter_id"]):
            raise AssertionError("registered Snapshot lost the compiled actual4 handshake tuple")
        if len(result.content) != 1 or json.loads(result.content[0].text) != observed:
            raise AssertionError("MCP text and structured Snapshot payloads differ")
        if (len(endpoint.requests) != 1
                or endpoint.requests[0]["type"] != "ping"
                or observed.get("native_command_history") != []):
            raise AssertionError("registered Snapshot unexpectedly dispatched gameplay or fabricated history")
        return {
            "schema": "xar.ck3_12004.snapshot-registered-mcp-fixture.v1",
            "status": "GREEN",
            "qualification": "offline compiled whole-state_snapshot registered consumer only",
            "native_wire_path": str(wire_path.resolve()),
            "native_identity_path": str(identity_path.resolve()),
            "native_identity": identity,
            "source_root": str(source_root.resolve()),
            "tool": TOOL,
            "arguments": {"include_native_command_history": False},
            "registered_query_calls": 1,
            "requests": endpoint.requests,
            "native_snapshot_id": whole_wire["snapshot_id"],
            "native_revision": whole_wire["revision"],
            "public_transport_revision": observed["revision"],
            "snapshot": observed,
            "separate_negative_scope": {
                "native_wire_path": str(negative_path.resolve()),
                "wire_type": negative_wire["type"],
                "full_read": identity["missing_settlement_full_read"],
                "independent_core_available": negative_core["core_available"],
                "complete_snapshot": negative_core["complete_snapshot"],
                "application_main_observed": negative_core["application_main_observed"],
                "ingested_as_full_snapshot": False,
            },
            "endpoint_boundary": "Offline packet I/O only; original compiled state_snapshot and revision ingested unchanged; no StubDriver or Service result",
            "pipe_or_game_access": False,
            "live_qualification": False,
        }
    finally:
        driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Repository root whose ck3_autonomous_player/src production modules are consumed")
    args = parser.parse_args()
    receipt = asyncio.run(consume_registered_snapshot(args.wire, args.source_root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
