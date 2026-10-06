"""First compiled native packets through the existing registered MCP query.

The existing registered query delegates directly to NativeDriver.
No invented Service method,
packet body, native getter result, or SDK Client session is used here.
Authoring this package does not run it. Root supplies the four actual compiled
reader/mailbox/serializer wire files and executes the sole qualification.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import sys


SCENARIOS = (
    "distinct_faith_positive_values",
    "legal_zero",
    "same_faith",
    "getter_failure_independent_of_old_gate",
)
TOOL = "ck3_query_player_religion_conversion_inputs_v1"
ROUTE = (
    "registered MCP tool -> NativeHeadlessGameplayDriver -> existing private "
    "transport -> production conversion-input/fervor normalizers"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Root integration tree containing ck3_autonomous_player/src")
    parser.add_argument("--native-fixtures-dir", type=Path, required=True,
                        help="Four unmodified command_result JSON files emitted by compiled C++")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema": "xar.conversion-fervor-inputs.registered-mcp-compound.v1",
        "status": "RED", "tool": TOOL, "route": ROUTE,
        "source_root": str(args.source_root),
        "native_fixture_directory": str(args.native_fixtures_dir),
        "game_actions": 0, "live_queries": 0, "sdk_sessions": 0,
        "qualification": "compiled controlled native fixture; not live game evidence",
        "native_body_mutated": False, "new_service_api_added": False,
        "native_request_id_rebound_for_transport": True,
    }
    checks = 0

    def check(condition: object, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    try:
        sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
        from xar_autoplayer.bridge.player_conversion_fervor_inputs import (
            normalize_player_conversion_fervor_inputs_v1,
        )
        from xar_autoplayer.bridge.player_religion_conversion_inputs_private_transport import (
            normalize_player_religion_conversion_inputs_v1,
            query_player_religion_conversion_inputs_private_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12003

        # These are the integration tree's production functions. Importing or
        # calling the external leaf directly would not qualify the new route.
        report["production_source_files"] = {
            "mcp": str(inspect.getsourcefile(create_server)),
            "driver": str(inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_player_religion_conversion_inputs_private_v1)),
            "transport": str(inspect.getsourcefile(query_player_religion_conversion_inputs_private_v1)),
            "inputs_normalizer": str(inspect.getsourcefile(normalize_player_religion_conversion_inputs_v1)),
            "fervor_normalizer": str(inspect.getsourcefile(normalize_player_conversion_fervor_inputs_v1)),
        }
        report["service_has_conversion_input_method"] = callable(getattr(
            GameplayBridgeService, "query_player_religion_conversion_inputs_private_v1", None,
        ))
        report["service_layer"] = (
            "create_server constructs GameplayBridgeService, but this existing tool calls "
            "the driver directly; no Service conversion-input call is claimed"
        )

        fixtures: list[tuple[str, dict[str, object]]] = []
        manifests: list[dict[str, object]] = []
        for scenario in SCENARIOS:
            path = args.native_fixtures_dir / (scenario + ".json")
            encoded = path.read_bytes()
            packet = json.loads(encoded.decode("utf-8-sig"))
            check(isinstance(packet, dict), scenario + ": compiled wire is an object")
            check(packet.get("type") == "command_result" and packet.get("protocol_version") == 1
                  and packet.get("ok") is True, scenario + ": compiled command_result envelope")
            request_id = packet.get("request_id")
            check(isinstance(request_id, str) and bool(request_id), scenario + ": native request ID")
            fixtures.append((scenario, packet))
            manifests.append({"scenario": scenario, "path": str(path), "bytes": len(encoded),
                              "sha256": hashlib.sha256(encoded).hexdigest(),
                              "native_request_id": request_id})
        report["native_fixtures"] = manifests

        class CompiledPacketDriver:
            """Only endpoint/snapshot harness; all query code is production code."""

            command_timeout_seconds = 1.0
            allow_private_player_religion_conversion_inputs_query = True
            query_player_religion_conversion_inputs_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_religion_conversion_inputs_private_v1
            )

            def __init__(self, scenario: str, packet: dict[str, object]) -> None:
                self.scenario = scenario
                self.packet = deepcopy(packet)
                result = packet["result"]
                native = result["player_religion_conversion_inputs"]
                self.snapshot = {
                    "snapshot_id": f"native:{result['snapshot_revision']}",
                    "revision": result["snapshot_revision"] + 4,
                    "native_revision": result["snapshot_revision"],
                    "date_raw": result["date_raw"],
                    "played_character": {"character_id": native["played_character_id"], "alive": True},
                    "paused": True, "map_ready": True,
                    "diagnostics": {"hello": {
                        "expected_ck3_version": result["game_version"],
                        "expected_ck3_sha256": result["executable_sha256"],
                    }},
                }
                self.sent: list[dict[str, object]] = []
                self.endpoint = self
                self.state = NativeProtocolState("offline-conversion-fervor:" + scenario)

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.snapshot)

            def send(self, request: dict[str, object]) -> None:
                self.sent.append(deepcopy(request))
                # Match the existing baseline offline PacketDriver pattern:
                # rebind only the outer transport nonce on an ingest copy.
                # Preserve the compiled source bytes and complete native result.
                correlated = deepcopy(self.packet)
                correlated["request_id"] = request["request_id"]
                check(correlated["result"] == self.packet["result"],
                      self.scenario + ": nonce correlation preserves complete native body")
                check(self.state.ingest(correlated) == "command_result",
                      self.scenario + ": real NativeProtocolState ingests compiled wire")

        async def exercise() -> list[dict[str, object]]:
            observed: list[dict[str, object]] = []
            for scenario, packet in fixtures:
                result = packet["result"]
                native = result["player_religion_conversion_inputs"]
                check(result["game_version"] == CK3_12003.game_version
                      and result["executable_sha256"] == CK3_12003.executable_sha256
                      and result["backend_id"] == CK3_12003.backend_id("player-religion-conversion-inputs-v1"),
                      scenario + ": compiled .3 result exact build/backend")
                check(native["schema"] == "ck3_12003_religion_conversion_inputs_v1",
                      scenario + ": compiled owning inputs .3 schema")
                driver = CompiledPacketDriver(scenario, packet)
                server = create_server(driver)
                listed = {tool.name: tool for tool in await server.list_tools()}
                check(TOOL in listed and listed[TOOL].annotations.read_only_hint is True,
                      scenario + ": existing registered query stays readonly")
                response = await server.call_tool(TOOL, {
                    "expected_revision": driver.snapshot["revision"],
                    "target_rite_id": native["target_rite_id"],
                })
                check(response.is_error is False, scenario + ": registered MCP accepts compiled native wire")
                actual = response.structured_content
                check(isinstance(actual, dict), scenario + ": structured production result")
                check({key: actual[key] for key in native} == native,
                      scenario + ": complete native domain preserved by production normalizers")
                check(actual["conversion_gates"] == native["conversion_gates"]
                      and actual["predicted_base_fulfillment"] == native["predicted_base_fulfillment"],
                      scenario + ": existing gates and prediction preserved")
                check(actual["available"] is True and result["status"] == "observed"
                      and actual["status"] == result["status"]
                      and actual["read_only"] is True,
                      scenario + ": sibling does not alter existing availability/status")
                check(actual["conversion_gates"]["available"] is True
                      and actual["predicted_base_fulfillment"]["available"] is True,
                      scenario + ": old source components remain available")
                fervor = actual["conversion_fervor"]
                check(fervor["schema"] == "ck3_12003_conversion_fervor_inputs_v1"
                      and fervor["read_only"] is True and fervor["raw_scale"] == 100000
                      and fervor["unit"] == "fervor_points"
                      and fervor["is_final_conversion_cost"] is False
                      and fervor["is_final_conversion_desire"] is False,
                      scenario + ": observation remains input rather than final fee/desire")
                check(all(fervor[key] == native[key] for key in (
                    "capture_epoch", "date_raw", "played_character_id"))
                    and fervor["requested_target_rite_id"] == native["target_rite_id"]
                    and all(fervor[key] == native["conversion_gates"][key] for key in (
                        "actor_faith_id", "target_faith_id")),
                    scenario + ": full Faith pair shares actual owning player/frame/target")
                if scenario == "getter_failure_independent_of_old_gate":
                    check(fervor["available"] is False
                          and fervor["unavailable_reason"] == "target_fervor_unavailable"
                          and fervor["actor_fervor_raw"] is None
                          and fervor["target_fervor_raw"] is None,
                          scenario + ": getter failure remains independent and both raws are unsampled")
                else:
                    check(fervor["available"] is True and fervor["unavailable_reason"] is None,
                          scenario + ": actual current scalar observations available")
                    expected_raws = {
                        "distinct_faith_positive_values": (7500000, 6000000),
                        "legal_zero": (0, 0),
                        "same_faith": (5500000, 5500000),
                    }[scenario]
                    check((fervor["actor_fervor_raw"], fervor["target_fervor_raw"]) == expected_raws,
                          scenario + ": compiled controlled getter values preserved, including legal zero")
                if scenario == "distinct_faith_positive_values":
                    check(fervor["actor_faith_id"] != fervor["target_faith_id"]
                          and actual["conversion_gates"]["same_faith"] is False,
                          scenario + ": distinct actual Faith IDs")
                elif scenario == "same_faith":
                    check(fervor["actor_faith_id"] == fervor["target_faith_id"]
                          and actual["conversion_gates"]["same_faith"] is True,
                          scenario + ": same actual Faith is available, not unavailable")
                check(actual["exe_sha256"] == CK3_12003.executable_sha256
                      and actual["exact_ck3_build"] == CK3_12003.game_version,
                      scenario + ": transport retains exact .3 provenance")
                check(len(driver.sent) == 1
                      and driver.sent[0]["step"] == "query-player-religion-conversion-inputs-v1"
                      and driver.sent[0]["expected_revision"] == result["snapshot_revision"]
                      and driver.sent[0]["expected_snapshot_revision"] == result["snapshot_revision"]
                      and driver.sent[0]["target_rite_id"] == native["target_rite_id"]
                      and "character_id" not in driver.sent[0]
                      and "played_character_id" not in driver.sent[0],
                      scenario + ": one existing query, native actor selection and unchanged target argument")
                check(driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0) is None,
                      scenario + ": production transport consumed actual command_result")
                observed.append({"scenario": scenario, "observation": actual,
                                 "request": driver.sent[0],
                                 "original_native_request_id": packet["request_id"]})
            return observed

        observed = asyncio.run(exercise())
        with (args.output_dir / "observed.json").open("x", encoding="utf-8") as stream:
            json.dump(observed, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        report.update(status="GREEN", scenarios=list(SCENARIOS), samples=len(observed),
                      native_domain_preserved=True, old_gate_prediction_status_preserved=True)
    except Exception as error:
        report.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        report["checks"] = checks
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
