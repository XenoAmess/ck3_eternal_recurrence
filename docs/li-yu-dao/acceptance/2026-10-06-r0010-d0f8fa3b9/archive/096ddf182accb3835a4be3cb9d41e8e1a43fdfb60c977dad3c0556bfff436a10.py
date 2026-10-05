import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-third-before-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
cp=RUN/'checkpoints/0068-third-open-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91536994 or save['sha256']!='c7d84400a24c922e6ce902a563c9294d80123394f86bc3862ccf31743234ff99':raise ValueError('Actual third-open save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0068-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK68')
sdk=pin(matches[0])
if sdk['bytes']!=2797089 or sdk['sha256']!='e36b329da253e2e27aeba5466adb5fc2a85b0138c30f1aa74918d1457cd19197':raise ValueError('Actual third-open SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-third-formal-JOIN-proposal-opened-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'third_before63_report':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'final_JOIN_business_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
