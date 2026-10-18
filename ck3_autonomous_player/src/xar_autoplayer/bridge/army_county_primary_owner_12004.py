"""Owned actual county-primary caller/phase joins; no query-time Army backfill."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from .army_observed_phase_contract_12004 import _typed, normalize_army_observed_phase_family_12004

KEY='county_primary_owner_at_writer_v1'
EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
FIELDS={
 'schema_version':'u32','source':'str','caller_return_rva':'u64','phase_entry_rva':'u64','phase_prefix_rva':'u64',
 'writer_invocation_token':'u64','writer_receiver_identity':'u64','source_carmy_identity':'u64',
 'phase_primary_manager_identity':'u64','phase_game_state_identity':'u64',
 'army_id':'i32?','native_carmy_id':'i32?','writer_full_regiment_id':'i32?',
 'phase_entry_event':'Token','writer_event':'Token','phase_prefix_roster_event':'Token',
 'phase_roster_occurrence':'i32?','army_roster_occurrence':'i32?',
 'receiver_identity_matches':'bool','writer_identity_matches':'bool',
 'actual_array_contains_writer':'bool','source_phase_roster_membership':'bool',
 'capture_failure_flags':'u32','source_complete':'bool'}

def need(ok,why):
 if not ok:raise ValueError('county primary owner '+why)

def later(a,b):
 return (a['clock_identity']>0 and a['clock_identity']==b['clock_identity'] and
         0<a['sequence']<b['sequence'] and a['thread_id'] is not None and
         a['thread_id']>0 and a['thread_id']==b['thread_id'])

def normalize_county_primary_owner_at_writer_v1(value):
 if value is None:return None
 need(type(value) is dict and set(value)==set(FIELDS),'exact DTO shape differs')
 for key,kind in FIELDS.items():_typed(value[key],kind,'county_primary_owner.'+key)
 need(value['schema_version']==1 and value['source']=='native_county_primary_R13_pre_date'
      and value['caller_return_rva']==0x24E25EE and value['phase_entry_rva']==0x2A99DA0
      and value['phase_prefix_rva']==0x2A99E76,'exact actual4 source differs')
 if value['source_complete']:
  need(value['capture_failure_flags']==0 and all(value[k] for k in (
       'writer_invocation_token','writer_receiver_identity','source_carmy_identity',
       'phase_primary_manager_identity','phase_game_state_identity')),
       'complete source lacks real native identities')
  need(all(value[k] is not None and value[k]!=-1 for k in ('army_id','native_carmy_id','writer_full_regiment_id')),
       'complete source lacks full-generation IDs')
  need(all(value[k] is not None and value[k]>=0 for k in ('phase_roster_occurrence','army_roster_occurrence')),
       'complete source lacks original roster occurrences')
  need(all(value[k] for k in ('receiver_identity_matches','writer_identity_matches',
       'actual_array_contains_writer','source_phase_roster_membership')),'complete source contradicts guarded reads')
  need(later(value['phase_entry_event'],value['phase_prefix_roster_event'])
       and later(value['phase_prefix_roster_event'],value['writer_event']),
       'complete source lacks the actual phase/prefix/writer thread order')
 return deepcopy(value)

def evaluate_county_primary_owner_evidence_12004(row,*,executable_sha256,
    after_sequence=0,before_unattributed_capture_failures=None):
 """Join one bound actual row's physical calls to independently returned phases.

 The caller binds process/exact-source/query fences. Native IDs are copied at
 invocation by the entry thunk, never filled from this row's current IDs.
 A global ring gap remains visible even when an individual returned call joins.
 """
 from .army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1
 from .army_physical_loss_evidence_12004 import evaluate_army_physical_loss_evidence_12004
 need(type(after_sequence) is int and after_sequence>=0,'baseline cursor malformed')
 result=dict(schema='xar.county_primary_owned_invocations.v1',status='unavailable',
     scope='retained_target_scoped_individual_calls',positive_invocations=[],other_qualified_invocations=[],
     excluded_invocations=[],individual_county_army_owner_observed=False,
     complete_army_loss_history=False,county_total_debit=None,whole_window_complete=False,
     new_live_evidence=False)
 if executable_sha256!=EXE:return result
 if row.get('status')!='available' or row.get('actual_loss_writer_observations_v1') is None:return result
 ids=[r['army_regiment_id'] for r in row['regiment_strengths']]
 family=normalize_actual_loss_writer_observations_v1(row['actual_loss_writer_observations_v1'],current_regiment_ids=ids)
 phase=normalize_army_observed_phase_family_12004('army_natural_phase_observations_v1',
     row.get('army_natural_phase_observations_v1'),expected_carmy_id=row['native_carmy_id'])
 physical=evaluate_army_physical_loss_evidence_12004(row,exact_source=True,after_sequence=after_sequence)
 valid={e['sequence']:e for kind in ('positive_events','other_observed_physical_events') for e in physical[kind]}
 result['global_journal_coverage']=deepcopy(physical.get('journal_coverage'))
 result['whole_window_complete']=bool(family['observer_installed'] and family['latest_sequence']>=after_sequence
     and (not family['oldest_available_sequence'] or after_sequence>=family['oldest_available_sequence']-1)
     and before_unattributed_capture_failures is not None
     and family['unattributed_capture_failures']==before_unattributed_capture_failures)
 contexts=[e.get(KEY) for e in family['events'] if e.get(KEY) is not None]
 tokens=Counter(c['writer_invocation_token'] for c in contexts)
 for event in family['events']:
  if event['sequence']<=after_sequence or event['caller_return_rva']!=0x24E25EE:continue
  c=event.get(KEY);reasons=[]
  if event['sequence'] not in valid:reasons.append('complete_physical_writer_fact_missing')
  if c is None:reasons.append('invocation_owner_not_captured')
  elif not c['source_complete']:reasons.append('native_owner_capture_incomplete')
  else:
   if (c['army_id']!=row['army_id'] or c['native_carmy_id']!=row['native_carmy_id']):reasons.append('different_invocation_Army')
   if c['writer_full_regiment_id']!=event['army_regiment_id']:reasons.append('different_invocation_ArRg')
   if tokens[c['writer_invocation_token']]!=1:reasons.append('writer_invocation_token_reused')
   matches=[r for r in (phase or {}).get('records',[]) if r['scope']['entry_event']==c['phase_entry_event']]
   if len(matches)!=1:reasons.append('unique_returned_phase_parent_missing')
   else:
    r=matches[0];s=r['scope'];roster=s['original_army_roster'];index=c['phase_roster_occurrence']
    if not (s['phase']=='pre_date' and s['actual_entry_rva']==0x2A99DA0
       and s['primary_manager_identity']==c['phase_primary_manager_identity']
       and s['game_state_identity']==c['phase_game_state_identity']
       and r['original_called'] and r['original_returned'] and r['same_clock_thread_order'] is True
       and later(c['writer_event'],r['returned_event'])):reasons.append('actual_parent_identity_thread_or_return_order_differs')
    if not (roster['boundary']=='pre_date_prefix_return' and roster['capture_rva']==0x2A99E76
       and roster['complete'] and roster['capture_event']==c['phase_prefix_roster_event']
       and 0<=index<len(roster['ordered_full_ids'])
       and roster['ordered_full_ids'][index]==(c['native_carmy_id']&0xffffffff)):
     reasons.append('original_parent_roster_occurrence_differs')
    if s['prefix_date_raw'] is None or event['observed_date_raw'] is None or (s['prefix_date_raw']&0xffffffff)!=(event['observed_date_raw']&0xffffffff):
     reasons.append('literal_prefix_date_differs')
  if reasons:
   result['excluded_invocations'].append(dict(sequence=event['sequence'],reasons=reasons));continue
  fact=deepcopy(valid[event['sequence']]);fact['county_primary_owner_at_writer_v1']=deepcopy(c)
  key='positive_invocations' if fact['actual_physical_soldier_debit']>0 else 'other_qualified_invocations'
  result[key].append(fact)
 result['individual_county_army_owner_observed']=bool(result['positive_invocations'] or result['other_qualified_invocations'])
 result['status']='retained_owned_county_primary_positive' if result['positive_invocations'] else 'no_qualified_positive_owner_join'
 return result
