import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
controls={}
for pref in ['0109-','0110-','0112-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
    p=matches[0];d=read(p);ref=pin(p);c=d['structuredContent']
    if pref=='0109-' and ref['sha256']!='929e9d361ac0c3903fb1822248cf50b5d1a3a13d80d3c901310bc6422e29e62d':raise ValueError('Fresh109 exact mismatch')
    if pref=='0112-' and ref['sha256']!='f8798c7497f5f364ad9cf84e6ec7d39c56122e3fbcb41d34e04ab3f0d72e37cd':raise ValueError('Typed112 exact mismatch')
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result'],'snapshot_excerpt':{k:c['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']} if 'snapshot' in c else None}
claimpath=controls['0110-']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Lineage exact SHA mismatch')
if permitref['sha256']!='a2c0a17d6347ccf7fb6178eb92339f7f2811ccdc691b56bca5c69b08e31a76bd':raise ValueError('Root permit exact SHA mismatch')
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal4':claim['claim_ordinal']==4,'parent_ordinal3':parent['claim_ordinal']==3,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-9e0a5f40b68f4b6c826dbdcd422f2dd0','differentUUID':claim['request_id']!=parent['request_id'],'before107_frame50_native49':claim['binding']['revision']==50 and claim['binding']['native_revision']==49,'lineage_parent_and_permit_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual fifth-lineage mismatch')
out={'schema':'lyd.r10.fifth-open-original-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'agent_native_or_claim_permit_operations':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'checks':checks,'controls':{k:{'original_SDK':v['original_SDK'],'snapshot':v['snapshot_excerpt']} for k,v in controls.items()}},ensure_ascii=False,indent=2))
