"""Pass only new phase-modifier reader packets through registered commander MCP."""
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
args = parser.parse_args()
sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.army_commander_candidates import QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY, query_army_commander_candidates_v1_step
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
from xar_autoplayer.bridge.mcp_server import create_server

class NativeReplay(NativeHeadlessGameplayDriver):
    def __init__(self, packet: dict):
        self.packet = deepcopy(packet)
        envelope = packet["result"]
        value = envelope["army_commander_candidates"]
        self.frame = {
            "paused": True, "map_ready": True, "revision": 4,
            "native_revision": envelope["snapshot_revision"],
            "snapshot_id": "commander-siege-phase-new-fixture:11",
            "date_raw": envelope["date_raw"],
            "played_character": {"character_id": 29829, "alive": True},
            "player_armies": [{"army_id": value["army_id"], "controllable": True, "owner_character_id": value["owner_character_id"]}],
            "active_wars": [],
        }
        self.endpoint = self.state = self
        self._request_sequence = 0
        self.command_timeout_seconds = 1.0
        self.requests = []
        self.history = []

    def take_snapshot(self):
        return deepcopy(self.frame)

    def capabilities(self):
        return {"bridge_capabilities": [QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY], "action_steps": _action_steps([QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY], player_armies=self.frame["player_armies"], paused=True), "backend_id": "native-headless"}

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet

    def _record_command(self, step, *, ok, result=None, error=None):
        self.history.append({"step": step, "ok": ok})

async def check_packets() -> list[dict]:
    paths = sorted(args.native_dir.glob("*.json"))
    require(len(paths) == 4, "Expected only the four new genuine production cases")
    driver = NativeReplay(json.loads(paths[0].read_text(encoding="utf-8-sig")))
    server = create_server(driver)
    tool = next(row for row in await server.list_tools() if row.name == "ck3_query_army_commander_candidates_v1")
    require(getattr(tool.annotations, "read_only_hint", getattr(tool.annotations, "readOnlyHint", None)) is True, "Existing registered commander query remains read-only")
    reports = []
    cases = [(path.stem, json.loads(path.read_text(encoding="utf-8-sig")), path) for path in paths]
    legacy = deepcopy(cases[0][1])
    for row in legacy["result"]["army_commander_candidates"]["candidates"]:
        row.pop("siege_phase_time_modifier_raw")
    cases.append(("legacy-v1-field-omitted", legacy, cases[0][2]))
    expected_amounts = {
        "phase-zero-negative": [0, -10000],
        "phase-positive-missing-key": [10000, 0],
        "phase-read-getter-unavailable": [None, None],
        "phase-container-unavailable": [None, -10000],
        "legacy-v1-field-omitted": [None, None],
    }
    for name, packet, path in cases:
        require(packet["ok"] is True, "Genuine native query envelope is successful")
        driver.__init__(packet)
        expected = deepcopy(packet["result"]["army_commander_candidates"])
        for row in expected["candidates"]:
            row.setdefault("siege_phase_time_modifier_raw", None)
        result = await server.call_tool("ck3_query_army_commander_candidates_v1", {"army_id": expected["army_id"], "expected_revision": 4})
        observed = result.structured_content
        require(isinstance(observed, dict), "Registered MCP returned structured output")
        require(observed["army_commander_candidates"] == expected, "Production normalize/primitive/service/registered MCP preserve genuine native candidate values")
        require([row["siege_phase_time_modifier_raw"] for row in observed["army_commander_candidates"]["candidates"]] == expected_amounts[name], "Observed signed phase modifier / legal zero / optional null are unchanged")
        require(len(driver.requests) == 1, "Only one existing read-only production request is emitted per case")
        require(driver.requests[0]["step"] == query_army_commander_candidates_v1_step(expected["army_id"]), "Existing public-CUnit step is retained")
        require(driver.requests[0]["expected_revision"] == packet["result"]["snapshot_revision"], "Native request retains genuine snapshot revision")
        require(observed["queried_revision"] == 4 and observed["queried_native_revision"] == packet["result"]["snapshot_revision"], "Registered result preserves separate public/native revisions")
        require(all(row["quality_observable"] is True and row["available"] is True for row in expected["candidates"]), "New optional phase input does not erase existing candidate quality")
        reports.append({"case": name, "status": "GREEN", "native_packet": path.as_posix(), "native_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "native_packet_derived": name == "legacy-v1-field-omitted", "phase_raw": expected_amounts[name]})
    return reports

out = args.native_dir.parent / "REGISTERED-MCP-RESULT.json"
try:
    report = {"status": "GREEN", "readiness": "static-ready", "cases": asyncio.run(check_packets()), "explicit_require_checks": checks, "asserts_used": 0, "sdk_calls_to_game": 0, "game_operations": 0, "window_operations": 0, "legacy_case": "derived old-v1 omission only; not a genuine additional native reader case"}
except Exception as error:
    report = {"status": "RED", "error": repr(error), "traceback": traceback.format_exc(), "explicit_require_checks": checks, "sdk_calls_to_game": 0}
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
