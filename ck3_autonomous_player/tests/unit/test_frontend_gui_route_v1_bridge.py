from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from xar_autoplayer.bridge.frontend_gui_route_contract import (
    ACTIVATE_FRONTEND_NEW_GAME_V1_CAPABILITY,
    ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
    QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
    QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
    normalize_frontend_gui_route_v1,
    normalize_frontend_new_game_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


def _route(route: str) -> dict[str, object]:
    return {
        "schema": "ck3-frontend-gui-route-v1",
        "schema_version": 1,
        "step": QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
        "accepted": True,
        "route": route,
        "backend_id": "native-headless",
    }


def _action() -> dict[str, object]:
    return {
        "schema": "ck3-frontend-gui-action-v1",
        "schema_version": 1,
        "step": ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
        "accepted": True,
        "status": "verified",
        "action": "open_new_game",
        "input_backend": "native_gui_semantic_activation",
        "uses_ocr": False,
        "uses_keyboard": False,
        "uses_mouse": False,
        "before": _route("main_menu"),
        "acknowledgement": {
            "step": ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
            "accepted": True,
            "status": "acknowledged_verification_pending",
        },
        "after": _route("bookmarks"),
        "postcondition_verified": True,
        "backend_id": "native-headless",
    }


class _FrontendDriver:
    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "injected-dll-named-pipe",
            "snapshot": False,
            "bridge_capabilities": [
                QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
                ACTIVATE_FRONTEND_NEW_GAME_V1_CAPABILITY,
            ],
        }

    def query_frontend_gui_route_v1(self) -> dict[str, object]:
        return _route("main_menu")

    def activate_frontend_new_game_v1(self) -> dict[str, object]:
        return _action()


class FrontendGuiRouteV1ContractTests(unittest.TestCase):
    def test_route_and_action_require_semantic_postcondition(self) -> None:
        normalized_route = normalize_frontend_gui_route_v1(
            {
                "step": QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
                "accepted": True,
                "status": "coat_of_arms_designer",
                "backend_id": "native-headless",
            }
        )
        self.assertEqual(normalized_route["route"], "coat_of_arms_designer")

        normalized_action = normalize_frontend_new_game_v1(
            {
                "step": ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
                "accepted": True,
                "status": "acknowledged_verification_pending",
                "backend_id": "native-headless",
            },
            before=_route("main_menu"),
            after=_route("bookmarks"),
        )
        self.assertTrue(normalized_action["postcondition_verified"])
        self.assertFalse(normalized_action["uses_ocr"])
        self.assertFalse(normalized_action["uses_keyboard"])
        self.assertFalse(normalized_action["uses_mouse"])

        with self.assertRaisesRegex(ValueError, "postcondition"):
            normalize_frontend_new_game_v1(
                {
                    "step": ACTIVATE_FRONTEND_NEW_GAME_V1_STEP,
                    "accepted": True,
                    "status": "acknowledged_verification_pending",
                },
                before=_route("main_menu"),
                after=_route("ruler_designer"),
            )

    def test_native_driver_query_uses_revision_zero_frontend_transport(
        self,
    ) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        calls: list[dict[str, object]] = []

        def execute(
            step: str,
            *,
            expected_revision: int,
            required_capability: str,
            allow_frontend_revision_zero: bool,
        ) -> dict[str, object]:
            calls.append(
                {
                    "step": step,
                    "expected_revision": expected_revision,
                    "required_capability": required_capability,
                    "allow_frontend_revision_zero": (
                        allow_frontend_revision_zero
                    ),
                }
            )
            return {
                "step": step,
                "accepted": True,
                "status": "main_menu",
                "backend_id": "native-headless",
            }

        driver._execute_primitive_step = execute
        self.assertEqual(driver.query_frontend_gui_route_v1()["route"], "main_menu")
        self.assertEqual(
            calls,
            [
                {
                    "step": QUERY_FRONTEND_GUI_ROUTE_V1_STEP,
                    "expected_revision": 0,
                    "required_capability": QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
                    "allow_frontend_revision_zero": True,
                }
            ],
        )

    def test_service_preserves_zero_input_native_contract(self) -> None:
        service = GameplayBridgeService(_FrontendDriver())
        self.assertEqual(service.query_frontend_gui_route_v1()["route"], "main_menu")
        self.assertTrue(
            service.activate_frontend_new_game_v1()["postcondition_verified"]
        )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class FrontendGuiRouteV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_closed_zero_input_tools(self) -> None:
        from mcp import Client

        async with Client(create_server(_FrontendDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            for name in (
                "ck3_query_frontend_gui_route_v1",
                "ck3_activate_frontend_new_game_v1",
            ):
                self.assertEqual(tools[name].input_schema.get("required", []), [])
                self.assertFalse(tools[name].input_schema["additionalProperties"])
            query = await client.call_tool("ck3_query_frontend_gui_route_v1", {})
            self.assertFalse(query.is_error)
            self.assertEqual(query.structured_content["route"], "main_menu")
            action = await client.call_tool(
                "ck3_activate_frontend_new_game_v1", {}
            )
            self.assertFalse(action.is_error)
            self.assertTrue(action.structured_content["postcondition_verified"])


if __name__ == "__main__":
    unittest.main()
