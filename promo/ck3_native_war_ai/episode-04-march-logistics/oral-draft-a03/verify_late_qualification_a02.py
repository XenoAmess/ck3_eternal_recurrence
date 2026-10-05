"""Focused stdlib verification of append-only a02, without game/raw/media/Git access."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'portable-manifest-a02.json').read_bytes())
checks=[]
def check(name,value):
    if value is not True:
        raise ValueError(name)
    checks.append(name)
for row in manifest['files']:
    rel=row['path']
    check('safe relative '+rel, ':' not in rel and '\\' not in rel and '..' not in Path(rel).parts and not rel.startswith('/'))
    raw=(ROOT/rel).read_bytes()
    check('bytes/SHA '+rel,(len(raw),hashlib.sha256(raw).hexdigest())==(row['bytes'],row['sha256']))
check('14 old files exact retained',len(manifest['unchanged_a01_files'])==14 and all(
    (len((ROOT/r['path']).read_bytes()),hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest())==(r['bytes'],r['sha256'])
    for r in manifest['unchanged_a01_files']))
check('original body SHA unchanged',hashlib.sha256((ROOT/'six-chapter-narration-a03.md').read_bytes()).hexdigest()=='220cd7d85f995b62609d4ce3fd71760fc55748f80ab252d8725579fc04134e83')
check('original ledger SHA unchanged',hashlib.sha256((ROOT/'claim-ledger-a03.json').read_bytes()).hexdigest()=='6cb9a93476cb5f9fc70221b6969711db2ba57c691ebb411c1f3f8899b428477a')
p=json.loads((ROOT/'provenance/r0173-master-source-pins-a02.json').read_bytes())
check('formal source commit',p['source_commit']=='700b6917ad7ee1a9ca7bcb930b114f8bd4f11498')
check('exact two formal source pins',[(r['bytes'],r['sha256']) for r in p['source_files']]==[(5650,'7393ef0d024ff68dbe8ab771937ae3fa91d3a1ad2a0bf0443fa149708a07485f'),(47381,'4abb9de818d1dbf1dd7ad4e572bb90cadfff1b3d9bedf998af7b9133375eded8')])
check('five independent windows', [r['original_days'] for r in p['observed_windows']]==[[45,47],[49,50],[64,66],[70,72],[74,76]])
q=p['protocol']
check('original90daybudget not reset',q['original_start_raw']==53147376 and q['absolute_end_raw']==53149536 and q['latest_raw']==53149200 and q['original_days_used']==76 and q['remaining_original_days']==14 and q['budget_reset'] is False)
v=p['integer_window_70to72']
check('actual +7/+3 separate integer window',v['Main_current_after']-v['Main_current_before']==7 and v['child_current_after']-v['child_current_before']==3 and v['DATA_integer_gain_rows']==6 and v['stock_and_supply_anchors_unchanged'] is True)
s=p['stock_window_74to76']
check('actual +20 separate stock window',s['Main_stock_raw_after']-s['Main_stock_raw_before']==2000000 and s['scale']==100000 and s['Main_success_update_raw']==53149200 and s['full27actual37DATA_rows_unchanged'] is True and s['same_window_as_integer_gain'] is False)
check('child stock unchanged at100',s['child_stock_raw_before']==s['child_stock_raw_after']==10000000)
check('day50 site commander scope',p['day50_site']['Main0']['commander_character_id']==27357 and p['day50_site']['child204_native199']['commander_character_id']==33388 and 'Only' in p['day50_site']['commander_scope'])
check('whole vs split save roles',p['save_roles']['ABC_unsplit_whole_sha256'].startswith('d052') and p['save_roles']['qualification_split_backup_sha256'].startswith('c43f') and p['save_roles']['qualified_split_is_ABC_common_start'] is False and p['save_roles']['bytes_read_copied_or_rehashed']==0)
check('world control unread preserved',p['world_control']['continuous_occupation_controller_garrison_unchanged_proven'] is False and p['world_control']['unread_fields'] is None and p['world_control']['old_STOP_receipts_relabelled_success'] is False)
check('payload version/hash null preserved',p['subject']['payload_game_version'] is None and p['subject']['payload_executable_sha256'] is None)
check('ABC and film credits0',p['credits']=={'ABC_completed_arms':0,'film':0,'clean_span':0,'human_signoff':0})
text=(ROOT/'late-qualification-addendum-a02.md').read_text(encoding='utf-8')
defs=dict(re.findall(r'^\[([^\]]+)\]: (\S+)$',text,re.M))
check('late source public pinned links',all(link.startswith('https://github.com/XenoAmess/ck3_eternal_recurrence/blob/'+p['source_commit']+'/') for link in defs.values()))
check('late reference labels resolve',all(key in defs for key in re.findall(r'\[[^\]]+\]\[([^\]]+)\]',text)))
check('late package-relative pin link resolves',(ROOT/'provenance/r0173-master-source-pins-a02.json').is_file())
print(json.dumps({'status':'PASS','scope':'Focused append-only text/source qualification boundaries only','checks':len(checks),'files':len(manifest['files']),'unchanged_original_files':14,'newSDK_UI_GameMediaGitSecurityProviderCalls':0},ensure_ascii=False))
