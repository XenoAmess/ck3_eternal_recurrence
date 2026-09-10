from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import xar_autoplayer.coat_of_arms_resources as resources
from xar_autoplayer.bridge.mcp_server import create_server


class _Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        executable = root / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture-ck3-executable")
        self.executable_sha256 = hashlib.sha256(
            executable.read_bytes()
        ).hexdigest().upper()

        coa = root / "game" / "gfx" / "coat_of_arms"
        patterns = coa / "patterns"
        emblems = coa / "colored_emblems"
        palettes = coa / "color_palettes"
        patterns.mkdir(parents=True)
        emblems.mkdir(parents=True)
        palettes.mkdir(parents=True)
        (patterns / "50_coa_designer_patterns.txt").write_text(
            """
# fixture pattern manifest
pattern_alpha.dds = { colors = 1 }
pattern_hidden.dds = {
    colors = 2
    visible = no
}
pattern_missing.dds = { colors = 3 }
""".strip(),
            encoding="utf-8",
        )
        (patterns / "pattern_alpha.dds").write_bytes(b"pattern-alpha")
        (patterns / "pattern_hidden.dds").write_bytes(b"pattern-hidden")
        (emblems / "50_coa_designer_emblems.txt").write_text(
            """
ce_alpha.dds = { colors = 2 category = animals }
ce_beta.dds = { colors = 1 category = abstract visible = no }
""".strip(),
            encoding="utf-8",
        )
        (emblems / "ce_alpha.dds").write_bytes(b"emblem-alpha")
        (emblems / "ce_beta.dds").write_bytes(b"emblem-beta")
        (palettes / "50_coa_designer_palettes.txt").write_text(
            """
coa_designer_background_colors = {
    red = {}
    blue_light = {}
}
""".strip(),
            encoding="utf-8",
        )

    def query(self, kind: str, **kwargs: object) -> dict[str, object]:
        with patch.object(
            resources,
            "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return resources.query_coat_of_arms_resource_catalog_v1(
                str(self.root), kind, **kwargs
            )


class CoatOfArmsResourceCatalogV1Tests(unittest.TestCase):
    def test_pattern_page_preserves_designer_order_and_asset_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            result = fixture.query("pattern")
        self.assertEqual(result["status"], "indexed")
        self.assertEqual(result["total"], 2)
        self.assertEqual(
            [item["name"] for item in result["items"]],
            ["pattern_alpha.dds", "pattern_missing.dds"],
        )
        first, missing = result["items"]
        self.assertTrue(first["asset_exists"])
        self.assertEqual(
            first["asset_sha256"],
            hashlib.sha256(b"pattern-alpha").hexdigest().upper(),
        )
        self.assertFalse(missing["asset_exists"])
        self.assertIsNone(missing["asset_sha256"])
        provenance = result["provenance"]
        self.assertFalse(provenance["engine_registration_observed"])
        self.assertFalse(provenance["dlc_and_mod_overrides_included"])

    def test_hidden_filter_query_and_pagination_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            first = fixture.query(
                "pattern", visible_only=False, offset=0, limit=1
            )
            hidden = fixture.query(
                "pattern", query="hidden", visible_only=False
            )
        self.assertEqual(first["returned"], 1)
        self.assertTrue(first["has_more"])
        self.assertEqual(first["next_offset"], 1)
        self.assertEqual(hidden["total"], 1)
        self.assertFalse(hidden["items"][0]["visible"])

    def test_emblem_categories_and_palette_are_read_from_vanilla_manifests(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            emblems = fixture.query("colored_emblem", visible_only=False)
            colors = fixture.query("color")
        self.assertEqual(emblems["items"][0]["category"], "animals")
        self.assertEqual(emblems["items"][0]["colors"], 2)
        self.assertEqual(
            [item["name"] for item in colors["items"]],
            ["red", "blue_light"],
        )
        self.assertIsNone(colors["items"][0]["relative_path"])

    def test_wrong_executable_and_invalid_requests_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            with self.assertRaises(resources.CoatOfArmsResourceCatalogError):
                resources.query_coat_of_arms_resource_catalog_v1(
                    str(fixture.root), "pattern"
                )
            with self.assertRaises(ValueError):
                fixture.query("textured_emblem")
            with self.assertRaises(ValueError):
                fixture.query("pattern", limit=201)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CoatOfArmsResourceCatalogV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_closed_schema_and_pages_catalog(
        self,
    ) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            with patch.object(
                resources,
                "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
                fixture.executable_sha256,
            ):
                async with Client(create_server(object())) as client:
                    listed = await client.list_tools()
                    tools = {tool.name: tool for tool in listed.tools}
                    tool = tools[
                        "ck3_query_coat_of_arms_resource_catalog_v1"
                    ]
                    self.assertFalse(tool.input_schema["additionalProperties"])
                    self.assertEqual(
                        set(tool.input_schema["required"]),
                        {"game_directory", "kind"},
                    )
                    result = await client.call_tool(
                        "ck3_query_coat_of_arms_resource_catalog_v1",
                        {
                            "game_directory": str(fixture.root),
                            "kind": "colored_emblem",
                            "query": "alpha",
                            "limit": 10,
                        },
                    )
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content["total"], 1)
                    rejected = await client.call_tool(
                        "ck3_query_coat_of_arms_resource_catalog_v1",
                        {
                            "game_directory": str(fixture.root),
                            "kind": "pattern",
                            "unexpected": True,
                        },
                    )
                    self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
