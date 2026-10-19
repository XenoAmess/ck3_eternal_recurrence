"""Pure finite feeder port; actual C16 cold admission is supplied after readiness."""
import ast,copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import prepare_checkpoint6397_c16_sources_v1 as controls

T=controls.T
A='ROOT-C16-SAVE6397-FEEDER-ADMISSION90.json'
BASE={'root_p37c15_same_game_loop_feeder88.py':'a86354ab365d45daa745536dc06d99d7818a982b188f1134f608c7e39db9a324',
 'root_continuity_window_c15_88.py':'fd815b7b201ed1a061b559f5763cfc19eeb95f2564c2d8ead12f99e282b4e80d',
 'launch_c15_feeder88.py':'785beb8ea082f456206cf1af0065f9a48fd2887e2db6c305f5ca01ca76a90ff7'}
ADMITTED='''def admitted():
    global BASELINE_CYCLES,BASELINE_DATE_RAW
    a=read(N/"ROOT-C16-SAVE6397-FEEDER-ADMISSION90.json")
    if (a.get("schema")!="xar.C16-cold6397-feeder/v1" or a.get("machine_id")!="xenoamess-full-tower-eb9d2c1186"
            or type(a.get("first_control_sequence")) is not int or a["first_control_sequence"]<=6874
            or a.get("ordinary_cycle_credit")!=0 or a.get("original_actions_replayed") is not False
            or a.get("window_origin_reset") is not False):raise ValueError("exact C16 admission required")
    def checked(r):
        p=Path(r["path"])
        if pin(p)!={"path":r["path"],"sha256":r["sha256"]} or p.stat().st_size!=r["bytes"]:raise ValueError("C16 source differs")
        return read(p)
    s=a["sources"];old=checked(s["old_ledger"]);cold=checked(s["cold_admission"])
    marker=checked(s["cold_bound"]);game=checked(s["actual_Game"]);current=checked(s["map_admission"])
    from root_checkpoint6397_cold_contract_c16 import validate_abnormal_closure,exact
    validate_abnormal_closure(cold);tail=exact(cold["historical_tail"],"historical_tail")
    ended=exact(cold["interruption"],"interruption")
    oldref=next(r for r in ended["sources"] if r.get("original_source","").endswith("ROOT-ACTUAL-GAME-LAUNCH-C15.json"))
    oldgame=checked(oldref);f=marker["opening_frame"];cp=marker["checkpoint"]
    dates={3039:53202720,**{r[0]:r[3] for r in tail["rows"]}}
    if (old.get("machine_id")!=a["machine_id"] or old["game_binding"]!={"pid":oldgame["pid"],"creation_date":oldgame["creation_date"]}
            or oldgame["pid"]!=115472 or oldgame["creation_filetime"]!=134368932806525787
            or old["last_settled_date_raw"]!=dates.get(old["last_settled_cycles"])
            or marker.get("schema")!="xar.c16.normal-checkpoint-cold-bound/v1" or marker.get("machine_id")!=a["machine_id"]
            or marker["completed_cycles"]!=3039 or marker["T0_date_raw"]!=53144328
            or marker["new_ordinary_cycle_credit"]!=0 or marker["AUTO_or_MET_replayed"] is not False
            or cp["sha256"]!="417b06a63310cf3c59544394024b387a3fc2700dced3c08b42aa5980bfeb27cb"
            or cp["history_index"]!=2083 or cp["date_raw"]!=53202720
            or cold["new_Game"]!={k:game[k] for k in ("pid","creation_filetime","creation_date")}
            or game["creation_filetime"]==134368932806525787 or game.get("old_save_loaded") is not True
            or game.get("load_save_name")!="xar_checkpoint" or current.get("status")!="GREEN" or current.get("reviewer")!="/root"
            or current["actual_initial_frame"]!=f or current["game_pid"]!=game["pid"] or current["game_creation_filetime"]!=game["creation_filetime"]
            or f["date_raw"]!=53202720 or f["actor_character_id"]!=40526 or f["episode_run_id"]!="native-40526-1bec95182886"
            or type(f["native_revision"]) is not int or f["native_revision"]<=0):raise ValueError("C16 cold facts differ")
    BASELINE_CYCLES=3039;BASELINE_DATE_RAW=53144328
    return {**a,"old_ledger":old,"game":game,"opening":f}
'''
ATTACH='''def continuity_attach(v,first_control=3,resume_admission=None):
    if resume_admission is not None or first_control!=v["first_control_sequence"]:raise ValueError("follow admitted new FULL only")
    ledger=WindowLedger(CONTINUITY_WINDOW);s=ledger.load();p=pin(N/"ROOT-C16-SAVE6397-FEEDER-ADMISSION90.json")
    if s.get("last_C16_SAVE6397")==p:
        if s["status"] not in ("running","complete"):raise ValueError("later interruption unresolved")
        return s
    if s!=v["old_ledger"]:raise ValueError("old ledger changed")
    return ledger.apply("C16_SAVE6397_cold_verified",{"machine_id":"xenoamess-full-tower-eb9d2c1186","source":p,
        "evidence_id":"C16-SAVE6397:"+p["sha256"],"old_ledger":v["old_ledger"],"game":v["game"],"frame":v["opening"]})
'''
BRANCH='''    if kind == "C16_SAVE6397_cold_verified":
        frame=frame_binding(details["frame"]);new=game_binding(details["game"])
        if (state!=details["old_ledger"] or state["game_binding"]["pid"]!=115472 or new["pid"]==115472
                or state["start_date_raw"]!=53144328 or state["target_date_raw"]!=53407128
                or frame["date_raw"]!=53202720 or frame["actor_character_id"]!=40526
                or frame["episode_run_id"]!="native-40526-1bec95182886"):raise ValueError("finite C16 saved boundary differs")
        state.update(status="running",game_binding=new,latest_binding=frame,last_settled_cycles=3039,last_settled_date_raw=53202720,
            cold_handoff_count=state.get("cold_handoff_count",0)+1,last_C16_SAVE6397=details["source"],
            C16_rollback_history={"old_ledger_cycles":state["last_settled_cycles"],"historical_cycles":3273,
                "historical_date_raw":53204424,"checkpoint_cycles":3039,"unsaved_tail_cycles":234,"unsaved_tail_days":71,
                "ordinary_credit":0,"unknown_AUTO":6874,"unknown_replayed":False,"old_game":state["game_binding"]},
            previous_interruption=state.get("interruption"))
        return state
'''

