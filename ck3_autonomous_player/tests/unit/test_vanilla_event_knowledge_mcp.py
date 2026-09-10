from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_list_vanilla_event_evidence_v1,
    _ck3_list_vanilla_event_knowledge_v1,
    _ck3_query_vanilla_event_knowledge_v1,
    _ck3_query_vanilla_event_source_provenance_v1,
    _ck3_read_vanilla_event_evidence_v1,
    create_server,
)
from xar_autoplayer.vanilla_events import (  # noqa: E402
    ck3_list_vanilla_event_knowledge_v1,
    list_vanilla_event_evidence_v1,
    portable_event_keys_v1,
    query_vanilla_event_knowledge_v1,
    query_vanilla_event_source_provenance_v1,
    read_vanilla_event_evidence_v1,
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

    def test_discovery_evidence_and_source_helpers_are_offline(self) -> None:
        expected_knowledge = ck3_list_vanilla_event_knowledge_v1(
            limit=2,
            portable_event_keys=portable_event_keys_v1(),
        )
        knowledge = _ck3_list_vanilla_event_knowledge_v1(limit=2)
        evidence = _ck3_list_vanilla_event_evidence_v1(limit=1)
        evidence_id = evidence["evidence"][0]["evidence_id"]

        self.assertEqual(knowledge, expected_knowledge)
        self.assertEqual(evidence, list_vanilla_event_evidence_v1(limit=1))
        self.assertEqual(
            _ck3_read_vanilla_event_evidence_v1(
                evidence_id,
                max_bytes=32,
            ),
            read_vanilla_event_evidence_v1(evidence_id, max_bytes=32),
        )
        self.assertEqual(
            _ck3_query_vanilla_event_source_provenance_v1(
                EVENT_DEFINITION_KEY,
            ),
            query_vanilla_event_source_provenance_v1(EVENT_DEFINITION_KEY),
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

    async def test_mcp_lists_and_calls_all_portable_read_only_tools(self) -> None:
        from mcp import Client

        expected_names = {
            "ck3_query_vanilla_event_knowledge_v1",
            "ck3_list_vanilla_event_knowledge_v1",
            "ck3_list_vanilla_event_evidence_v1",
            "ck3_read_vanilla_event_evidence_v1",
            "ck3_query_vanilla_event_source_provenance_v1",
        }
        async with Client(create_server(_OfflineDriver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            knowledge = await client.call_tool(
                "ck3_list_vanilla_event_knowledge_v1",
                {"query": "health.1010", "limit": 1},
            )
            evidence = await client.call_tool(
                "ck3_list_vanilla_event_evidence_v1",
                {"limit": 1},
            )
            evidence_payload = evidence.structured_content or {}
            evidence_id = evidence_payload["evidence"][0]["evidence_id"]
            read = await client.call_tool(
                "ck3_read_vanilla_event_evidence_v1",
                {"evidence_id": evidence_id, "max_bytes": 32},
            )
            source = await client.call_tool(
                "ck3_query_vanilla_event_source_provenance_v1",
                {"key": EVENT_DEFINITION_KEY},
            )
            rejected = await client.call_tool(
                "ck3_list_vanilla_event_evidence_v1",
                {"limit": 1, "bundle_root": "Z:/must-not-be-exposed"},
            )

        self.assertTrue(expected_names.issubset(tools))
        self.assertFalse(knowledge.is_error)
        self.assertEqual(knowledge.structured_content["status"], "available")
        self.assertIsNotNone(knowledge.structured_content["dataset_sha256"])
        self.assertFalse(evidence.is_error)
        self.assertIsNotNone(evidence_payload["dataset_sha256"])
        self.assertFalse(read.is_error)
        self.assertEqual(read.structured_content["evidence_id"], evidence_id)
        self.assertLessEqual(read.structured_content["content_bytes"], 32)
        self.assertIsInstance(
            read.structured_content[
                "historical_artifact_may_contain_nonportable_locators"
            ],
            bool,
        )
        self.assertFalse(source.is_error)
        self.assertTrue(
            source.structured_content["caller_candidates_are_lexical_only"]
        )
        self.assertTrue(rejected.is_error)
        self.assertNotIn(
            "bundle_root",
            tools["ck3_list_vanilla_event_evidence_v1"].input_schema[
                "properties"
            ],
        )


if __name__ == "__main__":
    unittest.main()
