import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-third-post-cancel-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
cp=RUN/'checkpoints/0088-fourth-open-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91538147 or save['sha256']!='8615285b73caa1e34364e2a78a351a8f9c2f813d6587a8c7a926f4fe12b3df53':raise ValueError('Actual fourth-open save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0088-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK88')
sdk=pin(matches[0])
if sdk['bytes']!=3495015 or sdk['sha256']!='4d658405af1e757a445458bb68163204abc9e87ee5887bfb4459fb75408e23b9':raise ValueError('Actual fourth-open SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-fourth-formal-JOIN-proposal-opened-after-cancellation-no-new-reset-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'third_cancel_before82':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'final_JOIN_business_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
