"""Strict parent-entry raw contract. Pure stdlib; no native calls."""
import hashlib,json
SCHEMA="xar.maintenance.parent_entry.raw.v1"
MODE="parent-entry-execution-once-v1"
PREFIX_SHA="d44f03f2855791f5fb4ee339dc21b28917e981d419df5cb4f1ecb89ba20aa517"
EXPECTED_KEYS={"machine_id","synthetic","pid","created","entry","character","full_id","context","local_player_id","game_state","date_raw","absolute_day","foreign_limit","capture_ms","admission_id","owner_binding"}
def need(ok,message):
    if not ok:raise ValueError("parent entry: "+message)
def integer(x,name,minimum=0,maximum=(1<<64)-1):
    need(type(x) is int and minimum<=x<=maximum,name+" integer/bounds")
    return x
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def parse_meta(text):
    need(type(text) is str and len(text.encode())<=32768,"meta cap")
    out={}
    for line in text.splitlines():
        need("=" in line,"meta line")
        k,v=line.split("=",1)
        need(k and k not in out and "\x00" not in v,"meta duplicate/NUL")
        out[k]=v
    return out
def cold_expected(meta,machine_id,timeout_ms):
    def num(key):return int(meta[key],0)
    need(meta["parent_schema"]=="xar.maintenance.parent_entry.cold-meta.v1","cold schema")
    return dict(machine_id=machine_id,synthetic=True,pid=num("pid"),created=num("created"),entry=num("parent_entry"),
      character=num("character"),full_id=num("full_id"),context=num("context"),local_player_id=num("local_player_id"),
      game_state=num("game_state"),date_raw=num("date_raw"),absolute_day=num("absolute_day"),
      foreign_limit=num("foreign_limit"),capture_ms=timeout_ms,admission_id="synthetic-cold",owner_binding=None)
