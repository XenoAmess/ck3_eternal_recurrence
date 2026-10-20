import ast
import builtins
import datetime as dt
import difflib
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parent
N=ROOT.parent
D=Path('D:/workspace/ck3_eternal_recurrence')
W=Path('C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree')
HEAD='0f548b643782c479bc3eebd3ffef14d710c13d06'
BC='bc63851081462413d0cc6ebe62e37490707ee6a9'
MID='desktop-3fevhd2-1c74096080'
TASK='e04-ci-fixture-repair-1830-20261020-a01'
TEST='ck3_autonomous_player/tests/unit/test_siege_research_continuation_v2.py'
FIXTURE='ck3_autonomous_player/tests/fixtures/p55_actual265_route_projection.json'
CONSUMER='ck3_autonomous_player/src/xar_autoplayer/war_mercenary_consumer_v1.py'
METHOD='test_actual_r3_reason_separates_cash_priority_555_from_shared_hostile_4783'
MIRROR=ROOT/'mirror'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0')
sys.dont_write_bytecode=True

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def meter(p): return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
def put(p,b):
    if isinstance(b,dict) or isinstance(b,list): b=(json.dumps(b,ensure_ascii=False,indent=2)+'\n').encode()
    elif isinstance(b,str): b=b.encode()
    old=p.stat().st_size if p.exists() else 0
    assert meter(ROOT)-old+len(b)<=196608, 'child hard budget'
    assert meter(N)-old+len(b)<=4194304, 'parent hard budget'
    assert dt.datetime.now(dt.timezone.utc)<dt.datetime(2026,10,20,18,28,tzinfo=dt.timezone.utc)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def call(argv):
    start=now();p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV,cwd=D)
    out,err=p.communicate(timeout=45);rc=p.wait()
    r={'argv':argv,'started_at_utc':start,'ended_at_utc':now(),'pid':p.pid,'actual_original_popen_wait':True,'returncode':rc,'stdout_bytes':len(out),'stdout_sha256':sha(out),'stderr_bytes':len(err),'stderr_sha256':sha(err)}
    if err: r['stderr']=err.decode('utf-8','replace')[:3000]
    assert rc==0, r
    return r,out

def blob(path,head=HEAD):
    return call(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W),'show',head+':'+path])

