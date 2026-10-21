"""Run the existing modified finally method, using its actual pure receipt fixture.

Extract only the named existing method/functions to avoid unrelated full fixture
trees. The resolver, client and entry are the actual selected sources.
"""
from __future__ import annotations
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT/'candidate/tools'
sys.path.insert(0,str(TOOLS))
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_client as client

def git_source(name: str) -> bytes:
    return subprocess.check_output(['git','-C',
        'C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree',
        'show','9592cefdda846fc0242430d8fef1fef1f58c81a0:tools/'+name],
        env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_OPTIONAL_LOCKS='0'))

def main() -> None:
    contract = ModuleType('_reviewer_existing_receipt_contract')
    contract.__file__='git:9592cef:tools/steam_offline_state_contract.py'
    sys.modules[contract.__name__]=contract
    exec(compile(git_source('steam_offline_state_contract.py'),contract.__file__,'exec'),contract.__dict__)
    functions = ast.parse(git_source('ck3_mod_acceptance_test_background_fixture.py'))
    selected = [node for node in functions.body if isinstance(node,ast.FunctionDef)
        and node.name in ('_write_result','write_unavailable_receipt_fixture')]
    if len(selected)!=2:
        raise AssertionError('Exact two existing fixture functions required')
    import datetime
    scope = dict(globals(), ProbeResult=contract.ProbeResult, parse_result=contract.parse_result,
                 datetime=datetime.datetime, timezone=datetime.timezone)
    exec(compile(ast.Module(body=selected,type_ignores=[]),'<exact existing background fixture functions>','exec'),scope)
    source = ast.parse((TOOLS/'test_ck3_mod_acceptance_operator_quit.py').read_bytes())
    klass = next(node for node in source.body if isinstance(node,ast.ClassDef) and node.name=='OperatorQuitTests')
    method = next(node for node in klass.body if isinstance(node,ast.FunctionDef)
        and node.name=='test_failed_entry_finally_uses_actual_hold_fallback_and_keeps_failure')
    exec(compile(ast.Module(body=[method],type_ignores=[]),'<exact existing finally test method>','exec'),scope)
    testcase = type('ExistingFinallyOnly',(unittest.TestCase,),{'entry':entry,'module':client,
        method.name:scope[method.name]})
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(testcase))
    if not result.wasSuccessful():
        raise SystemExit(1)

if __name__=='__main__':
    main()
