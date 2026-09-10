from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.coat_of_arms_configured_resources import (
    query_coat_of_arms_configured_resource_catalog_v1,
    read_coat_of_arms_configured_resource_asset_v1,
)
from xar_autoplayer.coat_of_arms_resources import CoatOfArmsResourceCatalogError


def _dds(four_cc: bytes, width: int = 8, height: int = 4) -> bytes:
    header = bytearray(128)
    header[:4] = b"DDS "
    header[4:8] = (124).to_bytes(4, "little")
    header[12:16] = height.to_bytes(4, "little")
    header[16:20] = width.to_bytes(4, "little")
    header[28:32] = (1).to_bytes(4, "little")
    header[84:88] = four_cc
    return bytes(header) + bytes(range(16))


def _write_configuration(user_root: Path, enabled: list[str]) -> None:
    (user_root / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": enabled, "disabled_dlcs": []}),
        encoding="utf-8",
    )


def _write_pattern_mod(
    user_root: Path,
    key: str,
    name: str,
    manifest: str,
    assets: dict[str, bytes],
) -> str:
    content_root = user_root / f"content-{key}"
    pattern_root = content_root / "gfx" / "coat_of_arms" / "patterns"
    pattern_root.mkdir(parents=True)
    (pattern_root / f"50_{key}_patterns.txt").write_text(
        manifest,
        encoding="utf-8",
    )
    for asset_name, data in assets.items():
        (pattern_root / asset_name).write_bytes(data)
    descriptor_root = user_root / "mod"
    descriptor_root.mkdir(exist_ok=True)
    descriptor_name = f"{key}.mod"
    (descriptor_root / descriptor_name).write_text(
        "\n".join(
            (
                f'name="{name}"',
                'tags={ "Graphics" }',
                f'path="{content_root.as_posix()}"',
            )
        ),
        encoding="utf-8",
    )
    return f"mod/{descriptor_name}"


