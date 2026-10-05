import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
expected={'0189-':'b057797a256ff624bca696a971d7dfbcb59c335cb6b88586cddc45864befa0bf','0190-':'3922ec62eda2bc9656b32cad4301e14fae5a8f4c10561778d3d06c2e3b837bbe','0191-':'a5bd21654f491b9b0a501a5a9bc22b8e7eaf8d0c3f754eddd2c6ffa55f93a25a','0193-':'bdfc31c44eed5b329106d3651d64f9491c233318a7be19f423f800b796e81193'};cs={}
for pref,sha in expected.items():
    ps=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'));assert len(ps)==1;p=ps[0];ref=pin(p);assert ref['sha256']==sha,(pref,ref)
    d=read(p);c=d['structuredContent'];cs[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'isError':d['isError'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'result':c['result']}
    if 'snapshot_after' in c:
        f=c['snapshot_after'];cs[pref]['snapshot_after_frame']={k:f.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']};cs[pref]['snapshot_after_wallet_actor']=f['played_character']
    p_req=p.with_name(p.name.replace('.sdk-result.json','.request.json'))
    if p_req.exists():cs[pref]['original_request']={'ref':pin(p_req),'exact_JSON':read(p_req)}
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.eighth-final-confirm-and-ACK-original-controls.v1','receipts':cs,'agent_game_operations':False,'ordinary193_query_only_row_availability_not_detach_eligibility_proof':True},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'controls':{k:{'ref':c['original_SDK'],'snapshot_frame':c.get('snapshot_after_frame'),'selection':{n:c['result'].get(n) for n in ['event_instance_id','option_index','option_number','event_selection']},'event':None if c['result'].get('current_event_window_context') is None else {n:c['result']['current_event_window_context'].get(n) for n in ['current_event_instance_id','event_definition_key','options']},'query':c['result'].get('character_interaction_ordinary_context')} for k,c in cs.items()}},ensure_ascii=False,indent=2))
