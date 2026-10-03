"""Pass genuine native occupation packets through the registered MCP tool."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import traceback

checks = 0

def require(value: bool, message: str) -> None:
    global checks
    checks += 1
    if not value:
        raise RuntimeError(message)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--projection-root", type=Path, required=True)
parser.add_argument("--native-dir", type=Path, required=True)
parser.add_argument("--out", type=Path)
args = parser.parse_args()
paths = sorted(args.native_dir.glob("*.json"))
if not paths:
    parser.error("provide genuine native reader/serializer packets")
sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.war_occupation_targets_contract import (
    QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY,
    normalize_war_occupation_targets_v1,
    query_war_occupation_targets_v1_step,
)


class NativeReplay(NativeHeadlessGameplayDriver):
    """Keep production execute_step and replace only external transport/frame."""

    def __init__(self, packet: dict[str, object]):
        self.packet = deepcopy(packet)
        envelope = packet["result"]
        value = envelope["war_occupation_targets_v1"]
        self.frame = {
            "paused": True, "map_ready": True, "revision": 4,
            "native_revision": envelope["snapshot_revision"],
            "snapshot_id": "war-occupation-native-fixture:11",
            "episode_run_id": "owned-war-occupation-focused-fixture",
            "diagnostics": {"connection_generation": 1},
            "date_raw": envelope["date_raw"],
            "played_character": {"character_id": 29829, "alive": True},
            "player_armies": [],
            "active_wars": [{"war_id": value["war_id"], "player_side": "defender"}],
        }
        self.endpoint = self.state = self
        self._request_sequence = 0
        self.command_timeout_seconds = 1.0
        self.requests = []
        self.history = []

    def take_snapshot(self):
        return deepcopy(self.frame)

    def capabilities(self):
        return {
            "bridge_capabilities": [QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY],
            "action_steps": _action_steps(
                [QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY],
                active_wars=self.frame["active_wars"], paused=True,
            ),
            "backend_id": "native-headless",
        }

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet

    def _record_command(self, step, *, ok, result=None, error=None):
        self.history.append({"step": step, "ok": ok})


async def check_packets():
    reports = []
    first = json.loads(paths[0].read_text(encoding="utf-8-sig"))
    driver = NativeReplay(first)
    server = create_server(driver)
    tool = next(row for row in await server.list_tools()
                if row.name == "ck3_query_war_occupation_targets_v1")
    properties = tool.input_schema["properties"]
    require(properties["war_id"]["minimum"] == 0 and
            properties["war_id"]["maximum"] == 2**31 - 1,
            "registered MCP preserves the complete non-negative int32 ID range")
    require(tool.input_schema["required"] == ["war_id"],
            "registered MCP requires the selected full WarID")
    require(getattr(tool.annotations, "read_only_hint",
                    getattr(tool.annotations, "readOnlyHint", None)) is True,
            "occupation query advertises read-only behavior")
    for path in paths:
        packet = json.loads(path.read_text(encoding="utf-8-sig"))
        require(packet["ok"] is True, "native serializer packet is a completed query")
        envelope = packet["result"]
        value = envelope["war_occupation_targets_v1"]
        expected = normalize_war_occupation_targets_v1(
            value, expected_war_id=value["war_id"], expected_actor_character_id=29829,
            expected_snapshot_revision=envelope["snapshot_revision"],
            expected_date_raw=envelope["date_raw"], expected_player_side="defender",
        )
        driver.__init__(packet)
        response = await server.call_tool(
            "ck3_query_war_occupation_targets_v1",
            {"war_id": value["war_id"], "expected_revision": 4},
        )
        require(getattr(response, "is_error", False) is False,
                "registered SDK invocation must not return an MCP error")
        observed = response.structured_content
        require(observed["war_occupation_targets_v1"] == expected,
                "genuine native payload survives driver, service and registered MCP")
        require(observed["queried_revision"] == 4 and
                observed["queried_native_revision"] == envelope["snapshot_revision"],
                "public and native query revisions remain separate")
        require(observed["read_only"] is True and observed["backend_id"] == "native-headless",
                "registered MCP publishes a read-only native observation")
        require(len(driver.requests) == 1, "typed query sends exactly one native request")
        request = driver.requests[0]
        require(request["step"] == query_war_occupation_targets_v1_step(value["war_id"]) and
                request["expected_revision"] == envelope["snapshot_revision"],
                "typed native request keeps the full WarID and native frame")
        require(driver.history == [{"step": request["step"], "ok": True}],
                "production command result records one successful read-only request")
        if path.stem == "defender-ordered-native-counts":
            require([row["holding_title_id"] for row in expected["rows"]
                     if row["territory_side"] == "defender"] ==
                    [0x0100085F, 0, 2144, 0x0100085F],
                    "Python preserves native order, duplicates, full generation and legal zero")
            outside = next(row for row in expected["rows"] if row["holding_title_id"] == 2144)
            require(outside["is_occupied"] is True and
                    outside["occupier_side"] == "outside_war" and
                    outside["counted_occupied_by_opposing_side"] is False,
                    "outside-war geographic occupation is not native war occupation credit")
            absent = next(row for row in expected["rows"] if row["holding_title_id"] == 0)
            require(absent["occupying_character_id"] is None and
                    absent["is_occupied"] is False and absent["occupier_side"] == "none",
                    "native legal occupation absence remains null, not a zero-ID occupant")
        elif path.stem.startswith("available-empty") or path.stem == "available-war-zero":
            require(expected["available"] is True and expected["collection_complete"] is True and
                    expected["rows"] == [] and expected["unavailable_reason"] is None,
                    "real empty native collection remains available and complete")
        elif path.stem.startswith("unavailable-"):
            require(expected["available"] is False and expected["collection_complete"] is False and
                    bool(expected["unavailable_reason"]),
                    "failed native read remains explicitly unavailable through MCP")
        reports.append({"case": path.stem, "packet": str(path),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "status": "GREEN", "observation_status": expected["status"],
                        "war_id": value["war_id"]})
    return reports


output = args.out or args.native_dir.parent / "PYTHON-CONSUMER-RESULT.json"
try:
    cases = asyncio.run(check_packets())
    report = {"status": "GREEN", "readiness": "static-ready",
              "checks": checks, "cases": cases, "game_operations": 0,
              "sdk_calls_to_game": 0, "window_operations": 0,
              "live_validation": False, "whole_dll_built": False}
except Exception as error:
    report = {"status": "RED", "classification": "harness-or-consumer",
              "checks": checks,
              "error": f"{type(error).__name__}: {error}",
              "traceback": traceback.format_exc(), "game_operations": 0}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
