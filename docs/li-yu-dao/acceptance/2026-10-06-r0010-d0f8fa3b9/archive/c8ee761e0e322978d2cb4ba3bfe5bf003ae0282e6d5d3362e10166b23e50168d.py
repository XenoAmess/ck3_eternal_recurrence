import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-third-open-join-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
matches=[p for p in (RUN/'checkpoints').glob('0082-*') if (p/'checkpoint.ck3').is_file()]
if len(matches)!=1:raise ValueError('Need unique retained checkpoint82')
cp=matches[0];save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91533790 or save['sha256']!='d4dbf44188328d2094da1ccdbdf5944f82ba48f6e911f954f4becc145457175d':raise ValueError('Actual post-cancel save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0082-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK82')
sdk=pin(matches[0])
if sdk['bytes']!=3487321 or sdk['sha256']!='03dbc508120e6912322bdb594eabbe576e7cb14f97c2c8b330a203056973f285':raise ValueError('Actual post-cancel SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-third-post-explicit-cancel-after-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'third_open_before68':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'final_JOIN_business_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
