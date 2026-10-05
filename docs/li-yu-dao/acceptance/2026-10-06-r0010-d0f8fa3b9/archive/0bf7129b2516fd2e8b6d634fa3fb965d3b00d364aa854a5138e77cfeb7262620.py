import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-fourth-open-join-readback-20261005-001';BASELINE=BASE/'r10-actual-third-post-cancel-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
matches=[p for p in (RUN/'checkpoints').glob('0107-*') if (p/'checkpoint.ck3').is_file()]
if len(matches)!=1:raise ValueError('Need unique retained checkpoint107')
cp=matches[0];save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91535016 or save['sha256']!='120c11e39e8dfac92c48c0a8e6ea9ba10ad7bffd9891e844eaaf90188ff1809b':raise ValueError('Actual post-cancel save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0107-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK107')
sdk=pin(matches[0])
if sdk['bytes']!=4508505 or sdk['sha256']!='851f1482849edb75975127112c748ec191d9275dcf0982ac4a76b73b40a1eab7':raise ValueError('Actual post-cancel SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-fourth-post-explicit-cancel-after-source-sign-attempt-and-ACK-result-undetermined','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'fourth_open_before88':pin(PREV/'REPORT.json'),'third_cancel_baseline82':pin(BASELINE/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'original_SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
