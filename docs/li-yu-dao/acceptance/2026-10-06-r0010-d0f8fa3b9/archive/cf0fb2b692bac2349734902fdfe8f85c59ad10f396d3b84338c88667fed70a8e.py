import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010';PLAN_DIR=RUN/'root-serial-player-plans/eighth-player-options'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
planref=pin(PLAN_DIR/'PLAN.exact.json');resultref=pin(PLAN_DIR/'RESULT.json');result=read(resultref['path'])
if planref['sha256']!='c3c294d740e1532649a3388d646bda1c5f658cbc1fb60aee5bf6934def177b6b' or result['plan_sha256']!=planref['sha256']:raise ValueError('Exact player plan SHA mismatch')
records=[row for row in result['records'] if row['sequence']==172]
if len(records)!=1:raise ValueError('Need unique typed172 in actual RESULT')
typedrecord=records[0];controls={}
for pref in ['0169-','0170-','0172-']:
    if pref=='0172-':p=Path(typedrecord['sdk'])
    else:
        matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
        if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
        p=matches[0]
    d=read(p);ref=pin(p);c=d['structuredContent']
    if pref=='0169-' and (ref['bytes']!=7623 or ref['sha256']!='2af6ac611ba6f593cfefb69310b81c8f4660a78b2e5dc82f6e920d99b3980930'):raise ValueError('Fresh169 exact mismatch')
    if pref=='0170-' and ref['sha256']!='38252c3e782ed63afb33630a200c7565d7412652b3288199a4e0d0fe91ac4b96':raise ValueError('Initiate170 exact mismatch')
    if pref=='0172-' and (ref['sha256']!=typedrecord['sdk_sha256'] or not p.name.startswith('0172-')):raise ValueError('Typed172 exact RESULT ref mismatch')
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result'],'snapshot_excerpt':{k:c['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']} if 'snapshot' in c else None}
claimpath=controls['0170-']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Lineage exact SHA mismatch')
if permitref['sha256']!='abcaa729aca5bfcdee96ccc61c88d473bc4af5ef758394d11faa493f7fae0b06':raise ValueError('Root actual permit exact SHA mismatch')
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal7':claim['claim_ordinal']==7,'parent_ordinal6':parent['claim_ordinal']==6,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-cf364b502ddb47e58fb8ccbf5832a44f','differentUUID':claim['request_id']!=parent['request_id'],'before167_frame79_native78':claim['binding']['revision']==79 and claim['binding']['native_revision']==78,'lineage_parent_and_permit_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual eighth-lineage mismatch')
out={'schema':'lyd.r10.eighth-open-original-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'permit_root_supplied_sha':'abcaa729aca5bfcdee96ccc61c88d473bc4af5ef758394d11faa493f7fae0b06','permit_actual_sha_exactly_verified_against_claim_lineage':True,'root_player_plan':{'ref':planref,'exact_JSON':read(planref['path'])},'root_player_result':{'ref':resultref,'exact_JSON':result},'typed172_record_used':typedrecord,'other_five_callbacks_not_used_as_save171_business_result':True,'agent_native_or_claim_permit_operations':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'checks':checks,'controls':{k:{'original_SDK':v['original_SDK'],'snapshot':v['snapshot_excerpt']} for k,v in controls.items()}},ensure_ascii=False,indent=2))
