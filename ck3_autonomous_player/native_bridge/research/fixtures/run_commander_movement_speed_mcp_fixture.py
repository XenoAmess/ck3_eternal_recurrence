"""Check new production movement-speed packets through existing registered MCP."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--tools-root", type=Path,
                        help="Repository tools import path for a source-only sandbox")
    args = parser.parse_args()
    if args.tools_root is not None:
        sys.path.insert(0, str(args.tools_root))
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge.army_commander_candidates as consumer
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
    from xar_autoplayer.bridge.mcp_server import create_server

    require(Path(consumer.__file__).resolve() == (
        args.projection_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/army_commander_candidates.py"
    ).resolve(), "Combined projected production consumer is loaded")

    class NativeReplay(NativeHeadlessGameplayDriver):
        """Production execute_step/service/MCP; only wire transport and paused frame replaced."""
        def __init__(self, packet: dict):
            self.packet = deepcopy(packet)
            envelope = packet["result"]
            body = envelope["army_commander_candidates"]
            self.frame = {
                "paused": True, "map_ready": True, "revision": 4,
                "native_revision": envelope["snapshot_revision"],
                "snapshot_id": "commander-movement-speed-new-fixture:11",
                "date_raw": envelope["date_raw"],
                "played_character": {"character_id": 29829, "alive": True},
                "player_armies": [{"army_id": body["army_id"], "controllable": True,
                                   "owner_character_id": 29829}],
                "active_wars": [],
            }
            self.endpoint = self.state = self
            self._request_sequence = 0
            self.command_timeout_seconds = 1.0
            self.requests, self.history = [], []

        def take_snapshot(self):
            return deepcopy(self.frame)

        def capabilities(self):
            capability = consumer.QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY
            return {"bridge_capabilities": [capability],
                    "action_steps": _action_steps([capability],
                        player_armies=self.frame["player_armies"], paused=self.frame["paused"]),
                    "backend_id": "native-headless"}

        def send(self, request):
            self.requests.append(deepcopy(request))

        def wait_for_command_result(self, request_id, timeout):
            packet = deepcopy(self.packet)
            packet["request_id"] = request_id
            return packet

        def _record_command(self, step, *, ok, result=None, error=None):
            self.history.append({"step": step, "ok": ok})

    async def run() -> dict:
        paths = sorted(args.native_dir.glob("*.json"))
        require(len(paths) == 19, "Exactly nineteen new production reader/serializer packets exist")
        packets = {path.stem: json.loads(path.read_text(encoding="utf-8-sig")) for path in paths}
        driver = NativeReplay(packets["speed-positive-route"])
        server = create_server(driver)
        tool = next(row for row in await server.list_tools()
                    if row.name == "ck3_query_army_commander_candidates_v1")
        require(getattr(tool.annotations, "read_only_hint",
            getattr(tool.annotations, "readOnlyHint", None)) is True,
            "The existing registered commander tool remains read only")
        native_reports = []
        for path in paths:
            packet = packets[path.stem]
            driver.__init__(packet)
            expected = packet["result"]["army_commander_candidates"]
            result = await server.call_tool("ck3_query_army_commander_candidates_v1",
                {"army_id": expected["army_id"], "expected_revision": 4})
            observed = result.structured_content
            require(isinstance(observed, dict) and
                observed.get("army_commander_candidates") == expected,
                "Production registered MCP preserves the genuine serialized native packet")
            speed = observed["army_commander_candidates"]["current_movement_speed"]
            require(speed["snapshot_revision"] == 11 and speed["date_raw"] == packet["result"]["date_raw"],
                    "Nested movement context remains bound to the enclosing paused native frame")
            require(observed["queried_revision"] == 4 and observed["queried_native_revision"] == 11,
                    "Public and native revision domains remain distinct")
            require(len(driver.requests) == 1 and driver.requests[0]["step"] ==
                consumer.query_army_commander_candidates_v1_step(expected["army_id"]) and
                driver.requests[0]["expected_revision"] == 11,
                "One existing selected public-CUnit read is sent with its native revision")
            require(all(speed[name]["scale"] == 100000 for name in ("land", "naval", "current_edge")),
                    "Each independent native movement rate retains Q100000 scale")
            if path.stem == "speed-legitimate-zero":
                require(all(speed[name]["status"] == "available" and speed[name]["raw"] == 0
                    for name in ("land", "naval", "current_edge")),
                    "Observed zero survives the production serializer and registered consumer")
            if path.stem == "speed-empty-route":
                require(speed["current_edge"]["status"] == "not_applicable" and
                    speed["current_edge"]["raw"] is None and speed["current_edge"]["unavailable_reason"] == "empty_route",
                    "Empty route is explicitly not applicable, never a fabricated zero edge rate")
            if path.stem == "speed-candidate-getter-unavailable":
                require(expected["status"] == "unavailable" and speed["context_observable"] is True and
                    all(speed[name]["status"] == "available" for name in ("land", "naval", "current_edge")),
                    "Candidate failure does not erase independently observed selected-unit totals")
            native_reports.append({"case": path.stem, "status": "GREEN",
                "native_packet": path.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "rate_statuses": {name: speed[name]["status"] for name in ("land", "naval", "current_edge")}})

        baseline = packets["speed-positive-route"]["result"]["army_commander_candidates"]
        consumer_reports = []
        for name, mutate in (
            ("wrong-speed-public-full-id", lambda x: x["current_movement_speed"].update(public_cunit_id=83886367 ^ 0x01000000)),
            ("wrong-speed-internal-full-id", lambda x: x["current_movement_speed"].update(native_carmy_id=50331794 ^ 0x01000000)),
            ("wrong-speed-date", lambda x: x["current_movement_speed"].update(date_raw=53236632)),
            ("wrong-speed-native-revision", lambda x: x["current_movement_speed"].update(snapshot_revision=12)),
            ("wrong-speed-getter-provenance", lambda x: x["current_movement_speed"]["land"].update(native_getter_rva="0x24AAC00")),
            ("wrong-rate-scale", lambda x: x["current_movement_speed"]["naval"].update(scale=100)),
            ("available-rate-null", lambda x: x["current_movement_speed"]["land"].update(raw=None)),
            ("unavailable-rate-nonnull", lambda x: x["current_movement_speed"]["current_edge"].update(status="unavailable")),
        ):
            derived = deepcopy(baseline)
            mutate(derived)
            rejected = False
            try:
                consumer.normalize_army_commander_candidates_v1(derived,
                    expected_army_id=83886367, expected_snapshot_revision=11, expected_date_raw=53236608)
            except ValueError:
                rejected = True
            require(rejected, "Production consumer rejects a mismatched native ID/frame/rate contract")
            consumer_reports.append({"case": name, "status": "GREEN", "derived_packet": True})
        for name, mutate in (
            ("legacy-speed-block-omitted", lambda x: x.pop("current_movement_speed")),
            ("legacy-speed-block-null", lambda x: x.update(current_movement_speed=None)),
        ):
            derived = deepcopy(baseline)
            mutate(derived)
            normalized = consumer.normalize_army_commander_candidates_v1(derived,
                expected_army_id=83886367, expected_snapshot_revision=11, expected_date_raw=53236608)
            require(normalized == derived, "Legacy omission/null stays absent without fabricated speed values")
            consumer_reports.append({"case": name, "status": "GREEN", "derived_packet": True})
        for name, mutate, expected_reason in (
            ("registered-unpaused-scope", lambda frame: frame.update(paused=False), "paused CK3 snapshot"),
            ("registered-outside-controllable-scope", lambda frame: frame["player_armies"][0].update(controllable=False), "current controllable player scope"),
        ):
            driver.__init__(packets["speed-positive-route"])
            mutate(driver.frame)
            try:
                result = await server.call_tool("ck3_query_army_commander_candidates_v1",
                    {"army_id": 83886367, "expected_revision": 4})
                structured = result.structured_content
                rejected = getattr(result, "is_error", getattr(result, "isError", False)) is True or (
                    isinstance(structured, dict) and (structured.get("ok") is False or "error" in structured))
            except Exception as error:
                if expected_reason not in str(error):
                    raise
                rejected = True
            require(rejected and driver.requests == [],
                    "Existing registered paused player scope rejects before sending a native request")
            consumer_reports.append({"case": name, "status": "GREEN", "derived_frame": True})
        return {"native_cases": native_reports, "consumer_cases": consumer_reports}

    output = args.native_dir.parent / "REGISTERED-MCP-RESULT.json"
    try:
        results = asyncio.run(run())
        report = {"status": "GREEN", "readiness": "static-ready", **results,
            "explicit_require_checks": checks, "asserts_used": 0,
            "sdk_calls_to_game": 0, "game_operations": 0, "window_operations": 0,
            "native_functions_executed": False,
            "scope": "Real production reader/serializer tested with synthetic memory/callbacks; existing production driver/service/registered MCP replay. No live credit."}
    except Exception as error:
        report = {"status": "RED", "error": repr(error), "traceback": traceback.format_exc(),
            "explicit_require_checks": checks, "sdk_calls_to_game": 0}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "receipt": output.as_posix(),
        "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
