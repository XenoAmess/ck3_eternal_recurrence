import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OLD=BASE/'r10-actual-eighth-precommit-readback-20261006-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0192-eighth-post-join-save';save=pin(cp/'checkpoint.ck3');assert save['bytes']==91604449 and save['sha256']=='9534d61d4f426ca8df0f4866695b7234f5ff477c296f084c1868a29424ae06d0'
sdk=pin(RUN/'mcp-client-evidence-002/0192-r10-0193-eighth-post-join-save.sdk-result.json');assert sdk['bytes']==8056003 and sdk['sha256']=='01d0423c11b77729082189df4a76c3ef4f2ab556238d0511c2a0a2582012863a'
metadata=pin(cp/'checkpoint-metadata.json');copies=[]
for src in [OLD/'reader/read_actual_checkpoint.py',*(OLD/'reader/dependencies').glob('*.py'),OLD/'inspect_new.py']:
    dst=HERE/src.relative_to(OLD);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f:f.write(src.read_bytes())
    copies.append({'source':pin(src),'copy':pin(dst),'exact_equal':src.read_bytes()==dst.read_bytes()})
req=json.loads((OLD/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-eighth-JOIN-final-confirm-and-ACK-post-business-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'exact_reader_copies':copies,'precommit187_sealed':pin(OLD/'SEALED.json'),'actual_new_AST_count_so_far':0,'old_save_reparsed':False,'business_credit_until_actual_readback':False})
print(json.dumps({'request':pin(HERE/'REQUEST.actual.json'),'save':save,'SDK':sdk},ensure_ascii=False,indent=2))
