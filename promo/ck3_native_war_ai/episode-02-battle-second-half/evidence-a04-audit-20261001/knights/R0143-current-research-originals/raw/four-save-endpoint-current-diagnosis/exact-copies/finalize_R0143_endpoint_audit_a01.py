"""Read-only R0143 four-save facts and original-pixel/native binding audit."""
from pathlib import Path
import hashlib,json,sys,collections
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
O=B/'R0143-four-save-endpoint-audit-reinforcement-a01'
ROOT=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-07-trace-diagnostic')
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
P=LIVE/'scoped-ui-research-attempt-01'
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(n,v):
 with(O/n).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ident(O/n)
def one(rows,key):
 v=[r['value']for r in rows if r['key']==key];assert len(v)<=1
 return v[0]if v else None
def copy(p,name):
 p=Path(p);before=ident(p);dst=O/'exact-copies'/name
 with p.open('rb')as i,dst.open('xb')as o:
  while b:=i.read(1048576):o.write(b)
 assert ident(p)==before and ident(dst)['sha256']==before['sha256']
 return {'original':before,'exact_copy':ident(dst)}
def checked(pin):
 now=ident(pin['path']);assert now['bytes']==pin['bytes']and now['sha256']==pin['sha256'].upper();return Path(pin['path'])
def main():
 sys.stdout.reconfigure(encoding='utf-8');config=read(ROOT/'current-run-bindings.json');confpin=ident(ROOT/'current-run-bindings.json')
 report=read(O/'R0143-actual-endpoint-semantic-facts.json');verification=read(O/'R0143-four-save-endpoint-verification.json')
 assert verification['status']=='PASS_ORIGINAL_FOUR_SAVE_BINDINGS_AND_ENDPOINT_PROJECTIONS_ONLY'
 states=[read(O/(row['label']+'-full-selected-saved-projection.json'))for row in report['saved_state_rows']]
 endpoint_checks=[]
 for l,r,title in [(0,1,'before_UI'),(1,2,'one_day'),(2,3,'after_UI')]:
  entries=[]
  for i,cid in enumerate([config['victim_id'],config['killer_id']]):
   a,b=report['saved_state_rows'][l]['characters'][i],report['saved_state_rows'][r]['characters'][i]
   entries.append({'character_id':cid,'base6skills_equal':a['base_skills']==b['base_skills'],'traitkeys_equal':a['trait_keys']==b['trait_keys'],'saved_trait_xp_amounts_equal':a['saved_trait_xp_amounts']==b['saved_trait_xp_amounts'],'signature_variable_entries_equal':a['signature_weapon_entries']==b['signature_weapon_entries'],'saved_kills_before':a['saved_kills'],'saved_kills_after':b['saved_kills']})
  endpoint_checks.append({'interval':title,'saved_only_comparisons':entries})
 report['net_character_domain_checks']=endpoint_checks
 active=[]
 for row in report['saved_state_rows']:
  combat=next(v for v in row['saved_combat_endpoint']if v['path'].startswith('/combats['))
  rs=combat['sides']['defender']['saved_men_at_arms_regiment_order']
  active.append({'label':row['label'],'defender_army_order':combat['sides']['defender']['saved_army_order'],'defender_men_at_arms_regiment_order':rs,'defender_regiment_row_count':len(rs),'saved_endpoints_only':True})
 report['saved_active_defender_regiment_endpoints']=active
 before,after=report['actual_UI_knight_getter_outputs']
 report['original_UI_getter_set_difference']={s:{'before_order':before[s]['original_ONCLICK_CharacterID_order'],'after_order':after[s]['original_ONCLICK_CharacterID_order'],'removed':[v for v in before[s]['original_ONCLICK_CharacterID_order']if v not in after[s]['original_ONCLICK_CharacterID_order']],'added':[v for v in after[s]['original_ONCLICK_CharacterID_order']if v not in before[s]['original_ONCLICK_CharacterID_order']]}for s in ['left','right']}
 copies=[];ui=[]
 for phase,date in [('before',config['before_date_raw']),('after',config['after_date_raw'])]:
  for suffix,subject in [('victim-character-original-ui-binding.json',config['victim_id']),('killer-character-original-ui-binding.json',config['killer_id']),('combat-original-ui-binding.json',config['combat_id']),('combat-fit-full-combat-panel-binding.json',config['combat_id'])]:
   path=P/(phase+'-'+suffix);v=read(path);assert v['source_binding']==confpin
   for field in ['source_values','query_values','post_pixels_values']:
    values=v[field];assert values['date_raw']==date and values['paused']is True and values['actor']==config['actor_id']and values['army_id']==config['public_unit_id']and values['army_state']=='combat'and values['bridge_pid']==config['native_session_binding']['bridge_pid']and values['episode_run_id']==config['native_session_binding']['episode_run_id']and values['connection_generation']==config['native_session_binding']['connection_generation']
   assert all(v['query_values'][k]==v['post_pixels_values'][k]for k in ['date_raw','paused','actor','revision','native_revision','army_id','army_state','bridge_pid','episode_run_id','connection_generation'])
   bodies=[]
   for receipt_key,body_key in [('readback','readback_body'),('post_pixels_readback','post_pixels_readback_body')]:
    response=read(checked(v[receipt_key]['response']));body=response['body'];assert body==v[body_key]and response['result']=='CALL_COMPLETED'
    assert body['accepted']is True and body['available']is True and body['effective_visible']is True and body['current_subject_id']==subject and body['date_raw']==date and body['paused']is True and body['played_character_id']==config['actor_id']and body['application_owner_thread_verified']is True and body['gui_owner_binding_verified']is True and body['rng_owner_is_ui_admission_gate']is False
    bodies.append(body)
   assert all(bodies[0][k]==bodies[1][k]for k in ['thread_id','gui_owner_address','gui_context_address','current_subject_id','native_revision'])
   image=checked(v['image']['image']);assert v['image']['pid']==config['native_session_binding']['bridge_pid']
   copies.append(copy(path,path.name));copies.append(copy(image,image.name))
   ui.append({'phase':phase,'subject_id':subject,'binding':ident(path),'image':ident(image),'PID':v['image']['pid'],'HWND':v['image']['hwnd'],'kind':v['image']['kind'],'date_raw':date,'paused':True,'query_revision':v['query_values']['revision'],'post_pixels_revision':v['post_pixels_values']['revision'],'GUI_actual_thread':bodies[0]['thread_id'],'GUI_context':bodies[0]['gui_context_address'],'GUI_owner':bodies[0]['gui_owner_address'],'samepaused_afterpixels_binding_verified':True,'visual_approval_by_this_auditor':False,'fullpanel_visual_claim_inferred':False})
  reviewpath=P/(phase+'-ui-root-review.json');review=read(reviewpath);assert review['source_binding']==confpin and review['original_pixels_actually_reviewed']is True
  assert review['source_values']['date_raw']==date and review['source_values']['paused']is True and review['source_values']['bridge_pid']==config['native_session_binding']['bridge_pid']
  for pin in review['reviewed_images']:
   image=checked(pin)
   if not(O/'exact-copies'/image.name).exists():copies.append(copy(image,image.name))
  checked(review['full_panel_original_image']);copies.append(copy(reviewpath,reviewpath.name))
  ui.append({'phase':phase,'original_root_review':ident(reviewpath),'reviewed_images':review['reviewed_images'],'original_root_actual_pixel_review_flag':review['original_pixels_actually_reviewed'],'observations':review['observations'],'movie_signoff':False,'this_report_does_not_create_new_UI_approval':True})
 report['actual_original_pixel_and_snapshot_bindings']=ui
 mon=read(O/'monitor-original-schema-inspection.json');assert mon['accepted']is False and mon['status']=='failed'and mon['failure_flags']==8 and mon['truncated']is True and mon['detours_uninstalled']is True
 report['actual_monitor_partial_only']=mon
 finished=read(P/'one-day-finished.json');assert finished['source_binding']==confpin and finished['day_postcondition_verified']is True and finished['trace_retry_or_extra_day']is False and finished['trace_finish_body']is None
 report['actual_daily_finish_publication_missing']={'original':ident(P/'one-day-finished.json'),'trace_error':finished['trace_error'],'trace_body':None,'strict_causal_or_selector_verifier':'NOT_RUN','day_postcondition_verified':finished['day_postcondition_verified']}
 domains_path=B/'D26-13-domain-semantic-preparation-reinforcement-a01/case-closure-checklist.json';domains=read(domains_path)['domains'];copies.append(copy(domains_path,'sourcebound-13-domain-requirements-prep-only.json'))
 report['13_domain_case_verdicts']=[{'domain':d['domain'],'status':'pending','available_resolution':'actual R0143 saved endpoints + partial failed monitor only','remaining':d['required_actual_evidence'],'reason':'Daily native managed trace export failed; operation/branch writer evidence not published. Equal endpoints are not branch-no-write evidence.'}for d in domains]
 report['kind']='ACTUAL_R0143_FOUR_SAVE_ENDPOINT_SEMANTIC_FACTS_A01';report['source_notice']='Runtime419cac1a956c7be356d886256c7bc689cda5327d and actual DLL0F752E3F50B778BE140CCE08589AFB88C9C08073D7EFDFFAD82C31330A51C42D; parser bytes are copied from that immutable source; later writable evaluator not used.'
 report['all_engine_RNG_unchanged']='UNKNOWN';report['no_prior_run_values_loaded']=True
 facts=write('R0143-actual-endpoint-semantic-facts-a01.json',report)
 names=['prepare_R0143_endpoint_audit_a01.py','run_R0143_audit_logged_a01.py','inspect_R0143_endpoints_a01.py','inspect_R0143_UI_binding_shapes_a01.py','inspect_R0143_UI_review_refs_a01.py','decode_R0143_four_endpoints_a01.py','summarize_R0143_saved_facts_a01.py','finalize_R0143_endpoint_audit_a01.py','R0143-endpoint-audit-reader-derivation-a01.json']
 for prefix in ['R0143-reader-prepare-a01','R0143-input-inspection-a01','R0143-four-save-decode-a01','R0143-UI-shapes-a01','R0143-UI-refs-a01','R0143-saved-facts-a01']:
  names += [prefix+s for s in ['-intent.json','-process.json','.stdout.bin','.stderr.bin']]
 for n in names:copies.append(copy(B/n,n))
 for row in verification['saved_states']:assert ident(row['immutable']['path'])==row['immutable']
 receipt=write('R0143-final-readonly-endpoint-receipt-a01.json',{'kind':'ACTUAL_R0143_FOUR_IMMUTABLE_SAVE_ENDPOINT_ONLY_RECEIPT','facts':facts,'verification':ident(O/'R0143-four-save-endpoint-verification.json'),'runtime_source_commit':config['source_commit'],'runtime_native_binding':config['native_session_binding'],'actual_four_save_decodes':'All four real Rakaly0.8.19 melt exit0; original checkpoint/native body/SHA/date/revision/PID separately verified','no_previous_run_raw_or_trace_used':True,'exact_source_process_and_UI_copies':copies,'four_original_saves':[v['immutable']for v in verification['saved_states']],'asset_index':[ident(p)for p in O.rglob('*')if p.is_file()],'global_bundle_complete':False,'case_13_domain_complete':False,'selector_closed':False,'case_actual_death_cause_closed':False,'strict_causal_or_monitor_verifier':'NOT_RUN','no_source_Git_CK3_screen_video_action':True})
 print(json.dumps({'facts':facts,'receipt':receipt,'actual_saved_characters':[{'label':r['label'],'chars':[{k:c[k]for k in ['character_id','status','death_date','death_reason','death_killer_id','regiment_id','base_skills','prestige_currency','prestige_accumulated','saved_kills','signature_weapon_entries']}for c in r['characters']]}for r in report['saved_state_rows']],'RNG':[r['saved_RNG']for r in report['three_window_endpoints']],'UI_delta':report['original_UI_getter_set_difference'],'saved_active_regiments':active},ensure_ascii=False))
if __name__=='__main__':main()