def function(source,name,new):
    n=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines(True);return ''.join(lines[:n.lineno-1])+new+''.join(lines[n.end_lineno:])
def build_sources():
    src={n:controls.read(T/n,h) for n,h in BASE.items()}
    f=controls.prior.port(src['root_p37c15_same_game_loop_feeder88.py'],controls.MAP)
    f=f.replace('root_continuity_window_c16_88','root_continuity_window_c16_90')
    before=ast.parse(f);f=function(function(f,'admitted',ADMITTED),'continuity_attach',ATTACH);after=ast.parse(f)
    for n in before.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name not in ('admitted','continuity_attach'):
            m=next(m for m in after.body if isinstance(m,type(n)) and m.name==n.name)
            if ast.dump(n)!=ast.dump(m):raise ValueError('original feeder function changed')
    old=src['root_continuity_window_c15_88.py'];key='    if kind == "C15_cold6322_rollback_verified":'
    ledger=controls.swap(old,key,BRANCH+key)
    if ledger.replace(BRANCH,'')!=old:raise ValueError('original ledger changed')
    launcher=controls.prior.port(src['launch_c15_feeder88.py'],controls.MAP).replace('root_p37c16_same_game_loop_feeder88.py','root_p37c16_same_game_loop_feeder90.py')
    out={'root_p37c16_same_game_loop_feeder90.py':f.encode(),'root_continuity_window_c16_90.py':ledger.encode(),'launch_c16_feeder90.py':launcher.encode()}
    for n,b in out.items():compile(b,n,'exec')
    if sum(map(len,out.values()))>65536:raise ValueError('64KiB three-source cap exceeded')
    return out

if __name__=='__main__':
    out=build_sources()
    print(json.dumps({'machine_id':controls.prior.MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_READY_ACTUAL_ADMISSION_REQUIRED','source_bytes':sum(map(len,out.values())),
        'sources':{n:{'bytes':len(b),'sha256':controls.digest(b)} for n,b in out.items()},'admission_basename':A}))
