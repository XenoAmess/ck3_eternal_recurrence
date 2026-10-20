from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
root=Path(__file__).resolve().parent
D=Path('D:/workspace/ck3_eternal_recurrence')
L=Path('C:/ck3-e04-resume-20261020-a01/r08-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0223/case-output')
def pin(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
specs={
 'ck3_autonomous_player/native_bridge/src/war_payment_runtime_12004.cpp':['kDescriptions','{0x24E8DB0','{0x28B9950','{0x285EE40','{0x285EED0','{0x285EFF0','{0x28B9490','WarPaymentHook12004::'],
 'ck3_autonomous_player/native_bridge/src/war_payment_passive_12004.cpp':['g_transition =','if (!Ready(b))','if (b.retain_actor','if (!permit.admitted())','generic_wallet_context.emplace','r.caller_return_rva==kWarPaymentGenericReturn','r.natural_parent_metadata =','InvokeWarPaymentTransition','InvokeWarPaymentGateway','InvokeWarPaymentWriter'],
 'ck3_autonomous_player/native_bridge/include/xar_bridge/war_payment_runtime_12004.hpp':['kWarPaymentHookCount','enum class WarPaymentHook','raw4_getter'],
 'ck3_autonomous_player/native_bridge/include/xar_bridge/war_payment_passive_12004.hpp':['enum class WarPaymentKind','WarPaymentNaturalParent12004','parent_transition_entry','generic_wallet_context','retain_actor'],
 'ck3_autonomous_player/native_bridge/src/ck3_12003_war_cash_current_reader.cpp':['ReadActor','expense_context_character(actor)','raw.character','ReadWarPaymentGenericValues'],
 'ck3_autonomous_player/native_bridge/include/xar_bridge/war_payment_generic_context_12004.hpp':['0x1C0','0x2C0','0x2C8','0x28','0x30','context_identity_after'],
 'ck3_autonomous_player/native_bridge/include/xar_bridge/army_natural_phase_scope_12004.hpp':['kArmyNaturalPreDate','kArmyNaturalPostDate','enum class ArmyNaturalPhaseKind','InvokeArmyNaturalPhaseScope'],
 'ck3_autonomous_player/native_bridge/src/war_payment_json_12004.cpp':['natural_journal_status','natural_parent_returns'],
 'ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/cold_observer.cpp':['full_window_all_writes_covered','KnownCopyCallerJson','capture-known-copy-caller','steady_clock::now()','RawFieldWriteTrap'],
 'ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/prepare_writer_admission.py':['argv=[','native_argv_tail','timeout_ms<=30000'],
 'tools/ck3_mod_acceptance_cases/r08_writer_controller.py':['return admission["argv"]==','tail=[','--expected-hits'],
 'docs/ck3-native-ai/episode04-r08-readonly-maintenance-sufficiency-12004.md':['310999','386622','290FD20','角色','读取顺序'],
 'docs/ck3-native-ai/episode04-r08-settlement-parent-order-12004.md':['28F7840','28F7934','2C13F60','28BFD80'],
 'docs/ck3-native-ai/episode04-r08-copy-callee28d6170-12004.md':['28A645B','28A6466','2C0','2C8'],
 'docs/ck3-native-ai/acceptance/2026-10-16-r0174-maintenance-source/PARENT-HOOK-SOURCE-ANCHOR.contract-a01.json':['SOURCE_ANCHOR_ONLY','entry_rva','entry_register_contract','minimal_candidate_changes'],
}
sources=[]
for relative,terms in specs.items():
 p=D/relative;b=p.read_bytes();lines=b.decode('utf-8-sig').splitlines()
 matches=[dict(line=i,text=s) for i,s in enumerate(lines,1) if any(t in s for t in terms)]
 sources.append(dict(repository_relative_path=relative,pin=pin(p,b),anchors=matches))
actual=[]
for rel in ['r08-writer-control/C-D-WRITERS.actual.json','r08-writer-control/watch/ACTUAL-WRITERS.json']:
 p=L/rel;b=p.read_bytes();v=json.loads(b)
 actual.append(dict(pin=pin(p,b),value=v))
timing=json.loads((root/'TIMING-CASH-READBACK.compact-a02.actual.json').read_bytes())
cashrow=next(r for r in timing['rows'] if r['path'].endswith('cash-after.common-view.json'))
value=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
 source_head=subprocess.check_output(['git','-C',str(D),'rev-parse','HEAD'],text=True).strip(),
 source_status=subprocess.check_output(['git','-C',str(D),'status','--porcelain','--untracked-files=no'],text=True),
 machine_cli=subprocess.check_output(['python',str(D/'tools/ck3_live_run_id.py'),'machine'],text=True).strip(),
 source_pins=sources,actual_small_writer_results=actual,
 natural_after=dict(source_pin=cashrow['pin'],json_pointer='/body/war_payment_observations_v1',
   status=cashrow['projection']['journal']['natural_journal_status'],
   original_returns=cashrow['projection']['journal']['natural_parent_returns']),
 no_native_actions=True,consumer_selector_executions=0,
 raw_or_full_native_report_copies=0,source_or_worktree_writes=0)
b=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')
out=root/'SOURCE-AND-SMALL-FACTS.actual.json'
assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+len(b)<=131072,len(b)
out.write_bytes(b)
print(json.dumps(dict(pin=pin(out,b),source_head=value['source_head'],source_status=value['source_status'],machine_cli=value['machine_cli'],lane_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))))
for r in sources:
 if 'current_reader' in r['repository_relative_path'] or 'controller.py' in r['repository_relative_path']:print(json.dumps(r,ensure_ascii=False))
print(json.dumps(actual,ensure_ascii=False))
