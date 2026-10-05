import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';OPEN=BASE/'r10-actual-sixth-open-join-readback-20261005-001';BASELINE=BASE/'r10-actual-fifth-post-cancel-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0149-sixth-post-cancel-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91537192 or save['sha256']!='5ab8d308bd2f3858388f86cc34289683c30cf8efa43515283c001421c40affe1':raise ValueError('Actual sixth post-cancel save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0149-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK149')
sdk=pin(matches[0])
if sdk['sha256']!='182bf0eb58d07269ab5f7c9946a40d976a02fdb6fe57ada671ae5c5dfdb6fea1':raise ValueError('Actual sixth post-cancel SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [OPEN/'reader/read_actual_checkpoint.py',*(OPEN/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((OPEN/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-sixth-post-explicit-cancel-after-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(OPEN/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'sixth_open_before129':pin(OPEN/'REPORT.json'),'fifth_cancel_baseline125':pin(BASELINE/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
