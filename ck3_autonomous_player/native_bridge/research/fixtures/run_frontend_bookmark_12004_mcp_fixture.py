"""Replay native 1.20.0.4 bookmark-model packets through existing MCP routes.

Authored offline consumer; this file's presence is AUTHORED_NOTRUN evidence.
Only its later execution can produce a consumer result. No game endpoint is
constructed. The generic ck3_execute_step route still requires a semantic map
snapshot, so its frontend rejection is checked without inventing revision 0
map state. The existing registered bookmark-character Start tool consumes the
private native model through its production frontend revision-0 primitive.
Its auxiliary route/ACK replies are fixture data. No semantic map or campaign
root is supplied, and a Start ACK therefore ends at unavailable observation.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import traceback


EXACT_VERSION = "1.20.0.4"
EXACT_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
DEFAULT_CHARACTER_KEY = "bookmark_rags_to_riches_duke_robert"
CHECKS = 0
PRIVATE_FIELDS = {
    "step", "accepted", "status", "private_scope", "gui_chain_vtable_rvas",
    "interface_application_chain_level", "owner_chain_vtable_rvas",
    "owner_chain_rtti_type_rvas", "direct_owner_unavailable_reason",
    "registry_owner_unavailable_reason", "registry_owner_match_count",
    "verified_owner_route", "setup_view_vtable_rva",
    "setup_view_matches_bookmarks_root", "selected_bookmark_group_key",
    "selected_bookmark_key", "selected_date_raw", "selected_date_low_raw",
    "selected_character_index", "hovered_character_index",
    "bookmark_character_count", "bookmark_character_capacity_raw",
    "bookmark_character_allocator_raw", "candidate_keys",
    "supported_1066_candidate_index", "supported_1066_candidate_present",
    "supported_1066_government_key", "supported_1066_feudal",
    "supported_1066_date_matches", "candidate_identity_ready",
    "unavailable_reason",
}


def require(value: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not value:
        raise RuntimeError(message)


def digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def response_text(response: object) -> str:
    return "\n".join(str(getattr(row, "text", ""))
                     for row in getattr(response, "content", []))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--character-name-key", default=DEFAULT_CHARACTER_KEY)
    args = parser.parse_args()
    paths = sorted(args.native_dir.glob("*.json"))
    if not paths:
        parser.error("provide native-produced complete private probe command_result JSON files")
    output = args.out or args.native_dir.parent / "FRONTEND-BOOKMARK-MCP-CONSUMER-RESULT.json"
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))

    try:
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        from xar_autoplayer.bridge.frontend_gui_route_contract import (
            ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY,
            ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_STEP,
            ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
            ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
            FEUDAL_1066_CHARACTER_NAME_KEYS,
            PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
            PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP,
            QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
            QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
            frontend_gui_route_binding_from_capabilities,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps

        require(args.character_name_key in FEUDAL_1066_CHARACTER_NAME_KEYS,
                "fixture selects an existing supported bookmark character")

        class NativeReplay(NativeHeadlessGameplayDriver):
            """Replace only external frames/transport and command-history sink."""

            def __init__(self, packet: dict[str, object]):
                self.packet = deepcopy(packet)
                self.endpoint = self.state = self
                self._request_sequence = 0
                self.command_timeout_seconds = 1.0
                self.frontend_transition_timeout_seconds = 0.05
                self.requests: list[dict[str, object]] = []
                self.native_frames: list[dict[str, object]] = []
                self.history: list[dict[str, object]] = []

            def capabilities(self):
                capabilities = [
                    QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
                    PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
                    ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY,
                    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
                ]
                return {
                    "backend_id": "native-headless", "mode": "native-headless",
                    "source": "injected-dll-named-pipe", "visual_fallback": False,
                    "bridge_capabilities": capabilities,
                    "action_steps": _action_steps(capabilities),
                    "snapshot": False,
                    "diagnostics": {
                        "connected": True, "bridge_pid": 12004,
                        "connection_generation": 1,
                        "hello": {
                            "pid": 12004, "connection_generation": 1,
                            "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                            "expected_ck3_version": EXACT_VERSION,
                            "expected_ck3_sha256": EXACT_SHA256,
                            "game_adapter_status": "ready", "ck3_build_match": True,
                            "capabilities": capabilities,
                        },
                    },
                }

            def take_snapshot(self, **kwargs):
                raise BridgeUnavailableError(
                    "native game state is not available yet; offline frontend "
                    "fixture has no semantic map snapshot"
                )

            def send(self, request):
                require(request["type"] == "execute_step" and
                        request["protocol_version"] == 1 and
                        request["expected_revision"] == 0,
                        "frontend transport keeps the real revision-0 command envelope")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id, timeout):
                request = self.requests[-1]
                require(request["request_id"] == request_id,
                        "fixture response is bound to the submitted request")
                step = request["step"]
                if step == PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP:
                    packet = deepcopy(self.packet)
                    packet["request_id"] = request_id
                    self.native_frames.append(deepcopy(packet))
                    return packet
                if step == QUERY_FRONTEND_GUI_ROUTE_V1_STEP:
                    status = "bookmarks"
                elif step in {
                    ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_STEP,
                    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
                }:
                    status = "acknowledged_verification_pending"
                else:
                    raise RuntimeError(f"unexpected offline frontend step: {step}")
                # These auxiliary fixture replies never come from or go to CK3.
                return {
                    "type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True,
                    "result": {"step": step, "accepted": True, "status": status},
                }

            def _record_command(self, step, *, ok, result=None, error=None):
                self.history.append({"step": step, "ok": ok,
                                     "result": deepcopy(result), "error": error})

        async def check_packets():
            cases = []
            for path in paths:
                packet = json.loads(path.read_text(encoding="utf-8-sig"))
                require(isinstance(packet, dict) and packet.get("type") == "command_result"
                        and packet.get("protocol_version") == 1 and packet.get("ok") is True,
                        "input is a genuine complete native command_result envelope")
                value = packet.get("result")
                require(isinstance(value, dict) and PRIVATE_FIELDS <= value.keys()
                        and value["step"] == PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP
                        and value["private_scope"] == "exact-build-bookmarks-model-v1",
                        "input retains every field of the production private formatter")
                input_digest = digest(packet)
                driver = NativeReplay(packet)
                require(frontend_gui_route_binding_from_capabilities(driver.capabilities())
                        == {"bridge_pid": 12004, "connection_generation": 1},
                        "production frontend binder admits the exact actual4 identity")
                server = create_server(driver)
                names = {row.name for row in await server.list_tools()}
                require("ck3_execute_step" in names and
                        "ck3_activate_frontend_start_1066_bookmark_character_v1" in names,
                        "both checks use existing registered MCP tools")

                generic = await server.call_tool(
                    "ck3_execute_step",
                    {"step": PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP, "expected_revision": 0},
                )
                require(getattr(generic, "is_error", False) is True and
                        "no semantic map snapshot" in response_text(generic),
                        "generic execute_step preserves its genuine map snapshot requirement")
                require(not driver.requests and len(driver.history) == 1
                        and driver.history[0]["ok"] is False,
                        "unchanged production execute_step records rejection before transport")

                # The actual frontend primitive must preserve the whole native
                # private payload, including nullable fields and native zeroes.
                driver.__init__(packet)
                projected = driver._execute_primitive_step(
                    PROBE_FRONTEND_BOOKMARK_MODEL_V1_STEP,
                    expected_revision=0,
                    required_capability=PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
                    allow_frontend_revision_zero=True,
                )
                require(projected == {**value, "backend_id": "native-headless"},
                        "production primitive retains the complete native private payload")
                require(len(driver.native_frames) == 1 and
                        driver.native_frames[0]["result"] == value,
                        "native replay changes only request correlation, never the result")

                # Run the real typed driver/service/registered-tool consumer.
                # Requeries replay the same native model; selection ACK never
                # rewrites it into a selected candidate or invents a map.
                driver.__init__(packet)
                typed = await server.call_tool(
                    "ck3_activate_frontend_start_1066_bookmark_character_v1",
                    {"character_name_key": args.character_name_key},
                )
                require(getattr(typed, "is_error", False) is True,
                        "offline Start consumer cannot claim a verified campaign")
                require(driver.native_frames and
                        all(frame["result"] == value for frame in driver.native_frames),
                        "registered Start consumer receives unchanged native producer results")
                steps = [request["step"] for request in driver.requests]
                selections = steps.count(ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_STEP)
                starts = steps.count(ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP)
                require(selections <= 1 and starts <= 1,
                        "one candidate consumes at most one setter and one Start ACK")
                keys = value["candidate_keys"]
                target = value["supported_1066_candidate_index"]
                selected = value["selected_character_index"]
                eligible = (value["candidate_identity_ready"] is True
                            and isinstance(keys, list) and type(target) is int
                            and 0 <= target < len(keys)
                            and keys[target] == args.character_name_key
                            and type(selected) is int and -1 <= selected < len(keys))
                detail = response_text(typed)
                if not eligible:
                    require(selections == starts == 0 and
                            "not bound to the requested" in detail,
                            "unavailable identity stops before fixture mutation ACKs")
                    outcome = "candidate_unavailable_before_selection"
                elif selected != target:
                    require(selections == 1 and starts == 0 and
                            "did not publish the requested native character" in detail,
                            "selection eligibility does not manufacture selected observation")
                    outcome = "selection_eligible_observation_unavailable"
                elif starts:
                    require(starts == 1 and selections == 0 and
                            "no paused player map was independently observed" in detail,
                            "eligible selected candidate ends at unavailable post-map observation")
                    outcome = "selected_candidate_eligible_post_map_unavailable"
                else:
                    require(selections == 0 and
                            "did not publish the requested native character" in detail,
                            "invalid selected date/government stops before Start")
                    outcome = "selected_candidate_identity_unavailable"
                require(digest(packet) == input_digest and driver.packet == packet,
                        "all routes leave the genuine native packet unchanged")
                cases.append({
                    "case": path.stem, "packet": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "native_result_sha256": digest(value), "status": "GREEN",
                    "consumer_outcome": outcome,
                    "native_candidate_identity_ready": value["candidate_identity_ready"],
                    "registered_native_probe_reads": len(driver.native_frames),
                    "fixture_selection_acks": selections, "fixture_start_acks": starts,
                    "requests": driver.requests, "native_result": value,
                    "registered_tool_error": detail,
                    "generic_route": "semantic_map_snapshot_required",
                    "campaign_verified": False,
                })
            require(any(case["fixture_start_acks"] == 1 for case in cases),
                    "native cases include an eligible selected candidate consumed before post-map failure")
            return cases

        cases = asyncio.run(check_packets())
        report = {
            "status": "GREEN", "readiness": "static-ready", "checks": CHECKS,
            "exact_version": EXACT_VERSION, "exact_executable_sha256": EXACT_SHA256,
            "cases": cases, "game_operations": 0, "sdk_calls_to_game": 0,
            "window_operations": 0, "live_validation": False,
            "campaign_verified": False, "whole_dll_built": False,
            "registered_route": "ck3_activate_frontend_start_1066_bookmark_character_v1",
            "generic_route": "unchanged_ck3_execute_step_requires_semantic_map_snapshot",
            "auxiliary_replies": "fixture_only_route_and_ack_no_post_map_frame",
        }
        exit_code = 0
    except Exception as error:
        report = {
            "status": "RED", "classification": "harness-or-consumer", "checks": CHECKS,
            "error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(), "game_operations": 0,
            "sdk_calls_to_game": 0, "window_operations": 0,
            "live_validation": False, "campaign_verified": False,
        }
        exit_code = 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"},
                     ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