def bus(action,*extra):
    r,b=call([sys.executable,'-B','-X','utf8','D:/workspace/.codex-task-bus/bin/codex_task_bus.py',action,*extra])
    if action in ('register','status'): r['response']=json.loads(b)
    else: r['response_retained_as_hash_only']=True
    old=ROOT/'BUS.actual.jsonl'
    line=(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    put(old,(old.read_bytes() if old.exists() else b'')+line)

def prepare():
    cap=N/'capacity/CI-FIXTURE-REPAIR192-SOURCE4-CHILD-ADMISSION.actual-a01.json'
    b=cap.read_bytes();assert len(b)==3157 and sha(b)=='e295a582ca2e08aece8c8c4d9fc4017660bcb858d75871e452a124141905abdb'
    bus('register','--task',TASK,'--repo',str(D),'--summary','Source-only exact0f548 dynamic import fixture repair, real pure formatter,192KiB mirror','--next-step','One selected method AST seam plus negative baseline and module restoration checks; no D/W/Git writes')
    bus('poll','--task',TASK,'--limit','5');bus('list','--require-existing')
    receipts=[];pins=[]
    paths=[TEST,FIXTURE,'tools/g2_saved_campaign/decision_display_contract_v1.py','tools/g2_saved_campaign/decision_observation_feed.py','tools/g2_saved_campaign/live_decision_overlay.py']
    data={}
    for path in paths:
        r,b=blob(path);receipts.append(r);data[path]=b
        pins.append({'repo_path':path,'bytes':len(b),'sha256':sha(b)})
    original=data[TEST].decode()
    old='''        for name in ("decision_observation_feed", "live_decision_overlay"):
            path = root / "tools/g2_saved_campaign" / (name + ".py")
            spec = importlib.util.spec_from_file_location("war_reason_test_" + name, path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            modules.append(module)
'''
    new='''        contract_name = "decision_display_contract_v1"
        contract_path = root / "tools/g2_saved_campaign" / (contract_name + ".py")
        contract_spec = importlib.util.spec_from_file_location(contract_name, contract_path)
        contract = importlib.util.module_from_spec(contract_spec)
        # Register the real sibling for its dataclasses and the feed import;
        # restore any prior module when this local loading context exits.
        with mock.patch.dict(sys.modules, {contract_name: contract}):
            contract_spec.loader.exec_module(contract)
            for name in ("decision_observation_feed", "live_decision_overlay"):
                path = root / "tools/g2_saved_campaign" / (name + ".py")
                spec = importlib.util.spec_from_file_location("war_reason_test_" + name, path)
                module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                modules.append(module)
'''
    assert original.count(old)==1
    candidate=original.replace('import json\n','import json\nimport sys\n',1).replace(old,new)
    data[TEST]=candidate.encode()
    # Keep all original assertions byte-identical in AST form.
    def asserts(s): return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
    assert asserts(original)==asserts(candidate)
    assert sum(map(len,data.values()))+meter(ROOT)+25000<=196608
    for path,b in data.items(): put(MIRROR/path,b)
    patch=''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/'+TEST,tofile='b/'+TEST))
    put(ROOT/'SIBLING-CONTRACT-IMPORT.candidate.patch',patch)
    dependencies=[CONSUMER,'ck3_autonomous_player/src/xar_autoplayer/bridge/player_mercenary_context.py','ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py']
    dependency_pins=[]
    for path in dependencies:
        r,b=blob(path);receipts.append(r)
        r,bc=blob(path,BC);receipts.append(r)
        actual=(D/path).read_bytes();assert actual==b==bc
        dependency_pins.append({'path':str(D/path),'repo_path':path,'bytes':len(b),'sha256':sha(b),'bc_blob_equals_0f_blob_equals_actual_D_bytes':True})
    put(ROOT/'SOURCE-AND-PREPARATION.actual.json',{'machine_id':MID,'observed_at_utc':now(),'exact_head':HEAD,'parent_capacity':{'path':str(cap),'bytes':3157,'sha256':sha(cap.read_bytes())},'repo_target':TEST,'baseline_inputs':pins,'actual_D_read_only_dependencies':dependency_pins,'candidate_test':{'path':str(MIRROR/TEST),'bytes':len(data[TEST]),'sha256':sha(data[TEST])},'mirror_bytes':sum(map(len,data.values())),'all_original_assertion_ASTs_preserved':True,'whole_src_subtrees_equal':False,'whole_class_or_exact_checkout_test_claimed':False,'read_Popen_receipts':receipts})
    print(json.dumps({'prepared':True,'mirror_bytes':sum(map(len,data.values())),'aggregate_bytes':meter(ROOT),'patch_bytes':len(patch.encode()),'patch_sha256':sha(patch.encode())}))

def focused():
    sys.path.insert(0,str(D/'ck3_autonomous_player/src'))
    consumer=importlib.import_module('xar_autoplayer.war_mercenary_consumer_v1')
    consumer_source=(D/CONSUMER).read_text(encoding='utf-8')
    fn=next(n for n in ast.parse(consumer_source).body if isinstance(n,ast.FunctionDef) and n.name=='annotate_war_decision_reason_v1')
    locals_={n.id for n in ast.walk(fn) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}|{n.arg for n in ast.walk(fn) if isinstance(n,ast.arg)}
    external={n.id for n in ast.walk(fn) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}-locals_-set(dir(builtins))
    assert external=={'Mapping','QUERY_STEP','ROOT_STEP'},external
    from collections.abc import Mapping
    assert consumer.Mapping is Mapping
    production=importlib.import_module('xar_autoplayer.bridge.player_mercenary_context')
    root_contract=importlib.import_module('xar_autoplayer.bridge.campaign_root_context_contract')
    assert consumer.QUERY_STEP==production.STEP and consumer.ROOT_STEP==root_contract.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
    source_record=json.loads((ROOT/'SOURCE-AND-PREPARATION.actual.json').read_text())
    for p in source_record['actual_D_read_only_dependencies']:
        b=Path(p['path']).read_bytes();assert sha(b)==p['sha256']
    _,baseline=blob(TEST)
    candidate_path=MIRROR/TEST
    def method(source,tag):
        parsed=ast.parse(source)
        cls=next(n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name=='SiegeResearchContinuationTests')
        node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==METHOD)
        cls.body=[node]
        namespace={'__file__':str(candidate_path),'__name__':'selected_siege_fixture_'+tag,'Path':Path,'json':json,'sys':sys,'importlib':importlib,'unittest':unittest,'mock':mock,'annotate_war_decision_reason_v1':consumer.annotate_war_decision_reason_v1,'FIXTURE':MIRROR/FIXTURE}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'git-selected-method:'+tag,'exec'),namespace)
        return namespace['SiegeResearchContinuationTests'](METHOD)
    records=[]
    with mock.patch.dict(sys.modules):
        sys.modules.pop('decision_display_contract_v1',None)
        case=method(baseline.decode(),'original-0f548')
        try: getattr(case,METHOD)()
        except ModuleNotFoundError as e:
            assert e.name=='decision_display_contract_v1'
            records.append({'case':'original selected method, missing sibling','expected_error':type(e).__name__,'missing_name':e.name,'passed':True})
        else: raise AssertionError('baseline unexpectedly passed')
    candidate=candidate_path.read_text(encoding='utf-8')
    for preexisting in (False,True):
        with mock.patch.dict(sys.modules):
            sentinel=types.ModuleType('decision_display_contract_v1')
            if preexisting: sys.modules['decision_display_contract_v1']=sentinel
            else: sys.modules.pop('decision_display_contract_v1',None)
            before=sys.modules.copy();before_path=sys.path[:];calls={}
            def profile(frame,event,arg):
                if event=='call' and frame.f_code.co_name in ('project_plan','project_card','reason_text') and str(MIRROR) in frame.f_code.co_filename:
                    key=frame.f_code.co_name;calls[key]=calls.get(key,0)+1
            case=method(candidate,'candidate')
            sys.setprofile(profile)
            try: getattr(case,METHOD)()
            finally: sys.setprofile(None)
            assert sys.path==before_path
            assert sys.modules.keys()==before.keys() and all(sys.modules[k] is v for k,v in before.items())
            assert calls.get('project_plan',0)>=2 and calls.get('project_card',0)>=1 and calls.get('reason_text',0)>=3,calls
            records.append({'case':'candidate original selected method','preexisting_canonical_module':preexisting,'all_original_method_assertions_passed':True,'sys_modules_and_path_restored':True,'real_production_function_call_counts':calls})
    print(json.dumps({'machine_id':MID,'observed_at_utc':now(),'status':'FOCUSED_SELECTED_METHOD_PASS','method':METHOD,'actual_resource_anchor___file__':str(candidate_path),'anchor_is_real_file':candidate_path.is_file(),'fixture_is_real_file':(MIRROR/FIXTURE).is_file(),'scope':'one original method AST seam; omits unrelated heavy imports, not full class/master checkout','real_consumer_function_external_globals':sorted(external),'consumer_binding_modules_exact_D_bc_0f':True,'records':records},ensure_ascii=False))

