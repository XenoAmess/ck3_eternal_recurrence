"""One new compiled .4 whole-wire compound through ten registered queries.

Prepared AUTHORED_NOTRUN on 2026-10-07 (2026-W41). Root later supplies the new
native producer document; this worker runs no imports, tests, builds or game.
The hello, snapshot and endpoint are separately labeled synthetic fixtures.
create_server constructs the production Service; the existing religion query
handlers directly call the real driver's private queries and normalizers.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


ROUTES = {
    "query-player-religion-context-v1": ("ck3_query_player_religion_context_v1", "player_religion_context", False),
    "query-player-religion-hostility-v1": ("ck3_query_player_religion_hostility_v1", "player_religion_hostility", True),
    "query-player-religion-doctrine-catalogue-v1": ("ck3_query_player_religion_doctrine_catalogue_v1", "player_religion_doctrine_catalogue", False),
    "query-player-religion-numeric-special-parameters-v1": ("ck3_query_player_religion_numeric_special_parameters_v1", "player_religion_numeric_special_parameters", False),
    "query-player-religion-personal-parameters-v1": ("ck3_query_player_religion_personal_parameters_v1", "player_religion_personal_parameters", False),
    "query-player-religion-conversion-terms-v1": ("ck3_query_player_religion_conversion_terms_v1", "player_religion_conversion_terms", True),
    "query-player-religion-conversion-choices-v1": ("ck3_query_player_religion_conversion_choices_v1", "player_religion_conversion_choices", False),
    "query-player-religion-conversion-reasons-v1": ("ck3_query_player_religion_conversion_reasons_v1", "player_religion_conversion_reasons", True),
    "query-player-religion-conversion-inputs-v1": ("ck3_query_player_religion_conversion_inputs_v1", "player_religion_conversion_inputs", True),
    "query-player-religion-conversion-outcome-v1": ("ck3_query_player_religion_conversion_outcome_v1", "player_religion_conversion_outcome", True),
}
CONTEXT_ADDONS = (
    "player_spiritual_fulfillment_progress",
    "player_mystical_communion_decision_terms",
    "player_pilgrimage_activity_type_terms",
    "player_pilgrimage_headless_activity_terms",
    "player_pilgrimage_candidate_routes",
    "player_confession_decision_terms",
    "player_confession_rite_permission",
    "player_church_income_profile",
    "player_spiritual_fulfillment_type",
    "player_church_tax_inputs",
    "player_piety_devotion_profile",
    "player_rite_virtue_sin_profile",
    "player_vow_of_poverty_terms",
)
NATIVE_REVISION = 171
NATIVE_DATE_RAW = 53286648
NATIVE_CAPTURE_EPOCH = 12004
ACTOR = 29829
TARGET_RITE_ID = 0x86000003


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    checks: list[str] = []
    observations: list[dict] = []
    report = {
        "schema": "xar.religion-adopted-addons-12004-registered-compound-first.v1",
        "status": "RED", "source_root": str(args.source_root),
        "native_fixture": str(args.native_fixture),
        "preparation_status": "AUTHORED_NOTRUN", "prepared_on": "2026-10-07",
        "iso_week": "2026-W41", "tests_run_by_preparing_worker": False,
        "live": False, "game_operations": 0, "planned_compound_cases": 1,
        "actual_compound_cases": 0,
        "registered_query_path": (
            "create_server instantiates GameplayBridgeService; the ten existing religion "
            "query handlers directly call NativeHeadlessGameplayDriver private queries "
            "and production normalizers"),
        "synthetic_sources": {
            "hello": "In-memory harness hello, canonical actual .4 identity; no live hello.",
            "snapshot": "Paused map fixture using unchanged native player/revision/date; no live snapshot.",
            "endpoint": "In-memory protocol receiver; no pipe connection or native process.",
        },
    }

    def check(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    try:
        sys.path.insert(0, str(args.source_root / "tools"))
        sys.path.insert(0, str(args.source_root / "ck3_workshop_mcp/src"))
        sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build

        native_bytes = args.native_fixture.read_bytes()
        report["native_fixture_sha256"] = hashlib.sha256(native_bytes).hexdigest()
        document = json.loads(native_bytes.decode("utf-8-sig"))
        packets = document["samples"]
        report["fixture_provenance"] = document["fixture_provenance"]
        check("synthetic" in str(document["fixture_provenance"]).lower(),
              "new native world/callback provenance remains explicitly synthetic")
        check(isinstance(packets, list) and len(packets) == 10,
              "one new native producer document supplies exactly ten whole packets")
        check({packet["result"]["step"] for packet in packets} == set(ROUTES),
              "all ten existing religion query routes occur exactly once")

        class Endpoint:
            pipe_name = r"\\.\pipe\religion-adopted-addons-12004-offline-compound"

            def __init__(self, packet: dict, expected_request: dict) -> None:
                self.packet = packet
                self.expected_request = expected_request
                self.on_frame = None
                self.requests: list[dict] = []

            def start(self, on_frame, on_disconnect) -> None:
                self.on_frame = on_frame

            def publish(self, frame: dict) -> None:
                check(callable(self.on_frame), "real driver registers its protocol receiver")
                self.on_frame(deepcopy(frame))

            def send(self, request: dict) -> None:
                if request["type"] != "execute_step":
                    return
                self.requests.append(deepcopy(request))
                check(request == self.expected_request,
                      "registered query retains exact original request/step/frame/target: " + request["step"])
                self.publish(self.packet)

            def transport_error(self):
                return None

            def close(self) -> None:
                pass

        def state(result: dict, primary: dict) -> dict:
            revision = result["snapshot_revision"]
            return {
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": f"native:{revision}", "revision": revision,
                "state": {
                    "phase": "map_hud", "date": "fixture-only", "date_raw": result["date_raw"],
                    "speed": 1, "paused": True, "map_ready": True, "history": [],
                    "active_event": None, "pending_character_interaction": None,
                    "played_character": {"character_id": primary["played_character_id"], "alive": True},
                    "player_armies": [], "active_wars": [],
                },
            }

        async def exercise() -> None:
            for packet in packets:
                check(packet["type"] == "command_result" and packet["protocol_version"] == 1
                      and packet["ok"] is True, "complete native command_result envelope retained")
                result = packet["result"]
                step = result["step"]
                tool, primary_key, targeted = ROUTES[step]
                primary = result[primary_key]
                check(require_exact_native_build(result["game_version"], result["executable_sha256"]) == CK3_12004,
                      "whole native result binds the canonical actual .4 tuple: " + step)
                check(result["backend_id"] == CK3_12004.backend_id(step[len("query-"):])
                      and result["domain_key"] == primary_key + "_v1",
                      "existing native backend/domain identities retained: " + step)
                check(result["accepted"] is True and result["private_build"] is True
                      and result["read_only"] is True and result["advertised"] is False,
                      "existing private readonly result flags retained: " + step)
                check(result["snapshot_revision"] == NATIVE_REVISION and result["date_raw"] == NATIVE_DATE_RAW,
                      "original compiled native revision/date retained: " + step)
                check(primary["played_character_id"] == ACTOR and primary["date_raw"] == NATIVE_DATE_RAW
                      and primary["capture_epoch"] == NATIVE_CAPTURE_EPOCH
                      and primary["capture_epoch"] != result["snapshot_revision"],
                      "Robert player frame and distinct native capture epoch retained: " + step)
                check(primary["available"] is True and result["status"] == "observed",
                      "new producer observes the selected existing query family: " + step)
                check(packet["request_id"].startswith("g2-read-"),
                      "original native packet uses the existing G2 query request prefix")
                expected_request = {
                    "type": "execute_step", "protocol_version": 1,
                    "request_id": packet["request_id"], "step": step,
                    "expected_revision": result["snapshot_revision"],
                    "expected_snapshot_revision": result["snapshot_revision"],
                }
                if targeted:
                    check(primary["target_rite_id"] == TARGET_RITE_ID,
                          "original target Rite retains its complete generation DWORD: " + step)
                    expected_request["target_rite_id"] = primary["target_rite_id"]
                siblings = CONTEXT_ADDONS if step == "query-player-religion-context-v1" else (
                    ("faith_numeric_final",) if step == "query-player-religion-numeric-special-parameters-v1" else ())
                for key in siblings:
                    component = result[key]
                    if key == "player_pilgrimage_candidate_routes":
                        check(isinstance(component, list) and len(component) == 1,
                              "new native pilgrimage scene retains its one candidate route as a list")
                        components = component
                    else:
                        components = (component,)
                    for native_component in components:
                        check(isinstance(native_component, dict) and native_component["available"] is True,
                              "new complete native sibling component is observed: " + key)
                        check(native_component["capture_epoch"] == primary["capture_epoch"]
                              and native_component["date_raw"] == primary["date_raw"]
                              and native_component["played_character_id"] == primary["played_character_id"],
                              "native sibling remains in its original owner-pump player frame: " + key)
                        check(native_component["schema"].startswith("ck3_12004_"),
                              "native sibling schema is already actual .4: " + key)
                native_before = deepcopy(packet)
                endpoint = Endpoint(packet, expected_request)
                driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                     command_timeout_seconds=1.0)
                try:
                    for route_step in ROUTES:
                        permission = "allow_private_" + route_step[len("query-"):-len("-v1")].replace("-", "_") + "_query"
                        setattr(driver, permission, True)
                    hello = {
                        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                        "pid": 4242, "session_generation": 0,
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                        "capabilities": ["game.state.snapshot"] + ["game.command." + key for key in ROUTES],
                    }
                    snapshot_frame = state(result, primary)
                    endpoint.publish(hello)
                    endpoint.publish(snapshot_frame)
                    before = driver.take_snapshot()
                    check(before["native_revision"] == result["snapshot_revision"]
                          and before["date_raw"] == result["date_raw"],
                          "synthetic protocol snapshot uses the original native packet frame")
                    server = create_server(driver)
                    registered = {item.name: item for item in await server.list_tools()}
                    check(tool in registered and registered[tool].annotations.read_only_hint,
                          "same existing readonly MCP tool is registered: " + tool)
                    arguments = {"expected_revision": before["revision"]}
                    if targeted:
                        arguments["target_rite_id"] = primary["target_rite_id"]
                    # Keep the complete original compiled command_result. The
                    # production G2 transport generates only its request token.
                    with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                               return_value=SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])):
                        report["actual_compound_cases"] = 1
                        response = await server.call_tool(tool, arguments)
                    check(not response.is_error,
                          "new whole native packet passes the real registered query and normalizers: " + tool)
                    actual = response.structured_content
                    check(isinstance(actual, dict) and len(endpoint.requests) == 1,
                          "one registered query consumes one whole compiled packet: " + step)
                    check(actual["exact_ck3_build"] == CK3_12004.game_version
                          and actual["exe_sha256"] == CK3_12004.executable_sha256,
                          "registered result preserves actual .4 source provenance: " + step)
                    check(primary["schema"].startswith("ck3_12004_")
                          and actual["schema"] == primary["schema"],
                          "native primary schema is already actual .4 and never retagged: " + step)
                    for key, value in primary.items():
                        check(actual[key] == value, "whole native primary field retained: " + step + "." + key)
                    for key in siblings:
                        check(actual[key] == result[key],
                              "whole actual .4 native sibling retained without transplant: " + key)
                    for key in ("backend_id", "domain_key", "snapshot_revision", "status", "read_only", "advertised"):
                        check(actual[key] == result[key], "native query envelope field retained: " + step + "." + key)
                    check(actual["query_date_raw"] == result["date_raw"]
                          and actual["queried_native_revision"] == result["snapshot_revision"]
                          and actual["queried_revision"] == before["revision"]
                          and actual["queried_snapshot_id"] == before["snapshot_id"],
                          "registered metadata binds the original frame and real driver semantic revision")
                    check(packet == native_before, "original whole native packet remains unchanged after consumption")
                    observations.append({
                        "step": step, "tool": tool, "native_packet": native_before,
                        "protocol_request": endpoint.requests[0], "mcp_arguments": arguments,
                        "registered_result": actual, "synthetic_hello": hello,
                        "synthetic_snapshot": snapshot_frame,
                        "normalized_native_siblings": list(siblings),
                    })
                finally:
                    driver.close()
            check(args.native_fixture.read_bytes() == native_bytes,
                  "new compiled producer document remains byte-identical")

        asyncio.run(exercise())
        report.update(status="GREEN", actual_new_native_packets=len(packets),
                      full_context_addons=len(CONTEXT_ADDONS),
                      faith_numeric_final_same_packet=True, whole_native_domain_preserved=True)
    except Exception as error:
        report.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        report["checks"] = checks
        report["completed_packets"] = len(observations)
        with (args.output_dir / "COMPOUND-CONSUMPTION.json").open("x", encoding="utf-8") as output:
            output.write(json.dumps(observations, indent=2) + "\n")
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
