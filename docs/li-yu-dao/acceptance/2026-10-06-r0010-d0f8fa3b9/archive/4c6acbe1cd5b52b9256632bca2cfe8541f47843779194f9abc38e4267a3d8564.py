import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OLD=BASE/'r10-actual-eighth-post-join-readback-20261006-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0200-cycle-before-detach-save';save=pin(cp/'checkpoint.ck3');assert save['bytes']==91604322 and save['sha256']=='9c8a8ed09a096f540cf64bee63ee9fd16b31c57923e9fea3e35b806cdb75c610'
sdk=pin(RUN/'mcp-client-evidence-002/0200-r10-0201-cycle-before-detach-save.sdk-result.json');assert sdk['bytes']==8199031 and sdk['sha256']=='1ff1f902b8ca070243449a74b77e61baa3c1c596dc6a463bbd7053a114b1bddb'
metadata=pin(cp/'checkpoint-metadata.json');copies=[]
for src in [OLD/'reader/read_actual_checkpoint.py',*(OLD/'reader/dependencies').glob('*.py'),OLD/'inspect_new.py']:
    dst=HERE/src.relative_to(OLD);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f:f.write(src.read_bytes())
    copies.append({'source':pin(src),'copy':pin(dst),'exact_equal':src.read_bytes()==dst.read_bytes()})
req=json.loads((OLD/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-cycle-before-DETACH-explicit-fixture-reset-not-natural-expiry-or-DETACH','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req);write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'exact_reader_copies':copies,'cached_postJOIN192_SEALED':pin(OLD/'SEALED.json'),'actual_new_AST_count_so_far':0,'old_save_reparsed':False,'DETACH_credit':False,'natural_expiry_credit':False})
print(json.dumps({'request':pin(HERE/'REQUEST.actual.json'),'save':save,'SDK':sdk},ensure_ascii=False,indent=2))
