import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';OPEN=BASE/'r10-actual-fifth-open-join-readback-20261005-001';BASELINE=BASE/'r10-actual-fourth-post-cancel-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0125-fifth-post-cancel-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91535983 or save['sha256']!='55b352c47d89ee41ef86479026627f84ebcb35736848daa4e70178bb06a74db2':raise ValueError('Actual fifth post-cancel save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0125-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK125')
sdk=pin(matches[0])
if sdk['bytes']!=5206437 or sdk['sha256']!='7a9768a2e921c36e6625e04d807cb9b7a417a45f9cff9f1771b76e73a67b1b09':raise ValueError('Actual fifth post-cancel SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [OPEN/'reader/read_actual_checkpoint.py',*(OPEN/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((OPEN/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-fifth-post-explicit-cancel-after-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(OPEN/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'fifth_open_before111':pin(OPEN/'REPORT.json'),'fourth_cancel_baseline107':pin(BASELINE/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
