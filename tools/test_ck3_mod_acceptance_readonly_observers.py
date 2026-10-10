"""Real MCP argument models for the shared existing readonly observers; no CK3."""
from __future__ import annotations
import ast
import argparse
import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated
import sys
import unittest
from pydantic import AfterValidator, Field, ValidationError
from mcp.server import MCPServer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.confucian_challenger_graph_v1 import validate_faith_ids


def actual_register():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    names = {'register_succession_title_readonly_tools', '_forbid_unknown_tool_arguments_v1'}
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                             *(node for node in tree.body if
                               (isinstance(node, ast.FunctionDef) and node.name in names) or
                               (isinstance(node, ast.Assign) and any(
                                   isinstance(target, ast.Name) and target.id == 'ConfucianFaithSelectorV1'
                                   for target in node.targets)))],
                        type_ignores=[])
    namespace = {'NormalExitRevisionV1': Annotated[int, Field(strict=True, gt=0, lt=2**64)],
                 'Annotated': Annotated, 'Field': Field, 'AfterValidator': AfterValidator,
                 'validate_faith_ids': validate_faith_ids}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), 'exec'), namespace)
    return namespace['register_succession_title_readonly_tools']


class ReadonlyObserverTests(unittest.TestCase):
    def register(self, cache=False, title=False, challenger=False, service=None):
        server = MCPServer(name='shared-readonly-contract')
        self.calls = []
        def query(kind, **args):
            self.calls.append((kind, args)); return {'actual_service_result': kind, **args}
        service = service or SimpleNamespace(query_actor_cached_succession_v1=lambda **kw: query('cache', **kw),
                                  query_confucian_religious_title_v1=lambda **kw: query('title', **kw),
                                  query_confucian_assembly_predicates_v1=lambda **kw: query('assembly', **kw),
                                  query_confucian_challenger_graph_v1=lambda **kw: query('graph', **kw))
        actual_register()(server, service, SimpleNamespace(allow_private_actor_cached_succession_queries=cache,
                                                          allow_private_confucian_readonly_queries=title,
                                                          allow_private_confucian_challenger_queries=challenger))
        return server._tool_manager._tools

    def test_default_inventory_is_unchanged(self):
        self.assertEqual(self.register(), {})
        self.assertEqual(self.calls, [])

    def test_only_explicit_boolean_permissions_register_tools(self):
        self.assertEqual(self.register(cache=1, title='true'), {})
        self.assertEqual(set(self.register(cache=True)), {'ck3_query_actor_cached_succession_v1'})
        self.assertEqual(set(self.register(title=True)), {'ck3_query_confucian_religious_title_v1', 'ck3_query_confucian_assembly_predicates_v1'})

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
                           ('title', 'ck3_query_confucian_religious_title_v1'),
                           ('assembly', 'ck3_query_confucian_assembly_predicates_v1')]:
            tool = tools[name]
            value = tool.fn_metadata.arg_model.model_validate({'expected_revision': 7})
            self.assertEqual(tool.fn(**value.model_dump()), {'actual_service_result': kind, 'expected_revision': 7})
            annotations = tool.annotations.model_dump(by_alias=True)
            self.assertTrue(annotations['readOnlyHint'])
            self.assertFalse(annotations['destructiveHint'])
        self.assertEqual(self.calls, [('cache', {'expected_revision': 7}), ('title', {'expected_revision': 7}),
                                      ('assembly', {'expected_revision': 7})])


