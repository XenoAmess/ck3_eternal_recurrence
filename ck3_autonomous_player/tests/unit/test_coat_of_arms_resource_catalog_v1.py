from __future__ import annotations

import base64
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
        self.pattern_alpha = self.dds(four_cc=b"DXT1", width=16, height=8)
        (patterns / "pattern_alpha.dds").write_bytes(self.pattern_alpha)
        (patterns / "pattern_hidden.dds").write_bytes(b"pattern-hidden")
        (emblems / "50_coa_designer_emblems.txt").write_text(
            """
ce_alpha.dds = { colors = 2 category = animals }
ce_beta.dds = { colors = 1 category = abstract visible = no }
""".strip(),
            encoding="utf-8",
        )
        self.emblem_alpha = self.dds(four_cc=b"DXT5", width=32, height=16)
        (emblems / "ce_alpha.dds").write_bytes(self.emblem_alpha)
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

        named_colors = root / "game" / "common" / "named_colors"
        named_colors.mkdir(parents=True)
        (named_colors / "default_colors.txt").write_text(
            """
colors = {
    red = hsv { 0.02 0.8 0.45 }
    brown = hsv360 { 21 74 45 }
}
""".strip(),
            encoding="utf-8",
        )
        game_shaders = root / "game" / "gfx" / "FX" / "coat_of_arms"
        jomini_shaders = root / "jomini" / "gfx" / "FX" / "coat_of_arms"
        clausewitz_shaders = root / "clausewitz" / "gfx" / "FX" / "cw"
        game_shaders.mkdir(parents=True)
        jomini_shaders.mkdir(parents=True)
        clausewitz_shaders.mkdir(parents=True)
        for path in (
            clausewitz_shaders / "utility.fxh",
            game_shaders / "coat_of_arms_pattern.shader",
            game_shaders / "coat_of_arms_textured_emblem.shader",
            jomini_shaders / "coat_of_arms_pattern.fxh",
            jomini_shaders / "coat_of_arms_textured_emblem.fxh",
        ):
            path.write_text(f"fixture shader {path.name}\n", encoding="utf-8")
        self.surface_mask = self.dds(four_cc=b"DXT1", width=64, height=64)
        (coa / "coa_mask_texture.dds").write_bytes(self.surface_mask)

    def query(self, kind: str, **kwargs: object) -> dict[str, object]:
        with patch.object(
            resources,
            "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return resources.query_coat_of_arms_resource_catalog_v1(
                str(self.root), kind, **kwargs
            )

    def read(self, kind: str, name: str) -> dict[str, object]:
        with patch.object(
            resources,
            "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return resources.read_coat_of_arms_resource_asset_v1(
                str(self.root), kind, name
            )

    def render_support(self) -> dict[str, object]:
        with patch.object(
            resources,
            "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
            self.executable_sha256,
        ):
            return resources.read_coat_of_arms_render_support_v1(str(self.root))

    @staticmethod
    def dds(*, four_cc: bytes, width: int, height: int) -> bytes:
        data = bytearray(128)
        data[:4] = b"DDS "
        data[4:8] = (124).to_bytes(4, "little")
        data[12:16] = height.to_bytes(4, "little")
        data[16:20] = width.to_bytes(4, "little")
        data[28:32] = (1).to_bytes(4, "little")
        data[84:88] = four_cc
        return bytes(data) + b"fixture-payload"


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
            hashlib.sha256(fixture.pattern_alpha).hexdigest().upper(),
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

    def test_asset_read_is_manifest_owned_and_reports_dds_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            result = fixture.read("colored_emblem", "ce_alpha.dds")
        self.assertEqual(result["schema"], "ck3-coat-of-arms-resource-asset-v1")
        self.assertEqual(result["dds"]["four_cc"], "DXT5")
        self.assertEqual(result["dds"]["width"], 32)
        self.assertEqual(result["dds"]["height"], 16)
        self.assertEqual(base64.b64decode(result["asset_base64"]), fixture.emblem_alpha)
        self.assertFalse(result["provenance"]["engine_registration_observed"])

    def test_asset_read_rejects_non_manifest_names_and_non_asset_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            with self.assertRaises(resources.CoatOfArmsResourceCatalogError):
                fixture.read("pattern", "..\\binaries\\ck3.exe")
            with self.assertRaises(ValueError):
                fixture.read("color", "red")

    def test_render_support_binds_shader_sources_colors_and_surface_mask(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            result = fixture.render_support()
        self.assertEqual(result["schema"], "ck3-coat-of-arms-render-support-v1")
        self.assertEqual(
            base64.b64decode(result["surface_mask"]["asset_base64"]),
            fixture.surface_mask,
        )
        self.assertEqual(result["surface_mask"]["dds"]["four_cc"], "DXT1")
        self.assertEqual(len(result["provenance"]["shader_sources"]), 5)
        colors = {item["name"]: item for item in result["named_colors"]}
        self.assertEqual(colors["red"]["model"], "hsv")
        self.assertEqual(colors["red"]["rgb"], [0.45, 0.1332, 0.09])
        self.assertEqual(colors["brown"]["model"], "hsv360")
        self.assertTrue(
            result["render_contract"]["overlay_function_body_available"]
        )

    def test_render_support_fails_closed_when_a_shader_source_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _Fixture(Path(directory))
            (fixture.root / "jomini" / "gfx" / "FX" / "coat_of_arms"
             / "coat_of_arms_pattern.fxh").unlink()
            with self.assertRaises(resources.CoatOfArmsResourceCatalogError):
                fixture.render_support()


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

                    asset_tool = tools[
                        "ck3_read_coat_of_arms_resource_asset_v1"
                    ]
                    self.assertFalse(asset_tool.input_schema["additionalProperties"])
                    asset = await client.call_tool(
                        "ck3_read_coat_of_arms_resource_asset_v1",
                        {
                            "game_directory": str(fixture.root),
                            "kind": "pattern",
                            "name": "pattern_alpha.dds",
                        },
                    )
                    self.assertFalse(asset.is_error)
                    self.assertEqual(
                        asset.structured_content["dds"]["four_cc"], "DXT1"
                    )
                    support = await client.call_tool(
                        "ck3_read_coat_of_arms_render_support_v1",
                        {"game_directory": str(fixture.root)},
                    )
                    self.assertFalse(support.is_error)
                    self.assertEqual(
                        support.structured_content["surface_mask"]["dds"]["width"],
                        64,
                    )


if __name__ == "__main__":
    unittest.main()
