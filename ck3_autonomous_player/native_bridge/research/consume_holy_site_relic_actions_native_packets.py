"""Consume complete C++ relic action formatter packets with actual MCP SDK."""
from __future__ import annotations
import argparse
from contextlib import redirect_stderr
from datetime import datetime,timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-source-root',type=Path,required=True)
    parser.add_argument('--native-consumer-manifest',type=Path)
    parser.add_argument('--common-hook-manifest',type=Path)
    parser.add_argument('--state-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.exists() or args.state_root.exists():
        raise FileExistsError('Use new immutable output and state-root paths')
    repo=Path(__file__).resolve().parents[3]
    base=args.base_source_root.resolve()
    hooks=args.common_hook_manifest or repo/'tools/relic-action-common-hooks-a01.json'
    os.environ['XAR_RELIC_ACTION_BASE_SOURCE_ROOT']=str(base)
    os.environ['XAR_RELIC_ACTION_COMMON_HOOK_MANIFEST']=str(hooks.resolve())
    os.environ['XAR_RELIC_ACTION_STATE_ROOT']=str(args.state_root.resolve())
    if args.native_consumer_manifest:
        os.environ['XAR_RELIC_ACTION_NATIVE_MANIFEST']=str(args.native_consumer_manifest.resolve())
    else:os.environ.pop('XAR_RELIC_ACTION_NATIVE_MANIFEST',None)
    machine=subprocess.check_output([sys.executable,'-B','-X','utf8',str(base/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    def pin(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    test_path=repo/'ck3_autonomous_player/tests/unit/test_holy_site_relic_actions_12004_native_mcp.py'
    transport=repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/relic_action_private_transport.py'
    report={'schema':'holy-site-relic-actions-real-mcp-consumer-v1','machine_id':machine,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAILED','tests_run':0,'tests_skipped':[],
        'failures':[],'errors':[],'mcp_results':[],'test_source':pin(test_path),'transport_source':pin(transport),
        'common_hook_manifest':pin(hooks),'native_consumer_manifest':pin(args.native_consumer_manifest) if args.native_consumer_manifest else None,
        'native_boundary_mocked':['endpoint I/O','hello','state_snapshot'],
        'production_layers':['NativeHeadlessGameplayDriver._execute_primitive_step','GameplayBridgeService','create_server','MCP ClientSession'],
        'live_game_qualification':False,'real_engine_callback_execution_proven':False,
        'isolated_source_bound_native_formatters':True,'full_native_dll_linked':False,'state_root':str(args.state_root)}
    args.state_root.mkdir(parents=True,exist_ok=False)
    stream,diagnostics=io.StringIO(),io.StringIO()
    try:
        with redirect_stderr(diagnostics):
            spec=importlib.util.spec_from_file_location('holy_site_relic_action_native_mcp_tests',test_path)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        report.update(status='COMPILED_NATIVE_RELIC_ACTION_PACKETS_THROUGH_REAL_MCP_PASS' if args.native_consumer_manifest and result.wasSuccessful() and not result.skipped
            else 'STATIC_OPTIN_PASS_NATIVE_TESTS_SKIPPED' if result.wasSuccessful() else 'FAILED',
            tests_run=result.testsRun,tests_skipped=[{'test':str(t),'reason':r} for t,r in result.skipped],
            failures=[{'test':str(t),'detail':d} for t,d in result.failures],errors=[{'test':str(t),'detail':d} for t,d in result.errors],
            mcp_results=module.RelicActionsNativeMcpTests.actual_mcp_results,common_source_hooks=module.HOOKS)
    except Exception:report['errors'].append({'test':'consumer_bootstrap','detail':traceback.format_exc()})
    report.update(test_log=stream.getvalue(),captured_stderr=diagnostics.getvalue(),completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  retained_state_files=[pin(p) for p in args.state_root.rglob('*') if p.is_file()])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='') as handle:
        json.dump(report,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(stream.getvalue(),end='')
    print(json.dumps({'status':report['status'],'output':str(args.output),'bytes':args.output.stat().st_size,
                      'tests_run':report['tests_run'],'mcp_results':len(report['mcp_results'])}))
    return 1 if report['status']=='FAILED' else 0


if __name__=='__main__':raise SystemExit(main())
