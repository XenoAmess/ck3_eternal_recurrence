from pathlib import Path
import json
b=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0142-four-save-endpoint-audit-reinforcement-a01')
p=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06/scoped-ui-research-attempt-01/before-pre-ui-checkpoint-saved-pair.json')
pair=json.loads(p.read_text(encoding='utf-8'));snapshot=json.loads(Path(pair['snapshot']['response']['path']).read_text(encoding='utf-8'))
v=snapshot['body']['player_armies']
with(b/'actual-army-schema-a02.json').open('x',encoding='utf-8')as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(v))
