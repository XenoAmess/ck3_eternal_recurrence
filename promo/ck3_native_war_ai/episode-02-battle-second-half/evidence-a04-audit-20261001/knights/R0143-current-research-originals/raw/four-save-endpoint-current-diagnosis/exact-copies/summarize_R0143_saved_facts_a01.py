"""Semantic saved endpoint summary, not scoped runtime causal closure."""
from pathlib import Path
import hashlib,json,sys,re,collections
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
OUT=B/'R0143-four-save-endpoint-audit-reinforcement-a01'
LABELS=['before-pre-ui-checkpoint','before','after-pre-ui-checkpoint','after']
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return{'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,value):
 with(OUT/name).open('x',encoding='utf-8',newline='\n')as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 return ident(OUT/name)
def one(ast,key):
 values=[r['value']for r in ast if r['key']==key]
 if len(values)>1:raise ValueError('Duplicate singleton '+key)
 return values[0]if values else None
def scalars(ast,key):
 v=one(ast,key)
 return [r['value']for r in v]if isinstance(v,list)else v
def named_variable_blocks(ast,key):
 found=[]
 def walk(v,path):
  if not isinstance(v,list):return
  if any(r['key']in['name','flag']and isinstance(r['value'],str)and r['value'].strip(chr(34))==key for r in v):found.append({'path':path,'complete_entry':v})
  for i,r in enumerate(v):walk(r['value'],path+'/'+str(r['key'])+'#'+str(i))
 walk(ast,'');return found
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 verified=read(OUT/'R0143-four-save-endpoint-verification.json')
 assert verified['status']=='PASS_ORIGINAL_FOUR_SAVE_BINDINGS_AND_ENDPOINT_PROJECTIONS_ONLY'
 states=[read(OUT/(label+'-full-selected-saved-projection.json'))for label in LABELS]
 char_rows=[]
 for s in states:
  chars=[]
  for c in s['characters']:
   alive=one(c['entries'],'alive_data');dead=one(c['entries'],'dead_data')
   fields={k:v for k,v in c.items()if k not in['entries','exact_extract']}
   fields['saved_kills']=scalars(alive if alive is not None else dead,'kills')
   fields['saved_trait_xp_amounts']=one(c['entries'],'trait_xp_amounts');fields['complete_saved_death_data']=dead;fields['saved_death_artifact_field']=one(dead,'artifact')if dead is not None else None;fields['saved_death_artifact_missing_not_actual_native_null']=dead is not None and not any(r['key']=='artifact'for r in dead)
   fields['trait_XP_original_field_candidates']=[r for r in c['entries']if any(k in str(r['key']).lower()for k in['xp','experience'])]
   fields['signature_weapon_entries']=named_variable_blocks(c['entries'],'signature_weapon')
   fields['complete_selected_character_extract']=c['exact_extract'];chars.append(fields)
  combat=[]
  for row in s['objects']['matched_combat_blocks']:
   entry={'path':row['path'],'sides':{}}
   for side in ['attacker','defender']:
    ast=one(row['entries'],side)
    if ast is None:continue
    maa=one(ast,'men_at_arms')
    rs=one(ast,'regiment_stats')
    entry['sides'][side]={'saved_army_order':scalars(ast,'armies'), 'saved_men_at_arms_regiment_order':[one(r['value'],'regiment')for r in maa]if maa is not None else None, 'saved_knight_stats_character_order':[one(r['value'],'knight')for r in rs if one(r['value'],'knight')not in[None,'4294967295','-1']]if rs is not None else None, 'complete_variables':one(ast,'variables'),'complete_character_casualty_rows':[r['value']for r in ast if r['key']=='character']}
   entry['saved_width']=one(row['entries'],'combat_width');entry['saved_base_width']=one(row['entries'],'base_combat_width')
   combat.append(entry)
  char_rows.append({'label':s['label'],'projection':ident(OUT/(s['label']+'-full-selected-saved-projection.json')),'date_raw':s['date_raw'],'characters':chars,'saved_combat_endpoint':combat,'saved_RNG_top_level':s['rng_top_level']})
 intervals=[]
 for title in ['before_UI_saved_endpoints','single_day_saved_endpoints','after_UI_saved_endpoints']:
  d=read(OUT/(title+'-complete-endpoint-deltas.json'))
  intervals.append({'interval':title,'full_endpoint_original':ident(OUT/(title+'-complete-endpoint-deltas.json')),'saved_RNG':d['saved_top_level_RNG_comparison'],'full_two_character_leaf_deltas':d['full_character_deltas'],'battle_ledger_slain_knight_entry_deltas':[{'path':r['path'],'selected_leaf_deltas':[x for x in r['all_scalar_leaf_deltas']if any(k in x['path']for k in['battle_event','slain','variables','knight','regiment','current','casualties'])]}for r in d['full_case_combat_deltas']], 'house_DB_change_count':len(d['full_house_DB_deltas']),'all_accolade_saved_deltas':d['accolade_section_deltas']})
 rawUI=[]
 live=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
 for label,expected_date in [('before',53146848),('after',53146872)]:
  p=live/'ck3-output/interactive-requests-responses'/(label+'-root-review-combat-readonly.json');wrapper=read(p);body=wrapper['body']
  assert wrapper['result']=='CALL_COMPLETED'and body['accepted']is True and body['status']=='observed'and body['current_subject_id']==16777218 and body['date_raw']==expected_date and body['played_character_id']==29829 and body['paused']is True
  assert body['combat_knights_read_available']is True
  entry={'label':label,'original':ident(p),'date_raw':body['date_raw'],'native_revision':body['native_revision'],'GUI_original_thread':body['thread_id'],'scope':'original_native_UI_GetLeft/RightKnightBreakdown_output_not_pixels_or_full_regiment_roster','UI_roster_full_ids_flag':body['combat_roster_full_ids_available']}
  for side in ['left','right']:
   markup=body[side+'_knight_breakdown'];count=body[side+'_knight_count'];onclick=re.findall(r'ONCLICK:CHARACTER,(\d+)',markup)
   assert type(count)is int and isinstance(markup,str)and len(onclick)==count
   entry[side]={'native_UI_count':count,'original_ONCLICK_CharacterID_order':[int(v)for v in onclick],'original_markup':markup}
  rawUI.append(entry)
 result={'kind':'ACTUAL_R0143_SAVED_ENDPOINT_FACTS_AND_ORIGINAL_NATIVE_UI_GETTER_OUTPUT','four_save_verification':ident(OUT/'R0143-four-save-endpoint-verification.json'),'saved_state_rows':char_rows,'three_window_endpoints':intervals,'actual_UI_knight_getter_outputs':rawUI,'source_notice':'Runtime419cac / actual R0143 DLL0F752E3F... and exact parser source stored in endpoint verification. No writable evaluator or previousrun raw used.','death_tuple_resolution':'Saved death date/reason/killer/artifact endpoint only; native request/queue/commit tuple unavailable.','native_monitor_status':'failed/acceptedfalse/flags8/truncated128; partial house/getter rows retained, no complete monitor inference.','case_13_domain_complete':False,'global_bundle_complete':False,'selector_closed':False,'case_actual_death_cause_closed':False,'six_gap_verdict':'This endpoint report does not replace separate current original-pixel UI reviews. Mechanism3 remain pending.', 'all_engine_RNG_unchanged':'UNKNOWN','semantic_limits':['No original scoped operation-before/after tree is available for branch-no-write or per-operation accounting.','No native source numericID bound by cached history; saved combat order and native UI markup order are separately reported.','Original native UI markup is freshgetter output, not a pixel approval or fullregiment roster proof.','Equal saved endpoint fields do not prove unchanged intraday state.']}
 receipt=write('R0143-actual-endpoint-semantic-facts.json',result)
 print(json.dumps({'receipt':receipt,'saved_char_summaries':[{ 'label':r['label'],'chars':[{k:c[k]for k in['character_id','status','death_date','death_reason','death_killer_id','base_skills','prestige_currency','prestige_accumulated','regiment_id']}for c in r['characters']]}for r in char_rows],'RNG':[{'interval':r['interval'],'RNG':r['saved_RNG']}for r in intervals],'UIcounts':[{'label':r['label'],'left':r['left']['native_UI_count'],'right':r['right']['native_UI_count']}for r in rawUI]},ensure_ascii=False))
if __name__=='__main__':main()
