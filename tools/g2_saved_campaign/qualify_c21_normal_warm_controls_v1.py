"""Focused C21 source/optional-env checks; harmless children, never an SDK."""
import ast
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from datetime import datetime, timezone, timedelta

import prepare_c21_normal_warm_controls_v1 as p

DEPENDENCIES = p.REPO/'tools/.venv/Lib/site-packages'
STDIO_PATH = DEPENDENCIES/'mcp/client/stdio.py'
STDIO_SHA = 'bc987925a3da72f4ca59ccd627a6fc6ba258582d50515a532503abe6d1b9dbab'
DRIVER = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src17/xar_autoplayer/bridge/native_driver.py')
DRIVER_SHA = 'cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab'
CARD_SHA = '09caeac85c2f92bf80f0cfcd5e903b9fdca9d7ffb43ca6b6562e5b3046abd77a'
CHILD_RESULTS = []


def unique(nodes, reason):
    values = list(nodes)
    p.require(len(values) == 1, reason)
    return values[0]


def setup_sources():
    graph, report = p._source_graph_v1()
    queue = ast.parse(graph['root_p37c21_sdk_queue.py'])
    main = unique((n for n in queue.body if isinstance(n,ast.AsyncFunctionDef) and n.name == 'main'), 'one actual main')
    assign = unique((n for n in main.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'child_env'), 'actual child_env assignment')
    wal = unique((i for i,n in enumerate(main.body) if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'wal_value'), 'one WAL input read')
    # Compile the actual candidate statements, not a reimplemented env function.
    selected = copy.deepcopy([assign,*main.body[wal:wal+2]])
    env_code = compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])), 'actual-C21-child-env', 'exec')
    stdio_source = p.checked(STDIO_PATH,13827,STDIO_SHA)
    sys.path.insert(0,str(DEPENDENCIES))
    from mcp.client import stdio
    p.require(Path(stdio.__file__).resolve() == STDIO_PATH.resolve()
        and importlib.metadata.version('mcp') == '2.0.0', 'actual pinned MCP dependency required')
    p.require(p.KEY not in stdio.DEFAULT_INHERITED_ENV_VARS, 'WAL unexpectedly entered default inheritance')
    client = unique((n for n in ast.walk(ast.parse(stdio_source))
        if isinstance(n,ast.AsyncFunctionDef) and n.name == 'stdio_client'), 'one actual stdio client')
    spawn = unique((n for n in ast.walk(client) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name) and n.func.id == '_create_platform_compatible_process'), 'one actual MCP spawn')
    expression = unique((k.value for k in spawn.keywords if k.arg == 'env'), 'one actual MCP spawn env expression')
    merge = compile(ast.Expression(copy.deepcopy(expression)),'actual-MCP-spawn-env','eval')
    driver = ast.parse(p.checked(DRIVER,1637048,DRIVER_SHA))
    assignment = unique((n for n in ast.walk(driver) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Attribute) and t.attr=='allow_driver_state_wal_v1' for t in n.targets)), 'one original Driver WAL predicate')
    predicate = ast.unparse(assignment.value)
    return graph,report,env_code,stdio,merge,predicate


