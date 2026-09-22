from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.ck3_save_artifacts import (  # noqa: E402
    Ck3ProfileArtifactInspector,
    SaveArtifactError,
    require_seedable_ck3_save_v1,
)
class Ck3SaveArtifactTests(unittest.TestCase):
    def test_inventory_distinguishes_zip_raw_and_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile"
            save_dir = profile / "save games"
            save_dir.mkdir(parents=True)
            with zipfile.ZipFile(save_dir / "zipped.ck3", "w") as archive:
                archive.writestr("meta", b"meta")
                archive.writestr("gamestate", b"state")
            (save_dir / "raw.ck3").write_bytes(
                b"SAV0100\nmeta_data={\n\tversion=\"fixture\"\n}\n"
            )
            (save_dir / "binary.ck3").write_bytes(
                b"SAV0101e741a8ef0000864d\n"
                b"U1\x01\x00\x03\x00\x8f\x05\x01\x00"
                b"opaque-binary-body"
            )
            (profile / "last_save.ck3").write_bytes(b"not a CK3 save")

            result = Ck3ProfileArtifactInspector(profile).inspect_save_artifacts_v1()

            self.assertEqual(result["artifact_count"], 4)
            rows = {row["name"]: row for row in result["artifacts"]}
            self.assertEqual(rows["zipped.ck3"]["format"], "zip-ck3")
            self.assertTrue(rows["zipped.ck3"]["zip_valid"])
            self.assertTrue(rows["zipped.ck3"]["has_gamestate"])
            self.assertEqual(rows["zipped.ck3"]["integrity_scope"], "zip-crc")
            self.assertEqual(rows["raw.ck3"]["format"], "raw-ck3")
            self.assertEqual(rows["raw.ck3"]["integrity_scope"], "header-only")
            self.assertEqual(rows["raw.ck3"]["raw_header_kind"], "text")
            self.assertIsNone(rows["raw.ck3"]["integrity_ok"])
            self.assertEqual(rows["binary.ck3"]["format"], "raw-ck3")
            self.assertEqual(rows["binary.ck3"]["integrity_scope"], "header-only")
            self.assertTrue(rows["binary.ck3"]["raw_header_valid"])
            self.assertEqual(rows["binary.ck3"]["raw_header_kind"], "binary")
            self.assertEqual(rows["last_save.ck3"]["format"], "unknown")
            self.assertEqual(rows["last_save.ck3"]["integrity_scope"], "none")
            self.assertFalse(result["path_argument_accepted"])

    def test_seed_contract_accepts_raw_and_rejects_zip_without_gamestate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile"
            save_dir = profile / "save games"
            save_dir.mkdir(parents=True)
            (save_dir / "raw.ck3").write_bytes(b"SAV0100\nmeta_data={\n}\n")
            (save_dir / "binary.ck3").write_bytes(
                b"SAV0101adfe46810000864d\n"
                b"U1\x01\x00\x03\x00\x8f\x05\x01\x00"
            )
            with zipfile.ZipFile(save_dir / "missing.ck3", "w") as archive:
                archive.writestr("meta", b"only-meta")
            rows = {
                row["name"]: row
                for row in Ck3ProfileArtifactInspector(profile)
                .inspect_save_artifacts_v1()["artifacts"]
            }
            require_seedable_ck3_save_v1(rows["raw.ck3"])
            require_seedable_ck3_save_v1(rows["binary.ck3"])
            with self.assertRaisesRegex(SaveArtifactError, "contain gamestate"):
                require_seedable_ck3_save_v1(rows["missing.ck3"])


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class Ck3SaveArtifactMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_pathless_tool(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.driver import DevelopmentReportDriver
        from xar_autoplayer.bridge.mcp_server import create_server

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            save_dir = profile / "save games"
            save_dir.mkdir(parents=True)
            (save_dir / "fixture.ck3").write_bytes(
                b"SAV0100\nmeta_data={\n}\t\n"
            )
            server = create_server(
                DevelopmentReportDriver(root),
                profile_dir=profile,
            )
            async with Client(server) as client:
                listed = await client.list_tools()
                tools = {tool.name: tool for tool in listed.tools}
                self.assertIn("ck3_inspect_save_artifacts_v1", tools)
                self.assertTrue(
                    tools[
                        "ck3_inspect_save_artifacts_v1"
                    ].annotations.read_only_hint
                )
                schema = tools["ck3_inspect_save_artifacts_v1"].input_schema
                self.assertEqual(schema.get("properties"), {})
                self.assertFalse(schema.get("additionalProperties", True))
                called = await client.call_tool("ck3_inspect_save_artifacts_v1", {})
                self.assertFalse(called.is_error)
                self.assertEqual(called.structured_content["artifact_count"], 1)
                rejected = await client.call_tool(
                    "ck3_inspect_save_artifacts_v1",
                    {"path": str(root)},
                )
                self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
