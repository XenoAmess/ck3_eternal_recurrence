"""Bounded source migration: exact reviewed two files, 67 unchanged, no game."""
from pathlib import Path
from dataclasses import replace
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
D=Path(__file__).parent/'dependencies'
REGISTRATION_SHA='9943abd7b8bdce64af7b10767c9e95df8ef4f1b4b8739df5322c612e1279f75f'
POLICY_SHA='e0900b603ba818f6160545c07c54cf310c26ef7af5bb9d2f0080b5b385790113'
OLD_CONTRACT_SHA='a95b8f65cf46b731c4556ffb12bbce38d47de61ede8222c383f85209c9730643'
ALLOWED={'common/scripted_effects/lyd_c3_head_factory.txt','common/scripted_effects/lyd_i3b_setup_effects.txt'}
class MigrationError(ValueError):pass
def need(ok,reason):
 if not ok:raise MigrationError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def valid_sha(x):return type(x)is str and re.fullmatch('[0-9a-f]{64}',x)is not None
def exact(obj,keys,label):need(type(obj)is dict and set(obj)==set(keys),'closed '+label);return obj
def jread(data):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate JSON key '+k);d[k]=v
  return d
 def constant(x):raise MigrationError('nonfinite JSON '+x)
 return json.loads(data.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=constant)
def reference(path):
 p=Path(path);data=p.read_bytes();return {'path':p.as_posix(),'bytes':len(data),'sha256':sha(data)}
def read_ref(desc):
 exact(desc,{'path','bytes','sha256'},'migration artifact descriptor')
 need(type(desc['path'])is str and desc['path'] and type(desc['bytes'])is int and 0<desc['bytes']<=8*1024*1024 and valid_sha(desc['sha256']),'pending migration artifact')
 p=Path(desc['path']);need(p.stat().st_size==desc['bytes'],'migration artifact size differs');b=p.read_bytes();need(sha(b)==desc['sha256'],'migration artifact hash differs');return b
def policy():
 registration_raw=(D/'final_business_policy_registration.json').read_bytes()
 need(sha(registration_raw)==REGISTRATION_SHA,'registered final migration policy changed')
 registered=jread(registration_raw)
 need(registered['schema']=='lyd.final-business-migration-policy-registration.v2' and valid_sha(registered['approved_policy_sha256']) and registered['approved_policy_sha256']==POLICY_SHA,'ROOT final migration policy is pending')
 raw=(D/'business_migration_policy_v2.json').read_bytes();need(sha(raw)==POLICY_SHA,'frozen migration policy differs')
 old=(D/'frozen_business_contract.json').read_bytes();need(sha(old)==OLD_CONTRACT_SHA,'old69 contract changed')
 p=jread(raw);need(p['schema']=='lyd.business-contract-limited-migration-policy.v2' and set(p['allowed_exact_changed_files'])==ALLOWED,'limited policy schema/files')
 return p,jread(old)['files']
def verify_business_map(current):
 p,old=policy();need(type(current)is dict and set(current)==set(old) and len(current)==69,'complete exact69 business keys required')
 changed={k for k in old if current[k]!=old[k]};need(changed==ALLOWED,'migration changes outside exact two reviewed files')
 for rel in changed:need(current[rel]==p['allowed_exact_changed_files'][rel]['after']['sha256'],'unreviewed changed file bytes '+rel)
 need(sum(current[k]==old[k] for k in old)==67,'all other67 business files must remain exact')
 return {'changed_files':sorted(changed),'unchanged_exact_files':67,'business_files':69}
