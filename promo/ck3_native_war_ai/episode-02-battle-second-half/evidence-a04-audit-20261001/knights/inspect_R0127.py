import json
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path("C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-nextday-live-20261001-a03")
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
for p in sorted((ROOT/"ck3-output/interactive-requests").glob("*.json")):
    req=read(p)
    response=ROOT/"ck3-output/interactive-requests-responses"/p.name
    row=read(response) if response.exists() else {}
    b=row.get("body",{})
    print(json.dumps({"name":p.name,"request":req,"result":row.get("result"),"at":row.get("at"),
        "driver":{k:row.get("driver_state",{}).get(k) for k in ("pipe_name","connection_generation","bridge_pid","episode_run_id")},
        "body_keys":list(b),"body":{k:b.get(k) for k in ("accepted","date_raw","paused","revision","snapshot_id","starting_date_raw","ending_date_raw","elapsed_days","requested_horizon_days","postcondition_verified","status") if k in b},
        "checkpoint":b.get("checkpoint")},ensure_ascii=False))
trace=read(ROOT/"ck3-output/interactive-requests-responses/knight-new-trace-finish.json")["body"]["managed_trace"]
print("MANAGED",json.dumps({k:v for k,v in trace.items() if k!="trace"},ensure_ascii=False))
print("TRACE_KEYS",list(trace["trace"]))
print("TRACE_SCALARS",json.dumps({k:v for k,v in trace["trace"].items() if not isinstance(v,(dict,list))},ensure_ascii=False))
for k,v in trace["trace"].items():
    if isinstance(v,list):print("TRACE_LIST",k,len(v),list(v[0]) if v and isinstance(v[0],dict) else None)
index=read(Path(__file__).parent/"nextday-live-R0127.json")
for a in [index["sdk_completion"], *index["sources"]]:
    if a["path"].endswith("completion.json"):
        print("SDK_COMPLETION",json.dumps(read(Path(a["path"])),ensure_ascii=False))
print("REPORT",json.dumps(read(ROOT/"ck3-output/capture-report.json"),ensure_ascii=False))
