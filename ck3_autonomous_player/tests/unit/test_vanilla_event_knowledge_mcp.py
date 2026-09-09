from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_vanilla_event_knowledge_v1,
    create_server,
)
from xar_autoplayer.vanilla_events import (  # noqa: E402
    query_vanilla_event_knowledge_v1,
)


EVENT_DEFINITION_KEY = "prison_notification.2002"
CK3_BUILD = "1.19.0.6"


class _OfflineDriver:
    """Prove the knowledge tool never consults a gameplay backend."""

    @staticmethod
    def _unexpected() -> dict[str, object]:
        raise AssertionError("offline vanilla-event knowledge touched CK3")

    def capabilities(self) -> dict[str, object]:
        return self._unexpected()

    def take_snapshot(self) -> dict[str, object]:
        return self._unexpected()

    def execute_step(
        self,
        step: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        del step, expected_revision
        return self._unexpected()

    def wait_for_change(
        self,
        after_revision: int,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        del after_revision, timeout_seconds
        return self._unexpected()


class VanillaEventKnowledgeHelperTests(unittest.TestCase):
    def test_helper_returns_the_registry_response_without_ck3(self) -> None:
        expected = query_vanilla_event_knowledge_v1(
            EVENT_DEFINITION_KEY,
            ck3_build=CK3_BUILD,
        )

        self.assertEqual(
            _ck3_query_vanilla_event_knowledge_v1(EVENT_DEFINITION_KEY),
            expected,
        )
        self.assertEqual(
            _ck3_query_vanilla_event_knowledge_v1(
                EVENT_DEFINITION_KEY,
                ck3_build=CK3_BUILD,
            ),
            expected,
        )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class VanillaEventKnowledgeMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_lists_and_calls_closed_offline_query(self) -> None:
        from mcp import Client

        expected = query_vanilla_event_knowledge_v1(
            EVENT_DEFINITION_KEY,
            ck3_build=CK3_BUILD,
        )
        async with Client(create_server(_OfflineDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_query_vanilla_event_knowledge_v1"]
            result = await client.call_tool(
                "ck3_query_vanilla_event_knowledge_v1",
                {"event_definition_key": EVENT_DEFINITION_KEY},
            )
            rejected = await client.call_tool(
                "ck3_query_vanilla_event_knowledge_v1",
                {
                    "event_definition_key": EVENT_DEFINITION_KEY,
                    "ck3_build": CK3_BUILD,
                    "unexpected": True,
                },
            )

        self.assertEqual(
            {"event_definition_key", "ck3_build"},
            set(tool.input_schema["properties"]),
        )
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content, expected)
        self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
