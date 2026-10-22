"""Consume actual C++ pilgrimage serializer packets through Driver and registered MCP."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_pilgrimage_planner_contract import parse_pilgrimage_option_key


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError("actual serializer packet requires JSON objects with string keys")
    return {key: item for key, item in value.items()}


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("actual serializer packet identity is not an exact integer")
    return value


def pin(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class FixtureEndpoint:
    """Keep the exact producer envelope; only bind its fixture nonce to this SDK request."""
    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = packet
        self.sent: list[dict[str, object]] = []

    def send(self, value: dict[str, object]) -> None:
        self.sent.append(deepcopy(value))

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        if len(self.sent) != 1 or timeout <= 0:
            raise ValueError("finite serializer consumer must dispatch exactly once")
        if self.packet.get("request_id") != "owned-fixture:pilgrimage-execution":
            raise ValueError("unexpected original serializer fixture nonce")
        result = deepcopy(self.packet)
        result["request_id"] = request_id
        return result


class FixtureDriver:
    query_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.query_player_pilgrimage_planner_private_v1
    submit_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.submit_player_pilgrimage_planner_private_v1
    allow_private_player_pilgrimage_execution = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.endpoint = self.state = FixtureEndpoint(packet)
        body = obj(obj(packet["result"])["player_pilgrimage_planner"])
        native_revision = integer(body["snapshot_revision"])
        self.source: dict[str, object] = {
            "snapshot_id": "owned-cpp-wire:" + str(native_revision),
            "revision": native_revision + 1, "native_revision": native_revision,
            "date_raw": integer(body["date_raw"]),
            "played_character": {"character_id": integer(body["played_character_id"]), "alive": True},
            "played_character_gold": {"raw": 1000000000, "scale": 100000},
            "paused": True, "map_ready": True, "episode_run_id": "owned-cpp-wire-fixture",
            "diagnostics": {"connection_generation": 1, "hello": {
                "expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
                "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "pid": 1234}},
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.source)

    def capabilities(self) -> dict[str, object]:
        return {}


async def consume(folder: Path) -> list[dict[str, object]]:
    from mcp import Client
    expected = {
        "read": ("read", False), "can-select-false": ("can_select", False),
        "quote-dynamic-index": ("quote", False), "start-pending": ("start", True),
        "start-unknown": ("start", True), "post-pending": ("post", False),
        "post-full-generation": ("post", False), "quote-unavailable": ("quote", False),
        "hajj-read": ("read", False), "hajj-quote": ("quote", False), "hajj-start": ("start", True),
        "worldly-read": ("read", False), "worldly-quote": ("quote", False), "worldly-start": ("start", True),
    }
    if {path.name for path in folder.iterdir()} != {name + ".json" for name in expected} | {"PROVENANCE.json"}:
        raise ValueError("all fourteen original packets and provenance are required")
    provenance = obj(json.loads((folder / "PROVENANCE.json").read_bytes()))
    if provenance.get("game_queried") is not False or provenance.get("owned_result_dtos") is not True:
        raise ValueError("actual owned serializer provenance is required")
    rows: list[dict[str, object]] = []
    for name, (operation, submit) in expected.items():
        path = folder / (name + ".json")
        packet = obj(json.loads(path.read_bytes()))
        body = obj(obj(packet["result"])["player_pilgrimage_planner"])
        key = parse_pilgrimage_option_key("pilgrimage_type_" + name.split("-")[0]
            if name.startswith(("hajj-", "worldly-")) else "pilgrimage_type_pious")
        if body.get("special_option_key") != key or body.get("operation") != operation:
            raise ValueError("producer option/operation differs from the finite fixture name")
        driver = FixtureDriver(packet)
        args: dict[str, object] = {"expected_revision": integer(driver.source["revision"]),
                                  "operation": operation, "option_key": key}
        if operation in {"can_select", "start"}:
            args["province_id"] = 2577
        if submit:
            args["policy_positive"] = True
        tool = "ck3_submit_player_pilgrimage_planner_v1" if submit else "ck3_query_player_pilgrimage_planner_v1"
        async with Client(create_server(driver)) as client:
            result = await client.call_tool(tool, args)
            if result.is_error:
                raise ValueError("actual C++ packet was rejected by registered MCP: " + name)
            normalized = obj(result.structured_content)
        if normalized.get("special_option_key") != key or normalized.get("automatic_retry") is not False:
            raise ValueError("SDK option or retry semantics changed")
        if len(driver.endpoint.sent) != 1 or driver.endpoint.sent[0].get("expected_option_key") != key:
            raise ValueError("registered MCP failed to bind the exact original option")
        rows.append({"name": name, "packet": pin(path), "option_key": key,
                     "operation": operation, "status": normalized["operation_status"],
                     "native_request_count": 1, "registered_mcp": True})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    from ck3_live_run_id import current_machine_id
    rows = asyncio.run(consume(args.packets.resolve()))
    receipt = {"schema": "ck3-pilgrimage-three-option-native-sdk-mcp-consumer-v1",
        "machine_id": current_machine_id(), "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS", "packets_consumed": rows, "no_skips": True,
        "game_started": False, "actual_live_business_qualified": False}
    with args.receipt.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": "PASS", "packets": len(rows), "receipt": pin(args.receipt)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