def actual_child_env(code, environ):
    scope = {'os':SimpleNamespace(environ=environ), 'dependency_root':str(DEPENDENCIES),
        'N':p.T, 'FRONTEND_TIMEOUT_SECONDS':60, 'FRONTEND_READ_RESERVE_SECONDS':10}
    exec(code,scope)
    return scope['child_env']


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph,cls.report,cls.env_code,cls.stdio,cls.merge,cls.predicate = setup_sources()

    def test_optional_env_through_actual_MCP_expression_and_harmless_child(self):
        for value in (None,'0','1'):
            with self.subTest(value=value):
                incoming = {'UNRELATED_C21_TEST_KEY':'must_not_be_forwarded'}
                if value is not None: incoming[p.KEY] = value
                env = actual_child_env(self.env_code,incoming)
                self.assertNotIn('UNRELATED_C21_TEST_KEY',env)
                self.assertEqual(env.get(p.KEY),value)
                if value is None: self.assertNotIn(p.KEY,env)
                # Real dependency model and exact AST expression from its spawn.
                server = self.stdio.StdioServerParameters(command=sys._base_executable,env=env)
                merged = eval(self.merge,{'get_default_environment':self.stdio.get_default_environment,'server':server})
                script = ('import os,json;print(json.dumps({"value":os.environ.get('+repr(p.KEY)
                    +'),"driver_predicate":'+self.predicate+'}))')
                child = subprocess.run([sys._base_executable,'-B','-c',script],env=merged,
                    capture_output=True,text=True,timeout=10,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                self.assertEqual(child.returncode,0,child.stderr)
                observed = json.loads(child.stdout)
                self.assertEqual(observed,{'value':value,'driver_predicate':value=='1'})
                CHILD_RESULTS.append({'input':value,'stdout':observed,'exit_code':child.returncode,
                    'SDK_or_Game_process':False})

    def test_illegal_values_rejected_without_child_or_implicit_enable(self):
        for value in ('','true','01',' 1','2',1,True,{},[]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): actual_child_env(self.env_code,{p.KEY:value})

    def test_actual_anchor_missing_placeholder_or_other_rows_rejected(self):
        with self.assertRaises(ValueError): p.compose(anchor_raw=None,anchor_ref=None)
        record = {'machine_id':p.MACHINE,'actual':{'commit':'0123456789abcdef0123456789abcdef01234567',
            'parent':p.PARENT,'tree':'89abcdef0123456789abcdef0123456789abcdef',
            'ref':'refs/heads/campaign/SOURCE-FIXTURE-NOT-ACTUAL',
            'complete_manifest':{'file_count':1447,'source_bytes':59074855,
                'canonical_rows_JSON':{'sha256':p.ROWS_SHA}}}}
        def bind(value):
            raw=json.dumps(value).encode()
            return p.bind_actual_business_anchor_v1(raw,{'path':str(p.REPO/'SOURCE-FIXTURE-NOT-ACTUAL.json'),
                'bytes':len(raw),'sha256':p.sha(raw)})
        fixture = bind(record)
        self.assertFalse(fixture['runtime_admitted'])
        self.assertTrue(fixture['separate_export_Task_and_runtime_admissions_required'])
        for kind in ('placeholder','predecessor','rows'):
            value=copy.deepcopy(record)
            if kind=='placeholder':value['actual']['commit']='0'*40
            elif kind=='predecessor':value['actual']['commit']=p.PARENT
            else:value['actual']['complete_manifest']['canonical_rows_JSON']['sha256']='0'*64
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):bind(value)


def pin(path):
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':p.sha(raw)}


