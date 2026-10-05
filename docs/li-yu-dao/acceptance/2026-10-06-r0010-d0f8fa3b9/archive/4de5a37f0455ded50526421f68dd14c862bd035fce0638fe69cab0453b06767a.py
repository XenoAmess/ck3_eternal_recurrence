import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
s = json.loads((HERE / 'actual-save-001/STATE.json').read_text(encoding='utf-8'))
def compact(row):
    return None if row is None else {k: row.get(k) for k in ['present', 'tick', 'type', 'identity', 'number', 'boolean']}
def compactvars(rows):
    return {k: compact(v) for k,v in rows.items()}
def compactlists(rows):
    return {k: {'items': [{key: v.get(key) for key in ['type','identity','entries']} for v in row['items']], 'duration_entries': row['duration_entries']} for k,row in rows.items() if not any(w in k for w in ['doctrines','core','permitted','known','prohibited'])}
sm = s['summary']
print(json.dumps({k: v for k,v in sm.items() if k not in ['round_variables','stored_typed_roles','political7','actual_saved_native_modifiers']}, ensure_ascii=False, indent=2))
print('ACTOR_VARIABLES')
print(json.dumps(compactvars(s['all_actor_LYD_variables']), ensure_ascii=False, indent=2))
print('ACTOR_LISTS')
print(json.dumps(compactlists(s['all_actor_LYD_lists']), ensure_ascii=False, indent=2))
print('ROLES')
print(json.dumps({k: {'rite': v['rite'], 'variables': compactvars(v['variables']), 'lists': compactlists(v['lists'])} for k, v in s['character_roles'].items() if k != '31254'}, ensure_ascii=False, indent=2))
print('GRAPHS')
print(json.dumps({kind: {k: {'variables': compactvars(v['variables']), 'lists': compactlists(v['lists']), 'heads': v['heads']} for k, v in vals.items()} for kind, vals in s['source_target_related_graphs'].items()}, ensure_ascii=False, indent=2))
