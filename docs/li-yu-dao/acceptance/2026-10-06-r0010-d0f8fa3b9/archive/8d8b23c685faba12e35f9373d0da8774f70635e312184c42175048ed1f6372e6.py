import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-seventh-post-cancel-readback-20261006-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0171-eighth-open-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91542565 or save['sha256']!='04b22b41900f89b73f75d1295b12d4acd8021dd7081eab0bfdae9f813062c487':raise ValueError('Actual eighth-open save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0171-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK171')
sdk=pin(matches[0])
if sdk['bytes']!=6933331 or sdk['sha256']!='54c200e59829320a26f01f69b9727bf2c3e6e370e13d589525e9a5c482cd969b':raise ValueError('Actual eighth-open SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-eighth-formal-JOIN-proposal-opened-after-seventh-cancellation-no-new-reset-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'seventh_cancel_before167':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
