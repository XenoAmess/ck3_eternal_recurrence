from pathlib import Path
import hashlib,json,sys
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
O=B/'R0142-four-save-endpoint-audit-reinforcement-a02'
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return{'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,v):
 with(O/name).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ident(O/name)
def one(rows,key):
 values=[r['value']for r in rows if r['key']==key]
 assert len(values)<=1
 return values[0]if values else None
def named(rows,key):
 output=[]
 def walk(v,path):
  if not isinstance(v,list):return
  if any(r['key']in['name','flag']and isinstance(r['value'],str)and r['value'].strip('"')==key for r in v):output.append({'path':path,'complete_entry':v})
  for i,r in enumerate(v):walk(r['value'],path+'/'+str(r['key'])+'#'+str(i))
 walk(rows,'');return output
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 previous=O/'R0142-actual-endpoint-semantic-facts.json';result=read(previous)
 result['kind']='ACTUAL_R0142_SAVED_ENDPOINT_FACTS_A05'
 result['prior_derived_facts_preserved']=ident(previous)
 result['create_only_correction']='a04 signature_weapon_entries checked only name/unquoted key; actual save uses flag="signature_weapon". a05 reads original quoted flag/name and complete actual saved block. No native truth or originals changed.'
 states=[read(O/(row['label']+'-full-selected-saved-projection.json'))for row in result['saved_state_rows']]
 for s,row in zip(states,result['saved_state_rows']):
  for c,fields in zip(s['characters'],row['characters']):
   fields['signature_weapon_entries']=named(c['entries'],'signature_weapon')
   fields.pop('trait_XP_saved_block',None)
   fields['saved_trait_xp_amounts']=one(c['entries'],'trait_xp_amounts')
   fields['complete_saved_death_data']=one(c['entries'],'dead_data')
   fields['saved_death_artifact_field']=one(fields['complete_saved_death_data'],'artifact')if fields['complete_saved_death_data']is not None else None
   fields['saved_death_artifact_missing_not_actual_native_null']=fields['complete_saved_death_data']is not None and not any(r['key']=='artifact'for r in fields['complete_saved_death_data'])
 input_pairs=[]
 for l,r,title in[(0,1,'before_UI'),(1,2,'one_day'),(2,3,'after_UI')]:
  checks=[]
  for idx,cid in enumerate([33437,34120]):
   a,b=result['saved_state_rows'][l]['characters'][idx],result['saved_state_rows'][r]['characters'][idx]
   checks.append({'character_id':cid,'base6skills_equal':a['base_skills']==b['base_skills'],'traitkeys_equal':a['trait_keys']==b['trait_keys'],'saved_trait_xp_amounts_equal':a['saved_trait_xp_amounts']==b['saved_trait_xp_amounts'],'signature_variable_entries_equal':a['signature_weapon_entries']==b['signature_weapon_entries'],'saved_kills_before':a['saved_kills'],'saved_kills_after':b['saved_kills']})
  input_pairs.append({'interval':title,'saved_only_comparisons':checks})
 result['net_character_domain_checks']=input_pairs
 active=[]
 for row in result['saved_state_rows']:
  combat=next(v for v in row['saved_combat_endpoint']if v['path'].startswith('/combats['))
  active.append({'label':row['label'],'defender_army_order':combat['sides']['defender']['saved_army_order'],'defender_men_at_arms_regiment_order':combat['sides']['defender']['saved_men_at_arms_regiment_order'],'defender_regiment_row_count':len(combat['sides']['defender']['saved_men_at_arms_regiment_order']),'army18_and65_endpoint_only':True})
 result['saved_active_defender_regiment_endpoints']=active
 beforeUI,afterUI=result['actual_UI_knight_getter_outputs']
 result['original_UI_getter_set_difference']={side:{'before_order':beforeUI[side]['original_ONCLICK_CharacterID_order'],'after_order':afterUI[side]['original_ONCLICK_CharacterID_order'],'removed':[v for v in beforeUI[side]['original_ONCLICK_CharacterID_order']if v not in afterUI[side]['original_ONCLICK_CharacterID_order']],'added':[v for v in afterUI[side]['original_ONCLICK_CharacterID_order']if v not in beforeUI[side]['original_ONCLICK_CharacterID_order']]}for side in ['left','right']}
 assert result['original_UI_getter_set_difference']['left']['removed']==[33437]
 case_domains=read(B/'D26-13-domain-semantic-preparation-reinforcement-a01/case-closure-checklist.json')['domains']
 result['13_domain_case_verdicts']=[{'domain':d['domain'],'status':'pending','available_resolution':'endpoint + partial monitor originals only','remaining':d['required_actual_evidence'],'reason':'R0142 daily managed trace not published; independent monitor truncated. Endpoint values cannot replace actual operation tree/write/branch inventory.'}for d in case_domains]
 facts=write('R0142-actual-endpoint-semantic-facts-a05.json',result)
 items=[]
 for name in ['inspect_R0142_endpoints_a01.py','decode_R0142_four_endpoints_a01.py','decode_R0142_four_endpoints_a02.py','decode_R0142_four_endpoints_a03.py','repair_R0142_endpoint_script_a01.py','repair_R0142_endpoint_schema_a03.py','summarize_R0142_saved_facts_a04.py','finalize_R0142_endpoints_a05.py','R0142-four-save-decode-a01.stdout.bin','R0142-four-save-decode-a01.stderr.bin','R0142-four-save-decode-a02.stdout.bin','R0142-four-save-decode-a02.stderr.bin','R0142-four-save-decode-a03.stdout.bin','R0142-four-save-decode-a03.stderr.bin','R0142-saved-facts-a04.stdout.bin','R0142-saved-facts-a04.stderr.bin']:
  src=B/name;dst=O/'exact-copies'/name
  with dst.open('xb')as f:f.write(src.read_bytes())
  assert ident(dst)['sha256']==ident(src)['sha256']
  items.append({'original':ident(src),'exact_copy':ident(dst)})
 verification=read(O/'R0142-four-save-endpoint-verification.json')
 for row in verification['saved_states']:
  assert ident(row['immutable']['path'])==row['immutable']
 assets=[ident(p)for p in O.rglob('*')if p.is_file()]
 receipt=write('R0142-final-readonly-endpoint-receipt-a05.json',{'kind':'ACTUAL_R0142_FOUR_IMMUTABLE_SAVE_DECODER_ENDPOINT_RECEIPT','facts':facts,'verification':ident(O/'R0142-four-save-endpoint-verification.json'),'source_identity':'Runtime4ad and DLLC4C16 exact pin; parser copy runtime4ad; no sourcechange. Current mutable-tree evaluator not used.','four_original_saves':[s['immutable']for s in verification['saved_states']],'actual_commands':{'decode_a01':'syntax failure exit1 preserved','decode_a02':'schema mismatch army state -> correct army_state, exit2 preserved, no native failure claim','decode_a03':'actual4 Rakaly melt+projection exit0','semantic_a04':'exit0; narrower variable-name matcher corrected create-only in a05'},'process_and_code_exact_copies':items,'new_attempt_asset_index':assets,'global_bundle_complete':False,'case_13_domain_complete':False,'sole_death_cause_proven':False,'original_monitor_failed_flags8_truncated_true':True,'old_artifacts_unchanged':True,'no_CK3_or_native_request_or_Git_or_screen_or_video':True})
 print(json.dumps({'receipt':receipt,'facts':facts,'active_defender_regiments':active,'signature_summary':[{'label':r['label'],'weapon':r['characters'][1]['signature_weapon_entries']}for r in result['saved_state_rows']],'UI_delta':result['original_UI_getter_set_difference']},ensure_ascii=False))
if __name__=='__main__':main()
