"""Finite C11 metadata continuation; never submit a control or modify a ledger."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P=T.parent.parent/'p51-fresh1066-v20261019-prepare01'
O=P/'c11-prisoner4286-failure85'
MACHINE='xenoamess-full-tower-eb9d2c1186'
REVIEW=Path('Z:/ck3_mod_rewrite/_runtime/c11-feeder-review84')
ADMISSION='ROOT-C11-COLD-FEEDER-ADMISSION84.json'
BASES={'root_p37c10_same_game_loop_feeder81.py':'3607cf5f6555c8aeed6c1c56af3a0d3716ab7fbb3a7a68c4cc2b5437cde8fde7',
 'root_continuity_window_c10_81.py':'2c907f63d8cd3283b2404eeb2cab75fe9167049009eddc3e31068bf0864eb39f',
 'launch_c10_feeder81.py':'2bc31f2afe194ad9742fc7711ad266e84992b8e353ec06cc3d30f79f7bc6f90a'}

ADMITTED='''def admitted():
    global BASELINE_CYCLES,BASELINE_DATE_RAW
    verified=read(N/"ROOT-C11-COLD-FEEDER-ADMISSION84.json")
    if (verified.get("schema")!="xar.C11-cold-prisoner-resumed-feeder/v1"
            or verified.get("machine_id")!="xenoamess-full-tower-eb9d2c1186"
            or verified.get("completed_cycles")!=2035 or verified.get("first_control_sequence")!=4293
            or verified.get("ordinary_cycle_credit")!=0 or verified.get("original_actions_replayed") is not False
            or verified.get("window_origin_reset") is not False):raise ValueError("exact C11 metadata admission required")
    def checked(ref):
        if (pin(Path(ref["path"]))!={"path":ref["path"],"sha256":ref["sha256"]}
                or Path(ref["path"]).stat().st_size!=ref["bytes"]):raise ValueError("C11 metadata source changed")
        return read(Path(ref["path"]))
    sources=verified["sources"]
    recovery=checked(sources["recovery"]);cold=checked(recovery["cold_ready"])
    marker=checked(cold["cold_bound"]);launch=checked(cold["actual_Game"]);current=checked(cold["map_admission"])
    failed=checked(recovery["frozen_failure"]);old=checked(recovery["old_continuity_ledger"])
    turn=checked(recovery["settled_cycle"])
    for ref in recovery["actual_sources"].values():checked(ref)
    closed=checked(recovery["actual_sources"]["4289"])
    before=next(r for r in failed["source_refs"] if r["original_source"].endswith("p37-queue\\\\ROOT-CUMULATIVE-LOOP-STATE.json"))
    partial=checked(before)
    if (recovery["machine_id"]!="xenoamess-full-tower-eb9d2c1186"
            or recovery["status"]!="ACTUAL_ORIGINAL_READONLY_RESPONSE_RECONSUMED_AND_SETTLED"
            or recovery["original_response_replayed"] is not False or recovery["original_release_or_query_resubmitted"] is not False
            or recovery["install4287_MCP_calls"]!=0 or recovery["reconsume4288_MCP_calls"]!=0
            or cold["status"]!="ACTUAL_COLD_SEM_CAP_AND_ROOT_MAP_GREEN"
            or marker["completed_cycles"]!=2010 or marker["T0_date_raw"]!=53144328
            or marker["new_ordinary_cycle_credit"]!=0 or marker["AUTO_or_MET_replayed"] is not False
            or marker["opening_frame"]["date_raw"]!=53189040
            or current["status"]!="GREEN" or current["reviewer"]!="/root"
            or current["actual_initial_frame"]!=marker["opening_frame"]
            or current["game_pid"]!=launch["pid"]!=0
            or current["game_creation_filetime"]!=launch["creation_filetime"]
            or launch["pid"]!=15512 or launch["creation_filetime"]!=134368811928524228
            or failed["completed_cycles"]!=partial["completed_cycles"] or failed["completed_cycles"]!=2034
            or partial["before"]!=failed["before"] or failed["before"]["date_raw"]!=53189232
            or closed["result"]["is_error"] is not False
            or closed["request"]!={"sequence":4289,"command":"full_loop","arguments":{"max_turns":1}}
            or closed["result"]["structured_content"]!=recovery["actual_FULL4289_summary"]
            or recovery["completed_cycles"]!=2035 or recovery["current_frame"]!=turn["after"]
            or turn["global_turn"]!=2035 or turn["auto_sequence"]!=4286 or turn["date_delta_raw"]!=0
            or turn["observation"]["custody_causation_or_cost_credit_inferred"] is not False
            or turn["observation"]["replay_allowed"] is not False
            or recovery["current_frame"]["date_raw"]!=53189232
            or old["start_date_raw"]!=53144328 or old["target_date_raw"]!=53407128
            or old["last_settled_cycles"]!=2010 or old["last_settled_date_raw"]!=53189040):
        raise ValueError("actual cold/partial/settlement lineage differs")
    BASELINE_CYCLES=2035;BASELINE_DATE_RAW=53144328
    return {**verified,"old_ledger":old,"old_game":old["game_binding"],"new_game":launch,
        "fresh_opening":marker["opening_frame"],"partial_frame":failed["before"],"restored_frame":turn["after"],
        "failed_packet":recovery["frozen_failure"]}
'''

ATTACH='''def continuity_attach(verified,first_control=3,resume_admission=None):
    if resume_admission is not None or first_control!=verified["first_control_sequence"]:
        raise ValueError("only exact C11 existing FULL4293 continuation accepted")
    ledger=WindowLedger(CONTINUITY_WINDOW);prior=ledger.load()
    source=pin(N/"ROOT-C11-COLD-FEEDER-ADMISSION84.json")
    if prior.get("last_C11_prisoner_resume")==source:
        if prior.get("status") not in ("running","complete"):raise ValueError("later interruption remains unresolved")
        return prior
    if prior.get("last_cold_handoff_source")!=source and prior!=verified["old_ledger"]:
        raise ValueError("original pre-C11 continuity ledger changed")
    common={"machine_id":"xenoamess-full-tower-eb9d2c1186","source":source,"game":verified["new_game"]}
    ledger.apply("C11_native29_cold1863_verified",{**common,"evidence_id":"C11-cold:"+source["sha256"],
        "old_game":verified["old_game"],"frame":verified["fresh_opening"],"completed_cycles":2010})
    ledger.apply("repair_required",{**common,"evidence_id":"C11-original-FULL4237-failed:"+source["sha256"],
        "source":verified["failed_packet"],"frame":verified["partial_frame"],"completed_cycles":2034,
        "reason":"Original FULL4237 failed after24 genuinely settled cycles and8 days; AUTO4286 remained uncredited"})
    return ledger.apply("C11_prisoner4286_original_result_settled",{**common,"evidence_id":"C11-original4286-settled:"+source["sha256"],
        "frame":verified["restored_frame"],"completed_cycles":2035})
'''

BRANCH='''    if kind == "C11_native29_cold1863_verified":
        frame=frame_binding(details["frame"]);new=game_binding(details["game"])
        if (state["status"]!="repair_required" or details["old_game"]!=state["game_binding"]
                or state["game_binding"]["pid"]!=153556 or new["pid"]!=15512
                or state["start_date_raw"]!=53144328 or state["target_date_raw"]!=53407128
                or state["last_settled_cycles"]!=2010 or details["completed_cycles"]!=2010
                or state["last_settled_date_raw"]!=frame["date_raw"] or frame["date_raw"]!=53189040
                or frame["actor_character_id"]!=40526 or frame["episode_run_id"]!="native-40526-1bec95182886"
                or frame["native_revision"]!=1):raise ValueError("exact C11 cold provenance required")
        state.update(status="running",game_binding=new,latest_binding=frame,
            cold_handoff_count=state.get("cold_handoff_count",0)+1,last_cold_handoff_source=details["source"],
            last_cold_binding={"old_game":state["game_binding"],"new_game":new},previous_interruption=state.get("interruption"))
        return state
    if kind == "C11_prisoner4286_original_result_settled":
        frame=frame_binding(details["frame"])
        if (state["status"]!="repair_required" or game_binding(details["game"])!=state["game_binding"]
                or state["start_date_raw"]!=53144328 or state["target_date_raw"]!=53407128
                or state["last_settled_cycles"]!=2034 or details["completed_cycles"]!=2035
                or state["last_settled_date_raw"]!=frame["date_raw"] or frame["date_raw"]!=53189232
                or frame["actor_character_id"]!=40526 or frame["episode_run_id"]!="native-40526-1bec95182886"
                or frame["native_revision"]!=27):raise ValueError("exact original4286 settlement required")
        state.update(status="running",last_settled_cycles=2035,latest_binding=frame,
            manual_repair_count=state.get("manual_repair_count",0)+1,last_C11_prisoner_resume=details["source"],
            previous_interruption=state.get("interruption"))
        return state
'''


def require(ok,why):
    if not ok:raise ValueError('C11 feeder preparation: '+why)


def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path).resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def replace_function(text,name,replacement):
    n=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(keepends=True)
    return ''.join(lines[:n.lineno-1])+replacement+'\n'+''.join(lines[n.end_lineno:])


def build():
    source={}
    for name,digest in BASES.items():
        raw=(T/name).read_bytes();require(hashlib.sha256(raw).hexdigest()==digest,'actual base changed')
        source[name]=raw.decode('utf-8')
    feeder=source['root_p37c10_same_game_loop_feeder81.py']
    for old,new in [('root_continuity_window_c10_81','root_continuity_window_c11_84'),
        ('root_p37c10_same_game_loop_feeder81','root_p37c11_same_game_loop_feeder84'),('P37C10','P37C11'),('C10','C11'),
        ('ROOT-ACTUAL-GAME-LAUNCH-C4.json','ROOT-ACTUAL-GAME-LAUNCH-C11.json')]:feeder=feeder.replace(old,new)
    baseline=ast.parse(feeder)
    feeder=replace_function(feeder,'admitted',ADMITTED)
    feeder=replace_function(feeder,'continuity_attach',ATTACH)
    feeder=feeder.replace('p37-queue/ROOT-C11-NORMAL-SOURCE-WARM-BOUND.json','p37-queue/ROOT-C11-NORMAL-COLD-BOUND.json')
    after=ast.parse(feeder)
    for before in baseline.body:
        if isinstance(before,ast.FunctionDef) and before.name not in ('admitted','continuity_attach'):
            current=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name==before.name)
            require(ast.dump(before,include_attributes=False)==ast.dump(current,include_attributes=False),'unapproved function change: '+before.name)
    ledger=source['root_continuity_window_c10_81.py']
    needle='    if kind == "C10_normal_source_day1821_handoff_verified":'
    require(ledger.count(needle)==1,'actual ledger seam differs')
    ledger=ledger.replace(needle,BRANCH+needle)
    require(ledger.replace(BRANCH,'')==source['root_continuity_window_c10_81.py'],'existing ledger bytes changed')
    launcher=source['launch_c10_feeder81.py'].replace('root_p37c10_same_game_loop_feeder81.py','root_p37c11_same_game_loop_feeder84.py').replace('ROOT-P37C10-FEEDER.lock','ROOT-P37C11-FEEDER.lock')
    files={'root_p37c11_same_game_loop_feeder84.py':feeder.encode(),
        'root_continuity_window_c11_84.py':ledger.encode(),'launch_c11_feeder84.py':launcher.encode()}
    for name,raw in files.items():compile(raw,name,'exec')
    return files


def main():
    files=build()
    recovery=json.loads((O/'ACTUAL-RECOVERY.json').read_bytes())
    require(pin(O/'ACTUAL-RECOVERY.json')['sha256']=='020c5c68ac0f58cb67685028756c23f5b8d5115f11bc1a1c5776c74bfe44117c','sealed actual recovery changed')
    admission={'schema':'xar.C11-cold-prisoner-resumed-feeder/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'completed_cycles':2035,'first_control_sequence':4293,
        'ordinary_cycle_credit':0,'original_actions_replayed':False,'window_origin_reset':False,
        'sources':{'recovery':pin(O/'ACTUAL-RECOVERY.json')}}
    raw_ad=(json.dumps(admission,separators=(',',':'))+'\n').encode()
    # Execute the exact new admission/attach AST with only an in-memory ledger.
    ledger_ns={'__name__':'fixture'};exec(compile(files['root_continuity_window_c11_84.py'],'coldledger','exec'),ledger_ns)
    original=json.loads(Path(recovery['old_continuity_ledger']['path']).read_bytes())
    holder={'state':copy.deepcopy(original),'kinds':[]}
    class MemoryLedger:
        def __init__(self,path):pass
        def load(self):return copy.deepcopy(holder['state'])
        def apply(self,kind,details):
            holder['state']=ledger_ns['transition'](holder['state'],kind,details);holder['kinds'].append(kind)
            return copy.deepcopy(holder['state'])
    def read(path):
        return copy.deepcopy(admission) if Path(path)==T/ADMISSION else json.loads(Path(path).read_bytes())
    def finite_pin(path):
        if Path(path)==T/ADMISSION:return {'path':str(path),'sha256':hashlib.sha256(raw_ad).hexdigest()}
        p=pin(path);return {k:p[k] for k in ('path','sha256')}
    ns={'N':T,'Path':Path,'read':read,'pin':finite_pin,'WindowLedger':MemoryLedger,'CONTINUITY_WINDOW':T.parent/'ROOT-CONTINUITY-WINDOW.json'}
    tree=ast.parse(files['root_p37c11_same_game_loop_feeder84.py'])
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('admitted','continuity_attach')]
    exec(compile(ast.Module(body=selected,type_ignores=[]),'newfeederadmission','exec'),ns)
    verified=ns['admitted']();result=ns['continuity_attach'](verified,4293,None)
    require(result['last_settled_cycles']==2035 and result['last_settled_date_raw']==53189232
        and result['start_date_raw']==original['start_date_raw'] and result['target_date_raw']==original['target_date_raw']
        and result['window_id']==original['window_id'] and result['game_binding']['pid']==15512,'actual three-stage continuation differs')
    preserved=set(original)-{'status','game_binding','latest_binding','cold_handoff_count','last_cold_handoff_source',
        'previous_interruption','interruption','interrupted_window_id','last_settled_cycles','last_settled_date_raw','manual_repair_count'}
    require(all(result[k]==original[k] for k in preserved),'unrelated origin/wall metadata changed')
    wrong=copy.deepcopy(verified);wrong['new_game']['pid']=15513;holder['state']=copy.deepcopy(original)
    try:ns['continuity_attach'](wrong,4293,None)
    except ValueError:pass
    else:raise ValueError('foreign new Game accepted')
    require(sum(map(len,files.values()))*2+len(raw_ad)*2+8192<=131072,'128KiB cumulative feeder cap exceeded')
    require(not REVIEW.exists(),'create-only review already exists')
    REVIEW.mkdir(parents=True)
    for name,raw in {**files,ADMISSION:raw_ad}.items():
        with (REVIEW/name).open('xb') as f:f.write(raw)
    report={'schema':'xar.C11-cold-feeder-source-review/v1','machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_ONLY_NOT_RUNTIME_ADOPTED','producer':pin(__file__),'files':[pin(REVIEW/n) for n in (*files,ADMISSION)],
        'actual_admitted_and_attach_fixture_PASS':True,'wrong_new_Game_rejected':True,'other_feeder_function_AST_unchanged':True,
        'old_ledger_bytes_unchanged_except_two_inserted_branches':True,'first_control_sequence':4293,'live_calls_or_writes':0,
        'phases':['cold2010/1863','originalfailedFULL4237 partial2034/1871','original4286plusMET2035/1871'],
        'cumulative_review_install_admission_reserve_upper':sum(map(len,files.values()))*2+len(raw_ad)*2+8192}
    with (REVIEW/'REVIEW.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(pin(REVIEW/'REVIEW.json')));print(json.dumps(report['files']))


if __name__=='__main__':main()
