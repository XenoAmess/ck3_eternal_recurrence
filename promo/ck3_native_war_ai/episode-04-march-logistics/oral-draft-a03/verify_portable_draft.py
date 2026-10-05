"""Stdlib-only check of this frozen text draft; no Git/network/runtime/media access."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'portable-manifest-a01.json').read_bytes())
checks=[]
def check(name, value):
    if value is not True:
        raise ValueError(name)
    checks.append(name)
for row in manifest['files']:
    rel=row['path']
    check('safe relative file '+rel, ':' not in rel and '\\' not in rel and not rel.startswith('/') and '..' not in Path(rel).parts)
    raw=(ROOT/rel).read_bytes()
    check('bytes/SHA '+rel,len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'])
spoken=dict(re.findall(r'^\[(C\d{2}-\d{2})\] (.+)$',(ROOT/'six-chapter-narration-a03.md').read_text(encoding='utf-8'),re.M))
ledger=json.loads((ROOT/'claim-ledger-a03.json').read_bytes())
budget=json.loads((ROOT/'wordcount-budget-a03.json').read_bytes())
rows={r['id']:r for r in ledger['claims']}
check('69 original spoken paragraph IDs',len(spoken)==69 and set(spoken)==set(rows))
check('ledger exactly maps spoken text',all(spoken[key]==r['claim_summary'] for key,r in rows.items()))
check('6907 CJK count',sum(len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]',x)) for x in spoken.values())==6907)
base='https://github.com/XenoAmess/ck3_eternal_recurrence/blob/'
for key,row in ledger['source_catalog'].items():
    link=row['citation']
    check('portable source '+key,link.startswith(base) or (':' not in link and '\\' not in link and '..' not in Path(link).parts and (ROOT/link).is_file()))
check('all claim source keys',all(k in ledger['source_catalog'] for r in rows.values() for k in r['source_keys']))
for name in ('README.md','outline-and-shot-needs-a03.md','knowledge-code-references-a03.md'):
    text=(ROOT/name).read_text(encoding='utf-8')
    defs=dict(re.findall(r'^\[([^\]]+)\]: (\S+)$',text,re.M))
    check('reference labels '+name,all(k in defs for k in re.findall(r'\[[^\]]+\]\[([^\]]+)\]',text)))
    check('inline links '+name,all(k.startswith(base) or (ROOT/k).is_file() for k in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text)))
split=json.loads((ROOT/'sources/r0173-half-split-facts.json').read_bytes())
post=split['post_armies']
check('historical day44 split IDs',[(r['army_id'],r['native_carmy_id']) for r in post]==[(0,0),(204,199)])
check('historical day44 soldier values',[(r['current_soldiers'],r['maximum_soldiers']) for r in post]==[(3337,3371),(3342,3376)])
check('27actual and37DATA',sum(r['regiment_count'] for r in post)==27 and sum(r['DATA_count'] for r in post)==37)
check('samepaused copied inventory above childcap',split['endpoint_game_days_advanced']==0 and all(r['current_supply_raw']==11037716 for r in post) and post[1]['current_supply_capacity_raw']==10000000)
check('no future result or media credit',ledger['ABC_winner'] is None and ledger['actual_audio_duration_seconds'] is None and ledger['actual_video_duration_seconds'] is None and ledger['authority_limits']['clean_spans_certified'] is False and ledger['authority_limits']['signoff'] is False)
check('text estimate only within20to40',budget['estimate_is_text_only'] is True and 20<=budget['estimated_script_read_minutes'][0]<=budget['estimated_script_read_minutes'][1]<=40)
print(json.dumps({'status':'PASS','scope':'portable draft bytes/links/transcription only','checks':len(checks),'files':len(manifest['files']),'paragraphs':len(spoken),'CJK':6907,'newGameMediaProviderSecurityGitCalls':0},ensure_ascii=False))
