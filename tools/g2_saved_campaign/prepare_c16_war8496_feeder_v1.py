"""Pure finite feeder handoff after actual observation8496; no runtime writes."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import types

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
F = T.parent.parent / 'p51-fresh1066-v20261019-prepare01/c16-war-results8495-failure91'
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
ADMISSION = 'ROOT-C16-WAR8495-FEEDER-ADMISSION91.json'
PINS = {'root_p37c16_same_game_loop_feeder90.py': 'eb16c1c6139ce0719dd2b409fc70d4a24f87b23db2afd65f8e1f562028d6a245',
    'root_continuity_window_c16_90.py': '5ad54f9a296dabd81e8fa7472d048095ecb77f7c1c5717692ac721204331e7d9',
    'launch_c16_feeder90.py': 'bfe22c39a9c15825ac92dd3e596bc7d802d63e8817b9306365ee331637f0af39'}
INDEX_SHA = 'c1250d3b6011f3e6c9efb6c7cc286cafce3ce2a2902c4a54bf504094b345a6a8'
ADMITTED = '''def admitted():
    global BASELINE_CYCLES,BASELINE_DATE_RAW
    a=read(N/"ROOT-C16-WAR8495-FEEDER-ADMISSION91.json")
    if (a.get("schema")!="xar.C16-war8496-feeder/v1" or a.get("machine_id")!="xenoamess-full-tower-eb9d2c1186"
            or a.get("first_control_sequence")!=8500):raise ValueError("exact recovered C16 FULL8500 required")
    def checked(r):
        p=Path(r["path"])
        if pin(p)!={"path":r["path"],"sha256":r["sha256"]} or p.stat().st_size!=r["bytes"]:raise ValueError("C16 recovery source differs")
        return read(p)
    index=checked(a["actual_recovery"])
    if index.get("machine_id")!=a["machine_id"] or a["actual_recovery"]["sha256"]!="c1250d3b6011f3e6c9efb6c7cc286cafce3ce2a2902c4a54bf504094b345a6a8":raise ValueError("original actual recovery index differs")
    old=checked(index["old_ledger"]);audit=checked(index["audit"]);response=checked(index["response"])
    ended=checked(index["old_feeder_task_closed"]);request=checked(index["new_FULL8500_request"])
    final=checked(index["final_SEM"])["result"]["structured_content"]
    result=response["result"]["structured_content"];frame=audit["final_frame"]
    if (old["status"]!="repair_required" or old["last_settled_cycles"]!=3828 or old["last_settled_date_raw"]!=53217048
            or old["game_binding"]!={"pid":30852,"creation_date":"20261019160615.902761+000"}
            or old["start_date_raw"]!=53144328 or old["target_date_raw"]!=53407128
            or response["request"]["sequence"]!=8496 or response["result"].get("is_error") is not False
            or audit.get("status")!="observed_clear" or audit.get("window_presence")!="hidden"
            or result.get("status")!="observed_clear" or result.get("pending_retained") is not False
            or any(audit.get(k)!=0 for k in ("ordinary_cycle_credit","ui_closure_credit","new_pause_submissions","new_close_submissions"))
            or audit["original_pending"]["global_turn"]!=3829 or audit["original_auto"]!=8495
            or audit["completed_cycles_before_after"]!=3828 or audit["physical_date_drift_raw"]!=24
            or frame["date_raw"]!=53217072 or frame["native_revision"]!=1127 or frame["revision"]!=1128
            or frame["actor_character_id"]!=40526 or frame["episode_run_id"]!="native-40526-1bec95182886"
            or final.get("paused") is not True or final.get("map_ready") is not True
            or "war_results_window_v1_close_pending" not in final or final["war_results_window_v1_close_pending"] is not None
            or final["date_raw"]!=frame["date_raw"] or final["native_revision"]!=frame["native_revision"]
            or final["revision"]!=frame["revision"] or final["played_character"]["character_id"]!=40526
            or final["diagnostics"]["bridge_pid"]!=30852
            or ended.get("child_exit_code")!=0 or ended.get("bootstrap_exit_code")!=0
            or ended.get("job_active_after_stage")!=0 or ended.get("forced_remaining_cleanup") is not False
            or request!={"sequence":8500,"command":"full_loop","arguments":{"max_turns":30}}):raise ValueError("actual same-Game observation/closed old feeder differs")
    BASELINE_CYCLES=3828;BASELINE_DATE_RAW=53144328
    return {**a,"old_ledger":old,"opening":frame,"game":{"pid":30852,"creation_date":"20261019160615.902761+000"}}
'''
ATTACH = '''def continuity_attach(v,first_control=3,resume_admission=None):
    if resume_admission is not None or first_control!=8500:raise ValueError("follow actual FULL8500 only")
    ledger=WindowLedger(CONTINUITY_WINDOW);s=ledger.load();p=pin(N/"ROOT-C16-WAR8495-FEEDER-ADMISSION91.json")
    if s.get("last_C16_war8496")==p:
        if s["status"] not in ("running","complete"):raise ValueError("later interruption unresolved")
        return s
    if s!=v["old_ledger"]:raise ValueError("old ledger changed")
    return ledger.apply("C16_war8496_observed_clear",{"machine_id":"xenoamess-full-tower-eb9d2c1186",
        "source":p,"evidence_id":"C16-war8496:"+p["sha256"],"old_ledger":s,"game":v["game"],"frame":v["opening"]})
'''
EVENT = '''    if kind == "C16_war8496_observed_clear":
        frame=frame_binding(details["frame"])
        if (state!=details["old_ledger"] or state["status"]!="repair_required"
                or state["game_binding"]!=game_binding(details["game"]) or state["game_binding"]["pid"]!=30852
                or state["last_settled_cycles"]!=3828 or state["last_settled_date_raw"]!=53217048
                or state["start_date_raw"]!=53144328 or state["target_date_raw"]!=53407128
                or frame["date_raw"]!=53217072 or frame["native_revision"]!=1127 or frame["revision"]!=1128
                or frame["actor_character_id"]!=40526 or frame["episode_run_id"]!="native-40526-1bec95182886"):
            raise ValueError("exact C16 observation8496 continuation required")
        state.update(status="running",latest_binding=frame,last_settled_date_raw=53217072,
            last_C16_war8496=details["source"],previous_interruption=state.get("interruption"),
            war8496_recovery={"failed_FULL":8476,"original_AUTO":8495,"partial9_already_accounted":True,
                "original_close_replayed":False,"ordinary_cycle_credit":0,"ui_closure_credit":0,
                "physical_date_drift_raw":24,"physical_drift_credited_as_cycle":False})
        return state
'''


def replace_function(source, name, new):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+new+''.join(lines[node.end_lineno:])


def build_sources():
    raw={}
    for name,sha in PINS.items():
        payload=(T/name).read_bytes()
        if hashlib.sha256(payload).hexdigest()!=sha:raise ValueError('actual frozen feeder source changed')
        raw[name]=payload.decode()
    feeder=raw['root_p37c16_same_game_loop_feeder90.py'].replace('root_continuity_window_c16_90','root_continuity_window_c16_91')
    feeder=replace_function(replace_function(feeder,'admitted',ADMITTED),'continuity_attach',ATTACH)
    ledger=raw['root_continuity_window_c16_90.py'];anchor='    if kind == "C16_SAVE6397_cold_verified":\n'
    if ledger.count(anchor)!=1:raise ValueError('exact ledger insertion seam differs')
    ledger=ledger.replace(anchor,EVENT+anchor,1)
    launch=raw['launch_c16_feeder90.py'].replace('root_p37c16_same_game_loop_feeder90.py','root_p37c16_same_game_loop_feeder91.py')
    output={'root_p37c16_same_game_loop_feeder91.py':feeder.encode(),
        'root_continuity_window_c16_91.py':ledger.encode(),'launch_c16_feeder91.py':launch.encode()}
    for value in output.values():compile(value,'finite-feeder','exec')
    oldtree=ast.parse(raw['root_p37c16_same_game_loop_feeder90.py']);newtree=ast.parse(feeder)
    for node in oldtree.body:
        if isinstance(node,ast.FunctionDef) and node.name not in ('admitted','continuity_attach'):
            other=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
            if ast.dump(node)!=ast.dump(other):raise ValueError('original main/publish/other algorithm changed')
    return output


def qualification():
    sources=build_sources();index_path=F/'ACTUAL-RECOVERY-8496-CLOSED.json';raw=index_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INDEX_SHA:raise ValueError('actual recovery index changed')
    admission={'schema':'xar.C16-war8496-feeder/v1','machine_id':MACHINE,'first_control_sequence':8500,
        'actual_recovery':{'path':str(index_path),'bytes':len(raw),'sha256':INDEX_SHA}}
    def read(path):
        return admission if Path(path)==T/ADMISSION else json.loads(Path(path).read_bytes())
    def pin(path):return {'path':str(path),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    tree=ast.parse(sources['root_p37c16_same_game_loop_feeder91.py'])
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admitted')
    ns={'N':T,'Path':Path,'read':read,'pin':pin}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-admitted','exec'),ns)
    value=ns['admitted']()
    mod=types.ModuleType('finite_ledger');exec(compile(sources['root_continuity_window_c16_91.py'],'actual-ledger','exec'),mod.__dict__)
    old=value['old_ledger'];details={'evidence_id':'qualified-8496','source':{'path':'fixture','sha256':INDEX_SHA},
        'old_ledger':old,'frame':value['opening'],'game':value['game'],'machine_id':MACHINE}
    changed=mod.transition(old,'C16_war8496_observed_clear',details)
    for key in ('start_date_raw','target_date_raw','window_id','window_start_source','last_settled_cycles'):
        if changed[key]!=old[key]:raise ValueError('origin or settled credit changed')
    bad=copy.deepcopy(details);bad['game']['pid']+=1
    try:mod.transition(old,'C16_war8496_observed_clear',bad)
    except ValueError:pass
    else:raise ValueError('wrong old Game accepted')
    return admission,{'machine_id':MACHINE,'utc':datetime.now(timezone.utc).isoformat(),'D_writes':0,'Game_RPC':0,
        'checks':['actual closed recovery/admission PASS','original main/publish/all other functions AST equal',
            'finite reducer actual positive/wrong Game reject; original window/T0/cycles preserved'],
        'sources':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sources.items()},
        'source_bytes':sum(map(len,sources.values()))}


if __name__=='__main__':
    import sys
    admission,proof=qualification()
    output=Path(sys.argv[1])
    with output.open('x',encoding='utf-8') as stream:json.dump({'admission':admission,'qualification':proof},stream,indent=2);stream.write('\n')
    print(json.dumps(proof))