class ChallengerObserverTests(unittest.TestCase):
    register = ReadonlyObserverTests.register
    NAME = 'ck3_query_confucian_challenger_graph_v1'

    def test_graph_is_default_off_and_independent_of_g2_g3(self):
        self.assertEqual(self.register(), {})
        self.assertNotIn(self.NAME, self.register(cache=True, title=True))
        for value in (None, 1, 'true'):
            self.assertEqual(self.register(challenger=value), {})
        self.assertEqual(set(self.register(challenger=True)), {self.NAME})

    def test_graph_model_rejects_invalid_revision_and_selectors_before_service(self):
        tool = self.register(challenger=True)[self.NAME]
        self.assertFalse(tool.parameters['additionalProperties'])
        self.assertTrue(tool.parameters['properties']['faith_full_ids']['uniqueItems'])
        model = tool.fn_metadata.arg_model
        bad = [dict(expected_revision=v, faith_full_ids=[107])
               for v in (True, '3', 3.0, 0, 2**64)]
        bad += [dict(expected_revision=3, faith_full_ids=v)
                for v in ([], (), [True], ['107'], [107.0], [-1], [2**32-1], [107, 107], list(range(9)))]
        bad += [{}, {'expected_revision': 3},
                {'expected_revision': 3, 'faith_full_ids': [107], 'owner_faith': 107}]
        for arguments in bad:
            with self.subTest(arguments=arguments), self.assertRaises(ValidationError):
                model.model_validate(arguments)
        self.assertEqual(self.calls, [])

    def test_graph_wrapper_preserves_service_arguments_response_and_annotations(self):
        tool = self.register(challenger=True)[self.NAME]
        args = tool.fn_metadata.arg_model.model_validate(
            {'expected_revision': 7, 'faith_full_ids': [0, 2**32-2]}).model_dump()
        self.assertEqual(tool.fn(**args), {'actual_service_result': 'graph', **args})
        self.assertEqual(self.calls, [('graph', args)])
        hints = tool.annotations.model_dump(by_alias=True)
        self.assertEqual({key: hints[key] for key in
                          ('readOnlyHint', 'destructiveHint', 'idempotentHint', 'openWorldHint')},
                         dict(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))

    def graph_service(self):
        # Reuse the established inert transport/DTO fixtures; no SDK connection or game.
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/tests'))
        import test_confucian_challenger_graph_v1 as fixture
        driver = fixture.driver()
        driver.take_snapshot = lambda: copy.deepcopy(fixture.base.frame())
        service = object.__new__(fixture.base.GameplayBridgeService)
        service.driver = driver
        return fixture, driver, service

    def test_registered_graph_reaches_actual_service_and_native_request_contract(self):
        fixture, driver, service = self.graph_service()
        tool = self.register(challenger=True, service=service)[self.NAME]
        args = tool.fn_metadata.arg_model.model_validate(
            {'expected_revision': 3, 'faith_full_ids': fixture.FAITHS}).model_dump()
        result = tool.fn(**args)
        self.assertEqual(result['queried_revision'], 3)
        self.assertEqual(result['queried_native_revision'], 7)
        self.assertFalse(result['business_postcondition_verified'])
        self.assertFalse(result['full_product_acceptance_credit'])
        packet = json.loads(driver.endpoint.packets[0][4:])
        self.assertEqual(packet['faith_full_ids'], fixture.FAITHS)
        self.assertEqual(packet['expected_snapshot_revision'], 7)
        self.assertEqual(packet['step'], 'query-confucian-challenger-graph-v1')
        self.assertEqual(len(driver.endpoint.packets), 1)

    def test_actual_service_still_rejects_disabled_permission_and_crossed_frame(self):
        fixture, driver, service = self.graph_service()
        tool = self.register(challenger=True, service=service)[self.NAME]
        driver.allow_private_confucian_challenger_queries = False
        with self.assertRaises(fixture.UnsupportedStepError):
            tool.fn(expected_revision=3, faith_full_ids=fixture.FAITHS)
        self.assertEqual(driver.endpoint.packets, [])
        fixture, driver, service = self.graph_service()
        snapshots = [fixture.base.frame() for _ in range(4)]
        snapshots[-1]['diagnostics']['hello']['pid'] += 1
        driver.take_snapshot = lambda: copy.deepcopy(snapshots.pop(0))
        tool = self.register(challenger=True, service=service)[self.NAME]
        with self.assertRaises(fixture.BridgeUnavailableError):
            tool.fn(expected_revision=3, faith_full_ids=fixture.FAITHS)
        self.assertEqual(len(driver.endpoint.packets), 1)

    def test_host_parser_and_actual_forwarding_keep_independent_default_off(self):
        source = ROOT / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        parser = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'parser')
        guards = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                  and 'private_confucian_challenger_readonly' in ast.unparse(node.test)]
        self.assertEqual(len(guards), 2)
        namespace = {'argparse': argparse, 'Path': Path, '__file__': str(source), 'sys': sys, 'os': os}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser], type_ignores=[])), str(source), 'exec'), namespace)
        for flags, expected in (([], False), (['--private-confucian-challenger-readonly'], True),
                                (['--private-succession-title-readonly'], False)):
            args = namespace['parser']().parse_args(flags)
            state = {'args': args, 'driver_options': {}, 'child_args': []}
            for guard in guards:
                exec(compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), str(source), 'exec'), state)
            self.assertEqual(state['driver_options'], {'allow_private_confucian_challenger_queries': True} if expected else {})
            self.assertEqual(state['child_args'], ['--private-confucian-challenger-readonly'] if expected else [])


if __name__ == '__main__': unittest.main(verbosity=2)
