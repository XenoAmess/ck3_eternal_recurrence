from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.coat_of_arms_load_configuration import (
    query_coat_of_arms_load_configuration_v1,
)
from xar_autoplayer.coat_of_arms_resources import CoatOfArmsResourceCatalogError


def _write_configuration(user_root: Path, enabled: list[str]) -> bytes:
    payload = json.dumps(
        {"enabled_mods": enabled, "disabled_dlcs": ["dlc/test"]},
        separators=(",", ":"),
    ).encode()
    (user_root / "dlc_load.json").write_bytes(payload)
    return payload


def _write_directory_mod(user_root: Path) -> Path:
    content_root = user_root / "fixture-mod"
    pattern_root = content_root / "gfx" / "coat_of_arms" / "patterns"
    emblem_root = content_root / "gfx" / "coat_of_arms" / "colored_emblems"
    definition_root = (
        content_root / "common" / "coat_of_arms" / "coat_of_arms"
    )
    pattern_root.mkdir(parents=True)
    emblem_root.mkdir(parents=True)
    definition_root.mkdir(parents=True)
    (pattern_root / "50_fixture_patterns.txt").write_text(
        "fixture = {}", encoding="utf-8"
    )
    (pattern_root / "pattern_fixture.dds").write_bytes(b"DDS fixture")
    (emblem_root / "50_fixture_emblems.txt").write_text(
        "fixture = {}", encoding="utf-8"
    )
    (emblem_root / "ce_fixture.dds").write_bytes(b"DDS fixture")
    (definition_root / "fixture_coa.txt").write_text(
        "fixture = {}", encoding="utf-8"
    )

    descriptor_root = user_root / "mod"
    descriptor_root.mkdir()
    descriptor = descriptor_root / "fixture.mod"
    descriptor.write_text(
        "\n".join(
            (
                'version="1.0"',
                'tags={ "Gameplay" "Utilities" }',
                'name="Fixture CoA"',
                f'path="{content_root.as_posix()}"',
                'replace_path="gfx/coat_of_arms/patterns"',
                'remote_file_id="123"',
            )
        ),
        encoding="utf-8",
    )
    return descriptor


class CoatOfArmsLoadConfigurationV1Tests(unittest.TestCase):
    def test_projects_ordered_directory_mod_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            user_root = Path(directory)
            descriptor = _write_directory_mod(user_root)
            load_bytes = _write_configuration(user_root, ["mod/fixture.mod"])

            result = query_coat_of_arms_load_configuration_v1(str(user_root))

            self.assertEqual(
                result["schema"], "ck3-coat-of-arms-load-configuration-v1"
            )
            self.assertEqual(result["enabled_mod_count"], 1)
            self.assertEqual(result["disabled_dlcs"], ["dlc/test"])
            mod = result["mods"][0]
            self.assertEqual(mod["load_order"], 0)
            self.assertEqual(
                mod["descriptor_sha256"],
                hashlib.sha256(descriptor.read_bytes()).hexdigest().upper(),
            )
            self.assertEqual(mod["name"], "Fixture CoA")
            self.assertEqual(mod["version"], "1.0")
            self.assertEqual(mod["remote_file_id"], "123")
            self.assertEqual(mod["content_kind"], "directory")
            self.assertTrue(mod["content_root_exists"])
            self.assertEqual(
                mod["coa_replace_paths"], ["gfx/coat_of_arms/patterns"]
            )
            self.assertEqual(
                mod["resource_candidates"]["pattern_assets"],
                {
                    "relative_directory": "gfx/coat_of_arms/patterns",
                    "directory_exists": True,
                    "txt": [
                        "gfx/coat_of_arms/patterns/50_fixture_patterns.txt"
                    ],
                    "dds_count": 1,
                },
            )
            self.assertEqual(
                mod["resource_candidates"]["coat_of_arms_definitions"]["txt"],
                ["common/coat_of_arms/coat_of_arms/fixture_coa.txt"],
            )
            provenance = result["provenance"]
            self.assertEqual(
                provenance["load_configuration_sha256"],
                hashlib.sha256(load_bytes).hexdigest().upper(),
            )
            self.assertFalse(provenance["launcher_database_used"])
            self.assertFalse(provenance["engine_mount_observed"])
            self.assertFalse(provenance["resource_merge_applied"])

    def test_empty_configuration_does_not_infer_launcher_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            user_root = Path(directory)
            _write_configuration(user_root, [])

            result = query_coat_of_arms_load_configuration_v1(str(user_root))

            self.assertEqual(result["enabled_mod_count"], 0)
            self.assertEqual(result["mods"], [])
            self.assertFalse(result["provenance"]["launcher_database_used"])

    def test_rejects_descriptor_paths_outside_user_directory(self) -> None:
        for registry_path in ("../escape.mod", "C:/absolute.mod"):
            with self.subTest(registry_path=registry_path):
                with tempfile.TemporaryDirectory() as directory:
                    user_root = Path(directory)
                    _write_configuration(user_root, [registry_path])

                    with self.assertRaises(CoatOfArmsResourceCatalogError):
                        query_coat_of_arms_load_configuration_v1(str(user_root))

    def test_rejects_descriptor_with_both_path_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            user_root = Path(directory)
            content_root = user_root / "content"
            content_root.mkdir()
            descriptor_root = user_root / "mod"
            descriptor_root.mkdir()
            (descriptor_root / "ambiguous.mod").write_text(
                f'path="{content_root.as_posix()}"\narchive="fixture.zip"',
                encoding="utf-8",
            )
            _write_configuration(user_root, ["mod/ambiguous.mod"])

            with self.assertRaisesRegex(
                CoatOfArmsResourceCatalogError, "exactly one"
            ):
                query_coat_of_arms_load_configuration_v1(str(user_root))

    @unittest.skipIf(
        importlib.util.find_spec("mcp") is None,
        "optional MCP SDK not installed",
    )
    def test_official_mcp_sdk_exposes_load_configuration(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as directory:
            user_root = Path(directory)
            _write_configuration(user_root, [])

            async def invoke() -> object:
                async with Client(create_server(object())) as client:
                    listed = await client.list_tools()
                    tool = next(
                        item
                        for item in listed.tools
                        if item.name
                        == "ck3_query_coat_of_arms_load_configuration_v1"
                    )
                    self.assertFalse(tool.input_schema["additionalProperties"])
                    return await client.call_tool(
                        "ck3_query_coat_of_arms_load_configuration_v1",
                        {"user_directory": str(user_root)},
                    )

            result = asyncio.run(invoke())

            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["enabled_mod_count"], 0)
            self.assertFalse(
                result.structured_content["provenance"]["engine_mount_observed"]
            )


if __name__ == "__main__":
    unittest.main()
