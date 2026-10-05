import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OLD=BASE/'r10-actual-cycle-before-detach-readback-20261006-001'
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0235-detach-second-precommit-save';save=pin(cp/'checkpoint.ck3');assert save['bytes']==91605363 and save['sha256']=='83bd02e2f340f6f1aa70525a08aa004e6b2dce2326ac2568ea99b0b79183983d'
sdk=pin(RUN/'mcp-client-evidence-002/0235-r10-0236-detach-second-precommit-save.sdk-result.json');assert sdk['bytes']==10093591 and sdk['sha256']=='16462dddb6e1e4f51f3a0fe0bb102ea9b332f32e61a5d4dbe1acf26ef0de3d3d'
metadata=pin(cp/'checkpoint-metadata.json');copies=[]
for src in [OLD/'reader/read_actual_checkpoint.py',*(OLD/'reader/dependencies').glob('*.py'),OLD/'inspect_new.py']:
    dst=HERE/src.relative_to(OLD);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f:f.write(src.read_bytes())
    copies.append({'source':pin(src),'copy':pin(dst),'exact_equal':src.read_bytes()==dst.read_bytes()})
req=json.loads((OLD/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-second-DETACH-precommit-authorization-after-first-withdrawal-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')});write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'SDK':sdk,'metadata':metadata,'exact_reader_copies':copies,'cached_before200_SEALED':pin(OLD/'SEALED.json'),'actual_new_AST_count_so_far':0,'old_save_reparsed':False,'final_DETACH_credit':False})
print(json.dumps({'request':pin(HERE/'REQUEST.actual.json'),'save':save,'SDK':sdk},ensure_ascii=False,indent=2))
