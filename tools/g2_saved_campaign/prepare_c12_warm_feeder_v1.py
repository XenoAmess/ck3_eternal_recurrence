"""C12 same-Game continuity metadata port; no control, process or ledger writes."""
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from prepare_c11_cold_feeder_v1 import replace_function

T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
O=T.parent.parent/'p51-fresh1066-v20261019-prepare01/c12-war4892-warm86'
REVIEW=Path('Z:/ck3_mod_rewrite/_runtime/c12-feeder-review86')
ADMISSION='ROOT-C12-WARM-FEEDER-ADMISSION86.json'
MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE={'root_p37c11_same_game_loop_feeder84.py':'e7c62f93a6355e90772aa477936339c2abb20ae95125f8be4a2f8aa4ead0c55c',
 'root_continuity_window_c11_84.py':'833f4e6f55225c1a134df5fbe0133bc8807a599c707baf33d70092181914717d',
 'launch_c11_feeder84.py':'d75c813879c445e2095801f8ef73827820a011f16b29a77bd0d12755f234ad3b'}

ADMITTED='''def admitted():
    global BASELINE_CYCLES,BASELINE_DATE_RAW
    verified=read(N/"ROOT-C12-WARM-FEEDER-ADMISSION86.json")
    if (verified.get("schema")!="xar.C12-normal-source-warm-feeder/v1"
            or verified.get("machine_id")!="xenoamess-full-tower-eb9d2c1186"
            or verified.get("completed_cycles")!=2327 or verified.get("first_control_sequence")!=4896
            or verified.get("ordinary_cycle_credit")!=0 or verified.get("original_actions_replayed") is not False
            or verified.get("window_origin_reset") is not False):raise ValueError("exact C12 warm metadata required")
    def checked(ref):
        if (pin(Path(ref["path"]))!={"path":ref["path"],"sha256":ref["sha256"]}
                or Path(ref["path"]).stat().st_size!=ref["bytes"]):raise ValueError("C12 source pin changed")
        return read(Path(ref["path"]))
    ready=checked(verified["sources"]["warm_ready"]);old=checked(verified["sources"]["old_ledger"])
    clear=checked(ready["old_clear"]);cleared=checked(clear["response"])["result"]["structured_content"]
    before=checked(clear["state_before"]);closed=checked(ready["old_normal_closed"])
    marker=checked(ready["warm_bound"]);current=checked(ready["map_admission"])
    launch=read(N/"ROOT-ACTUAL-GAME-LAUNCH-C11.json")
    if (ready["machine_id"]!="xenoamess-full-tower-eb9d2c1186" or ready["driver_state_restore_kind"]!="same_pid_hot"
            or ready["completed_cycles"]!=2327 or ready["pending_cycle"] is not None or ready["ordinary_cycle_credit"]!=0
            or ready["Game_Native29_publisher_OBS_restarted"] is not False
            or ready["old4892_or_other_action_replayed"] is not False
            or ready["unsupported_Sway_execution_query_mask_preserved"] is not True
            or clear["completed_cycles"]!=2327 or clear["pending_cycle"] is not None or clear["new_RPC_calls"]!=0
            or clear["original4892_replayed"] is not False or clear["original_FULL4846_still_failed"] is not True
            or cleared["status"]!="blocked_no_action_observed_replan_required" or cleared["business_credit_added"] is not False
            or cleared["new_MCP_or_native_calls"]!=0 or cleared["fresh_frame"]!=before["before"]
            or closed["normal"] is not True or any(p["exit_code"]!=0 or p["kernel_exit_observed"] is not True for p in closed["processes"])
            or marker["completed_cycles"]!=2327 or marker["pending_cycle"] is not None
            or marker["fresh_opening"]!=ready["fresh_opening"] or marker["ordinary_cycle_credit"]!=0
            or current["status"]!="GREEN" or current["reviewer"]!="/root"
            or current["actual_initial_frame"]!=ready["fresh_opening"] or current["game_pid"]!=launch["pid"]
            or current["game_creation_filetime"]!=launch["creation_filetime"]
            or launch["pid"]!=15512 or launch["creation_filetime"]!=134368811928524228
            or ready["Game_pid"]!=launch["pid"] or ready["Game_creation_filetime"]!=launch["creation_filetime"]
            or old["start_date_raw"]!=53144328 or old["target_date_raw"]!=53407128
            or old["last_settled_cycles"]!=2327 or old["last_settled_date_raw"]!=53192808
            or ready["fresh_opening"]["date_raw"]!=53192808
            or ready["fresh_opening"]["native_revision"]<before["before"]["native_revision"]):
        raise ValueError("actual C12 clear/warm/Rootmap/settled lineage differs")
    BASELINE_CYCLES=2327;BASELINE_DATE_RAW=53144328
    return {**verified,"old_ledger":old,"new_game":launch,"fresh_opening":ready["fresh_opening"]}
'''

