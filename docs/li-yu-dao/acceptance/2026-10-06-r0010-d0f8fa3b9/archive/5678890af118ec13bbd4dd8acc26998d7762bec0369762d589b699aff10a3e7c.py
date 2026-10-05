import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-open-join-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
cp=RUN/'checkpoints/0031-post-source-sign-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91532053 or save['sha256']!='885393b25bca235361e0d2a242bb2791eaa5d578ef03ed9c849c0849370fc4d4':raise ValueError('Actual new save mismatch')
sdk=pin(RUN/'mcp-client-evidence-002/0031-r10-0032-post-source-sign-save.sdk-result.json')
if sdk['bytes']!=1506017 or sdk['sha256']!='0ae847445f65ec3aac099f5dbbc45272e6809ff13641e37b40e11b1aa3a9259b':raise ValueError('Actual new SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-after-source-sign-and-result-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'source007_proposal_pair_before':pin(PREV/'actual-save-001/REPORT.json'),'actual_new_parse_count_so_far':0,'final_JOIN_business_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
