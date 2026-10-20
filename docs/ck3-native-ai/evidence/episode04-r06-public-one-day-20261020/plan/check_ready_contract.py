"""Pure current-launcher checks. No process, SDK, DR or game access."""
from __future__ import annotations
import copy, importlib.util, json, pathlib, sys
from datetime import datetime, timezone
sys.dont_write_bytecode=True
REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
OUT=pathlib.Path(__file__).resolve().parent
p=REPO/'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/launch_live_refill_add.py'
s=importlib.util.spec_from_file_location('r06_readonly_current_launcher',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture(n):
    module=str(OUT/'synthetic'/'xar_ck3_bridge.dll')
    argv=[str(OUT/'synthetic'/'refill_add_hwprobe_12004.exe'),'--enable',
      '--pid','100','--thread','0','--regiment','2602','--slot','1','--created','123456',
      '--timeout-ms','30000','--raw',str(OUT/'synthetic'/'observer.raw.ndjson'),
      '--ready',str(OUT/'synthetic'/'observer.ready.json'),'--machine-id','desktop-3fevhd2-1c74096080',
      '--thread-policy','carrier-owned-target','--max-threads',str(n)]
    e=dict(schema='xar.ck3.refill_ADD_12004.hwprobe_ready.v4',machine_id='desktop-3fevhd2-1c74096080',pid=100,
      process_created_filetime=123456,thread_id=None,regi_full_id_u32=2602,physical_slot=1,
      carrier_module_path=module,carrier_source_epoch=20261018,thread_policy='carrier_owned_target',maximum_owned_threads=n)
    return dict(schema='xar.ck3.refill_ADD_12004.prepared_live_argv.v4',observer_launched=False,actual_ADD_observed=False,
      native_argv=argv,consume_argv=['synthetic-consumer'],ready_must_match=e,machine_id=e['machine_id'],
      carrier_module_path=module,carrier_source_epoch=20261018,observer_thread_policy='carrier_owned_target',maximum_owned_threads=n)

results=[]
def check(name,operation,accept):
    error=None
    try:operation();actual=True
    except (ValueError,KeyError,TypeError) as ex:actual=False;error=str(ex)
    results.append(dict(name=name,expected_accept=accept,actual_accept=actual,PASS=actual==accept,error=error))

for n in (65,256,257):
    f=fixture(n)
    check('scope-N-'+str(n),lambda f=f:m.validate_prepared_ready_scope(f),n<=256)
f=fixture(65); e=f['ready_must_match'];r={**e,'armed_thread_ids':list(range(1,66)),'armed_thread_count':65}
check('65-actual-armed-IDs-admitted-under-N65',lambda:m.validate_actual_ready(f,r,e),True)
f64=fixture(64);e64=f64['ready_must_match'];r64={**e64,'armed_thread_ids':list(range(1,66)),'armed_thread_count':65}
check('65-actual-armed-IDs-rejected-under-N64',lambda:m.validate_actual_ready(f64,r64,e64),False)
dup={**r,'armed_thread_ids':[1]*65}
check('duplicate-numeric-TIDs-rejected',lambda:m.validate_actual_ready(f,dup,e),False)
wrong={**r,'process_created_filetime':123457}
check('different-process-FILETIME-rejected',lambda:m.validate_actual_ready(f,wrong,e),False)
out=dict(schema='xar.e04.r06.current_ready_contract_pure_check.v1',machine_id='desktop-3fevhd2-1c74096080',
 observed_at_utc=datetime.now(timezone.utc).isoformat(),status='PASS' if all(x['PASS'] for x in results) else 'FAIL',
 cases=results,synthetic_only=True,native_execution=False,OS_thread_census=False,debugger_observed_generation_qualification=False,
 actual_READY_or_ADD_qualified=False,scope='Current Python launch contract accepts explicit N65; actual native accumulated-generation cap remains independently authoritative')
(OUT/'PURE-CONTRACT-CHECK.actual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
raise SystemExit(0 if out['status']=='PASS' else 1)
