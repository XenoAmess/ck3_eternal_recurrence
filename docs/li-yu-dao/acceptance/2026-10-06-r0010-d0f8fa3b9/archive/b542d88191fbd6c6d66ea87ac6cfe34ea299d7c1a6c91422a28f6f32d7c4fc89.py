import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
controls={}
for pref in ['0196-','0197-','0198-','0199-']:
    ps=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'));assert len(ps)==1;p=ps[0];d=read(p);c=d.get('structuredContent');row={'original_SDK':pin(p),'isError':d.get('isError'),'resultType':d.get('resultType'),'top_keys':list(d)}
    if c is not None:
        row['structuredContent_keys']=list(c);row.update({k:c.get(k) for k in ['schema','status','session_id','profile_sha256','result']})
        if 'snapshot_after' in c:row['snapshot_after_frame']={k:c['snapshot_after'].get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
    else:row['exact_content_without_structured_result']=d.get('content')
    q=p.with_name(p.name.replace('.sdk-result.json','.request.json'))
    if q.exists():row['original_request']={'ref':pin(q),'exact_JSON':read(q)}
    controls[pref]=row
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.explicit-cycle-reset-original-controls.v1','receipts':controls,'ROOT_reported196_original_RED_preserved_not_reissued':True,'fixture_not_natural_expiry':True,'agent_live_operations':False},f,ensure_ascii=False,indent=2);f.write('\n')
small={}
for k,c in controls.items():
    r=c.get('result') or {};e=r.get('current_event_window_context');small[k]={'ref':c['original_SDK'],'isError':c['isError'],'status':c.get('status'),'top_keys':c['top_keys'],'structured_keys':c.get('structuredContent_keys'),'result_keys':list(r),'frame':c.get('snapshot_after_frame'),'selection':{n:r.get(n) for n in ['event_instance_id','option_index','option_number','accepted','status']},'event':None if e is None else {'id':e.get('current_event_instance_id'),'key':e.get('event_definition_key'),'root':e.get('root_scope'),'options':e.get('options')},'exact_content_if_error_without_structured':c.get('exact_content_without_structured_result')}
print(json.dumps(small,ensure_ascii=False,indent=2))
