import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010';PLAN_DIR=RUN/'root-serial-player-plans/sixth-player-options'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
planref=pin(PLAN_DIR/'PLAN.exact.json');resultref=pin(PLAN_DIR/'RESULT.json');result=read(resultref['path'])
if planref['sha256']!='641f9529bca4d53f5ebf0fb584075109b85edc0f3b23b33c255ed329f418275b' or result['plan_sha256']!=planref['sha256']:raise ValueError('Exact player plan SHA mismatch')
records=[row for row in result['records'] if row['sequence']==130]
if len(records)!=1:raise ValueError('Need unique typed130 in actual RESULT')
typedrecord=records[0];controls={}
for pref in ['0127-','0128-','0130-']:
    if pref=='0130-':p=Path(typedrecord['sdk'])
    else:
        matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
        if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
        p=matches[0]
    d=read(p);ref=pin(p);c=d['structuredContent']
    if pref=='0127-' and (ref['bytes']!=7623 or ref['sha256']!='b233c9ed3ece500c5bc68357de621fea8b6c37ba72142dc3ffb302f4bcf940f6'):raise ValueError('Fresh127 exact mismatch')
    if pref=='0128-' and ref['sha256']!='63f1313773e6f6187531a7ea58a891483fad8a478043e3371e30aaa1631f1f05':raise ValueError('Initiate128 exact mismatch')
    if pref=='0130-' and (ref['sha256']!=typedrecord['sdk_sha256'] or not p.name.startswith('0130-')):raise ValueError('Typed130 exact RESULT ref mismatch')
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result'],'snapshot_excerpt':{k:c['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']} if 'snapshot' in c else None}
claimpath=controls['0128-']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Lineage exact SHA mismatch')
if permitref['sha256']!='350483fb0032e95b83d99e2321e02186f44d3190c2d2e206490517d88295485a':raise ValueError('Root permit exact SHA mismatch')
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal5':claim['claim_ordinal']==5,'parent_ordinal4':parent['claim_ordinal']==4,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-1d9cf9c7db6e4ea2be6872d6427cf2a4','differentUUID':claim['request_id']!=parent['request_id'],'before125_frame59_native58':claim['binding']['revision']==59 and claim['binding']['native_revision']==58,'lineage_parent_and_permit_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual sixth-lineage mismatch')
out={'schema':'lyd.r10.sixth-open-original-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'root_player_plan':{'ref':planref,'exact_JSON':read(planref['path'])},'root_player_result':{'ref':resultref,'exact_JSON':result},'typed130_record_used':typedrecord,'other_five_callbacks_not_used_as_save129_business_result':True,'agent_native_or_claim_permit_operations':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'checks':checks,'controls':{k:{'original_SDK':v['original_SDK'],'snapshot':v['snapshot_excerpt']} for k,v in controls.items()}},ensure_ascii=False,indent=2))
