from pathlib import Path
from decimal import Decimal
import argparse,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--before',required=True,type=Path);p.add_argument('--after',required=True,type=Path);p.add_argument('--fixture',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
before=json.loads(a.before.read_text(encoding='utf-8'));after=json.loads(a.after.read_text(encoding='utf-8'));fixture=json.loads(a.fixture.read_text(encoding='utf-8'))
b={c['character_id']:c for c in before['characters']};f={c['character_id']:c for c in after['characters']}
def ticks(c,key):
    v=c['variables'].get(key)
    if v is None:return 0
    assert v['type']=='value',(c['character_id'],key,v)
    return v['fixed5_ticks_exact']
def q(s):return int(Decimal(str(s))*100000)
rows=[];errors=[]
for case in fixture['base_skill_contract']:
    row={'case':case['case'],'roles':[]}
    for i,role in enumerate(('receiver','donor')):
        name=case[role+'_root_reference'];cid=after['root_references'][name];c=f[cid];old=b[cid]
        checks={'reference_same':before['root_references'][name]==cid,'alive':c['alive'],'basehealth_unchanged':c['base_health_saved']==old['base_health_saved'],'base_skills_unchanged':c['base_skill_save_field']==old['base_skill_save_field'],'health_balance_exact':ticks(c,'sxad_health_balance')==q(case['expected_health_balances'][i])}
        ledger=ticks(c,'sxad_health_balance');mods=[m for m in c['modifiers'] if m['key'] in ('sxad_health_gain_modifier','sxad_health_loss_modifier')]
        wanted='sxad_health_gain_modifier' if ledger>0 else 'sxad_health_loss_modifier'
        checks['single_signed_scale_projection']=not mods if ledger==0 else len(mods)==1 and mods[0]['key']==wanted and mods[0]['scale_q100000_ticks_exact']==abs(ledger)
        if not case.get('capacity_reverse_health_display_not_delta_asserted'):
            key='sxat_immediate_after_health' if role=='receiver' and case.get('receiver_dangerous_fixture_penalty_removed_after_immediate_sampling') else 'sxat_after_health'
            checks['health_delta_exact']=ticks(c,key)-ticks(c,'sxat_before_health')==q(case['expected_health_delta'][i])
        if case['case'].startswith('health-floor') and role=='donor':
            wanted_floor='3.00074' if case['case']=='health-floor-below-3_00074' else '3.00075'
            checks['literal_floor_baseline']=ticks(c,'sxat_before_health')==q(wanted_floor)
        row['roles'].append({'role':role,'character_id':cid,'checks':checks,'base_health_saved':c['base_health_saved'],'base_skills':c['base_skill_save_field'],'health_balance_ticks':ledger,'health_before_ticks':ticks(c,'sxat_before_health'),'health_immediate_after_ticks':ticks(c,'sxat_immediate_after_health'),'health_after_ticks':ticks(c,'sxat_after_health'),'production_health_modifiers':mods})
        errors.extend({'case':case['case'],'role':role,'character_id':cid,'failed_check':name} for name,value in checks.items() if not value)
    changes=[ticks(f[after['root_references'][case[r+'_root_reference']]],'sxad_health_balance')-ticks(b[before['root_references'][case[r+'_root_reference']]],'sxad_health_balance') for r in ('receiver','donor')]
    row['pair_health_ledger_change_ticks']=changes;row['raw_conservation']=sum(changes)==0
    if not row['raw_conservation']:errors.append({'case':case['case'],'failed_check':'pair_raw_conservation'})
    rows.append(row)
report={'schema':'sxad.health1.1.0-independent-check.v1','ok':not errors and after['pass_count']==20 and after['fail_count']==0 and after['missing_count']==0,'input_refs':[{'path':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in (a.before,a.after,a.fixture)],'case_count':len(rows),'script_marker_counts':[after['pass_count'],after['fail_count'],after['missing_count']],'cases':rows,'errors':errors,'scope':'Exact saved health ledger/scale/basehealth/base skills and recorded effective getter conservation. Cold reload and normal production UI separately pending.'}
with a.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
print(json.dumps({'ok':report['ok'],'cases':len(rows),'errors':errors,'output':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}))
raise SystemExit(0 if report['ok'] else 1)
