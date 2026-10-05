import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-fifth-post-cancel-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,data):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
cp=RUN/'checkpoints/0129-sixth-open-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91540327 or save['sha256']!='d331ba00e9865964a5e6319c00ae3da356070a54315437b43e73441be12ead76':raise ValueError('Actual sixth-open save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0129-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK129')
sdk=pin(matches[0])
if sdk['bytes']!=5214109 or sdk['sha256']!='840ed3bc19bfffda90be0e647d5f701e868bcd4017fba44dbe812200a8361331':raise ValueError('Actual sixth-open SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-sixth-formal-JOIN-proposal-opened-after-fifth-cancellation-no-new-reset-not-final-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
write('REQUEST.actual.json',req)
write('PREPARATION.json',{'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'fifth_cancel_before125':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'old_save_reparse':False,'final_JOIN_business_credit':False})
print(json.dumps({'save':save,'SDK':sdk,'request':pin(HERE/'REQUEST.actual.json')},ensure_ascii=False,indent=2))
