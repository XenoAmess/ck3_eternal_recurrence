import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
cs=read(HERE/'CONTROL-EVIDENCE.json')['receipts'];p=cs['0196-']['original_SDK']['path'];c=read(p)['structuredContent'];after=read(HERE/'actual-save-001/STATE.json');before=read(BASE/'r10-actual-eighth-post-join-readback-20261006-001/actual-save-001/STATE.json');av=after['all_actor_LYD_variables'];bv=before['all_actor_LYD_variables']
changes={k:{'before':bv.get(k),'after':av.get(k)} for k in sorted(set(bv)|set(av)) if bv.get(k)!=av.get(k)}
reason={'schema':'lyd.r10.cycle-reset196-original-RED-boundary.v1','original_SDK':cs['0196-']['original_SDK'],'original_request':cs['0196-'].get('original_request'),'status_exact':c.get('status'),'reason_exact':c.get('reason'),'original_receipt_path':c.get('receipt_path'),'original_receipt_ref':pin(c['receipt_path']) if c.get('receipt_path') and Path(c['receipt_path']).exists() else None,'196_not_reissued':True,'ROOT_reported_wrong_expected_decision_closed':True,'actual_execution_not_inferred_from_ACK_alone':'Independent197 snapshot/198 typed fixture4/199ACK/200save AST are retained separately','200_changed_actor_LYD_rows':changes,'school_study_CD':after['summary']['cooldown']}
snap=read(cs['0197-']['original_SDK']['path'])['structuredContent'];fr=snap.get('snapshot') or snap.get('observation_after');reason['independent197_snapshot_frame']={k:fr.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
with (HERE/'ORIGINAL-RESET-RED-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(reason,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(reason,ensure_ascii=False,indent=2))
