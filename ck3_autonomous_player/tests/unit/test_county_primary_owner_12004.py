"""One production consumer compound; synthetic native premises, no SDK/native run."""
from pathlib import Path
import argparse
from copy import deepcopy
import importlib.util
import json
import sys

def need(ok,why):
 if not ok:raise ValueError(why)

def rejected(call):
 try:call()
 except ValueError:return
 raise ValueError('Malformed source ownership was accepted')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True)
 p.add_argument('--candidate-root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists(),'Create-only compound result exists')
 sys.path.insert(0,str(a.repo/'ck3_autonomous_player/src'))
 import xar_autoplayer.bridge as package
 if a.candidate_root:
  package.__path__.insert(0,str(a.candidate_root/'ck3_autonomous_player/src/xar_autoplayer/bridge'))
  # The package initializer may already have loaded its old strict contracts.
  # Replace only this compound's owned dependency chain in RAM, never on disk.
  for name in ('army_actual_loss_writer_observations_contract','army_physical_loss_evidence_12004',
               'army_county_entry_loss_evidence_12004'):
   sys.modules.pop('xar_autoplayer.bridge.'+name,None)
 from xar_autoplayer.bridge.army_county_primary_owner_12004 import KEY,EXE,evaluate_county_primary_owner_evidence_12004 as consume
 from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1 as normalize
 from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import classify_retained_loss_writer_window_v1 as old_classify
 spec=importlib.util.spec_from_file_location('_existing_county_fixture',a.repo/'ck3_autonomous_player/tests/unit/test_army_county_entry_loss_evidence_12004.py')
 fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
 e=fixture.event(sequence=1000,caller=0x24E25EE)
 token=lambda seq:dict(clock_identity=0x123456,sequence=seq,thread_id=11)
 roster=dict(boundary='pre_date_prefix_return',capture_rva=0x2A99E76,capture_event=token(20),
     begin_identity=0x400000,end_identity=0x400004,count=1,complete=True,ordered_full_ids=[0])
 scope=dict(observed=True,phase='pre_date',actual_entry_rva=0x2A99DA0,caller_return_rva=0x123,
     primary_manager_identity=0x1000000,secondary_manager_identity=0x1000008,game_state_identity=0x2000000,
     session_identity=None,entry_event=token(10),date_raw=e['observed_date_raw']-24,
     prefix_date_raw=e['observed_date_raw'],absolute_day_raw=100,entry_c0_raw=0,saved_c0_raw=None,
     saved_mask02_admitted=None,saved_c0_observed_rva=0,saved_c0_event=dict(clock_identity=0,sequence=0,thread_id=None),
     original_army_roster=roster)
 record=dict(scope=scope,original_called=True,original_returned=True,raw_return_bits=0,
     returned_event=token(40),returned_date_raw=e['observed_date_raw'],returned_absolute_day_raw=101,
     returned_c0_raw=0,same_clock_thread_order=True)
 phase=dict(schema_version=1,source='owned_native_natural_army_phase_records',
     membership_basis='captured_parent_roster_full_CArmy_ID_occurrences',subject_full_carmy_id_u32=0,records=[record])
 owner=dict(schema_version=1,source='native_county_primary_R13_pre_date',caller_return_rva=0x24E25EE,
     phase_entry_rva=0x2A99DA0,phase_prefix_rva=0x2A99E76,writer_invocation_token=17,
     writer_receiver_identity=0x3000000,source_carmy_identity=0x3001000,
     phase_primary_manager_identity=scope['primary_manager_identity'],phase_game_state_identity=scope['game_state_identity'],
     army_id=0,native_carmy_id=0,writer_full_regiment_id=e['army_regiment_id'],
     phase_entry_event=token(10),writer_event=token(30),phase_prefix_roster_event=token(20),
     phase_roster_occurrence=0,army_roster_occurrence=0,receiver_identity_matches=True,
     writer_identity_matches=True,actual_array_contains_writer=True,source_phase_roster_membership=True,
     capture_failure_flags=0,source_complete=True)
 e[KEY]=owner;f=fixture.family([e]);f.update(oldest_available_sequence=872,latest_sequence=1383,overwritten_events=871)
 row=dict(status='available',army_id=0,native_carmy_id=0,regiment_strengths=[dict(army_regiment_id=e['army_regiment_id'])],
     actual_loss_writer_observations_v1=f,army_natural_phase_observations_v1=phase)
 def run(r):return consume(r,executable_sha256=EXE,after_sequence=0,before_unattributed_capture_failures=0)
 result=run(row)
 need(len(result['positive_invocations'])==1 and result['individual_county_army_owner_observed'],
      'Native Army0 owner plus actual physical debit did not join')
 need(result['positive_invocations'][0]['actual_physical_soldier_debit']==7
      and result['whole_window_complete'] is False and result['county_total_debit'] is None
      and result['complete_army_loss_history'] is False,'Individual join relaxed the global window contract')
 old=old_classify(f,current_regiment_ids=[e['army_regiment_id']],executable_sha256=EXE,
     after_sequence=0,before_unattributed_capture_failures=0)
 need(old['status']=='incomplete' and old['reasons']==['requested_window_overwritten']
      and old['army_at_invocation_observed'] is False and old['county_total_debit'] is None,
      'Old whole-window consumer changed')
 checks=['real_strict_normalizer_physical_and_phase_join_Army0','global_gap_kept_independent_of_individual_positive']
 bad=deepcopy(row);bad['actual_loss_writer_observations_v1']['events'][0][KEY]['army_id']=1
 need(not run(bad)['positive_invocations'],'Cross-Army source was backfilled from query membership');checks.append('different_invocation_Army_rejected')
 bad=deepcopy(row);bad['actual_loss_writer_observations_v1']['events'][0][KEY]['writer_event']['thread_id']=22
 rejected(lambda:run(bad));checks.append('cross_thread_token_rejected')
 bad=deepcopy(row);c=bad['actual_loss_writer_observations_v1']['events'][0][KEY]
 c['phase_entry_event']=token(110);c['phase_prefix_roster_event']=token(120);c['writer_event']=token(130)
 need(not run(bad)['positive_invocations'],'Different phase token was joined by date');checks.append('different_returned_phase_entry_token_rejected')
 bad=deepcopy(row);second=deepcopy(bad['actual_loss_writer_observations_v1']['events'][0]);second['sequence']=1001
 bad['actual_loss_writer_observations_v1']['events'].append(second);bad['actual_loss_writer_observations_v1']['event_count']=2
 need(not run(bad)['positive_invocations'],'One invocation token was reused across two writer calls');checks.append('reused_writer_invocation_token_rejects_both')
 bad=deepcopy(row);bad['actual_loss_writer_observations_v1']['events'][0].pop(KEY)
 need(not run(bad)['positive_invocations'],'Legacy missing owner was filled from row');checks.append('legacy_missing_owner_remains_unknown')
 bad=deepcopy(row);bad['actual_loss_writer_observations_v1']['events'][0]['actual_physical_soldier_debit']=999
 need(not run(bad)['positive_invocations'],'Owner source replaced physical proof');checks.append('physical_debit_forgery_rejected')
 bad=deepcopy(f);bad['events'][0]['caller_return_rva']=0x24E35FF
 rejected(lambda:normalize(bad,current_regiment_ids=[e['army_regiment_id']]));checks.append('foreign_caller_cannot_carry_county_owner')
 bad=deepcopy(row);bad['army_natural_phase_observations_v1']['records'][0]['original_returned']=False
 rejected(lambda:run(bad));checks.append('missing_actual_parent_return_rejected')
 report=dict(status='PASS_ONE_PRODUCTION_COUNTY_PRIMARY_OWNER_COMPOUND',checks=checks,
     native_inputs='explicitly synthetic source/register/phase/physical premises',
     native_thunk_or_DLL_built=False,native_code_executed=False,SDK_DR_game_calls=0,
     actual_R216_reclassified=False,whole_R04_live_credit=False,old_matrix_runs=0,optimization=sys.flags.optimize)
 with a.output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps(report));return 0

if __name__=='__main__':raise SystemExit(main())
