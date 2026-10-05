import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
control=read(HERE/'CONTROL-EVIDENCE.json');claim=control['receipts']['0042-']['original_action_claim']['exact_JSON'];lineage=claim['new_intent_lineage']
permitref=pin(lineage['permit_path']);parentref=pin(lineage['parent_claim_path'])
if permitref['sha256']!=lineage['permit_sha256'] or parentref['sha256']!=lineage['parent_claim_sha256']:raise ValueError('Actual new-intent lineage SHA mismatch')
permit=read(permitref['path']);parent=read(parentref['path'])
checks={'new_claim_ordinal1':claim['claim_ordinal']==1,'same_six_part_action_identity':parent['action_identity']==claim['action_identity'],'new_action_UUID':claim['request_id']=='ordinary-interaction-a50373f260354f6f83c8052eaf837c7f','different_action_UUID':claim['request_id']!=parent['request_id'],'permit_exact_SHA':permitref['sha256']==lineage['permit_sha256'],'parent_exact_SHA':parentref['sha256']==lineage['parent_claim_sha256'],'same_PID_actor_date_before39_binding':claim['binding']['game_pid']==13436 and claim['binding']['played_character_id']==31254 and claim['binding']['date_raw']==53144712 and claim['binding']['revision']==18 and claim['binding']['native_revision']==17}
if not all(checks.values()):raise ValueError('Actual lifecycle identity check failed')
d={'schema':'lyd.r10.second-proposal-new-intent-lineage-observation.v1','current_claim':control['receipts']['0042-']['original_action_claim'],'parent_claim':{'ref':parentref,'exact_JSON':parent},'permit':{'ref':permitref,'exact_JSON':permit},'checks':checks,'first_claim_preserved':True,'claim_status_only_not_business_credit':claim['status'],'agent_created_or_released_claims':False,'game_native_MCP_pipe_bus_operations':False}
with (HERE/'LINEAGE-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'ref':pin(HERE/'LINEAGE-EVIDENCE.json'),'checks':checks,'parent_claim_ordinal':parent.get('claim_ordinal'),'permit_schema':permit.get('schema')},ensure_ascii=False,indent=2))
