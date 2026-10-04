"""Compare exact saved health ledgers and native health across a cold reload."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser(description=__doc__)
for name in ['before','after','native-before','native-after','output']:
    p.add_argument('--'+name,required=True,type=Path)
args=p.parse_args()
first=args.before;second=args.after
old=json.loads(first.read_text(encoding='utf-8'));new=json.loads(second.read_text(encoding='utf-8'));a={c['character_id']:c for c in old['characters']};b={c['character_id']:c for c in new['characters']};rows=[]
def modifiers(c):return sorted((m['key'],m['scale_q100000_ticks_exact']) for m in c['modifiers'] if m['key'].startswith('sxad_'))
for cid,c in a.items():
    d=b[cid];checks={'alive':d['alive'],'basehealth_same':c['base_health_saved']==d['base_health_saved'],'base_skills_same':c['base_skill_save_field']==d['base_skill_save_field'],'variables_same':c['variables']==d['variables'],'production_modifiers_scale_same':modifiers(c)==modifiers(d)}
    rows.append({'character_id':cid,'checks':checks,'health_ledger':d['variables'].get('sxad_health_balance'),'production_modifier_scales':modifiers(d)})
def context(path):return json.loads(path.read_text(encoding='utf-8'))['result']['campaign_root_context']
native_before=args.native_before;native_after=args.native_after
x=context(native_before);y=context(native_after)
checks={'same_character_set':set(a)==set(b),'root_references_same':old['root_references']==new['root_references'],'all_character_fields_same':all(all(r['checks'].values()) for r in rows),'native_health_same':x['player_health']==y['player_health'],'same_date':x['date_raw']==y['date_raw'],'marker_counts_same':[old['pass_count'],old['fail_count'],old['missing_count']]==[new['pass_count'],new['fail_count'],new['missing_count']]==[20,0,0]}
out=args.output
report={'schema':'sxad.health-cold-reload-check.v1','ok':all(checks.values()),'checks':checks,'characters':rows,'native_health':y['player_health'],'source_refs':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (first,second,native_before,native_after)],'fixture_reset_prevented':'Only original modifier/SV definitions mounted; no events or on_actions in reload projection.'}
with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps({'ok':report['ok'],'checks':checks,'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}));raise SystemExit(0 if report['ok'] else 1)
