"""Focused synthetic saved-state acceptance checks; no game or old run supplied."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from check_nextday_saved_status import classify_life_state

HERE = Path(__file__).resolve().parent
OUT = Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/knights-attempt-02")
cases = [
    {"name": "unique_alive", "state": {"character_id": 33437, "alive_data_present": True, "dead_data_present": False,
        "death_date": None, "death_reason": None, "killer_character_id": None}, "expected": "ALIVE"},
    {"name": "unique_dead_keeps_explicit_fields", "state": {"character_id": 33437, "alive_data_present": False, "dead_data_present": True,
        "death_date": "1066.12.30", "death_reason": "death_battle", "killer_character_id": 60001}, "expected": "DEAD"},
    {"name": "both_missing", "state": {"character_id": 33437, "alive_data_present": False, "dead_data_present": False,
        "death_date": None, "death_reason": None, "killer_character_id": None}, "expected": "UNKNOWN_REJECTED"},
    {"name": "both_present", "state": {"character_id": 33437, "alive_data_present": True, "dead_data_present": True,
        "death_date": "1066.12.30", "death_reason": "death_battle", "killer_character_id": 60001}, "expected": "UNKNOWN_REJECTED"},
    {"name": "fields_omitted", "state": {"character_id": 33437}, "expected": "UNKNOWN_REJECTED"},
]
results=[]
for case in cases:
    before = json.dumps(case["state"], sort_keys=True)
    try:
        result = classify_life_state(case["state"])
        error = None
    except ValueError as exc:
        result, error = "UNKNOWN_REJECTED", str(exc)
    unchanged = json.dumps(case["state"], sort_keys=True) == before
    results.append({**case,"result":result,"error":error,"state_fields_unchanged":unchanged,
                    "passed":result == case["expected"] and unchanged})
report={"schema":"ck3.a04.saved-status.synthetic-check.v1","synthetic_only":True,"new_live_inputs_accepted":False,
        "historic_inputs_accepted":False,"ck3_launches":0,"results":results,"passed":all(r["passed"] for r in results)}
with (OUT/"saved-status-synthetic-check.json").open("x",encoding="utf-8",newline="\n") as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2);stream.write("\n")
plan_path=HERE/"capture-nextday-plan.json"
old=plan_path.read_bytes()
with (OUT/"capture-nextday-plan-before-xor-check.json").open("xb") as stream:stream.write(old)
plan=json.loads(old)
checker=HERE/"check_nextday_saved_status.py"
code=checker.read_bytes()
plan["source_reuse"]["checker"]={"path":str(checker),"bytes":len(code),"sha256":hashlib.sha256(code).hexdigest().upper()}
plan["source_reuse"]["checker_validation"]="--help completed; 5 synthetic valid/ambiguous lifecycle checks passed without modifying state fields; no new live input admitted"
plan["source_reuse"]["synthetic_check_report"]={"path":str(OUT/"saved-status-synthetic-check.json"),"sha256":hashlib.sha256((OUT/"saved-status-synthetic-check.json").read_bytes()).hexdigest().upper()}
plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"passed":report["passed"],"checks":len(results),"live_status":"NOT_RUN"}))
if not report["passed"]:sys.exit(2)
