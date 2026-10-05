import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OLD=BASE/'r10-actual-detach-second-precommit-readback-20261006-001'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0240-detach-second-post-save';save=pin(cp/'checkpoint.ck3');assert save['bytes']==91669783 and save['sha256']=='1d98f0d2482c02477f460127044690b1df128e806b2ffbfab399e945e3551a1d'
sdk=pin(RUN/'mcp-client-evidence-002/0240-r10-0241-detach-second-post-save.sdk-result.json');assert sdk['bytes']==10253579 and sdk['sha256']=='6ff44bbadd20a6d18a81d30939924d632547a261ff1d764413aba12dc3b31d4e'
metadata=pin(cp/'checkpoint-metadata.json');copies=[]
for src in [OLD/'reader/read_actual_checkpoint.py',*(OLD/'reader/dependencies').glob('*.py'),OLD/'inspect_new.py']:
    dst=HERE/src.relative_to(OLD);dst.parent.mkdir(parents=True,exist_ok=True);raw=src.read_bytes();adjustment=None
    if src.name=='read_actual_checkpoint.py':
        anchor='    selected_rites={rid};selected_faiths={fid}';replacement="    selected_rites={rid,'187'};selected_faiths={fid,'106'}"
        text=raw.decode('utf-8');assert text.count(anchor)==1;raw=text.replace(anchor,replacement).encode('utf-8');adjustment={'exact_old_line':anchor,'new_line':replacement,'purpose':'Retain bounded actual source106/backup187 graph observed in immutable192/200 caches when overwritten actor proposal refs stop selecting them','not_extra_save_AST_parse':True}
    with dst.open('xb') as f:f.write(raw)
    copies.append({'source':pin(src),'copy':pin(dst),'scope_extension':adjustment,'dependency_or_inspector_exact_equal':adjustment is not None or src.read_bytes()==dst.read_bytes()})
req=read(OLD/'REQUEST.actual.json');req.update({'phase':'actual-R10-second-DETACH-final-confirm-and-ACK-post-result-bounded-prior106-187-graphs-retained','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')});write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'SDK':sdk,'metadata':metadata,'qualified_AST_parser_reuse':copies,'precommit235_SEALED':pin(OLD/'SEALED.json'),'prior106_187_actual_cached_basis':pin(BASE/'r10-actual-cycle-before-detach-readback-20261006-001/actual-save-001/STATE.json'),'actual_new_AST_count_so_far':0,'old_save_reparsed':False,'final_DETACH_credit_until_readback':False})
print(json.dumps({'request':pin(HERE/'REQUEST.actual.json'),'save':save,'SDK':sdk,'bounded_graph_scope_extension_before_only_AST':True},ensure_ascii=False,indent=2))
