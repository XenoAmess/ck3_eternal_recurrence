"""Pure compact-receipt seam; no checkpoint body/native/provider access.

Exact SDK normalization bodies are pinned in dependencies. Provenance describes
independently preserved artifacts; consistency never grants actual acceptance.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent/'dependencies'))
import confucian_dto_primitives as sdk
from save_fields import stored
from bounded_save_parser import one

CONTRACT_HEAD='632f0a57a07aa6299052004589ed6f7632e7d8f7'
READER_SHA='eaf76fda320b6ff8414ac8390c411e42b9b79c94890cfbb5dfd2f7c1f0cd42c9'
SDK_METADATA_SHA='8f8ee5c1d59ef7c3456b46d697ff35033b4fb9cbb971948b135c03bf17247aec'
SDK_CODEC_SHA='a8ddde00321b53ec43fa1cebe38cd14f8ffc62407f61fbb95b8636476d044969'
BUSINESS_CONTRACT_SHA='a95b8f65cf46b731c4556ffb12bbce38d47de61ede8222c383f85209c9730643'
U32_MAX=2**32-1

class QualificationError(ValueError):pass
def need(ok,label):
 if not ok:raise QualificationError(label)
def exact(obj,keys,label):need(type(obj)is dict and set(obj)==set(keys),'closed '+label);return obj
def sha(data):return hashlib.sha256(data).hexdigest()
def valid_sha(value):return type(value)is str and re.fullmatch('[0-9a-f]{64}',value)is not None
def full_actor(value):
 need(type(value)is int and -(2**31)<=value<=U32_MAX-1 and value!=-1,'invalid actor generation')
 return value & U32_MAX
def strict_id(value,label):need(type(value)is int and 0<=value<U32_MAX,'invalid '+label);return value
def positive(value,label):need(type(value)is int and 0<value<2**64,'invalid '+label);return value
def unique_ids(value,label):
 need(type(value)is list and len(value)==len(set(value)),'duplicate/missing '+label)
 for i in value:strict_id(i,label)
 return value
def parse_json_buffer(data):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate JSON key '+k);d[k]=v
  return d
 def constant(token):raise QualificationError('nonfinite JSON '+token)
 return json.loads(data.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=constant)
def json_load(path):return parse_json_buffer(Path(path).read_bytes())
def load_descriptor(desc):
 exact(desc,{'path','bytes','sha256'},'compact artifact descriptor')
 need(type(desc['path'])is str and Path(desc['path']).suffix.lower()=='.json','only compact JSON artifacts may be opened')
 need(type(desc['bytes'])is int and 0<desc['bytes']<=8*1024*1024 and valid_sha(desc['sha256']),'bounded artifact metadata')
 p=Path(desc['path']);need(p.stat().st_size==desc['bytes'],'artifact size mismatch')
 data=p.read_bytes();need(sha(data)==desc['sha256'],'artifact SHA mismatch')
 return parse_json_buffer(data)

def frame_binding(snapshot):
 need(type(snapshot)is dict and snapshot.get('paused')is True and snapshot.get('map_ready')is True,'not a paused native checkpoint frame')
 actor=snapshot.get('played_character');diag=snapshot.get('diagnostics');hello=diag.get('hello')if type(diag)is dict else None
 need(type(actor)is dict and actor.get('alive')is True and type(hello)is dict and diag.get('connected')is True,'actual alive actor/connected HELLO required')
 try:sdk.snapshot_build_identity(snapshot)
 except ValueError as e:raise QualificationError('actual HELLO exact version/image/adapter differs: '+str(e))from e
 need(snapshot.get('one_life_terminal_reason')is None,'terminal frame')
 positive(snapshot.get('revision'),'public revision');positive(snapshot.get('native_revision'),'native revision')
 need(type(snapshot.get('snapshot_id'))is str and snapshot['snapshot_id'],'missing snapshot identity')
 need(type(snapshot.get('date_raw'))is int and -(2**31)<=snapshot['date_raw']<2**31,'date')
 need(type(hello.get('pid'))is int and 0<hello['pid']<2**32,'PID uint32');positive(diag.get('connection_generation'),'connection generation')
 full_actor(actor.get('character_id'))
 return {'revision':snapshot['revision'],'native_revision':snapshot['native_revision'],'date_raw':snapshot['date_raw'],
  'game_pid':hello['pid'],'connection_generation':diag['connection_generation'],'played_character_id':actor['character_id'],'snapshot_id':snapshot['snapshot_id']}

def outer_identity(receipt,provenance):
 need(type(receipt)is dict and receipt.get('schema')=='ck3.native-profile-receipt.v1','actual SDK profile receipt required')
 for key in ('session_id','profile_sha256','pipe_name'):
  need(receipt.get(key)==provenance[key],'SDK '+key+' provenance differs')
 need(type(receipt.get('recorded_at_utc'))is str and receipt['recorded_at_utc'] and type(receipt.get('receipt_path'))is str and receipt['receipt_path'],'receipt identity/time missing')

def validate_provenance(provenance,immutable_business_files):
 keys={'schema','source_head','source_export_sha256','DLL_sha256','session_id','profile_sha256','pipe_name','game_pid','connection_generation',
       'reader_contract_source_head','reader_sha256','sdk_metadata_sha256','sdk_codec_sha256','current_business_files','capture_epochs'}
 exact(provenance,keys,'actual source/profile/checkpoint provenance')
 need(provenance['schema']=='lyd.actual-sdk-checkpoint-provenance.v1','provenance schema')
 need(type(provenance['source_head'])is str and re.fullmatch('[0-9a-f]{40}',provenance['source_head']),'pending actual source HEAD')
 for k in ('source_export_sha256','DLL_sha256','profile_sha256'):need(valid_sha(provenance[k]),'pending '+k)
 need(provenance['reader_contract_source_head']==CONTRACT_HEAD and provenance['reader_sha256']==READER_SHA,'frozen reader contract differs')
 need(provenance['sdk_metadata_sha256']==SDK_METADATA_SHA and provenance['sdk_codec_sha256']==SDK_CODEC_SHA,'exact private23 metadata/codec differs')
 data=(Path(__file__).parent/'dependencies/frozen_business_contract.json').read_bytes()
 need(sha(data)==BUSINESS_CONTRACT_SHA,'frozen business contract bytes changed')
 fixed=json.loads(data)['files']
 need(type(immutable_business_files)is dict and immutable_business_files==fixed and provenance['current_business_files']==fixed,'actual business source bytes differ from fixed frozen69 contract')
 need(all(type(k)is str and valid_sha(v)for k,v in immutable_business_files.items()),'business manifest shape')
 need(all(type(provenance[k])is str and provenance[k]for k in ('session_id','pipe_name')),'pending session/pipe')
 need(type(provenance['game_pid'])is int and 0<provenance['game_pid']<2**32,'provenance PID uint32');positive(provenance['connection_generation'],'generation')
 exact(provenance['capture_epochs'],{'assembly_predicates','religious_title'},'independent expected capture epochs')
 for k,v in provenance['capture_epochs'].items():positive(v,k+' epoch')

def convert(provenance,checkpoint,state,g2_receipt,g3_receipt,*,immutable_business_files,artifact_hashes):
 """Join verified compact JSON objects; caller never supplies derived booleans.

 CLI verifies exact descriptor bytes before this pure function. Its output is a
 consistency observation, not authentication of the executing game/source.
 """
 validate_provenance(provenance,immutable_business_files)
 exact(artifact_hashes,{'provenance','checkpoint_receipt','saved_state','G2_receipt','G3_receipt'},'exact artifact hashes')
 need(all(valid_sha(v)for v in artifact_hashes.values()),'missing artifact hashes')
 for r in (checkpoint,g2_receipt,g3_receipt):outer_identity(r,provenance)
 need(checkpoint.get('status')=='native_gameplay_postcondition_verified' and checkpoint.get('uses_ocr')is False and checkpoint.get('uses_desktop_input')is False,'checkpoint SDK postcondition missing')
 before,after=checkpoint.get('snapshot_before'),checkpoint.get('snapshot_after')
 binding=frame_binding(before);later=frame_binding(after)
 build=sdk.snapshot_build_identity(before)
 need(build==sdk.snapshot_build_identity(after),'checkpoint exact build changed')
 need(binding==later,'checkpoint crossed native/public snapshot frame; independent new binding required')
 for k in ('played_character','active_event','pending_character_interaction','speed','local_player_id','episode_character_id'):
  need(before.get(k)==after.get(k),'checkpoint frame state changed '+k)
 need(binding['game_pid']==provenance['game_pid'] and binding['connection_generation']==provenance['connection_generation'],'checkpoint PID/connection differs')
 cp=checkpoint.get('result',{}).get('checkpoint')
 need(type(cp)is dict and cp.get('status')=='saved' and type(cp.get('path'))is str and cp['path'] and type(cp.get('size'))is int and cp['size']>0 and valid_sha(cp.get('sha256')) and cp.get('date_raw')==binding['date_raw'],'exact materialized checkpoint descriptor missing')
 need(state.get('schema')=='lyd.i3b.checkpoint-observations.v1' and state.get('source_head')==CONTRACT_HEAD and state.get('checkpoint_sha256')==cp['sha256'],'saved state checkpoint/source differs')
 identity=state.get('identity');need(type(identity)is dict,'saved identity missing')
 expected_identity={'actor_id':full_actor(binding['played_character_id']),'pid':binding['game_pid'],'session_id':provenance['session_id'],'revision':binding['native_revision'],'checkpoint_id':cp['path']}
 for k,v in expected_identity.items():need(type(identity.get(k))is type(v) and identity[k]==v,'saved identity differs '+k)
 need(state.get('actual_pass')is None and state.get('actual_native_runtime_pass')is None and state.get('formal_mandate_credit')is None,'saved state cannot carry invented actual/formal credit')
 outputs=[]
 for operation,receipt in (('assembly_predicates',g2_receipt),('religious_title',g3_receipt)):
  need(receipt.get('business_effects_verified')is False and receipt.get('full_product_acceptance_credit')is False,'SDK read cannot carry business credit')
  try:public=sdk.normalize_public_query(receipt.get('result'),binding,operation)
  except (ValueError,TypeError,AttributeError,KeyError)as e:raise QualificationError('malformed/bound '+operation+': '+str(e))from e
  nested='confucian_assembly_predicates'if operation=='assembly_predicates'else'confucian_religious_title'
  dto=public['native_result'][nested]
  need(sdk.exact_build_identity(dto['game_version'],dto['executable_sha256'])==build,'native query exact build differs from checkpoint')
  need(receipt.get('status')=='native_confucian_readonly_'+public['native_result']['status'],'SDK outer operation availability differs')
  need(dto['capture_epoch']==provenance['capture_epochs'][operation],'stale '+operation+' capture epoch')
  outputs.append((public,dto))
 (public2,g2),(public3,g3)=outputs
 common={'source_head':provenance['source_head'],'source_export_sha256':provenance['source_export_sha256'],'DLL_sha256':provenance['DLL_sha256'],
   'session_id':provenance['session_id'],'profile_sha256':provenance['profile_sha256'],'pipe_name':provenance['pipe_name'],
   'game_pid':binding['game_pid'],'connection_generation':binding['connection_generation'],'queried_snapshot_id':binding['snapshot_id'],
   'queried_revision':binding['revision'],'queried_native_revision':binding['native_revision'],'date_raw':binding['date_raw'],
   'played_character_id':binding['played_character_id'],'played_character_full_id':full_actor(binding['played_character_id']),
   'checkpoint':deepcopy(cp),'artifact_sha256':deepcopy(artifact_hashes),'G2_capture_epoch':g2['capture_epoch'],'G3_capture_epoch':g3['capture_epoch']}
 out={'schema':'lyd.sdk-checkpoint-qualified-native.v1','runtime_binding':common,'reader_contract_source_head':CONTRACT_HEAD,
      'native_predicates':None,'G2_status':'UNKNOWN','G2_reader_compatibility':None,'qualified_native_head':None,
      'G2_raw_public':deepcopy(public2),'G3_raw_public':deepcopy(public3),'actual_pass':None,'formal_mandate_credit':None,'business_postcondition_verified':False,'full_product_acceptance_credit':False}
 roster=state.get('roster');need(type(roster)is dict and roster.get('whole_world_living_records_scanned')is True and roster.get('faith_classification_complete')is True,'complete saved living Faith classification required')
 saved_members=unique_ids(roster.get('living_faith_ids'),'saved Faith members')
 saved_rites=unique_ids([r['id']for r in state.get('rites',[])],'saved Faith Rites')
 compatibility=[]
 if g2['available']and g2['predicates_complete']:
  need(g2['faith_id']==identity.get('faith_id') and g2['played_rite_id']==identity.get('main_rite_id'),'native/saved Faith/main differs')
  need(set(g2['complete_native_faith_member_ids'])==set(saved_members) and set(g2['complete_native_faith_rite_ids'])==set(saved_rites),'native/saved full Faith member/Rite sets differ')
  need(all(r['alive']is True for r in g2['members']),'complete native Faith roster contains nonliving member')
  if any(r['effective_learning']<0 for r in g2['members']):compatibility.append('reader_v1_rejects_valid_negative_effective_learning')
  if any(i==0 for i in saved_members+saved_rites):compatibility.append('reader_v1_rejects_valid_zero_full_reference')
  out['G2_reader_compatibility']={'compatible':not compatibility,'reasons':compatibility,'native_effective_learning_preserved':True}
  out['G2_status']='READER_SCHEMA_INCOMPATIBLE'if compatibility else'BOUND_COMPLETE_NATIVE_OBSERVATION'
  if not compatibility:
   out['native_predicates']={'schema':'lyd.i3b.native-predicates.v1','source_head':CONTRACT_HEAD,'checkpoint_sha256':cp['sha256'],'identity':deepcopy(identity),
     'complete_current_faith_roster':True,'human_character_ids':sorted(r['character_id']for r in g2['members']if r['is_ai']is False),
     'characters':[{k:r[k]for k in ('character_id','alive','adult','imprisoned','incapable','is_ai')}|{'learning':r['effective_learning']}for r in g2['members']],
     'rite_counties':{str(r['rite_id']):r['native_county_count']for r in g2['rites']},'evidence_sha256':artifact_hashes['G2_receipt']}
 else:out['G2_reader_compatibility']={'compatible':False,'reasons':['native_available_and_predicates_complete_required'],'native_effective_learning_preserved':True}
 head={'schema':'lyd.qualified-native-head.v1','status':'UNKNOWN','runtime_binding':deepcopy(common),'capture_epoch':g3['capture_epoch'],
  'native_graph':{k:deepcopy(g3[k])for k in ('graph_available','graph_unavailable_reason','legal_head_title_absent','faith_full_id','head_title_full_id','native_title_holder_full_id','native_title_holder_absent','native_title_class')},
  'title_properties':deepcopy(g3['title_properties']),'title_laws':deepcopy(g3['title_laws']),'static_qualification':deepcopy(g3['qualification']),
  'mod_owned_marker':None,'mod_owner_faith_variable':None,'saved_title_join':None,'saved_title_ownership_observed':None,'factory_contract_match':None,
  'saved_Title_type_binding':None,'saved_title_law_property_paths':None,'reader_compatibility':None,'actual_pass':None,'formal_mandate_credit':None}
 if g3['available']and g3['graph_available']:
  need(g3['faith_full_id']==identity.get('faith_id'),'G3 native/saved current Faith differs')
  if g3['legal_head_title_absent']is True:
   head['status']='BOUND_NATIVE_HEADLESS_OBSERVATION';head['factory_contract_match']=False
  else:
   t=g3['head_title_full_id'];saved=state.get('native_title');raw_ref=state.get('result_head_title_reference')
   if t==0:head['reader_compatibility']={'compatible':False,'reason':'reader_v1_rejects_valid_present_Title_zero'}
   else:head['reader_compatibility']={'compatible':True,'reason':None}
   if saved is not None:
    need(type(saved)is dict and saved.get('title_id')==t,'native/saved actual T differs')
    need(type(raw_ref)is dict and type(raw_ref.get('identity'))is str and raw_ref['identity']==str(t),'actual saved result T reference required')
    need(type(raw_ref.get('type'))is str and raw_ref['type'] and raw_ref['type']not in ('char','faith','rite','value','boolean'),'contradictory saved result T reference type')
    entries=saved.get('entries');need(type(entries)is list,'actual full saved T AST required')
    actual_ast_sha=sha(json.dumps(entries,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    need(saved.get('AST_sha256')==actual_ast_sha,'saved T full AST digest differs')
    raw_holder=one(entries,'holder')
    if raw_holder in (None,str(U32_MAX)):
     saved_holder=None
    else:
     need(type(raw_holder)is str and re.fullmatch('[0-9]+',raw_holder),'saved T holder syntax')
     saved_holder=strict_id(int(raw_holder),'saved T holder')
    need(saved_holder==g3['native_title_holder_full_id'],'saved/native actual T full holder differs')
    v,_,_=stored(entries);owned=v.get('lyd_c2_owned_head_title');owner=v.get('lyd_c2_owner_faith')
    need(saved.get('variables')==v,'saved T decoded variables differ from full AST')
    need(type(owned)is dict and owned.get('type')=='value'and owned.get('number')=='1','actual saved owned marker1 required')
    need(type(owner)is dict and owner.get('type')=='faith'and owner.get('identity')==str(identity['faith_id']),'actual saved typed ownerFaith required')
    head['saved_title_join']={'title_id':t,'AST_sha256':saved['AST_sha256'],'result_head_title_reference':deepcopy(raw_ref),'owned_marker':deepcopy(owned),'owner_faith_variable':deepcopy(owner),'saved_state_sha256':artifact_hashes['saved_state'],'saved_type_binding_status':deepcopy(state.get('native_reference_qualification'))}
    head['saved_title_ownership_observed']=True
   props=g3['title_properties'];laws=g3['title_laws']
   if props['available']and laws['available']:
    head['status']='BOUND_NATIVE_TITLE_FIELDS_OBSERVATION'if head['saved_title_join']is not None else'BOUND_NATIVE_FIELDS_SAVED_OWNERSHIP_UNKNOWN'
    head['factory_contract_match']=(g3['native_title_holder_absent']is False and g3['native_title_holder_full_id']==full_actor(binding['played_character_id']) and all(props[k]is True for k in ('destroy_if_invalid_heir','no_automatic_claims','definitive_form','always_follows_primary_heir'))and laws['temporal_head_of_faith_succession_law_member']is True)
 out['qualified_native_head']=head
 out['authority']='compact SDK/saved consistency only; actual execution/source authentication and formal ballot acceptance require independent ROOT evidence'
 return out

def run_request(request):
 exact(request,{'schema','artifacts','immutable_business_files','output'},'converter request')
 need(request['schema']=='lyd.sdk-checkpoint-conversion-request.v1','request schema')
 names={'provenance','checkpoint_receipt','saved_state','G2_receipt','G3_receipt'}
 exact(request['artifacts'],names,'compact input artifacts')
 objects={k:load_descriptor(request['artifacts'][k])for k in names}
 return convert(objects['provenance'],objects['checkpoint_receipt'],objects['saved_state'],objects['G2_receipt'],objects['G3_receipt'],immutable_business_files=request['immutable_business_files'],artifact_hashes={k:request['artifacts'][k]['sha256']for k in names})

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True,type=Path);a=p.parse_args()
 r=json_load(a.request);out=run_request(r);d=Path(r['output']);need(not d.exists(),'output already exists');d.mkdir(parents=True,exist_ok=False)
 (d/'QUALIFIED-NATIVE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(d),'G2_status':out['G2_status'],'head_status':out['qualified_native_head']['status'],'actual_pass':None}))
if __name__=='__main__':main()
