"""Root-only registered consumer FIRST of five original native release packets.

AUTHORED_NOTRUN. Native fixture captives, callbacks and dates are synthetic;
there is no SDK, named-pipe connection, game action, freedom or effect credit.
Only request_id is rebound to the production transport's fresh correlation ID.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
from pathlib import Path
import sys


_CASES = (
    "all_off_pending", "gain_hook_pending", "gain_hook_native_false",
    "gain_hook_copied_mask_changed", "gain_hook_native_refused",
)
_POSITIVE = {"all_off_pending", "gain_hook_pending"}
_SKIP = {"gain_hook_native_false", "gain_hook_native_refused"}
_QUERY_TOOL = "ck3_query_player_prisoner_collection_private_v1"
_ACTION_TOOL = "ck3_release_player_prisoner_private_v1"
_QUERY_STEP = "query-player-prisoner-collection-private-v1"
_ACTION_STEP = "submit-player-prisoner-release-private-v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-wire-dir", "--native-fixture-dir", dest="native_fixture_dir",
                        type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.source_root / "ck3_autonomous_player/src"),
                   str(args.source_root / "tools")]
    from mcp.server.mcpserver.exceptions import ToolError
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    class Endpoint:
        pipe_name = r"\unused-offline-prisoner-release-action-12004"

        def __init__(self, packet):
            self.packet = packet
            self.requests = []
            self.on_frame = None

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, frame):
            self.on_frame(copy.deepcopy(frame))

        def send(self, request):
            if request.get("type") == "ping":
                return
            require(request.get("type") == "execute_step"
                    and request.get("protocol_version") == 1,
                    "actual registered transport changed the native command protocol")
            self.requests.append(copy.deepcopy(request))
            query = self.packet["before_collection"]
            native = query["result"]
            mask = self.packet["native_expectations"]["requested_option_mask_bits"]
            if request.get("step") == _QUERY_STEP:
                require(request.get("expected_revision") == native["snapshot_revision"],
                        "collection request lost its native revision")
                require(("release_option_mask_bits" not in request if mask == 0 else
                         request.get("release_option_mask_bits") == mask),
                        "actual query changed the all-off or selected native mask")
                wire = copy.deepcopy(query)
            else:
                require(request.get("step") == _ACTION_STEP,
                        "registered release action changed its native step")
                prisoner = native["player_prisoner_collection"]["prisoners"][0]
                require(set(request) == {"type", "protocol_version", "request_id", "step",
                        "expected_revision", "release_query_sequence", "prisoner_character_id",
                        "release_option_mask_bits"}, "release request invented public action terms")
                require(request["expected_revision"] == native["snapshot_revision"]
                        and request["release_query_sequence"] == native["query_sequence"]
                        and request["prisoner_character_id"] == prisoner["prisoner_character_id"]
                        and request["release_option_mask_bits"] == mask,
                        "release action did not preserve queried frame/full ID/sequence/mask")
                wire = copy.deepcopy(self.packet["command_result"])
            wire["request_id"] = request["request_id"]
            self.publish(wire)

        def close(self):
            pass

        def transport_error(self):
            return None

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.ck3.prisoner-release-action-registered-first/v1",
              "status": "RED", "source_root": str(args.source_root),
              "compound_methods": 1, "registered_tool_methods": [_QUERY_TOOL, _ACTION_TOOL],
              "native_fixture_dir": str(args.native_fixture_dir), "cases": {},
              "scope": "offline_native_owned_memory_and_registered_mcp",
              "sdk_calls": 0, "game_actions": 0, "production_live_release": False,
              "material_result": False, "mailbox_route_fixture_covered": False,
              "native_wire_mutations": "request_id correlation only"}
    try:
        for case in _CASES:
            path = args.native_fixture_dir / (case + ".json")
            packet = json.loads(path.read_bytes())
            require(packet["scenario"] == case, "original native packet has a different scenario")
            endpoint = Endpoint(packet)
            state_dir = args.output_dir / case / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                state_dir=state_dir, command_timeout_seconds=0.1,
                allow_private_prisoner_collection_query=True,
                allow_private_prisoner_ransom_action=True)
            try:
                endpoint.publish(packet["hello"])
                endpoint.publish(packet["before_snapshot"])
                server = create_server(driver)
                tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
                require(_QUERY_TOOL in tools and _ACTION_TOOL in tools
                        and tools[_QUERY_TOOL].annotations.read_only_hint is True,
                        "the actual collection and release MCP tools were not registered")
                before = driver.take_snapshot()
                query_arguments = {"expected_revision": before["revision"], "ransom_ordinal": 0}
                if case != "all_off_pending":
                    query_arguments["release_option_keys"] = ["gain_hook"]
                response = asyncio.run(server.call_tool(_QUERY_TOOL, query_arguments))
                require(not response.is_error, case + ": production query rejected the whole native wire")
                collection = response.structured_content
                native = packet["before_collection"]["result"]
                require(all(collection.get(key) == value for key, value in native.items()),
                        case + ": query normalization changed native collection fields")
                row = collection["player_prisoner_collection"]["prisoners"][0]
                prisoner_id = row["prisoner_character_id"]
                require(prisoner_id == 0x03000002 and row["source_ordinal"] == 0
                        and row["custody_relation_verified"] is True,
                        "whole collection lost the synthetic full ID or independent custody")
                preview = row["unconditional_release_preview"] if case == "all_off_pending" else row["negotiated_release_preview"]
                action = None
                error = None
                try:
                    response = asyncio.run(server.call_tool(_ACTION_TOOL, {
                        "collection": collection, "prisoner_character_id": prisoner_id}))
                    if response.is_error:
                        error = str(response.content)
                    else:
                        action = response.structured_content
                except ToolError as failure:
                    error = str(failure)
                action_requests = [request for request in endpoint.requests
                                   if request.get("step") == _ACTION_STEP]
                native_expectations = packet["native_expectations"]
                if case in _POSITIVE:
                    require(error is None and action is not None and len(action_requests) == 1,
                            case + ": an accepted current offer was not submitted once")
                    require(action["status"] == "submitted_verification_pending"
                            and action["material_result"] is False
                            and action["release_option_mask_bits"] == native_expectations["requested_option_mask_bits"]
                            and action["costs"] == preview["costs"]
                            and action["acceptance"] == preview["acceptance"]
                            and action["pre_native_revision"] == native["snapshot_revision"],
                            case + ": pending result lost typed terms or claimed material freedom")
                    require(native_expectations["queue_calls"] == 1
                            and native_expectations["clone_calls"] == 1
                            and native_expectations["queued_option_mask_bits"] == action["release_option_mask_bits"],
                            case + ": registered pending mask differs from native owned clone")
                else:
                    require(error is not None and action is None
                            and native_expectations["queue_calls"] == 0,
                            case + ": a failed offer gained an action/material result")
                    require(len(action_requests) == (0 if case in _SKIP else 1),
                            case + ": observed refusal/false gate or native copy error took the wrong path")
                report["cases"][case] = {"native_packet": str(path),
                    "collection": collection, "requests": endpoint.requests,
                    "action": action, "error": error, "native_expectations": native_expectations}
            finally:
                driver.close()
        report["status"] = "GREEN"
    except Exception as failure:
        report["error"] = repr(failure)
        raise
    finally:
        (args.output_dir / "registered-consumer.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        summary = {key: report[key] for key in ("schema", "status", "compound_methods", "registered_tool_methods",
                   "source_root", "native_fixture_dir", "scope", "sdk_calls", "game_actions",
                   "production_live_release", "material_result", "mailbox_route_fixture_covered")}
        summary["rows"] = [{"scenario": case, "action_request_count": sum(
                request.get("step") == _ACTION_STEP for request in row["requests"]),
                "status": "pending" if row["action"] is not None else "blocked_or_native_red",
                "material_result": False} for case, row in report["cases"].items()]
        summary["detail"] = str(args.output_dir / "registered-consumer.json")
        if "error" in report:
            summary["error"] = report["error"]
        (args.output_dir / "CONSUMER-FIRST.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("release collection -> typed accepted terms -> registered action -> pending/native RED GREEN (offline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
