import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010';PLAN_DIR=RUN/'root-serial-player-plans/seventh-player-options'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
planref=pin(PLAN_DIR/'PLAN.exact.json');resultref=pin(PLAN_DIR/'RESULT.json');result=read(resultref['path'])
if planref['sha256']!='2f10fcafa46b99d6fab71adeb4a5ad8b1ae3571c50c89ff745465c75c5977604' or result['plan_sha256']!=planref['sha256']:raise ValueError('Exact player plan SHA mismatch')
records=[row for row in result['records'] if row['sequence']==154]
if len(records)!=1:raise ValueError('Need unique typed154 in actual RESULT')
typedrecord=records[0];controls={}
for pref in ['0151-','0152-','0154-']:
    if pref=='0154-':p=Path(typedrecord['sdk'])
    else:
        matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
        if len(matches)!=1:raise ValueError('Need unique actual SDK '+pref)
        p=matches[0]
    d=read(p);ref=pin(p);c=d['structuredContent']
    if pref=='0151-' and (ref['bytes']!=7623 or ref['sha256']!='21721efc900d1b41b2c01664daeb5b0c9d1e6771f581c01a159704193b1ea40c'):raise ValueError('Fresh151 exact mismatch')
    if pref=='0152-' and ref['sha256']!='4d8956229d7f369a1884e0c6a9bdbe92c44522a80741d861f62418b67f630c71':raise ValueError('Initiate152 exact mismatch')
    if pref=='0154-' and (ref['sha256']!=typedrecord['sdk_sha256'] or not p.name.startswith('0154-')):raise ValueError('Typed154 exact RESULT ref mismatch')
    controls[pref]={'original_SDK':ref,'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result'],'snapshot_excerpt':{k:c['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']} if 'snapshot' in c else None}
claimpath=controls['0152-']['result']['action_claim_path'];claimref=pin(claimpath);claim=read(claimpath);lineage=claim['new_intent_lineage'];parentref=pin(lineage['parent_claim_path']);permitref=pin(lineage['permit_path'])
if parentref['sha256']!=lineage['parent_claim_sha256'] or permitref['sha256']!=lineage['permit_sha256']:raise ValueError('Lineage exact SHA mismatch')
# This task did not supply a separate permit SHA; actual parent/permit bytes are still exactly verified against the current claim lineage above.
parent=read(parentref['path']);permit=read(permitref['path'])
checks={'ordinal6':claim['claim_ordinal']==6,'parent_ordinal5':parent['claim_ordinal']==5,'same_six_identity':claim['action_identity']==parent['action_identity'],'newUUID':claim['request_id']=='ordinary-interaction-ce6f9c27e43f4d1c9057fb7746fcb815','differentUUID':claim['request_id']!=parent['request_id'],'before149_frame70_native69':claim['binding']['revision']==70 and claim['binding']['native_revision']==69,'lineage_parent_and_permit_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'] and permitref['sha256']==lineage['permit_sha256']}
if not all(checks.values()):raise ValueError('Actual seventh-lineage mismatch')
out={'schema':'lyd.r10.seventh-open-original-control-lineage-evidence.v1','controls':controls,'current_claim':{'ref':claimref,'exact_JSON':claim},'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'lineage_checks':checks,'permit_root_supplied_sha':None,'permit_actual_sha_exactly_verified_against_claim_lineage':True,'root_player_plan':{'ref':planref,'exact_JSON':read(planref['path'])},'root_player_result':{'ref':resultref,'exact_JSON':result},'typed154_record_used':typedrecord,'other_five_callbacks_not_used_as_save153_business_result':True,'agent_native_or_claim_permit_operations':False}
with (HERE/'CONTROL-LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'checks':checks,'controls':{k:{'original_SDK':v['original_SDK'],'snapshot':v['snapshot_excerpt']} for k,v in controls.items()}},ensure_ascii=False,indent=2))
