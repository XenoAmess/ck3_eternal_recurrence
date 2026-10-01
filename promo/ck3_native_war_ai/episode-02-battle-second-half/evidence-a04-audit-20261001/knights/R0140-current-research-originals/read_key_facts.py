from pathlib import Path
import json
def dump(path):
 p=Path(path);v=json.loads(p.read_text(encoding='utf-8-sig'))
 print('\nFILE',p)
 for k,value in v.items():
  if k in {'sources','pins','checks','artifacts','records','stdio','commands'}:print(k,'count',len(value));continue
  text=json.dumps(value,ensure_ascii=False)
  print(k,text if len(text)<5000 else text[:300]+'... length '+str(len(text)))
base='C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-04-scoped-ui/'
for relative in ['native-sdk-attempt-01/completion.json','restoration-and-release-attempt-01/display-restore/readback.json']:
 dump(base+relative)
dump('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04/ck3-output/session-result.json')
dump('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/R0140-failed-UI-monitor-diagnostic-attempt-03/R0140-monitor-initial-state-diagnostic-a03.json')
dump('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/current-native-research-R0139.json')