def write_source_records(proof_path,plan_path):
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Qualification)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    graph,report=Qualification.graph,Qualification.report
    files=[pin(Path(p.__file__)),pin(Path(__file__))]
    now=datetime.now(timezone.utc)
    proof={'schema':'xar.C21-WAL-env-forward-source-qualification/v1','machine_id':p.MACHINE,
        'observed_at_utc':now.isoformat(),'status':'SOURCE_QUALIFIED_NOT_ADOPTED',
        'files':files,'tests_passed':result.testsRun,'harmless_children':CHILD_RESULTS,
        'real_dependency':pin(STDIO_PATH),'original_Driver_source':{'path':str(DRIVER),'sha256':DRIVER_SHA},
        'actual_candidate_env_statements_compiled':True,'actual_MCP_parameter_and_spawn_env_expression':True,
        'non_WAL_bootstrap_values_in_fixture':'dependency root/path and timing scalars only; no SDK main executed',
        'business_plan':report['business_plan'],'actual_new_Git_anchor_observed':False,
        'anchor_positive':'synthetic Root-record-shaped RAM input only, not actual Git or runtime authority',
        'public_missing_anchor_and_placeholder_rejected':True,'old_matrices_repeated':False,
        'seven_sources_RAM_bytes':sum(map(len,graph.values())),
        'sources':{name:{'bytes':len(raw),'sha256':p.sha(raw)} for name,raw in graph.items()},
        'namespace_inverse_bytes_AST_and_only_WAL_hunk':True,'protected_constants':report['protected_constants'],
        'unrelated_environment_forwarded':False,'Taskrole_whitelist_changed':False,
        'WAL_missing_or_zero_remains_optout':True,'illegal_values_explicitly_rejected':True,
        'current_C20_or_actual_writer_ON_claimed':False,'Game_Native_SDK_Task_RPC_Git_D_operations':0,
        'scratch_bytes':0,'source_card_sha256':CARD_SHA,'complete_source_cap_bytes':32768,
        'record_review_at_utc':(now+timedelta(days=180)).isoformat(),'future_writes_after_freeze':0}
    proof_raw=(json.dumps(proof,indent=2)+'\n').encode()
    plan={'schema':'xar.C21-WAL-env-forward-source-plan/v1','machine_id':p.MACHINE,
        'observed_at_utc':now.isoformat(),'status':'FUTURE_SOURCE_ONLY_NOT_EXPORTED',
        'producer':files[0],'qualifier':files[1],
        'proof':{'path':str(proof_path.resolve()),'bytes':len(proof_raw),'sha256':p.sha(proof_raw)},
        'entry':'prepare_c21_normal_warm_controls_v1.compose(anchor_raw=actual Root JSON bytes,anchor_ref={path,bytes,sha256}) -> seven RAM bytes and bindings',
        'actual_anchor_required_shape':{'machine_id':p.MACHINE,'actual':{
            'commit':'THEN_ACTUAL_NEW_COMMIT_NOT_A_PLACEHOLDER','parent':p.PARENT,
            'tree':'THEN_ACTUAL_TREE','ref':'refs/heads/campaign/THEN_ACTUAL_REF',
            'complete_manifest':{'file_count':1447,'source_bytes':59074855,
                'canonical_rows_JSON':{'sha256':p.ROWS_SHA}}}},
        'business_plan':report['business_plan'],'retained_physical_generation':'C16',
        'Native':'retained qualified Native29; no Native30 admission',
        'WAL_policy':report['WAL_policy'],'execution_query_mask':False,
        'classifier_sha256':p.CLASSIFIER_SHA,'complete_planner_and_stop_record_once_T0':'unchanged except currentview namespace',
        'output_sources':proof['sources'],'all_outputs_only_RAM':True,
        'then_actual_App_env_and_wal_writer_append_required_for_runtime_ON_claim':True,
        'future_export_and_Task_and_Runtime_authority':'not granted by this source package',
        'storage':{'complete_hard_bytes':32768,'scratch_bytes':0,'allocated_bytes':None,
            'physical_credit_bytes':0,'source_card_sha256':CARD_SHA},
        'record_review_at_utc':proof['record_review_at_utc'],'future_writes_after_freeze':0}
    plan_raw=(json.dumps(plan,indent=2)+'\n').encode()
    total=sum(row['bytes'] for row in files)+len(proof_raw)+len(plan_raw)
    p.require(total<=32768,'complete producer/qualifier/proof/plan/scratch cap exceeded')
    p.require(not proof_path.exists() and not plan_path.exists(),'create-only source records already exist')
    with proof_path.open('xb') as stream:stream.write(proof_raw)
    with plan_path.open('xb') as stream:stream.write(plan_raw)
    print(json.dumps({'complete_source_bytes':total,'tests_passed':result.testsRun,
        'producer':files[0],'qualifier':files[1],
        'proof':{'path':str(proof_path),'bytes':len(proof_raw),'sha256':p.sha(proof_raw)},
        'plan':{'path':str(plan_path),'bytes':len(plan_raw),'sha256':p.sha(plan_raw)},
        'RAM_sources':proof['sources'],'WAL_hunk_added_bytes':len(p.WAL_HUNK.encode())}))


if __name__=='__main__':
    if len(sys.argv)!=3:raise ValueError('two new Z source-record paths required')
    write_source_records(Path(sys.argv[1]),Path(sys.argv[2]))
