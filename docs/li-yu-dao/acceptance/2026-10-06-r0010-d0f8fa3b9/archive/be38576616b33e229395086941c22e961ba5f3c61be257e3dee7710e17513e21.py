import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
controls={}
for pref in ['0086-','0087-','0089-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
    p=matches[0];d=read(p);ref=pin(p);c=d['structuredContent']
    if pref=='0086-' and (ref['bytes']!=7623 or ref['sha256']!='87e2fdfb02e76bea3755285e6cf4bfcd7ec0588d5652e92bf83e548949e8de20'):raise ValueError('Fresh86 exact mismatch')
    if pref=='0087-' and not ref['sha256'].startswith('b423'):raise ValueError('Init87 SHA prefix mismatch')
    if pref=='0089-' and not ref['sha256'].startswith('4fa11a'):raise ValueError('Typed89 SHA prefix mismatch')
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result'],'snapshot_excerpt':{k:c['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']} if 'snapshot' in c else None}
    print(json.dumps({'prefix':pref,'ref':ref,'status':c['status'],'result_keys':list(c['result']),'snapshot':controls[pref]['snapshot_excerpt']},ensure_ascii=False))
claimpath=controls['0087-']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Lineage exact SHA mismatch')
if not permitref['sha256'].startswith('3807'):raise ValueError('Root permit SHA prefix mismatch')
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal3':claim['claim_ordinal']==3,'parent_ordinal2':parent['claim_ordinal']==2,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-76a5607e59804b76ad5dbe3f98fc126c','differentUUID':claim['request_id']!=parent['request_id'],'before82_frame39_native38':claim['binding']['revision']==39 and claim['binding']['native_revision']==38,'lineage_parent_and_permit_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual fourth-lineage mismatch')
out={'schema':'lyd.r10.fourth-open-original-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'agent_native_or_claim_permit_operations':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'checks':checks},ensure_ascii=False))
