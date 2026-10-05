import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OLD=BASE/'r10-actual-eighth-open-join-readback-20261006-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0187-eighth-precommit-save';save=pin(cp/'checkpoint.ck3')
assert save['bytes']==91540737 and save['sha256']=='5b3af804aa4d713e5115ba34f08bf16defdc5705900835e49f378e9abaa17415'
sdk=pin(RUN/'mcp-client-evidence-002/0187-r10-0188-eighth-precommit-save.sdk-result.json')
assert sdk['bytes']==7887659 and sdk['sha256']=='278e3ff2ab758a8b94dadf4a5b15a471fdf729845cfc4b774ff970479fe98e1c'
metadata=pin(cp/'checkpoint-metadata.json');copies=[]
for src in [OLD/'reader/read_actual_checkpoint.py',*(OLD/'reader/dependencies').glob('*.py'),OLD/'inspect_new.py']:
    dst=HERE/(src.relative_to(OLD));dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f:f.write(src.read_bytes())
    copies.append({'source':pin(src),'copy':pin(dst),'exact_bytes_equal':src.read_bytes()==dst.read_bytes()})
req=json.loads((OLD/'REQUEST.actual.json').read_text(encoding='utf-8'))
req.update({'phase':'actual-R10-eighth-JOIN-precommit-authorization-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'SDK':sdk,'metadata':metadata,'tool_exact_copies':copies,'cached_before171':pin(OLD/'actual-save-001/STATE.json'),'cached_baseline167':pin(BASE/'r10-actual-seventh-post-cancel-readback-20261006-001/actual-save-001/STATE.json'),'source171_target_ballot_qualification':pin(OLD/'TARGET-RITE-BALLOT-QUALIFICATION.json'),'actual_new_AST_count_so_far':0,'old_save_reparsed':False,'final_JOIN_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
