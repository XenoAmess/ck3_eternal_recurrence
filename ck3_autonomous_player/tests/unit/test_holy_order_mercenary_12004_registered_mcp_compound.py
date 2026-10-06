"""One compiled .4 whole-wire case through the four existing registered tools.

Root supplies a new native producer document with fixture_provenance and samples
of unchanged command_result packets. This file is prepared, not executed, by
the migration worker. Its endpoint/hello/snapshot are synthetic and use no pipe.
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


TOOLS = {
    "query-player-holy-order-context-v1": ("ck3_query_player_holy_order_context_v1", "player_holy_order_context"),
    "query-player-mercenary-context-v1": ("ck3_query_player_mercenary_context_v1", "player_mercenary_context"),
    "hire-holy-order-v1": ("ck3_hire_holy_order_v1", "holy_order_hire"),
    "hire-mercenary-v1": ("ck3_hire_mercenary_v1", "mercenary_hire"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "tools"))
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from jsonschema import Draft202012Validator
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build

    native_bytes = args.native_fixture.read_bytes()
    document = json.loads(native_bytes.decode("utf-8-sig"))
    packets = document["samples"]
    checks: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    check("synthetic" in str(document["fixture_provenance"]).lower(),
          "synthetic callback/game-memory provenance remains explicit")
    check(isinstance(packets, list) and bool(packets), "native producer supplies complete packets")
    seen = {packet["result"]["step"] for packet in packets}
    check(seen == set(TOOLS), "one compound producer covers both queries and both typed ACKs")
    actor = next(packet["result"]["player_holy_order_context"]["played_character_id"]
                 for packet in packets if packet["result"]["step"] == "query-player-holy-order-context-v1")
    check(actor == 29829, "fixture keeps the Robert current-player entrance")
    validators = {
        step: Draft202012Validator(json.loads((args.source_root / "ck3_autonomous_player/schemas" / name)
                                             .read_text(encoding="utf-8")))
        for step, name in {
            "hire-holy-order-v1": "holy-order-hire-action-v1.schema.json",
            "hire-mercenary-v1": "mercenary-hire-action-v1.schema.json",
        }.items()
    }

    class Endpoint:
        pipe_name = r"\\.\pipe\holy-mercenary-12004-offline-compound"

        def __init__(self, packet: dict) -> None:
            self.packet = packet
            self.on_frame = None
            self.requests: list[dict] = []

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, frame: dict) -> None:
            check(callable(self.on_frame), "real driver registers protocol receiver")
            self.on_frame(deepcopy(frame))

        def send(self, request: dict) -> None:
            if request["type"] != "execute_step":
                return
            self.requests.append(deepcopy(request))
            check(request["step"] == self.packet["result"]["step"], "only the selected native step is sent")
            check(request["request_id"] == self.packet["request_id"], "producer packet request identity retained")
            self.publish(self.packet)

        def transport_error(self):
            return None

        def close(self) -> None:
            pass

    def state(result: dict) -> dict:
        revision = result["snapshot_revision"]
        return {
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{revision}", "revision": revision,
            "state": {
                "phase": "map_hud", "date": "fixture-only", "date_raw": result["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": actor, "alive": True},
                "player_armies": [], "active_wars": [],
            },
        }

    async def exercise() -> list[dict]:
        observed = []
        for packet in packets:
            check(packet["type"] == "command_result" and packet["ok"] is True,
                  "genuine producer supplies command_result envelope")
            result = packet["result"]
            check(require_exact_native_build(result["game_version"], result["executable_sha256"]) == CK3_12004,
                  "new native output has actual exact .4 tuple")
            step = result["step"]
            tool, domain = TOOLS[step]
            native = result[domain]
            check(native["schema"].startswith("ck3_12004_"), "native family schema is rendered for actual .4")
            endpoint = Endpoint(packet)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                 command_timeout_seconds=1.0)
            driver.allow_private_player_religion_context_query = True
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 4242, "session_generation": 0,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot"] + ["game.command." + key for key in TOOLS],
            })
            endpoint.publish(state(result))
            before = driver.take_snapshot()
            server = create_server(driver)
            registered = {item.name: item for item in await server.list_tools()}
            check(tool in registered, "same existing tool is registered")
            arguments = {"expected_revision": before["revision"]}
            if step == "hire-holy-order-v1":
                arguments["holy_order_id"] = native["holy_order_id"]
            elif step == "hire-mercenary-v1":
                arguments["company_id"] = native["company_id"]

            # Bind the existing request-token seam, retaining the full original
            # producer envelope/body rather than rebuilding a command_result.
            execute = driver._execute_primitive_step

            def execute_with_native_request(selected_step, **kwargs):
                kwargs["protocol_request_id"] = packet["request_id"]
                return execute(selected_step, **kwargs)

            with patch.object(driver, "_execute_primitive_step", execute_with_native_request):
                if step == "query-player-holy-order-context-v1":
                    check(packet["request_id"].startswith("g2-read-"), "holy query uses existing G2 request prefix")
                    with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                               return_value=SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])):
                        response = await server.call_tool(tool, arguments)
                else:
                    response = await server.call_tool(tool, arguments)
            check(not response.is_error, "fresh whole native output passes registered MCP/service/driver")
            actual = response.structured_content
            check(len(endpoint.requests) == 1, "one existing request per producer sample")
            if step.startswith("query-"):
                check(registered[tool].annotations.read_only_hint, "query remains readonly")
                check(actual["schema"] == native["schema"], "new schema retained without retagging")
                check(require_exact_native_build(actual["game_version"], actual["executable_sha256"]) == CK3_12004,
                      "query preserves exact .4 identity")
                for key, value in native.items():
                    if key == "rows" and step == "query-player-mercenary-context-v1":
                        check(len(actual[key]) == len(value), "all native mercenary rows retained")
                        for copied, source in zip(actual[key], value):
                            check({name: copied[name] for name in source} == source,
                                  "mercenary row retains every native field alongside existing readiness")
                    else:
                        check(actual[key] == value, "whole native query field retained: " + key)
            else:
                validators[step].validate(result)
                check({key: actual[key] for key in result} == result, "entire native typed ACK retained")
                check(actual[domain]["after_state_observed"] is False, "ACK supplies no material after-state")
            observed.append({"step": step, "native_result": result, "registered_result": actual})
            driver.close()
        check(args.native_fixture.read_bytes() == native_bytes, "native producer file remains unchanged")
        return observed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.holy-order-mercenary-12004-compound-first.v1", "status": "RED",
        "native_fixture": str(args.native_fixture), "source_root": str(args.source_root),
        "native_fixture_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "synthetic_callbacks_and_snapshots": True, "live": False, "game_operations": 0,
        "tests_run_by_preparing_worker": False,
    }
    try:
        observations = asyncio.run(exercise())
        (args.output_dir / "COMPOUND-CONSUMPTION.json").write_text(
            json.dumps(observations, indent=2) + "\n", encoding="utf-8")
        report.update(status="GREEN", samples=len(packets), checks=checks, whole_native_domain_preserved=True)
    except Exception as error:
        report.update(error=str(error), checks=checks)
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
