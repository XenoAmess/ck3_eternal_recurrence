"""No-game contract tests for the private transcript-free native MCP read."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mcp import Client
from xar_autoplayer.bridge.mcp_server import create_server, parser


class SemanticDriver:
    def __init__(self, frame: dict[str, object], *, enabled: bool) -> None:
        self.frame = frame
        self.allow_private_semantic_snapshot_readonly = enabled
        self.semantic_calls = 0
        self.public_calls = 0

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        self.semantic_calls += 1
        return self.frame

    def take_snapshot(self) -> dict[str, object]:
        self.public_calls += 1
        return {**self.frame, "native_command_history": [{"index": 1}]}


class PrivateSemanticSnapshotMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_private_tool_is_opt_in_and_matches_public_semantics(self) -> None:
        frame = {"snapshot_id": "native:8", "revision": 9, "native_revision": 8,
                 "date_raw": 53219928, "paused": True, "map_ready": True,
                 "played_character": {"character_id": 29829},
                 "active_wars": [{"war_id": 16777231}],
                 "army_strengths": [{"army_id": 83886367}]}
        driver = SemanticDriver(frame, enabled=False)
        async with Client(create_server(driver)) as client:
            tools = await client.list_tools()
            self.assertNotIn("ck3_take_semantic_snapshot_private_v1",
                             [tool.name for tool in tools.tools])
        driver.allow_private_semantic_snapshot_readonly = True
        async with Client(create_server(driver)) as client:
            tools = await client.list_tools()
            compact_tool = next(tool for tool in tools.tools
                                if tool.name == "ck3_take_semantic_snapshot_private_v1")
            self.assertTrue(compact_tool.annotations.read_only_hint)
            diagnostics_tool = next(tool for tool in tools.tools
                                    if tool.name == "ck3_get_bridge_diagnostics")
            self.assertTrue(diagnostics_tool.annotations.read_only_hint)
            compact = await client.call_tool("ck3_take_semantic_snapshot_private_v1", {})
            public = await client.call_tool("ck3_take_snapshot", {})
        self.assertFalse(compact.is_error)
        self.assertEqual(compact.structured_content, frame)
        self.assertEqual({key: value for key, value in public.structured_content.items()
                          if key != "native_command_history"}, frame)
        self.assertNotIn("native_command_history", compact.structured_content)
        self.assertEqual(driver.semantic_calls, 1)
        self.assertEqual(driver.public_calls, 1)

    async def test_private_tool_rejects_transcript_and_oversize_frame(self) -> None:
        driver = SemanticDriver({"native_command_history": []}, enabled=True)
        async with Client(create_server(driver)) as client:
            transcript = await client.call_tool("ck3_take_semantic_snapshot_private_v1", {})
        self.assertTrue(transcript.is_error)
        driver.frame = {"snapshot_id": "native:8", "oversize": "x" * (8 * 1024 * 1024)}
        async with Client(create_server(driver)) as client:
            oversize = await client.call_tool("ck3_take_semantic_snapshot_private_v1", {})
        self.assertTrue(oversize.is_error)

    def test_flag_is_explicit(self) -> None:
        self.assertFalse(parser().parse_args([]).private_semantic_snapshot_readonly)
        self.assertTrue(parser().parse_args([
            "--private-semantic-snapshot-readonly"
        ]).private_semantic_snapshot_readonly)


if __name__ == "__main__":
    unittest.main()