ATTACH='''def continuity_attach(verified,first_control=3,resume_admission=None):
    if resume_admission is not None or first_control!=verified["first_control_sequence"]:
        raise ValueError("only exact existing C12 FULL4896 continuation accepted")
    ledger=WindowLedger(CONTINUITY_WINDOW);prior=ledger.load()
    source=pin(N/"ROOT-C12-WARM-FEEDER-ADMISSION86.json")
    if prior.get("last_sameGame_source_handoff")==source:
        if prior["status"] not in ("running","complete"):raise ValueError("later interruption unresolved")
        return prior
    if prior!=verified["old_ledger"]:raise ValueError("pre-C12 continuity ledger changed")
    return ledger.apply("C12_sameGame_source2020_warm_verified",{
        "machine_id":"xenoamess-full-tower-eb9d2c1186","evidence_id":"C12-normal-warm:"+source["sha256"],
        "source":source,"game":verified["new_game"],"frame":verified["fresh_opening"],"completed_cycles":2327})
'''

BRANCH='''    if kind == "C12_sameGame_source2020_warm_verified":
        frame=frame_binding(details["frame"])
        if (state["status"]!="repair_required" or game_binding(details["game"])!=state["game_binding"]
                or state["game_binding"]["pid"]!=15512 or state["start_date_raw"]!=53144328 or state["target_date_raw"]!=53407128
                or state["last_settled_cycles"]!=2327 or details["completed_cycles"]!=2327
                or state["last_settled_date_raw"]!=frame["date_raw"] or frame["date_raw"]!=53192808
                or frame["actor_character_id"]!=40526 or frame["episode_run_id"]!="native-40526-1bec95182886"
                or frame["native_revision"]<351):raise ValueError("exact sameGame C12 warm source required")
        state.update(status="running",latest_binding=frame,
            sameGame_source_handoff_count=state.get("sameGame_source_handoff_count",0)+1,
            manual_repair_count=state.get("manual_repair_count",0)+1,
            last_sameGame_source_handoff=details["source"],previous_interruption=state.get("interruption"))
        return state
'''


def require(ok,why):
    if not ok:raise ValueError('C12 feeder source: '+why)


def pin(path):
    p=Path(path);raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def build():
    sources={}
    for name,digest in BASE.items():
        raw=(T/name).read_bytes();require(hashlib.sha256(raw).hexdigest()==digest,'actual C11 base source differs')
        sources[name]=raw.decode('utf8')
    feeder=sources['root_p37c11_same_game_loop_feeder84.py']
    for old,new in [('root_continuity_window_c11_84','root_continuity_window_c12_86'),('P37C11','P37C12'),
        ('REQUEST-ADMISSION-CLOSED-C11','REQUEST-ADMISSION-CLOSED-C12'),
        ('p37-queue/ROOT-C11-NORMAL-COLD-BOUND.json','p37-queue/ROOT-C12-NORMAL-SOURCE-WARM-BOUND.json')]:feeder=feeder.replace(old,new)
    before=ast.parse(feeder)
    feeder=replace_function(feeder,'admitted',ADMITTED);feeder=replace_function(feeder,'continuity_attach',ATTACH)
    after=ast.parse(feeder)
    for node in before.body:
        if isinstance(node,ast.FunctionDef) and node.name not in ('admitted','continuity_attach'):
            other=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
            require(ast.dump(node,include_attributes=False)==ast.dump(other,include_attributes=False),'ordinary feeder changed: '+node.name)
    original=sources['root_continuity_window_c11_84.py'];needle='    if kind == "C11_native29_cold1863_verified":'
    require(original.count(needle)==1,'actual ledger insertion seam differs')
    ledger=original.replace(needle,BRANCH+needle)
    require(ledger.replace(BRANCH,'')==original,'prior ledger changed')
    launcher=sources['launch_c11_feeder84.py'].replace('root_p37c11_same_game_loop_feeder84.py','root_p37c12_same_game_loop_feeder86.py').replace('ROOT-P37C11-FEEDER.lock','ROOT-P37C12-FEEDER.lock')
    files={'root_p37c12_same_game_loop_feeder86.py':feeder.encode(),'root_continuity_window_c12_86.py':ledger.encode(),'launch_c12_feeder86.py':launcher.encode()}
    for name,raw in files.items():compile(raw,name,'exec')
    return files


