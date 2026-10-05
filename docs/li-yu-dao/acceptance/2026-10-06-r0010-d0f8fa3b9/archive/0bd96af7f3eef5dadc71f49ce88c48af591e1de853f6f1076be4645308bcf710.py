import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';OPEN=BASE/'r10-actual-seventh-open-join-readback-20261006-001';BASELINE=BASE/'r10-actual-sixth-post-cancel-readback-20261006-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0167-seventh-post-cancel-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91538159 or save['sha256']!='4aa783a16d446f8d9a7e1e1e622eaf77e39400ebe814ae40f4841fa5e2a7b3e9':raise ValueError('Actual seventh post-cancel save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0167-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK167')
sdk=pin(matches[0])
if sdk['bytes']!=6925653 or sdk['sha256']!='c950b7fd3d4905df2d8290ac9a5ae828d181ebf2a99da65783d2d76ac3b9cd64':raise ValueError('Actual seventh post-cancel SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [OPEN/'reader/read_actual_checkpoint.py',*(OPEN/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((OPEN/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-seventh-post-explicit-cancel-after-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(OPEN/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'seventh_open_before153':pin(OPEN/'REPORT.json'),'sixth_cancel_baseline149':pin(BASELINE/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
