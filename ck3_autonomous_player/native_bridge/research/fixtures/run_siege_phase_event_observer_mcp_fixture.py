"""Check two native phase-event packets through the registered occupation MCP."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True

CASES = (
    ("available-phase-event-state.json", True),
    ("no-active-phase-event-state.json", False),
)
EXPECTED_STATE = {
    "breach_level": 3,
    "starvation_level": 0,
    "disease_level": 4,
    "desertion_count": 0,
    "stalemate_count": 7,
}


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    roots = parser.add_mutually_exclusive_group(required=True)
    roots.add_argument("--projection-root", type=Path, help="Repository root containing ck3_autonomous_player/src and tools")
    roots.add_argument("--source-root", type=Path, help="Package project root containing src; its parent is the repository root")
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    project = args.source_root.resolve() if args.source_root else args.projection_root.resolve() / "ck3_autonomous_player"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "PYTHON-CONSUMER-RESULT.json"
    checks = 0

    def require(value: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not value:
            raise RuntimeError(message)

    report: dict[str, object] = {
        "status": "RED", "classification": "harness-or-consumer",
        "case_count": 2, "registered_mcp_calls": 0,
        "game_operations": 0, "sdk_calls_to_game": 0, "pipe_operations": 0,
        "window_operations": 0, "game_days_advanced": 0,
        "live_validation": False, "whole_dll_built": False,
    }
    try:
        sys.path.insert(0, str(project / "src"))
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.war_occupation_targets_contract import (
            QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY,
            query_war_occupation_targets_v1_step,
        )

        class NativePacketReplay(NativeHeadlessGameplayDriver):
            """Keep production execute_step; replace only external transport/frame."""

            def __init__(self, packet: dict[str, object]):
                self.packet = deepcopy(packet)
                body = packet["result"]
                value = body["war_occupation_targets_v1"]
                self.frame = {
                    "paused": True, "map_ready": True, "revision": 4,
                    "native_revision": body["snapshot_revision"],
                    "snapshot_id": "siege-phase-event-native-fixture:11",
                    "episode_run_id": "siege-phase-event-observer-focused-fixture",
                    "diagnostics": {"connection_generation": 1},
                    "date_raw": body["date_raw"],
                    "played_character": {"character_id": 29829, "alive": True},
                    "player_armies": [{"army_id": 83886367, "owner_character_id": 29829, "controllable": True}],
                    "active_wars": [{"war_id": value["war_id"], "player_side": value["player_side"]}],
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

        async def consume() -> list[dict[str, object]]:
            results = []
            for filename, active in CASES:
                path = args.native_dir / filename
                packet = json.loads(path.read_text(encoding="utf-8-sig"))
                require(packet["type"] == "command_result" and packet["ok"] is True,
                        "fixture uses the genuine native command-result wrapper")
                body = packet["result"]
                payload = body["war_occupation_targets_v1"]
                require(body["snapshot_revision"] == 11 and body["date_raw"] == 53237136
                        and payload["actor_character_id"] == 29829 and payload["war_id"] == 16777231,
                        "new fixture keeps its explicit native frame and full participant IDs")
                driver = NativePacketReplay(packet)
                server = create_server(driver)
                tool = next(row for row in await server.list_tools()
                            if row.name == "ck3_query_war_occupation_targets_v1")
                require(getattr(tool.annotations, "read_only_hint",
                                getattr(tool.annotations, "readOnlyHint", None)) is True,
                        "the real registered occupation handler advertises read-only behavior")
                response = await server.call_tool(
                    "ck3_query_war_occupation_targets_v1",
                    {"war_id": payload["war_id"], "expected_revision": 4},
                )
                report["registered_mcp_calls"] += 1
                require(getattr(response, "is_error", False) is False,
                        "registered production handler completes the native fixture query")
                observed = response.structured_content
                require(observed["read_only"] is True and observed["backend_id"] == "native-headless"
                        and observed["queried_revision"] == 4 and observed["queried_native_revision"] == 11,
                        "production caller keeps public and native revisions separate")
                require(len(driver.requests) == 1, "registered query sends one fixture transport request")
                request = driver.requests[0]
                require(request["step"] == query_war_occupation_targets_v1_step(16777231)
                        and request["expected_revision"] == 11,
                        "production request translates the selected full WarID and native revision")
                require(driver.history == [{"step": request["step"], "ok": True}],
                        "production execute_step records one successful read-only request")
                value = observed["war_occupation_targets_v1"]
                require(value["available"] is True and value["collection_complete"] is True
                        and len(value["rows"]) == 5 and len(value["side_counts"]) == 2,
                        "registered normalization preserves the native complete collection")
                targets = [row for row in value["rows"] if row["province_id"] == 2610]
                require(len(targets) == 2, "both native target occurrences are retained")
                states = []
                for row in targets:
                    require(row["siege_observable"] is True, "target siege absence/presence is a successful observation")
                    siege = row["active_siege"]
                    if active:
                        require(isinstance(siege, dict) and siege["siege_id"] == 0x03000021
                                and siege["besieging_army_id"] == 83886367,
                                "actual full SiegeID and public besieger identity survive the registered tool")
                        require(siege["phase_event_state"] == EXPECTED_STATE,
                                "current state retains real zeros and levels above the stock model cap")
                        require(all(type(item) is int for item in siege["phase_event_state"].values()),
                                "measured phase-event state stays integer rather than bool/null")
                        require(siege["assault_observable"] is False
                                and siege["prepared_selected_phase_event_enum"] == 5,
                                "current state is independent of assault; sentinel remains last-prepare diagnostic")
                        states.append({"phase_event_state": siege["phase_event_state"],
                                       "prepared_selected_phase_event_enum": siege["prepared_selected_phase_event_enum"]})
                    else:
                        require(siege is None, "legal no-Siege remains null for both native occurrences")
                        states.append(None)
                results.append({"case": filename, "status": "GREEN", "native_packet": pin(path),
                                "target_province_id": 2610, "target_occurrences": 2,
                                "normalized_target_states": states})
            return results

        report["cases"] = asyncio.run(consume())
        report.update(status="GREEN", readiness="static-ready", checks=checks,
                      production_path="registered MCP -> GameplayBridgeService -> NativeHeadlessGameplayDriver.execute_step -> shared occupation normalizer")
        report["production_modules"] = [
            pin(Path(sys.modules[name].__file__)) for name in (
                "xar_autoplayer.bridge.mcp_server", "xar_autoplayer.bridge.service",
                "xar_autoplayer.bridge.native_driver", "xar_autoplayer.bridge.war_contract",
                "xar_autoplayer.bridge.war_occupation_targets_contract",
            )
        ]
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}",
                      traceback=traceback.format_exc(), checks=checks)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": report["status"], "checks": checks,
                      "registered_mcp_calls": report["registered_mcp_calls"],
                      "receipt": str(output), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
