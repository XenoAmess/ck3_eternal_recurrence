"""Small R215 portable package verification; no big media reads."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent
index=json.loads((root/'SOURCE-PINS.json').read_bytes())
def need(ok,reason):
    if not ok: raise ValueError(reason)
need(index['schema']=='xar.e04.r215-21s-portable-small-source-index.v1','schema')
need(index['machine_id']=='desktop-3fevhd2-1c74096080','origin machine')
need(index['continuous_human_1x'] is False and index['human_signoff'] is False,'false signoff')
need(index['formal_dynamic_credit'] is False,'false dynamic credit')
rows=index['copied_small_members']
need(len(rows)==13 and sum(r['bytes'] for r in rows)==113313,'member count or size')
for row in rows:
    rel=Path(row['target_relative_path'])
    need(not rel.is_absolute() and '..' not in rel.parts,'unsafe relative path')
    path=root/rel
    need(path.is_file() and path.stat().st_size==row['bytes'],'missing or size changed: '+str(rel))
    need(hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'hash changed: '+str(rel))
audio=[r for r in rows if r['target_relative_path'].endswith('.mp3')]
need(len(audio)==1 and audio[0]['bytes']==83376,'audio count or bytes')
print('R215 portable small package PASS: 13 exact members; human 1x and signoff remain pending')
