import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
controls={}
for pref in ['0065-','0066-','0067-','0069-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
    p=matches[0];d=read(p);ref=pin(p)
    if pref=='0065-' and not ref['sha256'].startswith('55d7158'):raise ValueError('Fresh65 SHA prefix mismatch')
    if pref=='0066-' and not ref['sha256'].startswith('b70885f'):raise ValueError('Send66 SHA prefix mismatch')
    if pref=='0067-' and ref['sha256']!='f7194fca9435093c05ccf6a499e03a565f3ca167fec87c9772555731e835341f':raise ValueError('Snapshot67 exact SHA mismatch')
    if pref=='0069-' and not ref['sha256'].startswith('0e092c9'):raise ValueError('Typed69 SHA prefix mismatch')
    c=d['structuredContent'];controls[pref]={'original_SDK':ref,'isError':d['isError'],'structured_content_exact':c}
    print(json.dumps({'prefix':pref,'ref':ref,'schema':c.get('schema'),'keys':list(c),'result_keys':list(c.get('result',{}))},ensure_ascii=False))
claimpath=controls['0066-']['structured_content_exact']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Actual third lineage mismatch')
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal2':claim['claim_ordinal']==2,'parent_ordinal1':parent['claim_ordinal']==1,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-909f50b85bf448b9b453a0121efc3835','differentUUID':claim['request_id']!=parent['request_id'],'before63_frame30_native29':claim['binding']['revision']==30 and claim['binding']['native_revision']==29,'lineage_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual third lineage identity mismatch')
out={'schema':'lyd.r10.third-open-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'agent_claim_or_permit_writes':False,'native_pending_or_claim_receipt_is_business_result':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'lineage_checks':checks},ensure_ascii=False))
