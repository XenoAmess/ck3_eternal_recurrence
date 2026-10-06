"""Replay whole native .4 frontend frames through existing registered tools.

Requires the actual .4 frontend identity migration from dependency 089ee.
The normal production driver, protocol cache, Service and MCP registration
remain intact. A fixture endpoint supplies transport metadata and native
command_result frames; no game-state DTO or frontend action is manufactured.
Authoring this source does not establish a fixture pass or live capability.
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
import uuid


checks = 0


def require(value: bool, message: str) -> None:
    global checks
    checks += 1
    if not value:
        raise RuntimeError(message)


async def consume(args: argparse.Namespace) -> list[dict[str, object]]:
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.frontend_gui_route_contract import (
        FRONTEND_GUI_ROUTE_V1_BUILD_IDENTITIES,
        INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_CAPABILITY,
        INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP,
        INSPECT_FRONTEND_GUI_TREE_V1_CAPABILITY,
        INSPECT_FRONTEND_GUI_TREE_V1_STEP,
        QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
        QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
        frontend_gui_route_binding_from_capabilities,
        normalize_frontend_coat_of_arms_tree_inspection_v1,
        normalize_frontend_gui_route_v1,
        normalize_frontend_gui_tree_inspection_v1,
    )
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import DEFAULT_PIPE_NAME, NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.succession_transition_contract import (
        unknown_succession_lifecycle_binding_v1,
    )
    from xar_autoplayer.bridge.version_identity import CK3_12004

    identity = ("ck3-1.20.0.4-msvc-x64", CK3_12004.game_version, CK3_12004.executable_sha256)
    require(identity in FRONTEND_GUI_ROUTE_V1_BUILD_IDENTITIES,
            "adopt the actual .4 frontend identity dependency 089ee before this consumer")
    cases = [
        ("mainmenu-route.json", "ck3_query_frontend_gui_route_v1",
         QUERY_FRONTEND_GUI_ROUTE_V1_STEP, normalize_frontend_gui_route_v1, "main_menu", None),
        ("mainmenu-tree.json", "ck3_inspect_frontend_gui_tree_v1",
         INSPECT_FRONTEND_GUI_TREE_V1_STEP, normalize_frontend_gui_tree_inspection_v1,
         "mainmenu_panel_bottom", ["mainmenu_panel_bottom", "new_game"]),
        ("coa-route.json", "ck3_query_frontend_gui_route_v1",
         QUERY_FRONTEND_GUI_ROUTE_V1_STEP, normalize_frontend_gui_route_v1, "coat_of_arms_designer", None),
        ("coa-tree.json", "ck3_inspect_frontend_coat_of_arms_tree_v1",
         INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_STEP, normalize_frontend_coat_of_arms_tree_inspection_v1,
         "coat_of_arms_page", ["coat_of_arms_page", "coat_of_arms_preview"]),
    ]
    packets = []
    for filename, _, step, _, _, _ in cases:
        path = args.native_dir / filename
        packet = json.loads(path.read_text(encoding="utf-8-sig"))
        require(isinstance(packet, dict) and packet.get("type") == "command_result"
                and packet.get("protocol_version") == 1 and packet.get("ok") is True
                and isinstance(packet.get("result"), dict),
                f"complete native command_result envelope required: {filename}")
        require(packet["result"].get("step") == step and packet["result"].get("accepted") is True,
                f"normal native formatter retains the qualified registered step: {filename}")
        packets.append(packet)

    class PacketEndpoint:
        """Only the external transport is replaced; result payloads stay native."""

        pipe_name = DEFAULT_PIPE_NAME

        def __init__(self) -> None:
            self.requests: list[dict[str, object]] = []
            self.returned: list[dict[str, object]] = []
            self._on_frame = None
            self._on_disconnect = None

        def start(self, on_frame, on_disconnect) -> None:
            self._on_frame, self._on_disconnect = on_frame, on_disconnect
            on_frame({
                "type": "hello", "protocol_version": 1, "pid": 1,
                "connection_generation": 1, "game_adapter_id": identity[0],
                "expected_ck3_version": identity[1], "expected_ck3_sha256": identity[2],
                "game_adapter_status": "ready", "ck3_build_match": True,
                "capabilities": [QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
                                 INSPECT_FRONTEND_GUI_TREE_V1_CAPABILITY,
                                 INSPECT_FRONTEND_COAT_OF_ARMS_TREE_V1_CAPABILITY],
            })

        def send(self, request: dict[str, object]) -> None:
            self.requests.append(deepcopy(request))
            if request.get("type") == "ping":
                self._on_frame({"type": "pong", "protocol_version": 1,
                                "request_id": request["request_id"]})
                return
            index = len(self.returned)
            require(index < len(cases), "registered read-only tools send exactly the finite native observations")
            require(request.get("type") == "execute_step" and request.get("step") == cases[index][2]
                    and request.get("expected_revision") == 0,
                    "normal frontend primitive keeps its native revision-zero qualification")
            packet = deepcopy(packets[index])
            # Only request correlation changes; the whole native result and
            # every other producer envelope field remain unchanged.
            packet["request_id"] = request["request_id"]
            self.returned.append(deepcopy(packet))
            self._on_frame(packet)

        def close(self) -> None:
            if self._on_disconnect is not None:
                self._on_disconnect()

    endpoint = PacketEndpoint()
    state_dir = args.out.parent / f"generic-frontend-replay-state-{uuid.uuid4().hex}"
    driver = NativeHeadlessGameplayDriver(
        endpoint=endpoint, command_timeout_seconds=1.0, state_dir=state_dir,
        succession_lifecycle_binding=unknown_succession_lifecycle_binding_v1(),
    )
    reports = []
    try:
        binding = frontend_gui_route_binding_from_capabilities(driver.capabilities())
        require(binding == {"bridge_pid": 1, "connection_generation": 1},
                "production binder accepts only the adopted exact actual .4 frontend identity")
        require(driver.capabilities()["snapshot"] is False,
                "frontend tools operate from their real frontend binding without a fabricated game Snapshot")
        server = create_server(driver)
        registered = {tool.name: tool for tool in await server.list_tools()}
        for index, (filename, tool_name, step, normalize, target, names) in enumerate(cases):
            require(tool_name in registered and not registered[tool_name].input_schema.get("required"),
                    "existing registered frontend observer takes no manufactured caller state")
            response = await server.call_tool(tool_name, {})
            require(getattr(response, "is_error", False) is False,
                    f"registered normal Service observation completed: {filename}")
            observed = response.structured_content
            expected = normalize({**packets[index]["result"], "backend_id": "native-headless"})
            require(observed == expected,
                    "native whole frame survives production driver normalization, Service and registered MCP")
            require(endpoint.returned[index]["result"] == packets[index]["result"],
                    "transport preserves every original native result field")
            if names is None:
                require(observed["route"] == target and observed["backend_id"] == "native-headless",
                        "native route identifies the observed main-menu or CoA page")
            else:
                require(observed["scope_root_name"] == target and observed["root_available"] is True
                        and observed["truncated"] is False and observed["widget_count"] == 2
                        and [row["runtime_name"] for row in observed["widgets"]] == names
                        and observed["widgets"] == packets[index]["result"]["widgets"],
                        "complete native page census retains its exact measured widgets")
                require(observed["read_only"] is True and observed["uses_ocr"] is False
                        and observed["uses_keyboard"] is False and observed["uses_mouse"] is False,
                        "existing tree Service publishes read-only native observations")
            path = args.native_dir / filename
            reports.append({"case": path.stem, "status": "GREEN", "tool": tool_name,
                            "packet": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "observed_route_or_root": target})
        requests = [row for row in endpoint.requests if row["type"] == "execute_step"]
        require(len(requests) == len(cases) and [row["step"] for row in requests] == [row[2] for row in cases],
                "finite registered observations issue no frontend action or extra query")
        require(frontend_gui_route_binding_from_capabilities(driver.capabilities()) == binding
                and driver.capabilities()["snapshot"] is False,
                "normal frontend connection binding remains unchanged after all observations")
        return reports
    finally:
        driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    args.out = args.out or args.native_dir.parent / "GENERIC-FRONTEND-PYTHON-CONSUMER-RESULT.json"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        cases = asyncio.run(consume(args))
        report = {"status": "GREEN", "readiness": "static-ready", "checks": checks,
                  "cases": cases, "frontend_contract_dependency": "089ee actual .4 identity",
                  "game_operations": 0, "sdk_calls_to_game": 0, "window_operations": 0,
                  "live_validation": False, "whole_dll_built": False,
                  "hello_source": "fixture-transport"}
    except Exception as error:
        report = {"status": "RED", "classification": "harness-or-consumer", "checks": checks,
                  "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc(),
                  "game_operations": 0, "sdk_calls_to_game": 0, "window_operations": 0,
                  "live_validation": False}
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
