from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.ck3_runtime_diagnostics import (  # noqa: E402
    Ck3RuntimeDiagnosticsInspector,
)


class Ck3RuntimeDiagnosticsTests(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "profile"
        logs = profile / "logs"
        logs.mkdir(parents=True)
        (logs / "error.log").write_text(
            "[12:00:00][E] Error in character 123 at 0xABC\n"
            "[12:00:01][E] Error in character 456 at 0xDEF\n"
            "[12:00:02][F] Fatal marker\n",
            encoding="utf-8",
        )
        (logs / "debug.log").write_text(
            "[12:00:00][W] Game initialization started\n"
            "Main menu loaded\n",
            encoding="utf-8",
        )
        package = profile / "crashes" / "ck3_20260923_120000"
        (package / "logs").mkdir(parents=True)
        (package / "exception.txt").write_text(
            "Unhandled Exception C0000005\nStack Trace:\nframe one\nframe two\n",
            encoding="utf-8",
        )
        (package / "meta.yml").write_text(
            'AppName: "CK3"\nAppVersion: "1.19.0.6"\nMod_1: "Fixture"\n',
            encoding="utf-8",
        )
        (package / "logs" / "error.log").write_bytes(b"crash error")
        return profile

    def test_fixed_logs_severity_fingerprints_and_crash_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = self._profile(Path(temporary))
            result = Ck3RuntimeDiagnosticsInspector(
                profile
            ).query_engine_diagnostics_v1(fingerprint_limit=10, tail_limit=2)

            error = result["logs"]["error.log"]
            self.assertEqual(
                error["engine_severity_records"],
                {"fatal": 1, "error": 2, "warning": 0},
            )
            self.assertEqual(error["unique_fingerprint_count"], 2)
            self.assertEqual(error["fingerprints"][0]["occurrences"], 2)
            self.assertIn("not independent bugs", error["severity_count_semantics"])
            self.assertEqual(len(error["tail"]), 2)
            self.assertEqual(result["crashes"]["package_count"], 1)
            crash = result["crashes"]["packages"][0]
            self.assertEqual(
                crash["exception"]["headline"], "Unhandled Exception C0000005"
            )
            self.assertEqual(crash["exception"]["stack_trace"], ["frame one", "frame two"])
            self.assertEqual(crash["meta"]["AppVersion"], "1.19.0.6")
            self.assertEqual(crash["mods"], ["Fixture"])
            self.assertFalse(result["path_argument_accepted"])
            self.assertFalse(result["regex_argument_accepted"])

    def test_limits_reject_unbounded_requests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = self._profile(Path(temporary))
            inspector = Ck3RuntimeDiagnosticsInspector(profile)
            with self.assertRaisesRegex(ValueError, "fingerprint_limit"):
                inspector.query_engine_diagnostics_v1(fingerprint_limit=101)
            with self.assertRaisesRegex(ValueError, "tail_limit"):
                inspector.query_engine_diagnostics_v1(tail_limit=0)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class Ck3RuntimeDiagnosticsMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_calls_and_rejects_path(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.driver import DevelopmentReportDriver
        from xar_autoplayer.bridge.mcp_server import create_server

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = Ck3RuntimeDiagnosticsTests()._profile(root)
            server = create_server(
                DevelopmentReportDriver(root),
                profile_dir=profile,
            )
            async with Client(server) as client:
                listed = await client.list_tools()
                tools = {tool.name: tool for tool in listed.tools}
                tool = tools["ck3_query_engine_diagnostics_v1"]
                self.assertTrue(tool.annotations.read_only_hint)
                self.assertNotIn("path", tool.input_schema["properties"])
                self.assertNotIn("regex", tool.input_schema["properties"])
                self.assertFalse(tool.input_schema.get("additionalProperties", True))
                called = await client.call_tool(
                    "ck3_query_engine_diagnostics_v1",
                    {"fingerprint_limit": 5, "tail_limit": 2},
                )
                self.assertFalse(called.is_error)
                self.assertEqual(
                    called.structured_content["crashes"]["package_count"], 1
                )
                rejected = await client.call_tool(
                    "ck3_query_engine_diagnostics_v1",
                    {"path": str(profile)},
                )
                self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
