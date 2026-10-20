from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess
root=Path(__file__).resolve().parent
D=Path('D:/workspace/ck3_eternal_recurrence')
def pin(p):
 b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
index=json.loads((root/'SOURCE-AND-SMALL-FACTS.actual.json').read_bytes())
for row in index['source_pins']:
 assert pin(D/row['repository_relative_path'])==row['pin'],row['repository_relative_path']
head=subprocess.check_output(['git','-C',str(D),'rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(['git','-C',str(D),'status','--porcelain','--untracked-files=no'],text=True)
assert head==index['source_head']=='bc63851081462413d0cc6ebe62e37490707ee6a9'
assert not status,status
assert index['machine_cli']=='desktop-3fevhd2-1c74096080'
doc=root/'MECHANISM-FINDINGS.md'
links=re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf8'))
assert all((root/rel).is_file() for rel in links),links
extra=[]
for rel in ['docs/ck3-native-ai/episode04-r08-task-dispatch-source-gap-12004.md',
 'docs/ck3-native-ai/episode04-r08-b-next-20261020.md']:
 extra.append(dict(repository_relative_path=rel,pin=pin(D/rel)))
files=[pin(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='DELIVERY.actual.json']
v=dict(schema='xar.e04.r0223.next-opportunity-readonly-review.v1',
 machine_id=index['machine_id'],sealed_at_utc=datetime.now(timezone.utc).isoformat(),
 status='OFFLINE_FINDINGS_AND_ONE_UNIMPLEMENTED_FINITE_EXPERIMENT',
 source_head=head,source_tracked_status=status,source_pins_unchanged=True,
 read_only_source_and_actuals=True,main_report=pin(doc),source_index=pin(root/'SOURCE-AND-SMALL-FACTS.actual.json'),
 additional_repository_sources=extra,
 actual_conclusions=dict(c_d_qualified_traps=0,a_b_same_value_traps=2,
   current_rate_before_raw=386622,current_rate_after_raw=310621,
   current_raw_four_fields_before_after=[0,0,0,0],payment_records_after=0,
   army_natural_parent_returns_after=2,character_settlement_parent_observed='unknown; no such installed hook or DTO',
   producer_absence_proved=False,paid_payer_cadence='unknown',full_R08=False),
 installed_hook_families=dict(transition='24E8DB0',gateway='28B9950',personal_add='285EE40',
   personal_sub='285EED0',land_sub='285EFF0',conditional_raw4_getter='28B9490',
   character_settlement_28F7840=False),
 next_experiment=dict(selected='target Character opportunity at original entry28F7840',
   low_cost_implementation='new default-OFF execute-DR mode; not implemented or qualified',
   finite_candidate_budget=dict(watch_ms=30000,exact_days=1,aggregate_exec_stops=128,target_detail_records=8),
   negative_limit='foreign hits may exhaust128 before target; preserve incomplete and do not repeat sameS0',
   higher_cost_alternative='replace with qualified target-filtered entry counter if fuller daily negative coverage required; never run both',
   not_selected_for_next_scene=['known a/b copy caller capture','generic dispatch3F90A6F'],
   Root_decision_and_fresh_budget_still_required=True),
 collaboration_cross_check=dict(sender='/root/native_prepare',
   role='candidate-author capability report, not runtime evidence',
   dispatch_scope='job+38 dispatch/vptr+10 target and raw args; generic first job; no Character/payer/calendar join',
   parent_opportunity_more_direct=True),
 prohibited_actions=dict(game=0,SDK=0,DR=0,native_queries=0,builds=0,new_EXE_reads=0,
   consumer_or_selector_replays=0,D_or_W_writes=0,full_native_report_or_active_wars_copies_retained=0),
 own_derived_correction_receipts=['DERIVED-PROJECTION-CORRECTION.actual.json','TIMING-DERIVED-COMPACTION.actual.json'],
 local_links_checked=links,files=files,
 budget=dict(root=str(root),maximum_bytes=131072,scope_hard_stop_utc='2026-10-20T16:15:00Z',
   json_serialized_and_size_checked_before_write=True))
def enc():return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
current=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
v['budget']['bytes_before_receipt']=current
v['budget']['final_bytes_upper_bound']=current+12000
b=enc();assert len(b)<=12000,len(b)
assert current+len(b)<=131072,(current,len(b))
out=root/'DELIVERY.actual.json';out.write_bytes(b)
print(json.dumps(dict(receipt=pin(out),report=pin(doc),source_index=pin(root/'SOURCE-AND-SMALL-FACTS.actual.json'),
 actual_root_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),hard_stop_utc=v['budget']['scope_hard_stop_utc'])))