def normalize_rows(rows,expected):
    need(type(expected) is dict and set(expected)==EXPECTED_KEYS,"independent expected shape")
    need(type(rows) is list and 2<=len(rows)<=4096 and all(type(r) is dict for r in rows),"rows/cap")
    s=rows[0];t=rows[-1]
    need(s.get("kind")=="start" and s.get("schema")==SCHEMA and s.get("mode")==MODE,"start schema/mode")
    need(t.get("kind")=="terminal" and sum(r.get("kind")=="terminal" for r in rows)==1,"terminal unique last")
    need(type(expected["synthetic"]) is bool and type(expected["machine_id"]) is str and bool(expected["machine_id"]),"machine/type")
    for k in EXPECTED_KEYS:
        need(type(s.get(k)) is type(expected[k]) and s.get(k)==expected[k],"start binding "+k)
    for k in ("pid","created","entry","character","full_id","context","local_player_id","game_state"):
        integer(expected[k],k,1)
    integer(expected["date_raw"],"date",0,0xffffffff-25);integer(expected["absolute_day"],"day",0,0xfffffffe)
    need(expected["capture_ms"]>=500 and expected["capture_ms"]<=30000,"finite timeout")
    need(expected["foreign_limit"]==4096 or expected["synthetic"] and expected["foreign_limit"]==512,"foreign cap")
    need(s.get("target_record_limit")==1 and s.get("prefix_sha256")==PREFIX_SHA,"source/target cap")
    if not expected["synthetic"]:
        need(type(expected["owner_binding"]) is dict and expected["owner_binding"].get("episode_run_id") is None,"ordinary-null owner")
    armed={};births={};restored=set();retired=set();highest={};ready=False;captures=[];in_hold=False;closed=False;foreign_markers=0
    allowed={"arm","restore","thread_exited","ready","foreign_resume","parent_entry","unresolved_cleanup_hold","cleanup_thread_unarmed","cleanup_owned_execution"}
    for r in rows[1:-1]:
        kind=r.get("kind");need(kind in allowed,"unknown row kind")
        if kind=="arm":
            need(not closed,"no arm after capture closed")
            key=(integer(r.get("thread_id"),"TID",1),integer(r.get("thread_generation"),"generation",1))
            need(key not in armed and key[1]>highest.get(key[0],0),"generation/repeated arm")
            need(not any(k[0]==key[0] and k not in retired for k in armed),"live TID reused")
            need(r.get("success") is True and r.get("readback") is True,"arm failed")
            saved=r.get("saved_debug");actual=r.get("armed_debug")
            need(type(saved) is list and len(saved)==6 and all(type(v) is int and 0<=v<(1<<64) for v in saved) and saved[:4]==[0,0,0,0] and saved[5]&(0xff|0xffff0000)==0,"saved DR free/u64")
            need(type(actual) is list and len(actual)==6 and all(type(v) is int and 0<=v<(1<<64) for v in actual) and actual[0]==expected["entry"] and actual[1:4]==[0,0,0] and actual[5]&0xffff00ff==1,"execution DR")
            armed[key]=saved;births[key]=integer(r.get("thread_created"),"thread creation",1);highest[key[0]]=key[1]
        elif kind=="thread_exited":
            key=(r.get("thread_id"),r.get("thread_generation"));need(key in armed and key not in retired,"exit generation");retired.add(key)
        elif kind=="restore":
            closed=True
            key=(r.get("thread_id"),r.get("thread_generation"));need(key in armed and key not in retired,"restore generation")
            need(r.get("thread_created")==births[key] and r.get("readback") is True and r.get("equal_original") is True and r.get("debug")==armed[key],"exact original DR restore")
            restored.add(key)
        elif kind=="ready":
            need(not ready and armed and r.get("census_complete") is True,"READY census");ready=True
        elif kind=="parent_entry":
            need(ready and not closed and not in_hold and len(captures)==0,"one capture before cleanup")
            key=(r.get("thread_id"),r.get("thread_generation"));need(key in armed and key not in retired,"capture generation")
            need(r.get("thread_created")==births[key] and r.get("RIP")==expected["entry"] and r.get("RDX")==expected["character"] and r.get("DR6",0)&15==1,"original site/RDX/B0")
            for k in ("paid_maintenance_raw","payer","cadence"):need(r.get(k) is None,"no semantic payment")
            need(r.get("parent_return_observed") is False,"no parent return")
            captures.append(r)
        elif kind=="unresolved_cleanup_hold":
            need(r.get("cleanup_complete") is False and r.get("no_more_capture") is True and r.get("Popen_must_remain_retained") is True,"hold shape");in_hold=True;closed=True
        elif kind=="foreign_resume":
            key=(r.get("thread_id"),r.get("thread_generation"))
            need(key in armed and key not in retired and r.get("thread_created")==births[key] and r.get("count")==1 and foreign_markers==0,"foreign generation/count")
            need(ready and not closed and r.get("RIP_unchanged") is True and r.get("DR0_retained") is True and r.get("RF_once") is True and r.get("TF") is False,"foreign original continuation")
            foreign_markers+=1
        elif kind=="cleanup_thread_unarmed":
            closed=True
            tid=integer(r.get("thread_id"),"cleanup TID",1);gen=integer(r.get("thread_generation"),"cleanup generation",1)
            integer(r.get("thread_created"),"cleanup creation",1)
            need(gen>highest.get(tid,0) and not any(k[0]==tid and k not in retired for k in armed),"cleanup generation ownership")
            v=r.get("debug")
            need(r.get("readback") is True and type(v) is list and len(v)==6 and all(type(x) is int for x in v) and v[:4]==[0,0,0,0] and v[5]&(0xff|0xffff0000)==0,"unarmed debug residual")
            highest[tid]=gen
        elif kind=="cleanup_owned_execution":
            closed=True
            key=(r.get("thread_id"),r.get("thread_generation"));v=r.get("debug")
            need(key in armed and key not in retired and r.get("thread_created")==births[key],"late owned generation")
            need(r.get("owned_late_event") is True and r.get("RIP")==expected["entry"] and type(v) is list and len(v)==6 and all(type(x) is int and 0<=x<(1<<64) for x in v),"late event shape")
            need(type(r.get("restored_generation")) is bool and r["restored_generation"]==(key in restored),"late restored phase")
            if key in restored:need(v[:4]==armed[key][:4] and v[5]==armed[key][5] and v[4]&15 in (0,1),"queued late original vector")
            else:need(v[0]==expected["entry"] and v[1:4]==[0,0,0] and v[5]&0xffff00ff==1 and v[4]&15==1,"late active owned vector")
    need(ready and t.get("observation_thread_admission_complete") is True,"complete admitted thread coverage")
    need(t.get("cleanup_complete") is True and t.get("restored") is True and t.get("detached") is True and t.get("pending_event") is False and t.get("process_exited") is False,"clean actual terminal")
    need(set(armed)<=restored|retired,"missing generation restore/exit")
    need(t.get("capture_count")==len(captures),"capture count")
    count=integer(t.get("foreign_count"),"foreign count")
    need(count<=expected["foreign_limit"],"foreign limit exceeded")
    need(foreign_markers==int(count>0),"foreign first marker completeness")
    need(t.get("window_complete") is False and t.get("full_R08") is False,"no full window/business")
    qualified=False;unchanged=False
    if captures:
        r=captures[0]
        reads=r.get("first_read_complete") is True and r.get("second_read_complete") is True
        obj=reads and r.get("full_id_before")==r.get("full_id_after")==expected["full_id"] and r.get("magic_before")==r.get("magic_after")==0x43686172 and r.get("death_before")==r.get("death_after")==0
        clock=reads and r.get("state_before")==r.get("state_after")==expected["game_state"] and r.get("date_before")==r.get("date_after") and type(r.get("date_before")) is int and expected["date_raw"]<=r["date_before"]<=expected["date_raw"]+24 and r.get("day_before")==r.get("day_after") and type(r.get("day_before")) is int and expected["absolute_day"]<=r["day_before"]<=expected["absolute_day"]+1
        qualified=bool(obj and clock and r.get("source_anchor_matches") is True)
        unchanged=bool(reads and r.get("context_before")==r.get("context_after")==expected["context"])
        need(r.get("entry_owner_clock_qualified") is qualified and r.get("admitted_context_unchanged") is unchanged,"native claim versus independent recomputation")
    need(t.get("reason") in {"target_captured","target_read_incomplete","foreign_limit","timeout","cancel"},"qualified terminal reason")
    if t["reason"]=="target_captured":need(len(captures)==1 and qualified,"target reason/qualified")
    if t["reason"]=="target_read_incomplete":need(len(captures)==1 and not qualified,"incomplete target reason")
    if t["reason"] in {"timeout","cancel"}:need(not captures,"non-target reason cannot grant target")
    if t["reason"]=="foreign_limit":need(count==expected["foreign_limit"] and not captures,"exact hardlimit partial")
    return dict(target_entry_retained=bool(captures),target_entry_qualified=qualified,admitted_context_unchanged=unchanged,
       foreign_count=count,cleanup_complete=True,reason=t["reason"],window_complete=False,full_R08=False,
       paid_maintenance_raw=None,payer=None,cadence=None,synthetic=expected["synthetic"])
