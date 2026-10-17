"""Public case CLI grants each current-state query independently; no CK3."""
import argparse
import ast
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import ck3_mod_acceptance

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
TOOLS = ('ck3_query_player_religion_doctrines_v1', 'ck3_query_player_religion_tenets_v1',
         'ck3_query_player_holy_site_v1')
PERMISSIONS = ('allow_private_player_religion_doctrines_query',
               'allow_private_player_religion_tenets_query', 'allow_private_player_holy_site_query')


class CurrentReligionPublicOptinTests(unittest.TestCase):
    def test_actual_parser_and_permission_assignments_are_independent_default_off(self):
        tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
        parser = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'parser')
        assignments = [n for n in ast.walk(tree) if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Attribute) and t.attr in PERMISSIONS for t in n.targets)]
        self.assertEqual(len(assignments), len(TOOLS))
        namespace = dict(argparse=argparse, Path=Path, __file__=str(HOST), sys=sys, os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser], type_ignores=[])), str(HOST), 'exec'), namespace)
        for selected in ((), *((tool,) for tool in TOOLS), TOOLS):
            argv = [value for tool in selected for value in ('--case-read-only-mcp-tool', tool)]
            args = namespace['parser']().parse_args(argv)
            driver = SimpleNamespace(case_declared_read_only_mcp_tools=frozenset(args.case_read_only_mcp_tool))
            state = {'driver': driver}
            exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])), str(HOST), 'exec'), state)
            for tool, permission in zip(TOOLS, PERMISSIONS):
                self.assertEqual(getattr(driver, permission), tool in selected)
            self.assertTrue(set(selected) <= ck3_mod_acceptance.CASE_READ_ONLY_MCP_TOOLS)


if __name__ == '__main__': unittest.main()
