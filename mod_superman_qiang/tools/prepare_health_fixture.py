"""Controlled baseline before all production actions; external fixture only."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import argparse
from health_fixture_data import cases, SKILLS, DELTA, MAX, dec, seed
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',required=True,type=Path,help='A new external fixture directory; existing outputs are refused')
a=p.parse_args()
OUT=a.output.resolve();BASE=OUT.parent
cases[5]['donor_target']='10'

def character(role,flag):
 return 'create_character = { employer = root age = 30 gender_female_chance = 0 culture = root.culture faith = root.faith rite = root.rite dynasty = none random_traits = no '+ ' '.join(f'{s} = 10' for s in SKILLS)+f' save_scope_as = sxat_{role} }}\nscope:sxat_{role} = {{ add_character_flag = sxat_{role}_{flag} }}\n'
def fix(role,target):
 if target is None:return ''
 return f'''scope:sxat_{role} = {{
force_character_skill_recalculation = yes
set_variable = {{ name = sxat_fixture_health_fix value = {target} }}
change_variable = {{ name = sxat_fixture_health_fix subtract = health }}
if = {{ limit = {{ var:sxat_fixture_health_fix > 0 }} add_character_modifier = {{ modifier = sxat_fixture_health_gain_modifier years = 5 }} }}
else_if = {{ limit = {{ var:sxat_fixture_health_fix < 0 }} change_variable = {{ name = sxat_fixture_health_fix multiply = -1 }} add_character_modifier = {{ modifier = sxat_fixture_health_loss_modifier years = 5 }} }}
force_character_skill_recalculation = yes
}}\n'''
def restore(flag):
 return f'var:sxat_ref_receiver_{flag} = {{ save_scope_as = sxat_receiver }} var:sxat_ref_donor_{flag} = {{ save_scope_as = sxat_donor }}\n'

setup='debug_log = "SXAT: START health-1.1.0-targeted-matrix"\n'
action=''
verify=''
contracts=[]
markers=[]
for idx,c in enumerate(cases):
 flag=c['name'].replace('-','_')
 setup+=character('receiver',flag)+character('donor',flag)
 if idx==0:setup+=c['setup']
 for role in ('receiver','donor'):
  target=c[f'{role}_target']
  if role=='receiver' and target in ('0','-1'):target='5'
  setup+=fix(role,target)
 postsetup='' if idx==0 else c['setup']
 if c['name']=='health-reverse-capacity-boundaries':
  postsetup=postsetup.replace(seed('receiver',-MAX),'scope:sxat_receiver = { set_variable = { name = sxad_health_balance value = -1000000 } }\n')
 setup+=postsetup
 setup+=f'root = {{ set_variable = {{ name = sxat_ref_receiver_{flag} value = scope:sxat_receiver }} set_variable = {{ name = sxat_ref_donor_{flag} value = scope:sxat_donor }} }}\n'

 action+=restore(flag)
 if c['name']=='health-reverse-capacity-boundaries':action+='scope:sxat_receiver = { sxad_rebuild_health_modifier_effect = yes }\n'
 if c['receiver_target'] in ('0','-1'):
  loss='5' if c['receiver_target']=='0' else '6'
  action+=f'scope:sxat_receiver = {{ set_variable = {{ name = sxat_fixture_action_health_loss value = {loss} }} add_character_modifier = {{ modifier = sxat_fixture_health_action_loss_modifier years = 5 }} force_character_skill_recalculation = yes }}\n'
 conditions=[]
 expected_balances=[]
 for role in ('receiver','donor'):
  delta=Decimal(c[f'{role}_delta'])
  balance=Decimal(c[f'{role}_initial_balance'])
  raw_delta=DELTA if role=='receiver' else -DELTA
  if c['name'] in ('health-floor-below-3_00074','health-upper-balance-block','health-lower-balance-block','equal-experience-health-no-transfer') or c['skill_delta']:raw_delta=Decimal(0)
  expected=balance+raw_delta;expected_balances.append(dec(expected))
  action+=f'''scope:sxat_{role} = {{
force_character_skill_recalculation = yes
set_variable = {{ name = sxat_before_health value = health }}
set_variable = {{ name = sxat_expected_health value = health }}
change_variable = {{ name = sxat_expected_health add = {dec(delta)} }}
'''+''.join(f'set_variable = {{ name = sxat_before_{s} value = {s} }}\n' for s in SKILLS)+'}\n'
  conditions.append(f'scope:sxat_{role} = {{ sxad_health_balance_value = {dec(expected)} }}')
  # Current effective health is independently sampled after a day. Dangerous
  # fixture penalties are removed after immediate sampling to keep these
  # characters alive; their immediate getters remain explicit test evidence.
  immediate=c['receiver_target'] in ('0','-1') and role=='receiver'
  if c['name']=='health-reverse-capacity-boundaries':
   pass
  elif immediate:
   conditions.append(f'scope:sxat_{role} = {{ var:sxat_before_health = {c["receiver_target"]} var:sxat_immediate_after_health = var:sxat_expected_health }}')
  else:
   conditions.append(f'scope:sxat_{role} = {{ health = var:sxat_expected_health }}')
  if expected>0:conditions.append(f'scope:sxat_{role} = {{ has_character_modifier = sxad_health_gain_modifier NOT = {{ has_character_modifier = sxad_health_loss_modifier }} }}')
  elif expected<0:conditions.append(f'scope:sxat_{role} = {{ has_character_modifier = sxad_health_loss_modifier NOT = {{ has_character_modifier = sxad_health_gain_modifier }} }}')
  else:conditions.append(f'scope:sxat_{role} = {{ NOT = {{ has_character_modifier = sxad_health_gain_modifier }} NOT = {{ has_character_modifier = sxad_health_loss_modifier }} }}')
  for s in SKILLS:
   skill_balance=(1 if role=='receiver' else -1) if c['skill_delta']==s else (1000000 if role=='receiver' and c['counts'] else 0)
   conditions.append(f'scope:sxat_{role} = {{ sxad_{s}_balance_value = {skill_balance} }}')
  if c['counts']:conditions.append(f'scope:sxat_{role} = {{ var:sxad_sex_experience = {c["counts"][0 if role=="receiver" else 1]} }}')
 # Literal floor validation prevents a misnormalized fixture masquerading as
 # a successful guard test. Verify the real Q100000 baseline, not just result.
 if c['name'].startswith('health-floor'):
  conditions.append(f'scope:sxat_donor = {{ var:sxat_before_health = {c["donor_target"]} }}')
 if c['skill_delta']:
  s=c['skill_delta']
  for role,delta in [('receiver',1),('donor',-1)]:
   action+=f'scope:sxat_{role} = {{ set_variable = {{ name = sxat_expected_{s} value = {s} }} change_variable = {{ name = sxat_expected_{s} add = {delta} }} }}\n'
   conditions.append(f'scope:sxat_{role} = {{ {s} = var:sxat_expected_{s} }}')
 action+=c['action']+'\n'
 for role in ('receiver','donor'):
  action+=f'scope:sxat_{role} = {{ set_variable = {{ name = sxat_immediate_after_health value = health }} }}\n'
 if c['receiver_target'] in ('0','-1'):
  action+='scope:sxat_receiver = { remove_character_modifier = sxat_fixture_health_action_loss_modifier force_character_skill_recalculation = yes }\n'
 if c['name']=='health-reverse-capacity-boundaries':
  action+='scope:sxat_receiver = { add_character_modifier = { modifier = sxat_health_capacity_buffer_modifier years = 5 } force_character_skill_recalculation = yes }\n'
 verify+=restore(flag)
 for role in ('receiver','donor'):
  verify+=f'scope:sxat_{role} = {{ set_variable = {{ name = sxat_after_health value = health }} '+''.join(f'set_variable = {{ name = sxat_after_{s} value = {s} }} ' for s in SKILLS)+'}\n'
 verify+=f'if = {{ limit = {{ {" ".join(conditions)} }} set_variable = {{ name = sxat_case_{flag} value = 1 }} debug_log = "SXAT: PASS {c["name"]}" }}\nelse = {{ set_variable = {{ name = sxat_case_{flag} value = 0 }} debug_log = "SXAT: FAIL {c["name"]}" }}\n'
 markers.append('SXAT: PASS '+c['name'])
 contracts.append({'case':c['name'],'receiver_root_reference':'sxat_ref_receiver_'+flag,'donor_root_reference':'sxat_ref_donor_'+flag,'receiver_before':None if idx==0 else [10]*6,'donor_before':[10]*6,'expected':'base skills and basehealth identical to independently saved before-action checkpoint','expected_health_balances':expected_balances,'expected_health_delta':[c['receiver_delta'],c['donor_delta']],'mitigation':c['name']=='health-penalty-mitigation','skill_delta':c['skill_delta'],'receiver_dangerous_fixture_penalty_removed_after_immediate_sampling':c['receiver_target'] in ('0','-1'),'capacity_reverse_health_display_not_delta_asserted':c['name']=='health-reverse-capacity-boundaries'})

setup+='trigger_event = { id = sxat.2 days = 1 }\n'
action+='trigger_event = { id = sxat.4 days = 1 }\n'
verify+='set_variable = { name = sxat_health_matrix_done value = 1 } debug_log = "SXAT: END health-1.1.0-targeted-matrix"\n'
events='namespace = sxat\n'
events+='sxat.1 = { type = character_event hidden = yes immediate = {\n'+setup+'} }\n'
events+='sxat.2 = { type = character_event title = sxat_health_baseline_title desc = sxat_health_baseline_desc immediate = { set_variable = { name = sxat_health_baseline_ready value = 1 } debug_log = "SXAT: BASELINE_READY health-1.1.0" } option = { name = sxat_health_begin trigger_event = { id = sxat.3 } } }\n'
events+='sxat.3 = { type = character_event hidden = yes immediate = {\n'+action+'} }\n'
events+='sxat.4 = { type = character_event hidden = yes immediate = {\n'+verify+'} }\n'
payload={
 'descriptor.mod':'name="SXAD external health1.1.0 fixture"\nversion="0"\nsupported_version="1.20.*"\n',
 'common/on_action/sxat_on_actions.txt':'on_game_start_after_lobby = { on_actions = { sxat_health_start } }\nsxat_health_start = { effect = { every_player = { trigger_event = { id = sxat.1 days = 1 } } } }\n',
 'common/modifiers/sxat_health_modifiers.txt':'sxat_fixture_health_gain_modifier = { health = 1 scale = { value = sxat_fixture_health_gain_scale } }\nsxat_fixture_health_loss_modifier = { health = -1 scale = { value = sxat_fixture_health_loss_scale } }\nsxat_fixture_health_action_loss_modifier = { health = -1 scale = { value = sxat_fixture_action_loss_scale } }\nsxat_health_penalty_mitigation_modifier = { negate_health_penalty_add = 0.1 }\nsxat_health_capacity_buffer_modifier = { health = 1000001 }\nsxat_exhaust_prowess_negation_modifier = { prowess = -5 }\n',
 'common/script_values/sxat_health_values.txt':'sxat_fixture_health_gain_scale = { value = 0 if = { limit = { has_variable = sxat_fixture_health_fix } add = var:sxat_fixture_health_fix } }\nsxat_fixture_health_loss_scale = { value = 0 if = { limit = { has_variable = sxat_fixture_health_fix } add = var:sxat_fixture_health_fix } }\nsxat_fixture_action_loss_scale = { value = 0 if = { limit = { has_variable = sxat_fixture_action_health_loss } add = var:sxat_fixture_action_health_loss } }\n',
 'events/sxat_health_events.txt':events,
 'localization/simp_chinese/sxat_health_l_simp_chinese.yml':'l_simp_chinese:\n sxat_health_baseline_title:0 "测试夹具：健康基线已就绪"\n sxat_health_baseline_desc:0 "此窗口只属于外置验收夹具，不可用于宣传。请先保存独立基线存档并读取原生健康值，再开始20项测试。"\n sxat_health_begin:0 "开始本轮验收测试"\n',
}
OUT.mkdir(exist_ok=False)
files=[]
for rel,text in payload.items():
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);raw=text.encode('utf-8-sig');p.write_bytes(raw);files.append({'path':rel,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest={'schema':'sxad.external-health1.1.0-fixture.v2','fixture_root':OUT.as_posix(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'case_data_source_sha256':hashlib.sha256(Path(__file__).with_name('health_fixture_data.py').read_bytes()).hexdigest(),'expected_pass_markers':markers,'base_skill_contract':contracts,'required_start':'SXAT: START health-1.1.0-targeted-matrix','required_end':'SXAT: END health-1.1.0-targeted-matrix','case_count':20,'baseline_event_key':'sxat.2','baseline_save_required_before_choice':True,'total_calendar_days_to_result':3,'native_basehealth_writes':False,'files':files,'does_not_cover':['real normal UI','promotional gameplay','statistical7branch distribution','lifespan guarantees'],'ck3_started':False}
with (BASE/(OUT.name+'.fixture.json')).open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
print(json.dumps({'output':OUT.as_posix(),'cases':20,'files':len(files),'manifest_sha256':hashlib.sha256((BASE/(OUT.name+'.fixture.json')).read_bytes()).hexdigest()},ensure_ascii=False))
