import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
expected={'0145-':'5d8ba33c2db114aa6dd786f8fd8179c5cc0a56804252254d577a0fb2d8f30bbe','0146-':'f6329772afbe437c17b222b392ebc39a73455f3528d0f18a6172f2526c038189','0147-':'750c399c25872ac0b724aedd7c7b5bdca21baa41be3d6d8ffc232b89ee928c26','0148-':'c8ff563db0ec21d6f5ac0f8c8b3534d76ade85969f40e354b8401dafab975694','0150-':'27fff1d1a7533e83d39b72684a33f43a637c1dbb56110f0d9fe1c8cbfb8534ee'};controls={}
for pref,sha in expected.items():
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
    p=matches[0];d=read(p);ref=pin(p);c=d['structuredContent']
    if ref['sha256']!=sha:raise ValueError('Exact actual SDK mismatch '+pref)
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result']}
    if 'snapshot_after' in c:
        f=c['snapshot_after'];controls[pref]['snapshot_after_frame']={k:f.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
    if pref in ['0146-','0148-']:
        q=p.with_name(p.name.replace('.sdk-result.json','.request.json'));controls[pref]['original_request']={'ref':pin(q),'exact_JSON':read(q)}
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.sixth-explicit-cancel-original-controls.v1','receipts':controls,'agent_MCP_calls_or_game_operations':False,'fresh150_query_does_not_prove_new_initiation_or_host_release':True},f,ensure_ascii=False,indent=2);f.write('\n')
small={}
for k,v in controls.items():
    r=v['result'];ev=r.get('current_event_window_context');q=r.get('character_interaction_ordinary_context');small[k]={'ref':v['original_SDK'],'frame':v.get('snapshot_after_frame'),'selection':{name:r.get(name) for name in ['event_instance_id','option_index','option_number']},'typed_event':None if ev is None else {'id':ev['current_event_instance_id'],'key':ev['event_definition_key'],'root':ev['root_scope'],'options':[{'native':o['native_option_index'],'name':o['resolved_name']} for o in ev['options']]},'ordinary_context':None if q is None else {'pub':r['queried_revision'],'native':r['queried_native_revision'],'ready':q['ready_to_initiate'],'can_send':q['can_send'],'actor':q['player_character_id'],'recipient':q['recipient_id'],'actor_alive':q['actor_alive'],'key':q['interaction_key']}}
print(json.dumps({'controls':small,'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json')},ensure_ascii=False,indent=2))
