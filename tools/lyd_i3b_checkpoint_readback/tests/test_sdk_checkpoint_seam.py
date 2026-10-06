from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
P=Path(__file__).parents[1];sys.path.insert(0,str(P/'reader'));sys.path.insert(0,str(P/'reader/dependencies'))
import sdk_checkpoint_qualification as seam
import sdk_fixture_builders as f
from save_fields import stored

def fixture(actor=31254):
 snapshot=f.frame();snapshot['played_character']['character_id']=actor
 binding=seam.frame_binding(snapshot)
 dto2=f.assembly(binding)
 for r in dto2['members']:r['is_ai']=r['character_id']!=(actor&0xFFFFFFFF)
 dto3=f.title(binding);dto3['native_title_holder_full_id']=actor&0xFFFFFFFF
 native2=f.envelope('assembly_predicates',binding,dto2);native3=f.envelope('religious_title',binding,dto3)
 public2=seam.sdk.project_native_query(native2,binding,'assembly_predicates');public3=seam.sdk.project_native_query(native3,binding,'religious_title')
 business=json.loads((P/'reader/dependencies/frozen_business_contract.json').read_text(encoding='utf-8'))['files']
 provenance={'schema':'lyd.actual-sdk-checkpoint-provenance.v1','source_head':'f'*40,'source_export_sha256':'1'*64,'DLL_sha256':'2'*64,'session_id':'synthetic-session',
  'profile_sha256':'3'*64,'pipe_name':'synthetic-pipe','game_pid':991,'connection_generation':2,'reader_contract_source_head':seam.CONTRACT_HEAD,'reader_sha256':seam.READER_SHA,
  'sdk_metadata_sha256':seam.SDK_METADATA_SHA,'sdk_codec_sha256':seam.SDK_CODEC_SHA,'current_business_files':business,'capture_epochs':{'assembly_predicates':42,'religious_title':43}}
 def outer(result):return {'schema':'ck3.native-profile-receipt.v1','session_id':'synthetic-session','profile_sha256':'3'*64,'pipe_name':'synthetic-pipe','recorded_at_utc':'synthetic-time','receipt_path':'synthetic-receipt.json',
  'status':'native_confucian_readonly_observed','result':result,'business_effects_verified':False,'full_product_acceptance_credit':False}
 g2=outer(public2);g3=outer(public3)
 cp=outer({'checkpoint':{'status':'saved','path':'synthetic-new-checkpoint.ck3','size':123,'sha256':'4'*64,'date_raw':binding['date_raw']}})
 cp.update(status='native_gameplay_postcondition_verified',snapshot_before=copy.deepcopy(snapshot),snapshot_after=copy.deepcopy(snapshot),uses_ocr=False,uses_desktop_input=False)
 entries=[{'key':'holder','value':str(actor&0xFFFFFFFF)},{'key':'variables','value':[{'key':'data','value':[
  {'key':None,'value':[{'key':'flag','value':'"lyd_c2_owned_head_title"'},{'key':'data','value':[{'key':'type','value':'value'},{'key':'identity','value':'100000'}]}]},
  {'key':None,'value':[{'key':'flag','value':'"lyd_c2_owner_faith"'},{'key':'data','value':[{'key':'type','value':'faith'},{'key':'identity','value':'107'}]}]}]}, {'key':'list','value':[]}]}]
 variables,_,_=stored(entries)
 state={'schema':'lyd.i3b.checkpoint-observations.v1','source_head':seam.CONTRACT_HEAD,'checkpoint_sha256':'4'*64,
  'identity':{'actor_id':actor&0xFFFFFFFF,'faith_id':107,'main_rite_id':169,'pid':991,'session_id':'synthetic-session','revision':7,'checkpoint_id':'synthetic-new-checkpoint.ck3'},
  'actual_pass':None,'actual_native_runtime_pass':None,'formal_mandate_credit':None,
  'roster':{'whole_world_living_records_scanned':True,'faith_classification_complete':True,'living_faith_ids':dto2['complete_native_faith_member_ids']},
  'rites':[{'id':169},{'id':170}],
  'native_title':{'title_id':dto3['head_title_full_id'],'entries':entries,'AST_sha256':seam.sha(json.dumps(entries,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),'variables':variables},
  'result_head_title_reference':{'type':'synthetic_saved_title_discriminator','identity':str(dto3['head_title_full_id'])},'native_reference_qualification':{'status':'UNKNOWN'}}
 return {'provenance':provenance,'checkpoint':cp,'state':state,'g2':g2,'g3':g3,'business':business,'hashes':{k:str(i)*64 for i,k in enumerate(('provenance','checkpoint_receipt','saved_state','G2_receipt','G3_receipt'),1)}}
def run(d):return seam.convert(d['provenance'],d['checkpoint'],d['state'],d['g2'],d['g3'],immutable_business_files=d['business'],artifact_hashes=d['hashes'])
def payload(d,n):return d['g'+str(n)]['result']['native_result']['confucian_assembly_predicates'if n==2 else'confucian_religious_title']

class SeamTests(unittest.TestCase):
 def test_explicit_mapping_fullsets_humans_counties_distinct_epochs_and_head_join(self):
  d=fixture();out=run(d)
  self.assertEqual(out['native_predicates']['human_character_ids'],[31254])
  self.assertEqual(out['native_predicates']['rite_counties'],{'169':1,'170':0})
  self.assertEqual(out['runtime_binding']['G2_capture_epoch'],42);self.assertEqual(out['runtime_binding']['G3_capture_epoch'],43)
  head=out['qualified_native_head'];self.assertEqual(head['native_graph']['head_title_full_id'],0xF1000001)
  self.assertTrue(head['factory_contract_match']);self.assertIsNone(head['mod_owner_faith_variable'])
  self.assertEqual(head['saved_title_join']['owner_faith_variable']['identity'],'107');self.assertIsNone(head['saved_Title_type_binding'])
  self.assertIsNone(out['actual_pass']);self.assertFalse(out['full_product_acceptance_credit'])
 def test_independent_owner_frame_source_changes_rejected(self):
  cases=[lambda d:d['g2'].update(session_id='other'),lambda d:d['g3'].update(profile_sha256='9'*64),lambda d:d['g2']['result'].update(game_pid=992),
   lambda d:d['g3']['result'].update(connection_generation=3),lambda d:d['g2']['result'].update(queried_snapshot_id='stale'),lambda d:d['g3']['result'].update(queried_revision=2),
   lambda d:d['g2']['result'].update(queried_native_revision=8),lambda d:d['g3']['result'].update(date_raw=0),lambda d:d['state']['identity'].update(revision=3),
   lambda d:d['provenance']['current_business_files'].update({'events/lyd_i3b_institution_events.txt':'0'*64}),lambda d:d['checkpoint']['snapshot_after'].update(native_revision=8)]
  for mutate in cases:
   d=fixture();mutate(d)
   with self.assertRaises(seam.QualificationError):run(d)
 def test_epoch_stale_and_sdk_credit_mutation_rejected(self):
  for mutate in (lambda d:payload(d,2).update(capture_epoch=41),lambda d:payload(d,3).update(capture_epoch=42),lambda d:d['g2'].update(business_effects_verified=True),lambda d:d['g3']['result'].update(full_product_acceptance_credit=True)):
   d=fixture();mutate(d)
   with self.assertRaises(seam.QualificationError):run(d)
 def test_incomplete_predicate_unknown_not_zero_and_fullsets_mismatch(self):
  d=fixture();g=payload(d,2);g.update(predicates_complete=False,unavailable_reason='one leaf unavailable');g['members'][0].update(complete=False,unavailable_reason='prison unknown',imprisoned=None)
  o=run(d);self.assertIsNone(o['native_predicates']);self.assertEqual(o['G2_status'],'UNKNOWN');self.assertIsNone(payload({'g2':{'result':o['G2_raw_public']}},2)['members'][0]['imprisoned'])
  d=fixture();d['state']['roster']['living_faith_ids']=d['state']['roster']['living_faith_ids'][:-1]
  with self.assertRaises(seam.QualificationError):run(d)
  d=fixture();d['state']['rites'].pop()
  with self.assertRaises(seam.QualificationError):run(d)
 def test_unknown_counties_and_signed_learning_preserved_without_bridge(self):
  d=fixture();g=payload(d,2);g.update(predicates_complete=False,unavailable_reason='county unknown');g['rites'][1].update(complete=False,unavailable_reason='unknown',county_title_ids=None,native_county_count=None)
  out=run(d);self.assertIsNone(out['native_predicates']);self.assertIsNone(out['G2_raw_public']['native_result']['confucian_assembly_predicates']['rites'][1]['native_county_count'])
  d=fixture();payload(d,2)['members'][0]['effective_learning']=-1
  out=run(d);self.assertIsNone(out['native_predicates']);self.assertEqual(out['G2_status'],'READER_SCHEMA_INCOMPATIBLE')
  self.assertEqual(out['G2_raw_public']['native_result']['confucian_assembly_predicates']['members'][0]['effective_learning'],-1)
 def test_high_generation_actor_kept_and_only_minus_one_absent(self):
  d=fixture(-2147483646);o=run(d);self.assertEqual(o['runtime_binding']['played_character_full_id'],0x80000002)
  self.assertEqual(o['native_predicates']['identity']['actor_id'],0x80000002)
  for value in (-1,True):
   d=fixture();d['checkpoint']['snapshot_before']['played_character']['character_id']=value
   with self.assertRaises(seam.QualificationError):run(d)
 def test_native_false_property_and_law_nonmember_remain_false(self):
  d=fixture();payload(d,3)['title_properties']['definitive_form']=False
  o=run(d);self.assertFalse(o['qualified_native_head']['factory_contract_match']);self.assertFalse(o['qualified_native_head']['title_properties']['definitive_form'])
  d=fixture();laws=payload(d,3)['title_laws'];laws['complete_laws'].pop();laws.update(native_count=1,temporal_head_of_faith_succession_law_member=False)
  o=run(d);self.assertFalse(o['qualified_native_head']['factory_contract_match']);self.assertEqual(o['qualified_native_head']['title_laws']['native_count'],1)
 def test_known_absent_head_is_not_unknown_or_factory_success(self):
  d=fixture();g=payload(d,3)
  g.update(legal_head_title_absent=True,head_title_full_id=None,native_title_holder_full_id=None,native_title_holder_absent=None,native_title_class=None)
  for sub in ('title_holder','title_properties','title_laws'):
   row=g[sub]
   for k in row:
    if k not in ('available','unavailable_reason','expected_law_key'):row[k]=None
   row.update(available=False,unavailable_reason='known_absent_head')
  d['state']['native_title']=None;d['state']['result_head_title_reference']=None
  o=run(d);h=o['qualified_native_head'];self.assertEqual(h['status'],'BOUND_NATIVE_HEADLESS_OBSERVATION');self.assertFalse(h['factory_contract_match'])
  self.assertIsNone(h['native_graph']['head_title_full_id']);self.assertIsNone(h['title_properties']['definitive_form'])
 def test_present_title_zero_is_preserved_with_reader_compatibility_gap(self):
  d=fixture();payload(d,3)['head_title_full_id']=0;d['state']['native_title']=None;d['state']['result_head_title_reference']=None
  h=run(d)['qualified_native_head'];self.assertEqual(h['native_graph']['head_title_full_id'],0)
  self.assertFalse(h['native_graph']['legal_head_title_absent']);self.assertFalse(h['reader_compatibility']['compatible']);self.assertIsNone(h['saved_title_join'])
 def test_native_class_not_saved_type_or_owned_and_actual_full_ast_required(self):
  d=fixture();d['state']['native_title']['variables']['lyd_c2_owner_faith']['identity']='106'
  with self.assertRaises(seam.QualificationError):run(d)
  d=fixture();d['state']['native_title']['entries'].append({'key':'changed','value':'yes'})
  with self.assertRaises(seam.QualificationError):run(d)
  d=fixture();payload(d,3)['mod_owner_faith_variable']=107
  with self.assertRaises(seam.QualificationError):run(d)
 def test_artifact_bytes_sha_and_body_extension_rejected(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'receipt.json';p.write_text('{}',encoding='utf-8')
   with self.assertRaises(seam.QualificationError):seam.load_descriptor({'path':str(p),'bytes':2,'sha256':'0'*64})
  with self.assertRaises(seam.QualificationError):seam.load_descriptor({'path':'DO_NOT_OPEN.ck3','bytes':91669783,'sha256':'0'*64})
 def test_descriptor_parses_the_verified_buffer_even_if_file_changes(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'receipt.json';data=b'{"verified":true}';p.write_bytes(data)
   original=Path.read_bytes
   def race(path):
    result=original(path)
    if path==p:path.write_bytes(b'{"unverified":true}')
    return result
   with patch.object(Path,'read_bytes',race):
    actual=seam.load_descriptor({'path':str(p),'bytes':len(data),'sha256':seam.sha(data)})
   self.assertEqual(actual,{'verified':True})
 def test_matching_before_after_wrong_hello_pins_rejected(self):
  for key,value in (('expected_ck3_version','1.19.0.6'),('expected_ck3_sha256','0'*64)):
   d=fixture()
   for side in ('snapshot_before','snapshot_after'):d['checkpoint'][side]['diagnostics']['hello'][key]=value
   with self.assertRaises(seam.QualificationError):run(d)
 def test_known_non_title_discriminators_rejected(self):
  for kind in ('char','faith','rite','value','boolean'):
   d=fixture();d['state']['result_head_title_reference']['type']=kind
   with self.assertRaises(seam.QualificationError):run(d)
 def test_rehashed_saved_title_wrong_holder_rejected(self):
  d=fixture();row=d['state']['native_title'];row['entries'][0]['value']='65865'
  row['AST_sha256']=seam.sha(json.dumps(row['entries'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
  with self.assertRaises(seam.QualificationError):run(d)

if __name__=='__main__':unittest.main(verbosity=2)
