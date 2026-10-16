"""stdlib-only replay of exact R189 cuts through frozen production consumers."""
from pathlib import Path
import hashlib,importlib.util,json,sys,types
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
def main():
 evidence=json.loads((ROOT/'EVIDENCE.actual-a34.json').read_bytes())
 package=types.ModuleType('r189_frozen');package.__path__=[str(ROOT/'consumer')];sys.modules[package.__name__]=package
 for pin in evidence['consumer_files']:
  path=ROOT/'consumer'/Path(pin['path']).name;data=path.read_bytes()
  assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
 from r189_frozen.gui_refill_receiver_candidates_12004_contract import normalize_receiver_candidates,normalize_receiver_frame
 from r189_frozen.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004
 actual=[];common={}
 for cut in evidence['exact_body_cuts']:
  path=ROOT/cut['portable_path'];data=path.read_bytes()
  assert len(data)==cut['bytes'] and hashlib.sha256(data).hexdigest()==cut['sha256']
  raw=json.loads(data)
  if cut['key']=='receiver_entry_candidates_12004':
   clean=normalize_receiver_candidates(raw);assert clean==raw;actual.append(clean)
  else:common[cut['key']]=raw
 assert common['callback_binding_source_12004']==SOURCE_RECEIVER_12004
 assert normalize_receiver_frame(common['refill_receiver_frame_12004'])==evidence['frame']
 assert common['refill_receiver_public_binding_12004']==evidence['public_binding']
 assert len(actual)==2 and actual[0]==actual[1]
 for full in actual:
  assert full['status']=='unavailable' and full['unavailable_reason']=='candidate_parent_depth_exhausted'
  assert full['failure_diagnostic']['capture_pass']==1 and full['failure_diagnostic']['ancestor_depth']==8
  p=full['definition_chain_prefix_depth8'];assert p['status']=='available' and p['stable_double_read']
  assert not p['walk_complete'] and not p['native_receiver_selected']
  for row in p['rows']:
   depth=row['ancestor_depth']
   if depth in (0,4):
    assert row['definition_present'] and row['raw_definition_entry_count']==1
    e=row['entries'][0];assert e['entry_mode_40']==0 and e['entry_flag_4c']==0
    assert not e['direct_value_present'] and not e['provider_present'] and e['provider_slot2_rva'] is None
   elif depth in (1,2,3):assert row['definition_present'] and row['raw_definition_entry_count']==0 and not row['entries']
   else:assert depth in (5,6,7) and not row['definition_present'] and row['raw_definition_entry_count'] is None and not row['entries']
   assert row['parent_edge']=='context_e8' and row['parent_present']
 result=dict(status='PASS_ACTUAL_R189_PORTABLE_CUTS_FROZEN_STRICT_CONSUMER',machine_id=evidence['machine_id'],
  actual_candidate_count=2,exact_source_spans=5,unique_raw_copies=4,
  prefix_actual_available=True,eligible_parent_provider_RVAs=[],
  depth8_definition='unknown',native_receiver_selected=False,provider_execution=False,toggle=False,actual_ADD=False,
  offline_replay=True,new_live_observation=False,independent_after_snapshot_reconstructed=False)
 print(json.dumps(result))
if __name__=='__main__':main()