class CoatOfArmsConfiguredResourcesV1Tests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[list[str], bytes]:
        first_dds = _dds(b"DXT1", width=16, height=8)
        first = _write_pattern_mod(
            root,
            "first",
            "First graphics mod",
            "\n".join(
                (
                    "pattern_shared.dds = { colors = 1 category = shared }",
                    "pattern_first.dds = { colors = 2 }",
                    "pattern_hidden.dds = { visible = no }",
                )
            ),
            {
                "pattern_shared.dds": first_dds,
                "pattern_first.dds": _dds(b"DXT1"),
                "pattern_hidden.dds": _dds(b"DXT1"),
            },
        )
        second = _write_pattern_mod(
            root,
            "second",
            "Second graphics mod",
            "pattern_shared.dds = { colors = 3 category = shared }",
            {"pattern_shared.dds": _dds(b"DXT1", width=32, height=16)},
        )
        return [first, second], first_dds

    def test_pages_ordered_candidates_and_marks_name_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            enabled, _ = self.fixture(root)
            _write_configuration(root, enabled)

            result = query_coat_of_arms_configured_resource_catalog_v1(
                str(root),
                "pattern",
                query="shared",
                limit=10,
            )

            self.assertEqual(result["total"], 2)
            self.assertEqual(
                [item["load_order"] for item in result["items"]], [0, 1]
            )
            self.assertTrue(
                all(
                    item["potential_configured_name_conflict"]
                    for item in result["items"]
                )
            )
            self.assertTrue(
                all(
                    item["same_name_configured_candidate_count"] == 2
                    for item in result["items"]
                )
            )
            self.assertFalse(result["provenance"]["resource_merge_applied"])
            self.assertFalse(
                result["provenance"]["load_order_precedence_applied"]
            )

    def test_visibility_filter_and_page_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            enabled, _ = self.fixture(root)
            _write_configuration(root, enabled)

            visible = query_coat_of_arms_configured_resource_catalog_v1(
                str(root), "pattern", offset=1, limit=1
            )
            all_resources = query_coat_of_arms_configured_resource_catalog_v1(
                str(root), "pattern", visible_only=False, limit=10
            )

            self.assertEqual(visible["total"], 3)
            self.assertEqual(visible["returned"], 1)
            self.assertTrue(visible["has_more"])
            self.assertEqual(visible["next_offset"], 2)
            self.assertEqual(all_resources["total"], 4)

    def test_reads_asset_by_opaque_current_configuration_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            enabled, expected = self.fixture(root)
            _write_configuration(root, enabled)
            catalog = query_coat_of_arms_configured_resource_catalog_v1(
                str(root), "pattern", query="shared", limit=10
            )
            candidate_id = catalog["items"][0]["candidate_id"]

            result = read_coat_of_arms_configured_resource_asset_v1(
                str(root), "pattern", candidate_id
            )

            self.assertEqual(result["asset_base64"], base64.b64encode(expected).decode())
            self.assertEqual(result["dds"]["four_cc"], "DXT1")
            self.assertEqual(result["dds"]["width"], 16)
            self.assertFalse(result["provenance"]["resource_merge_applied"])

            _write_configuration(root, list(reversed(enabled)))
            with self.assertRaisesRegex(
                CoatOfArmsResourceCatalogError, "current configuration"
            ):
                read_coat_of_arms_configured_resource_asset_v1(
                    str(root), "pattern", candidate_id
                )

    def test_enumerates_archive_manifest_and_reads_its_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = _dds(b"DXT1", width=64, height=32)
            with zipfile.ZipFile(root / "fixture.zip", "w") as archive:
                archive.writestr(
                    "gfx/coat_of_arms/patterns/50_archive_patterns.txt",
                    "pattern_archive.dds = { colors = 2 }",
                )
                archive.writestr(
                    "gfx/coat_of_arms/patterns/pattern_archive.dds",
                    expected,
                )
            descriptor_root = root / "mod"
            descriptor_root.mkdir()
            (descriptor_root / "archive.mod").write_text(
                'name="Archive fixture"\ntags={ "Graphics" }\narchive="fixture.zip"',
                encoding="utf-8",
            )
            _write_configuration(root, ["mod/archive.mod"])

            result = query_coat_of_arms_configured_resource_catalog_v1(
                str(root), "pattern"
            )

            self.assertEqual(result["total"], 1)
            self.assertEqual(result["provenance"]["archive_mods_skipped"], 0)
            self.assertEqual(result["provenance"]["archive_mods_enumerated"], 1)
            self.assertEqual(result["archive_sources"][0]["load_order"], 0)
            item = result["items"][0]
            self.assertEqual(item["content_kind"], "archive")
            self.assertTrue(item["asset_exists"])
            self.assertIsNone(item["asset_sha256"])
            asset = read_coat_of_arms_configured_resource_asset_v1(
                str(root), "pattern", item["candidate_id"]
            )
            self.assertEqual(
                asset["asset_base64"], base64.b64encode(expected).decode()
            )
            self.assertEqual(asset["dds"]["width"], 64)
            self.assertEqual(asset["provenance"]["content_kind"], "archive")

    @unittest.skipIf(
        importlib.util.find_spec("mcp") is None,
        "optional MCP SDK not installed",
    )
    def test_official_mcp_sdk_exposes_closed_configured_tools(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            enabled, _ = self.fixture(root)
            _write_configuration(root, enabled)

            async def invoke() -> object:
                async with Client(create_server(object())) as client:
                    listed = await client.list_tools()
                    tools = {tool.name: tool for tool in listed.tools}
                    catalog_tool = tools[
                        "ck3_query_coat_of_arms_configured_resource_catalog_v1"
                    ]
                    asset_tool = tools[
                        "ck3_read_coat_of_arms_configured_resource_asset_v1"
                    ]
                    self.assertFalse(
                        catalog_tool.input_schema["additionalProperties"]
                    )
                    self.assertFalse(
                        asset_tool.input_schema["additionalProperties"]
                    )
                    return await client.call_tool(
                        "ck3_query_coat_of_arms_configured_resource_catalog_v1",
                        {
                            "user_directory": str(root),
                            "kind": "pattern",
                            "query": "shared",
                        },
                    )

            result = asyncio.run(invoke())

            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["total"], 2)


if __name__ == "__main__":
    unittest.main()