def run():
    r,out=call([sys.executable,'-B','-X','utf8',str(__file__),'focused'])
    r.update(machine_id=MID,observed_at_utc=now(),result=json.loads(out))
    put(ROOT/'FOCUSED-ORIGINAL-WAIT.actual.json',r)
    print(json.dumps(r,ensure_ascii=False))

def close():
    bus('status','--task',TASK,'--state','done','--repo',str(D),'--summary','Exact0f selected-method fixture repair candidate prepared; actual pure formatter PASS with negative baseline and module-restoration controls','--next-step','Root may review and separately authorize Git publishing; no D/W writes in this scope')
    bus('poll','--task',TASK,'--limit','5')
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            b=p.read_bytes();files.append({'relative_path':p.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':sha(b)})
    put(ROOT/'CLOSED.actual.json',{'machine_id':MID,'observed_at_utc':now(),'status':'SOURCE_ONLY_CANDIDATE_FOCUSED_SELECTED_METHOD_PASS','repo_target':TEST,'exact_baseline':HEAD,'files':files,'aggregate_bytes_before_this_receipt':meter(ROOT),'D_W_Git_build_SDK_game_screen_mutations':0,'owned_processes':[],'remaining_future_bytes':0,'no_business_or_full_CI_qualification':True})
    p=ROOT/'CLOSED.actual.json';print(json.dumps({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'aggregate_bytes':meter(ROOT)}))

if __name__=='__main__': {'prepare':prepare,'focused':focused,'run':run,'close':close}[sys.argv[1]]()