def parser():
 p,_=policy();path=D/'business_clausewitz_parser.py';need(reference(path)['sha256']==p['parser']['sha256'],'frozen business AST parser differs')
 spec=importlib.util.spec_from_file_location('qualified_business_migration_parser',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def verify_two_complete_AST(changed_bytes):
 need(type(changed_bytes)is dict and set(changed_bytes)==ALLOWED,'exact two AST inputs required')
 p,_=policy();m=parser()
 def single(b,k):
  e=[x for x in b.entries if x.key==k];need(len(e)==1,'nonunique migration AST '+k);return e[0].value
 def fp(x):return [(e.key,e.operator,fp(e.value)) for e in x.entries] if isinstance(x,m.Block) else x
 def ah(x):return sha(json.dumps(fp(x),ensure_ascii=True,separators=(',',':')).encode())
 out={}
 for rel,data in changed_bytes.items():
  approved=p['allowed_exact_changed_files'][rel];need(sha(data)==approved['after']['sha256'],'unreviewed AST bytes '+rel)
  before=(D/'migration_originals'/Path(rel).name).read_bytes();need(sha(before)==approved['before']['sha256'],'frozen original business file differs')
  old=m.parse_clausewitz(before.decode('utf-8-sig'));new=m.parse_clausewitz(data.decode('utf-8-sig'))
  need(ah(old)==approved['original_complete_AST_sha256'] and ah(new)==approved['candidate_complete_AST_sha256'],'complete business AST descriptor differs')
  if 'lyd_i3b_setup_effects' in rel:
   name='lyd_i3b_bind_event_effect';body=single(new,name);need(len(body.entries)==2 and body.entries[1].key=='if','qualified atomic preview guard shape')
   guarded=body.entries[1].value;limit=single(guarded,'limit')
   need([(e.key,e.operator,e.value) for e in limit.entries]==[('has_variable','=','lyd_i3b_serial'),('has_variable','=','lyd_i3b_nonce'),('has_variable','=','lyd_i3b_phase')],'preview guard three exact fields')
   projected=m.Block(tuple([body.entries[0]]+list(guarded.entries[1:])))
   normalized=replace(new,entries=tuple(replace(e,value=projected) if e.key==name else e for e in new.entries))
  else:
   name='lyd_c3_create_owned_temporal_head_effect';definition=single(new,name);body=single(definition,'if')
   removed=[];kept=[]
   for i,e in enumerate(body.entries):
    remove=e.key=='save_scope_value_as' or (e.key=='if' and any(r.key in ('save_scope_value_as','remove_realm_law') for r in e.value.entries))
    (removed if remove else kept).append(e)
   need(len(removed)==3 and removed[0].key=='save_scope_value_as','exact factory snapshot/capture/cleanup addition')
   inner=replace(body,entries=tuple(kept));newdef=replace(definition,entries=tuple(replace(e,value=inner) if e.key=='if' else e for e in definition.entries))
   normalized=replace(new,entries=tuple(replace(e,value=newdef) if e.key==name else e for e in new.entries))
  need(fp(normalized)==fp(old),'complete original AST differs after exact migration projection '+rel)
  out[rel]={'candidate_complete_AST_sha256':ah(new),'original_complete_AST_sha256':ah(old),'normalized_complete_AST_sha256':ah(normalized),'entire_original_AST_equal':True}
 return out
def verify_registry(registry,expected_head,immutable_business_files):
 exact(registry,{'schema','policy_sha256','source_head','source_export_report','source_root','production_root','production_manifest','business_manifest','changed_source_files','AST_projection','executing_reader_artifact','saved_faith_semantics_artifact'},'versioned migration registry')
 need(registry['schema']=='lyd.business-contract-migration-registry.v2' and registry['policy_sha256']==POLICY_SHA,'migration registry model differs')
 need(type(expected_head)is str and re.fullmatch('[0-9a-f]{40}',expected_head) and registry['source_head']==expected_head,'pending or different actual migration source HEAD')
 p,_=policy();need(expected_head not in (p['old_runtime_source_head'],p['old_contract_source_head']),'new migration cannot relabel old runtime/contract HEAD')
 export=jread(read_ref(registry['source_export_report']));need(export['source']['head']==expected_head and export['source_root']==registry['source_root'],'registry actual export source/head differs')
 bm=jread(read_ref(registry['business_manifest']));exact(bm,{'schema','source_head','files'},'actual business69 manifest')
 need(bm['schema']=='lyd.actual-business-manifest69.v2' and bm['source_head']==expected_head and bm['files']==immutable_business_files,'actual69 manifest/source differs')
 summary=verify_business_map(bm['files'])
 source_root=Path(registry['source_root']).resolve()/'mod_li_yu_dao';root=source_root.resolve()
 for rel,wanted in bm['files'].items():
  path=(root/rel).resolve();need(path.is_relative_to(root),'business path escaped export');need(reference(path)['sha256']==wanted,'actual exported business bytes differ '+rel)
 exact(registry['changed_source_files'],ALLOWED,'changed source descriptors')
 changed={rel:read_ref(desc) for rel,desc in registry['changed_source_files'].items()}
 for rel,desc in registry['changed_source_files'].items():need(Path(desc['path']).resolve()==(root/rel).resolve(),'changed source artifact outside actual export')
 ast_proof=verify_two_complete_AST(changed);need(registry['AST_projection']==ast_proof,'registry complete AST proof differs')
 pm=jread(read_ref(registry['production_manifest']));exact(pm,{'files','format_version','git_sha','mod_version','product_id'},'actual production70 manifest')
 need(pm['format_version']==1 and pm['git_sha']==expected_head and pm['product_id']=='mod_li_yu_dao' and type(pm['files'])is list and len(pm['files'])==70,'actual production70 source/product differs')
 records={}
 for row in pm['files']:
  exact(row,{'path','sha256','size'},'production file record');need(row['path'] not in records,'duplicate production record');records[row['path']]=row
 need(set(records)==set(bm['files'])|{'descriptor.mod'},'exact business69 plus descriptor required')
 prodroot=Path(registry['production_root']).resolve()
 for rel,row in records.items():
  wanted=p['descriptor']['sha256'] if rel=='descriptor.mod' else bm['files'][rel]
  need(row['sha256']==wanted and type(row['size'])is int and row['size']>0,'unreviewed production bytes '+rel)
  path=(prodroot/rel).resolve();need(path.is_relative_to(prodroot),'production path escaped');r=reference(path);need(r['bytes']==row['size'] and r['sha256']==row['sha256'],'actual production file differs '+rel)
 return summary|{'source_head':expected_head,'production_files':70,'AST_projection':ast_proof,'source_export_report':registry['source_export_report'],'production_manifest':registry['production_manifest'],'business_manifest':registry['business_manifest'],'actual_acceptance_credit':None}
