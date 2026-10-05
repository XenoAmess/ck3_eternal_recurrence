import hashlib,json
from pathlib import Path
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');HERE=Path(__file__).resolve().parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-second-post-sign-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
cp=RUN/'checkpoints/0063-third-before-save';save=pin(cp/'checkpoint.ck3')
if save['bytes']!=91533017 or save['sha256']!='40cc2bb630b1255217f09c727aa506572d1d3ab2af4aaf1ca13248306fe07b08':raise ValueError('Actual third-before save mismatch')
matches=list((RUN/'mcp-client-evidence-002').glob('0063-*.sdk-result.json'))
if len(matches)!=1:raise ValueError('Need unique actual SDK63')
sdk=pin(matches[0])
if sdk['bytes']!=2789421 or sdk['sha256']!='b8b719acb4f27d436e08adafc1eb828e68cca2b778fc504007831d140b49e058':raise ValueError('Actual third-before SDK mismatch')
metadata=pin(cp/'checkpoint-metadata.json');reader=HERE/'reader';reader.mkdir()
for source in [PREV/'reader/read_actual_checkpoint.py',*(PREV/'reader/dependencies').glob('*.py')]:
    dest=reader/source.name if source.name=='read_actual_checkpoint.py' else reader/'dependencies'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
req=json.loads((PREV/'REQUEST.actual.json').read_text(encoding='utf-8'));req.update({'phase':'actual-R10-third-intent-before-after-explicit-reset-not-new-business-result','save':save,'supporting_evidence':[sdk,metadata],'output':str(HERE/'actual-save-001')})
with (HERE/'REQUEST.actual.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(req,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'PREPARATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'save':save,'original_SDK':sdk,'metadata':metadata,'qualified_reader':pin(PREV/'reader/read_actual_checkpoint.py'),'exact_copied_reader':pin(reader/'read_actual_checkpoint.py'),'second_rejected_before57':pin(PREV/'REPORT.json'),'actual_new_parse_count_so_far':0,'business_or_natural_cooldown_expiry_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
