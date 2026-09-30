from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
FILES=[('open-pursuit-v1.json','BFDB15778131C7F82128F149EBFFFE62F84FED7B13FA1498E78D95C3C383EE4A'),('knight-reinf-v2.json','8387AD30580E03C7DD29DA3B10E9012DE5F5C7C8981F0243951A38C14814A8E7'),('terminal-close-v2.json','F77668E2EA4CBBB51846148A0F42A9659F195C501C4C23A8DB99148F67F50D60')]
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
rows={};sources=[]
for name,digest in FILES:
    path=ROOT/'visual-specs'/name;r=ref(path)
    if r['sha256']!=digest:raise ValueError(f'spec bytes changed {path}')
    data=json.loads(path.read_text(encoding='utf-8'))
    if set(rows)&set(data['utterances']):raise ValueError('duplicate visual key')
    rows.update(data['utterances']);sources.append(r)
story=json.loads((ROOT/'story-final-v2.json').read_text(encoding='utf-8'))
keys={f"{c['id']}-{u['id']}" for c in story['chapters'] for u in c['utterances']}
if set(rows)!=keys:raise ValueError('visual spec not complete')
output=ROOT/'visual-spec-final-v1.json'
with output.open('x',encoding='utf-8') as f:json.dump({'kind':'exact-ui-and-labelled-native-records','utterances':rows,'source_specs':sources,'story':ref(ROOT/'story-final-v2.json'),'human_signoff':'not-provided'},f,ensure_ascii=False,indent=2)
target=Path('C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/project/review-story-a04-board-specs.json')
with target.open('xb') as f:f.write(output.read_bytes())
print(json.dumps({'boards':len(rows),'spec':ref(output)}))
