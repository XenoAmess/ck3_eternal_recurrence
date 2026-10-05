import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
out={'schema':'lyd.r10.second-proposal-original-control-evidence.v1','receipts':{}}
for prefix in ['0041-','0042-','0044-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(prefix+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual SDK '+prefix+str(matches))
    p=matches[0];d=read(p);r=d['structuredContent'];actual=pin(p)
    if prefix=='0041-' and actual['sha256']!='25f1988bddbaa71ea475df2abdd8fd278218b70c536a08e474cd3f737e8a6496':raise ValueError('Fresh41 actual SDK SHA mismatch')
    result=r['result'];out['receipts'][prefix]={'original_SDK':actual,'receipt_schema':r['schema'],'status':r['status'],'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'isError':d['isError'],'result':result}
    claim=result.get('action_claim_path')
    if claim:out['receipts'][prefix]['original_action_claim']={'ref':pin(claim),'exact_JSON':read(claim)}
    if p.with_name(p.name.replace('.sdk-result.json','.request.json')).exists():out['receipts'][prefix]['original_request']=pin(p.with_name(p.name.replace('.sdk-result.json','.request.json')))
    print(json.dumps({'prefix':prefix,'path':str(p),'status':r['status'],'result_keys':list(result),'action_request_id':result.get('action_request_id'),'action_claim_path':claim,'query_native_revision':result.get('queried_native_revision'),'query_public_revision':result.get('queried_revision'),'event':{k:result.get('current_event_window_context',{}).get(k) for k in ['current_event_instance_id','event_definition_key','root_scope']}},ensure_ascii=False))
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(pin(HERE/'CONTROL-EVIDENCE.json'),ensure_ascii=False))