def main():
    files=build();ready=O/'ACTUAL-WARM-READY.json';oldpath=O/'CONTINUITY-BEFORE-C12.json'
    require(pin(ready)['sha256']=='9ccabdffecced5319ccaba51c923aceaeaab06de023891f0702844fd9f88a610'
        and pin(oldpath)['sha256']=='6b2aefcd8b026722c3ae686b4336bdd9928b1c9618b25d804c52af099e4a36e2','actual warm/oldledger pin differs')
    admission={'schema':'xar.C12-normal-source-warm-feeder/v1','machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'completed_cycles':2327,'first_control_sequence':4896,'ordinary_cycle_credit':0,'original_actions_replayed':False,'window_origin_reset':False,
        'sources':{'warm_ready':pin(ready),'old_ledger':pin(oldpath)}}
    raw_ad=(json.dumps(admission,separators=(',',':'))+'\n').encode()
    original=json.loads(oldpath.read_bytes());holder={'state':copy.deepcopy(original)};ns={}
    exec(compile(files['root_continuity_window_c12_86.py'],'actual-c12-ledger','exec'),ns)
    class MemoryLedger:
        def __init__(self,path):pass
        def load(self):return copy.deepcopy(holder['state'])
        def apply(self,kind,details):
            holder['state']=ns['transition'](holder['state'],kind,details);return holder['state']
    def read(path):return copy.deepcopy(admission) if Path(path)==T/ADMISSION else json.loads(Path(path).read_bytes())
    def finite_pin(path):
        p={'path':str(path),'sha256':hashlib.sha256(raw_ad).hexdigest()} if Path(path)==T/ADMISSION else pin(path)
        return {k:p[k] for k in ('path','sha256')}
    env={'N':T,'Path':Path,'read':read,'pin':finite_pin,'WindowLedger':MemoryLedger,'CONTINUITY_WINDOW':T.parent/'ROOT-CONTINUITY-WINDOW.json'}
    nodes=[n for n in ast.parse(files['root_p37c12_same_game_loop_feeder86.py']).body if isinstance(n,ast.FunctionDef) and n.name in ('admitted','continuity_attach')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-c12-admission-attach','exec'),env)
    verified=env['admitted']();result=env['continuity_attach'](verified,4896)
    changed={'status','latest_binding','sameGame_source_handoff_count','manual_repair_count','last_sameGame_source_handoff','previous_interruption'}
    require(result['status']=='running' and all(result[k]==v for k,v in original.items() if k not in changed),'origin/credit/window/wall changed')
    wrong=copy.deepcopy(verified);wrong['new_game']['pid']+=1;holder['state']=copy.deepcopy(original)
    try:env['continuity_attach'](wrong,4896)
    except ValueError:pass
    else:raise ValueError('foreign Game accepted')
    cap=sum(map(len,files.values()))*2+len(raw_ad)*2+8192
    require(cap<=131072,'128KiB review+install+receipt bound exceeded')
    require(not REVIEW.exists(),'create-only review already exists');REVIEW.mkdir(parents=True)
    for name,raw in {**files,ADMISSION:raw_ad}.items():
        with (REVIEW/name).open('xb') as f:f.write(raw)
    report={'machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_ONLY_FROZEN',
        'producer':pin(__file__),'files':[pin(REVIEW/n) for n in (*files,ADMISSION)],'metadata_gross_cap':cap,
        'cases':'Actual warm/clear/map inputs and exact admitted+attach PASS; foreign Game rejected; other feeder function AST equal, old ledger bytes preserved.',
        'partial22_recredited':False,'new_cold_claimed':False,'T0_endpoint_wall_window_preserved':True,'first_control':4896,'RPC_or_live_writes':0}
    with (REVIEW/'REVIEW.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(pin(REVIEW/'REVIEW.json')));print(json.dumps(report['files']))


if __name__=='__main__':main()
