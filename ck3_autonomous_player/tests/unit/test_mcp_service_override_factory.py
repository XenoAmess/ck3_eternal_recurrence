"""Actual factory/client composition; no game, native command, or frozen wrapper."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mcp import Client
from xar_autoplayer.bridge.driver import BridgeUnavailableError, DevelopmentReportDriver, GameplayBridgeDriver
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService


class ServiceOverrideFactoryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="xar-mcp-service-factory-")
        self.addCleanup(self.temp.cleanup)
        self.driver = DevelopmentReportDriver(Path(self.temp.name))

    def test_rejects_foreign_type_subclass_and_different_driver_identity(self) -> None:
        class DerivedService(GameplayBridgeService):
            pass

        for value in (object(), DerivedService(self.driver)):
            with self.subTest(value=type(value)), self.assertRaises(TypeError):
                mcp_server.create_server(self.driver, **{"service_override": value})
        other_driver = DevelopmentReportDriver(Path(self.temp.name))
        with self.assertRaises(ValueError):
            mcp_server.create_server(self.driver, service_override=GameplayBridgeService(other_driver))

    async def test_default_factory_constructs_exactly_one_actual_service(self) -> None:
        instances: list[GameplayBridgeService] = []
        original = GameplayBridgeService.__init__

        def tracked(service: GameplayBridgeService, driver: GameplayBridgeDriver) -> None:
            instances.append(service)
            original(service, driver)

        with patch.object(GameplayBridgeService, "__init__", new=tracked):
            server = mcp_server.create_server(self.driver)
            async with Client(server) as client:
                result = await client.session.call_tool("ck3_get_capabilities", {})
                self.assertFalse(result.is_error, str(result))
                self.assertEqual(result.structured_content["backend_id"], "vision-report")
        self.assertEqual(len(instances), 1)
        self.assertIs(instances[0].driver, self.driver)

    async def test_existing_control_and_canonical_v2_tools_share_the_same_service(self) -> None:
        service = GameplayBridgeService(self.driver)
        marker = {"service_fixture": "one exact retained instance"}

        def unexpected_constructor(*arguments: object, **keywords: object) -> None:
            raise AssertionError("override constructed a second service")

        with patch.object(GameplayBridgeService, "__init__", new=unexpected_constructor), \
                patch.object(service, "capabilities", return_value=marker) as capabilities, \
                patch.object(service, "query_normal_exit_context_v1", side_effect=BridgeUnavailableError("fixture read only")) as query:
            server = mcp_server.create_server(self.driver, service_override=service)

            def retained_control_fixture() -> dict[str, object]:
                return service.capabilities()

            server.tool()(retained_control_fixture)
            async with Client(server) as client:
                tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
                revision_schema = tools["ck3_query_normal_exit_context_v1"].input_schema["properties"]["expected_revision"]
                self.assertEqual(revision_schema["type"], "string")
                for name in ("ck3_get_capabilities", "retained_control_fixture"):
                    result = await client.session.call_tool(name, {})
                    self.assertFalse(result.is_error, str(result))
                    self.assertEqual(result.structured_content, marker)
                rejected = await client.session.call_tool("ck3_query_normal_exit_context_v1", {"expected_revision": 9007199254740993})
                self.assertTrue(rejected.is_error)
                query.assert_not_called()
                observed = await client.session.call_tool("ck3_query_normal_exit_context_v1", {"expected_revision": "9007199254740993"})
                self.assertTrue(observed.is_error)  # The real retained service receives the read and preserves its diagnostic.
                query.assert_called_once_with(expected_revision=9007199254740993)
                self.assertIn("fixture read only", " ".join(item.text for item in observed.content if item.type == "text"))
            self.assertEqual(capabilities.call_count, 2)
        self.assertIs(service.driver, self.driver)

    def test_modified_factory_boundary_passes_strict_types_with_real_dependency_models(self) -> None:
        """Check only changed source, importing real models; legacy bodies stay outside this lane."""
        from mypy import api

        source_path = Path(mcp_server.__file__)
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name == "_resolve_service_override_v1")
        factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "create_server")
        assignment = next(node for node in factory.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "service" for target in node.targets))
        checked_factory = ast.FunctionDef(name="_checked_factory_signature", args=factory.args,
            body=[assignment, ast.Raise(exc=ast.Call(func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                args=[ast.Constant(value="unchanged factory body excluded")], keywords=[]), cause=None)],
            decorator_list=[], returns=factory.returns, type_comment=None, type_params=[])
        imports = """from __future__ import annotations
import os
from collections.abc import Callable
from mcp.server import MCPServer
from xar_autoplayer.bridge.driver import GameplayBridgeDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
"""
        check_source = imports + ast.unparse(ast.fix_missing_locations(ast.Module(
            body=[helper, checked_factory], type_ignores=[]))) + "\n"
        with tempfile.TemporaryDirectory(prefix="xar-service-factory-types-") as task_dir:
            check_path = Path(task_dir) / "factory_boundary.py"
            check_path.write_text(check_source, encoding="utf-8")
            # A nonincremental check still writes caches unless explicitly disabled.
            # The real dependency graph is checked once and needs no persistent copy.
            stdout, stderr, status = api.run(["--strict", "--follow-imports=silent", "--no-incremental",
                "--cache-dir=" + os.devnull, "--python-executable=" + sys.executable,
                str(check_path)])
        self.assertEqual(status, 0, stdout + stderr)


if __name__ == "__main__":
    unittest.main()
