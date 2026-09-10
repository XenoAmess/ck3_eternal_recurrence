from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge.mcp_server import create_server
import xar_autoplayer.coat_of_arms_dlc_sources as dlc_sources


class CoatOfArmsInstalledDlcSourcesV1Tests(unittest.TestCase):
    def test_indexes_physical_dlc_candidates_without_claiming_entitlement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "binaries" / "ck3.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"fixture executable")
            executable_sha256 = dlc_sources._sha256(executable)
            dlc_root = root / "game" / "dlc"
            first = dlc_root / "dlc001_fixture"
            second = dlc_root / "dlc002_empty"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "dlc001.dlc").write_text(
                'name="Fixture DLC"\npath="dlc/dlc001_fixture"\nsteam_id="1"',
                encoding="utf-8",
            )
            (second / "dlc002.dlc").write_text(
                'name="Empty DLC"\npath="dlc/dlc002_empty"\nsteam_id="2"',
                encoding="utf-8",
            )
            patterns = first / "gfx" / "coat_of_arms" / "patterns"
            patterns.mkdir(parents=True)
            (patterns / "50_fixture.txt").write_text(
                "pattern_fixture.dds = { colors = 1 }",
                encoding="utf-8",
            )
            (patterns / "pattern_fixture.dds").write_bytes(b"DDS fixture")

            with patch.object(
                dlc_sources,
                "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
                executable_sha256,
            ):
                result = dlc_sources.query_coat_of_arms_installed_dlc_sources_v1(
                    str(root)
                )

        self.assertEqual(result["installed_descriptor_count"], 2)
        self.assertEqual(result["dlc_with_coa_candidates"], 1)
        self.assertEqual(result["coa_txt_file_count"], 1)
        self.assertEqual(result["coa_dds_file_count"], 1)
        self.assertTrue(result["items"][0]["has_coa_candidates"])
        self.assertFalse(result["items"][1]["has_coa_candidates"])
        self.assertFalse(result["provenance"]["store_entitlement_observed"])
        self.assertFalse(result["provenance"]["engine_mount_observed"])


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CoatOfArmsInstalledDlcSourcesV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_a_closed_schema(self) -> None:
        from mcp import Client

        async with Client(create_server(object())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_query_coat_of_arms_installed_dlc_sources_v1"]
            self.assertFalse(tool.input_schema["additionalProperties"])
            self.assertEqual(set(tool.input_schema["required"]), {"game_directory"})
            rejected = await client.call_tool(
                "ck3_query_coat_of_arms_installed_dlc_sources_v1",
                {"game_directory": "missing", "unexpected": True},
            )
            self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
