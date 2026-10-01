"""Read original files only; preserve compact inventory for R0142 archive planning."""
from pathlib import Path
import json,hashlib,datetime
OUT=Path(__file__).parent
ROOT=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
def identity(p):
 b=p.read_bytes();return {'path':str(p).replace('\\','/'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
names=[]
for group,root in [('controller',ROOT),('live',LIVE)]:
 for p in root.rglob('*'):
  if p.is_file() and ((group=='live' and (p.parent.name=='scoped-ui-research-attempt-01' or p.name in ['session-result.json','capture-report.json','timeline.json','native-start-readback.json'])) or (group=='controller' and p.suffix=='.json' and ('build' not in p.parts or p.name in ['candidate-manifest.json','build-result.json','ctest-result.json']))):
   rel=str(p.relative_to(root)).replace('\\','/')
   if any(x in rel for x in ['profile/','CMakeFiles/','steam-offline-originals','prepare-source-','bootstrap-artifacts']):continue
   names.append({'group':group,'relative_path':rel,'bytes':p.stat().st_size})
documents={}
for rel in ['current-run-bindings.json','frozen-release-build-attempt-01/candidate-manifest.json','native-sdk-attempt-01/completion.json','display-restore-and-release-attempt-01/display-restore/readback.json','display-restore-and-release-attempt-01/screen-release-CAS.json']:
 p=ROOT/rel
 if p.is_file():documents[rel]={'original':identity(p),'value':json.loads(p.read_text('utf-8-sig'))}
for rel in ['scoped-ui-research-attempt-01/before-ui-root-review.json','scoped-ui-research-attempt-01/after-ui-root-review.json','scoped-ui-research-attempt-01/before-saved-pair.json','scoped-ui-research-attempt-01/after-saved-pair.json','scoped-ui-research-attempt-01/one-day-finished.json','ck3-output/session-result.json','ck3-output/capture-report.json']:
 p=LIVE/rel
 if p.is_file():documents[rel]={'original':identity(p),'value':json.loads(p.read_text('utf-8-sig'))}
report={'schema':'ck3.R0142.archive-input-inspection/v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'names':names,'documents':documents,'scope':'Read-only original files; no game/process/source/Git/screen calls.'}
p=OUT/'current-input-inspection-a01.json'
with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':identity(p),'inventory':names,'document_keys':{k:list(v['value']) for k,v in documents.items()}},ensure_ascii=False))
