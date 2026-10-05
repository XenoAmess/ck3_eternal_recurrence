"""Current automatic-release input survives the existing registered MCP query, offline."""
from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
    from xar_autoplayer.bridge.player_holy_order_context_private_transport import (
        normalize_player_holy_order_context_v1,
        query_player_holy_order_context_private_v1,
    )

    tool_name = "ck3_query_player_holy_order_context_v1"
    native_bytes = args.native_fixture.read_bytes()
    packets = json.loads(native_bytes)["samples"]
    checks = 0
    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Driver:
        command_timeout_seconds = 1.0
        allow_private_player_religion_context_query = True
        query_player_holy_order_context_private_v1 = (
            NativeHeadlessGameplayDriver.query_player_holy_order_context_private_v1
        )
        def __init__(self, packet: dict) -> None:
            self.packet = packet
            result = packet["result"]
            body = result["player_holy_order_context"]
            self.snapshot = {
                "snapshot_id": f"native:{result['snapshot_revision']}",
                "revision": result["snapshot_revision"] + 1,
                "native_revision": result["snapshot_revision"],
                "date_raw": result["date_raw"],
                "played_character": {"character_id": body["played_character_id"], "alive": True},
                "paused": True, "map_ready": True,
                "diagnostics": {"hello": {
                    "expected_ck3_version": result["game_version"],
                    "expected_ck3_sha256": result["executable_sha256"],
                }},
            }
            self.sent: list[dict] = []
            self.endpoint = self
            self.state = NativeProtocolState("offline-fixture:holy-order-service-lifecycle")
        def take_snapshot(self) -> dict:
            return copy.deepcopy(self.snapshot)
        def send(self, request: dict) -> None:
            check(request["request_id"] == self.packet["request_id"], "native request identity")
            self.sent.append(copy.deepcopy(request))
            check(self.state.ingest(copy.deepcopy(self.packet)) == "command_result", "real protocol ingest")

    async def exercise() -> list[dict]:
        observed = []
        check(len(packets) == 4, "four focused new native lifecycle scenarios")
        for index, packet in enumerate(packets):
            driver = Driver(packet)
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            check(tools[tool_name].annotations.read_only_hint, "existing registered tool remains readonly")
            request_id = packet["request_id"]
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=request_id[len("g2-read-"):])):
                response = await server.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            check(not response.is_error, "registered MCP accepts native lifecycle observation")
            actual = response.structured_content
            native = packet["result"]["player_holy_order_context"]
            check({key: actual[key] for key in native} == native, "complete native domain preserved")
            check(len(driver.sent) == 1 and driver.sent[0]["step"] == "query-player-holy-order-context-v1",
                  "single existing native query dispatch")
            check("played_character_id" not in driver.sent[0], "actual player supplied by native frame")
            for row_index, row in enumerate(actual["rows"][:5]):
                terms = row["military_terms"]
                service = terms["service_lifecycle"]
                check(terms["can_hire"] is False and terms["available"] is (index != 1),
                      "lifecycle does not promote final hire or failed resource quote")
                check(service["applies_to_player"] is (row_index < 3),
                      "actual current-player employment controls lifecycle applicability")
                if row_index >= 3:
                    check(service["available"] is True and
                          all(service[key] is None for key in (
                              "release_eligible", "associated_regiment_in_combat", "release_check_queued")),
                          "other employer and unhired rows do not claim player service")
                elif index == 2:
                    check(service["available"] is False and service["release_eligible"] is None
                          and service["unavailable_reason"] == "native_service_lifecycle_binding_unavailable",
                          "missing binding stays unavailable")
                else:
                    check(service["release_eligible"] is (row_index == 2)
                          and service["associated_regiment_in_combat"] is (row_index == 1),
                          "native retain/combat-delay/release-ready inputs stay distinct")
                    if index == 3:
                        check(service["available"] is False and service["release_check_queued"] is None
                              and service["unavailable_reason"] == "native_release_check_queue_unavailable",
                              "queue failure retains native predicate observations")
                    else:
                        check(service["available"] is True and service["release_check_queued"] is (row_index != 0),
                              "fullID queue membership and condition recheck remain independent")
            check(actual["rows"][5]["military_terms"] is None, "nonmilitary service lifecycle inapplicable")
            observed.append(actual)
        # This new query field is optional in older frozen packets.
        old = copy.deepcopy(packets[0]["result"]["player_holy_order_context"])
        for row in old["rows"][:5]:
            del row["military_terms"]["service_lifecycle"]
        check(normalize_player_holy_order_context_v1(old, snapshot=Driver(packets[0]).snapshot) == old,
              "historical wire compatibility for the new lifecycle field")
        return observed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.holy-order-service-lifecycle-mcp-validation.v1", "status": "RED"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
        report.update(status="GREEN", samples=len(packets), checks=checks, tool=tool_name,
                      native_fixture=str(args.native_fixture),
                      native_fixture_sha256=hashlib.sha256(native_bytes).hexdigest(),
                      source_root=str(args.source_root), native_domain_preserved=True,
                      live_queries=0, sdk_sessions=0, game_actions=0,
                      new_path_source=[str(inspect.getsourcefile(fn)) for fn in (
                          normalize_player_holy_order_context_v1,
                          query_player_holy_order_context_private_v1)])
    except Exception as error:
        report.update(checks=checks, error=str(error))
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
