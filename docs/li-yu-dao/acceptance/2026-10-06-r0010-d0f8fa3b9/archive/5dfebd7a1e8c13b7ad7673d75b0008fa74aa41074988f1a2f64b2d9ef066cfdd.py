import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-second-open-join-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
cp=RUN/'checkpoints/0057-second-post-sign-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91533138 or save['sha256']!='13a87b974d2bc5e4d717f0d1b7877dfb4bcfcbde6781a4235fae902b1d8af6c9':raise ValueError('Actual second post-sign save mismatch')
sdk=pin(RUN/'mcp-client-evidence-002/0057-r10-0058-second-post-sign-save.sdk-result.json')
if sdk['bytes']!=2505173 or sdk['sha256']!='c90e009f3df7dd47502d7fc5140a862fb171901a67875e1025320ba19d658f44':raise ValueError('Actual second post-sign SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-second-after-source-sign-and-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'second_proposal_before43':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'final_JOIN_business_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
