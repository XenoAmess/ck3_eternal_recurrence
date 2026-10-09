"""Real MCP argument models for the shared existing readonly observers; no CK3."""
from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated
import unittest
from pydantic import Field, ValidationError
from mcp.server import MCPServer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'


def actual_register():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    names = {'register_succession_title_readonly_tools', '_forbid_unknown_tool_arguments_v1'}
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                             *(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names)],
                        type_ignores=[])
    namespace = {'NormalExitRevisionV1': Annotated[int, Field(strict=True, gt=0, lt=2**64)]}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), 'exec'), namespace)
    return namespace['register_succession_title_readonly_tools']


class ReadonlyObserverTests(unittest.TestCase):
    def register(self, cache=False, title=False):
        server = MCPServer(name='shared-readonly-contract')
        self.calls = []
        def query(kind, **args):
            self.calls.append((kind, args)); return {'actual_service_result': kind, **args}
        service = SimpleNamespace(query_actor_cached_succession_v1=lambda **kw: query('cache', **kw),
                                  query_confucian_religious_title_v1=lambda **kw: query('title', **kw))
        actual_register()(server, service, SimpleNamespace(allow_private_actor_cached_succession_queries=cache,
                                                          allow_private_confucian_readonly_queries=title))
        return server._tool_manager._tools

    def test_default_inventory_is_unchanged(self):
        self.assertEqual(self.register(), {})
        self.assertEqual(self.calls, [])

    def test_only_explicit_boolean_permissions_register_tools(self):
        self.assertEqual(self.register(cache=1, title='true'), {})
        self.assertEqual(set(self.register(cache=True)), {'ck3_query_actor_cached_succession_v1'})
        self.assertEqual(set(self.register(title=True)), {'ck3_query_confucian_religious_title_v1'})

    def test_real_mcp_model_rejects_stale_argument_shapes_before_service(self):
        for name, tool in self.register(True, True).items():
            self.assertFalse(tool.parameters['additionalProperties'])
            for arguments in ({}, {'expected_revision': True}, {'expected_revision': 0},
                              {'expected_revision': '3'}, {'expected_revision': 2**64},
                              {'expected_revision': 3, 'title_id': 42}):
                with self.subTest(tool=name, arguments=arguments), self.assertRaises(ValidationError):
                    tool.fn_metadata.arg_model.model_validate(arguments)
        self.assertEqual(self.calls, [])

    def test_wrapper_preserves_service_response_and_revision(self):
        tools = self.register(True, True)
        for kind, name in [('cache', 'ck3_query_actor_cached_succession_v1'),
                           ('title', 'ck3_query_confucian_religious_title_v1')]:
            tool = tools[name]
            value = tool.fn_metadata.arg_model.model_validate({'expected_revision': 7})
            self.assertEqual(tool.fn(**value.model_dump()), {'actual_service_result': kind, 'expected_revision': 7})
            annotations = tool.annotations.model_dump(by_alias=True)
            self.assertTrue(annotations['readOnlyHint'])
            self.assertFalse(annotations['destructiveHint'])
        self.assertEqual(self.calls, [('cache', {'expected_revision': 7}), ('title', {'expected_revision': 7})])


if __name__ == '__main__': unittest.main(verbosity=2)
