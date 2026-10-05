import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
inventory=read(RUN/'COLD-SOURCE-INVENTORY.json');production=inventory['enabled_mods'][0];root=Path(production['root'])
selected=['common/scripted_effects/lyd_c2_close_effects.txt','common/scripted_effects/lyd_c2_vote_effects.txt','common/scripted_effects/lyd_c2_commit_effects.txt','common/scripted_triggers/lyd_c2_consent_triggers.txt','common/script_values/lyd_c2_consent_values.txt','events/lyd_c2_consent_events.txt']
out={'schema':'lyd.r10.actual-negative-round-reason-source-evidence.v1','source_inventory':pin(RUN/'COLD-SOURCE-INVENTORY.json'),'source_files':{},'original_receipts':{},'source_only_excerpts':{}}
for rel in selected:
    p=root/rel;actual=pin(p);expected=next(f for f in production['files'] if f['relative_path']==rel)
    if actual['bytes']!=expected['bytes'] or actual['sha256']!=expected['sha256']:raise ValueError('Frozen source changed: '+rel)
    dest=HERE/'frozen-source'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(p.read_bytes())
    out['source_files'][rel]={'original':actual,'preserved':pin(dest),'cold_inventory_exact_match':True}
    lines=p.read_text(encoding='utf-8-sig').splitlines()
    tokens=['lyd_c2_reject_round_effect','lyd_c2_event_target_reject_effect','lyd_c2_event_holder_reject_effect','lyd_c2_event_head_reject_effect','lyd_c2_result value = 2','lyd_c2_retry_cooldown','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed','lyd.221','var:lyd_c2_result = 2','ai_chance = { base = 40 }','lyd_c2_source_quorum_value','lyd_c2_target_quorum_value']
    spans=set()
    for i,line in enumerate(lines):
        if any(token in line for token in tokens):spans.update(range(max(0,i-3),min(len(lines),i+6)))
    out['source_only_excerpts'][rel]=[{'line':i+1,'text':lines[i]} for i in sorted(spans)]
prefixes=['0020-r10-0020-player-consent-yes','0022-r10-0022-source-ballot-yes','0026-r10-0026-review-event-query','0027-r10-0027-source-sign','0028-r10-0028-sign-ack-query','0029-r10-0029-sign-ack-select']
for prefix in prefixes:
    p=RUN/'mcp-client-evidence-002'/f'{prefix}.sdk-result.json';d=read(p);r=d['structuredContent'];result=r['result']
    keep={k:v for k,v in result.items() if k not in ['current_event_window_context','saved_scopes','options','provenance','diagnostics','action_claim_path','source','binding']}
    if 'current_event_window_context' in result:
        c=result['current_event_window_context'];keep['current_event_window_context']={k:c.get(k) for k in ['status','snapshot_revision','date_raw','current_event_instance_id','event_definition_key','root_scope','options','readiness']}
    out['original_receipts'][prefix]={'ref':pin(p),'schema':r['schema'],'status':r['status'],'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'result_excerpt':keep}
out['interpretation_boundary']={'result2_mapping':'Rejected, sourced from frozen lyd.228 desc switch and reject_round effect','receiver_ballot_and_receiver_signature_are_separate':'Stored target vote_yes1 at serial/nonce7 does not imply target_signed','retry_cooldown_scope':'moving Rite169; actor cooldown lookup alone is insufficient','random_draw_or_actual_AI_option_trace_recorded':False,'exact_engine_random_cause':None,'final_JOIN_credit':False}
with (HERE/'REASON-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
for prefix,row in out['original_receipts'].items():
    x=row['result_excerpt'];c=x.get('current_event_window_context')
    print(prefix,json.dumps({'status':row['status'],'result_keys':list(x),'event':{k:c.get(k) for k in ['current_event_instance_id','event_definition_key','root_scope','options']} if c else None},ensure_ascii=False))
print('EVIDENCE',json.dumps(pin(HERE/'REASON-EVIDENCE.json'),ensure_ascii=False))
