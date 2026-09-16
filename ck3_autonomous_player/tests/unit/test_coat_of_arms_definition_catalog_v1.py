from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import xar_autoplayer.coat_of_arms_definitions as definitions
from xar_autoplayer.bridge.mcp_server import create_server


class _Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        executable = root / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture-ck3-executable")
        self.executable_sha256 = hashlib.sha256(executable.read_bytes()).hexdigest().upper()
        source = root / "game" / "common" / "coat_of_arms" / "coat_of_arms"
        source.mkdir(parents=True)
        (source / "01_base.txt").write_text(
            """
@x = 0.25
c_base = {
    pattern = "pattern_solid.dds"
    color1 = red
    colored_emblem = {
        texture = "ce_block_02.dds"
        instance = { position = { @x 0.5 } scale = { 1 1 } }
    }
}
d_alias = c_base
d_chain = d_alias
d_cycle_one = d_cycle_two
d_cycle_two = d_cycle_one
c_duplicate = { color1 = blue }
""".strip(),
            encoding="utf-8",
        )
        (source / "02_override.txt").write_text(
            """
# Static catalog must surface both candidates and never guess a winner.
c_duplicate = { color1 = red }
c_quoted = { pattern = "pattern_with_#_literal.dds" }
""".strip(),
            encoding="utf-8",
        )

    def query(self, **kwargs: object) -> dict[str, object]:
        with patch.object(
            definitions,
            "CK3_COAT_OF_ARMS_DEFINITION_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return definitions.query_coat_of_arms_definition_catalog_v1(
                str(self.root), **kwargs
            )

    def read(self, key: str) -> dict[str, object]:
        with patch.object(
            definitions,
            "CK3_COAT_OF_ARMS_DEFINITION_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return definitions.read_coat_of_arms_definition_v1(str(self.root), key)


class CoatOfArmsDefinitionCatalogV1Tests(unittest.TestCase):
    def test_catalog_handles_anonymous_vector_blocks_and_excludes_variables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            result = fixture.query(query="base")
        self.assertEqual(result["schema"], "ck3-coat-of-arms-definition-catalog-v1")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["key"], "c_base")
        self.assertEqual(result["items"][0]["kinds"], ["block"])
        self.assertFalse(result["provenance"]["engine_mount_observed"])
        self.assertFalse(result["provenance"]["engine_parent_composition_observed"])

    def test_read_resolves_only_an_unambiguous_alias_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            result = fixture.read("d_chain")
        self.assertEqual(result["status"], "resolved_block")
        self.assertEqual(result["resolved_key"], "c_base")
        self.assertEqual(
            [item["key"] for item in result["alias_chain"]],
            ["d_chain", "d_alias", "c_base"],
        )
        source = result["resolved_definition"]["source_utf8"]
        self.assertIn("position = { @x 0.5 }", source)
        self.assertFalse(result["provenance"]["variables_expanded"])
        self.assertFalse(result["provenance"]["parent_inheritance_materialized"])

    def test_duplicate_cycle_missing_and_invalid_key_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            duplicate = fixture.read("c_duplicate")
            cycle = fixture.read("d_cycle_one")
            missing = fixture.read("c_missing")
            with self.assertRaises(ValueError):
                fixture.read("../ck3.exe")
        self.assertEqual(duplicate["status"], "ambiguous_source_candidates")
        self.assertEqual(duplicate["direct_candidate_count"], 2)
        self.assertEqual(cycle["status"], "alias_cycle")
        self.assertEqual(missing["status"], "missing")

    def test_pagination_and_receipts_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            first = fixture.query(offset=0, limit=2)
            second = fixture.query(offset=2, limit=2)
        self.assertEqual(first["returned"], 2)
        self.assertTrue(first["has_more"])
        self.assertEqual(first["next_offset"], 2)
        self.assertEqual(second["offset"], 2)
        self.assertEqual(len(first["provenance"]["source_manifest_sha256"]), 64)
        self.assertEqual(first["provenance"]["source_files"], 2)

    @unittest.skipUnless(
        os.environ.get("CK3_GAME_DIRECTORY"),
        "set CK3_GAME_DIRECTORY for the exact-build source integration",
    )
    def test_exact_build_indexes_and_resolves_real_base_definitions(self) -> None:
        game_directory = os.environ["CK3_GAME_DIRECTORY"]
        england = definitions.read_coat_of_arms_definition_v1(
            game_directory, "k_england"
        )
        agder = definitions.read_coat_of_arms_definition_v1(
            game_directory, "d_agder"
        )
        queried = definitions.query_coat_of_arms_definition_catalog_v1(
            game_directory, query="england", limit=10
        )
        self.assertEqual(england["status"], "resolved_block")
        self.assertIn('pattern = "pattern_solid.dds"', england["resolved_definition"]["source_utf8"])
        self.assertEqual(agder["status"], "resolved_block")
        self.assertEqual(agder["alias_chain"][0]["alias_target"], "c_agder")
        self.assertGreaterEqual(queried["total"], 1)
        self.assertGreater(queried["provenance"]["source_files"], 0)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class CoatOfArmsDefinitionCatalogV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_closed_schemas_and_reads_alias(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            with patch.object(
                definitions,
                "CK3_COAT_OF_ARMS_DEFINITION_V1_EXE_SHA256",
                fixture.executable_sha256,
            ):
                async with Client(create_server(object())) as client:
                    listed = await client.list_tools()
                    tools = {tool.name: tool for tool in listed.tools}
                    query_tool = tools["ck3_query_coat_of_arms_definition_catalog_v1"]
                    read_tool = tools["ck3_read_coat_of_arms_definition_v1"]
                    self.assertFalse(query_tool.input_schema["additionalProperties"])
                    self.assertFalse(read_tool.input_schema["additionalProperties"])
                    result = await client.call_tool(
                        "ck3_read_coat_of_arms_definition_v1",
                        {"game_directory": str(fixture.root), "key": "d_chain"},
                    )
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content["resolved_key"], "c_base")
                    rejected = await client.call_tool(
                        "ck3_query_coat_of_arms_definition_catalog_v1",
                        {"game_directory": str(fixture.root), "unexpected": True},
                    )
                    self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
