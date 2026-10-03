"""Create an external fixture with separate prepare/action/verify events."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]
SKILLS=('diplomacy','martial','stewardship','intrigue','learning','prowess')

def marker(name: str, condition: str) -> str:
    result='sxat_case_'+name.replace('-','_')
    return f'if = {{ limit = {{ {condition} }} set_variable = {{ name = {result} value = 1 }} debug_log = "SXAT: PASS {name}" }}\nelse = {{ set_variable = {{ name = {result} value = 0 }} debug_log = "SXAT: FAIL {name}" }}\n'

def character(scope: str, age: int=30, skill: int=10, extra: str='') -> str:
    stats=' '.join(f'{s} = {skill}' for s in SKILLS)
    return f'''create_character = {{
employer = root
age = {age}
gender_female_chance = 0
culture = root.culture
faith = root.faith
rite = root.rite
random_traits = no
dynasty = none
{stats}
save_scope_as = {scope}
{extra}
}}\nscope:{scope} = {{ add_character_modifier = {{ modifier = sxat_exhaust_prowess_negation_modifier years = 5 }} }}\n'''

def prepare(output: Path) -> dict:
    output=output.resolve()
    if output.exists() or output==SOURCE or SOURCE in output.parents:
        raise ValueError('fixture output must be a new directory outside product source')
    cases=[]
    for skill in SKILLS:
        untouched=' '.join(f'scope:{who} = {{ {s} = var:sxat_before_{s} }}' for who in ('sxat_receiver','sxat_donor') for s in SKILLS if s!=skill)
        condition=f'scope:sxat_receiver = {{ {skill} = sxat_receiver_expected_{skill}_value }} scope:sxat_donor = {{ {skill} = sxat_donor_expected_{skill}_value }} {untouched}'
        cases.append((f'paired-{skill}', '', f'scope:sxat_receiver = {{ sxad_transfer_{skill}_effect = {{ DONOR = scope:sxat_donor }} }}', condition))
    unchanged=' '.join(f'scope:{who} = {{ {s} = var:sxat_before_{s} }}' for who in ('sxat_receiver','sxat_donor') for s in SKILLS)
    cases += [
        ('tie-no-drain','', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1 }} scope:sxat_donor = {{ var:sxad_sex_experience = 1 }}'),
        ('winner-previous-count', 'scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 1000 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 3 } }', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', 'scope:sxat_receiver = { var:sxad_sex_experience = 1001 sxat_total_gain_value = 1 } scope:sxat_donor = { var:sxad_sex_experience = 4 sxat_total_gain_value = -1 }'),
        ('reverse-winner', 'scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 2 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 20 } }', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', 'scope:sxat_receiver = { var:sxad_sex_experience = 3 sxat_total_gain_value = -1 } scope:sxat_donor = { var:sxad_sex_experience = 21 sxat_total_gain_value = 1 }'),
        ('anonymous-count-only','', 'scope:sxat_receiver = { had_sex_with_unknown_effect = { GENDER = female } }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1 has_trait = sxad_sex_experience }} scope:sxat_donor = {{ NOT = {{ has_variable = sxad_sex_experience }} }}'),
        ('vanilla-pair-once','', 'scope:sxat_receiver = { had_sex_with_effect = { CHARACTER = scope:sxat_donor PREGNANCY_CHANCE = 0 } }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1 }} scope:sxat_donor = {{ var:sxad_sex_experience = 1 }}'),
        ('tooltip-read-only','', 'show_as_tooltip = { scope:sxat_receiver = { had_sex_with_effect = { CHARACTER = scope:sxat_donor PREGNANCY_CHANCE = 0 } } }', f'{unchanged} scope:sxat_receiver = {{ NOT = {{ has_variable = sxad_sex_experience }} }} scope:sxat_donor = {{ NOT = {{ has_variable = sxad_sex_experience }} }}'),
        ('ai-pair-supported', '', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', 'scope:sxat_receiver = { is_ai = yes var:sxad_sex_experience = 1 } scope:sxat_donor = { is_ai = yes var:sxad_sex_experience = 1 }'),
        ('same-character-rejected', '', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_receiver } }', f'{unchanged} scope:sxat_receiver = {{ NOT = {{ has_variable = sxad_sex_experience }} }}'),
        ('minor-rejected', '', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_minor } } scope:sxat_minor = { sxad_record_unknown_effect = yes }', f'{unchanged} scope:sxat_receiver = {{ NOT = {{ has_variable = sxad_sex_experience }} }} scope:sxat_minor = {{ age = 17 NOT = {{ has_variable = sxad_sex_experience }} }}'),
        ('donor-floor-with-positive-modifier', 'scope:sxat_donor = { add_diplomacy_skill = -1000 add_trait = gregarious add_character_modifier = { modifier = sxat_positive_diplomacy_modifier years = 5 } }', 'scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }', unchanged),
        ('receiver-negative-modifier', 'scope:sxat_receiver = { add_character_modifier = { modifier = sxat_negative_diplomacy_modifier years = 5 } }', 'scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }', unchanged),
        ('receiver-upper-bound-probe', 'scope:sxat_receiver = { add_diplomacy_skill = 10000 }', 'scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }', f'OR = {{ AND = {{ {unchanged} }} AND = {{ scope:sxat_receiver = {{ diplomacy = sxat_receiver_expected_diplomacy_value }} scope:sxat_donor = {{ diplomacy = sxat_donor_expected_diplomacy_value }} }} }}'),
        ('million-experience', 'scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 1000000 } }', 'scope:sxat_receiver = { sxad_record_unknown_effect = yes }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1000001 }}'),
    ]
    for count in (99,100,101,92233720368546,92233720368547):
        cases.append((f'experience-boundary-{count}', f'scope:sxat_receiver = {{ set_variable = {{ name = sxad_sex_experience value = {count} }} }}', 'scope:sxat_receiver = { sxad_record_unknown_effect = yes }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = {min(count+1,92233720368547)} }}'))
    cases += [
        ('nonzero-tie-no-drain','scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 20 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 20 } }','scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }',f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 21 }} scope:sxat_donor = {{ var:sxad_sex_experience = 21 }}'),
        ('same-day-two-pairs','scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 10 } }','scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }','scope:sxat_receiver = { var:sxad_sex_experience = 12 sxat_total_gain_value = 2 } scope:sxat_donor = { var:sxad_sex_experience = 2 sxat_total_gain_value = -2 }'),
        ('no-sex-memory-still-counts','','scope:sxat_receiver = { save_scope_as = no_sex_memory had_sex_with_effect = { CHARACTER = scope:sxat_donor PREGNANCY_CHANCE = 0 } }',f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1 }} scope:sxat_donor = {{ var:sxad_sex_experience = 1 }}'),
        ('dead-partner-rejected','root = { set_variable = { name = sxat_dead_partner_donor value = scope:sxat_donor } } scope:sxat_donor = { death = { death_reason = death_natural_causes } }','scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }','scope:sxat_receiver = { NOT = { has_variable = sxad_sex_experience } } scope:sxat_donor = { is_alive = no }'),
        ('receiver-fractional-modifier', 'scope:sxat_receiver = { add_character_modifier = { modifier = sxat_fractional_diplomacy_modifier years = 5 } }', 'scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }', unchanged),
        ('donor-fractional-modifier', 'scope:sxat_donor = { add_diplomacy_skill = 1 add_character_modifier = { modifier = sxat_fractional_diplomacy_modifier years = 5 } }', 'scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }', unchanged),
        ('all-skills-no-transfer', 'scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 5 } } scope:sxat_donor = { '+ ' '.join(f'add_{s}_skill = -1000' for s in SKILLS) +' add_trait = gregarious add_character_modifier = { modifier = sxat_positive_diplomacy_modifier years = 5 } set_variable = { name = sxad_sex_experience value = 2 } }', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 6 }} scope:sxat_donor = {{ var:sxad_sex_experience = 3 }}'),
        ('minor-16-rejected', '', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_minor } } scope:sxat_minor = { sxad_record_unknown_effect = yes }', f'{unchanged} scope:sxat_receiver = {{ NOT = {{ has_variable = sxad_sex_experience }} }} scope:sxat_minor = {{ age = 16 NOT = {{ has_variable = sxad_sex_experience }} }}'),
        ('player-ai-pair-supported', 'scope:sxat_receiver = { remove_character_flag = sxat_receiver_player_ai_pair_supported } root = { save_scope_as = sxat_receiver add_character_flag = sxat_receiver_player_ai_pair_supported set_variable = { name = sxad_sex_experience value = 5 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 2 } }', 'scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }', 'scope:sxat_receiver = { is_ai = no var:sxad_sex_experience = 6 sxat_total_gain_value = 1 } scope:sxat_donor = { is_ai = yes var:sxad_sex_experience = 3 sxat_total_gain_value = -1 }'),
        ('vanilla-memory-stress-preserved', 'scope:sxat_receiver = { add_trait = lustful add_stress = 100 set_relation_lover = scope:sxat_donor if = { limit = { stress_level = 1 } set_variable = { name = sxat_pre_stress_one value = 1 } } } scope:sxat_donor = { add_trait = lustful add_stress = 100 if = { limit = { stress_level = 1 } set_variable = { name = sxat_pre_stress_one value = 1 } } }', 'scope:sxat_receiver = { had_sex_with_effect = { CHARACTER = scope:sxat_donor PREGNANCY_CHANCE = 0 } }', f'{unchanged} scope:sxat_receiver = {{ var:sxad_sex_experience = 1 var:sxat_pre_stress_one = 1 stress_level = 0 any_memory = {{ memory_type = had_sex }} }} scope:sxat_donor = {{ var:sxad_sex_experience = 1 var:sxat_pre_stress_one = 1 stress_level = 0 }}'),
    ]
    # A3 stores permanent points in a signed modifier ledger. Native base
    # attributes must remain byte-for-byte equal to their pre-action arrays.
    untouched_diplomacy=' '.join(f'scope:{who} = {{ {s} = var:sxat_before_{s} }}' for who in ('sxat_receiver','sxat_donor') for s in SKILLS if s!='diplomacy')
    paired_diplomacy=f'scope:sxat_receiver = {{ diplomacy = sxat_receiver_expected_diplomacy_value }} scope:sxat_donor = {{ diplomacy = sxat_donor_expected_diplomacy_value }} {untouched_diplomacy}'
    updated=[]
    for name,setup,action,condition in cases:
        if name=='donor-floor-with-positive-modifier':condition=paired_diplomacy
        elif name=='receiver-negative-modifier':condition=f'scope:sxat_receiver = {{ diplomacy = var:sxat_before_diplomacy }} scope:sxat_donor = {{ diplomacy = sxat_donor_expected_diplomacy_value }} {untouched_diplomacy}'
        elif name=='receiver-upper-bound-probe':condition=untouched_diplomacy
        elif name in ('receiver-fractional-modifier','donor-fractional-modifier'):
            # Record actual display totals instead of assuming a rounding rule.
            condition=untouched_diplomacy
        elif name=='all-skills-no-transfer':
            setup=setup.replace('add_trait = gregarious add_character_modifier = { modifier = sxat_positive_diplomacy_modifier years = 5 }','add_character_modifier = { modifier = sxat_zero_all_skills_modifier years = 5 }')
        elif name=='player-ai-pair-supported':
            # External test setup only: a known player base array allows an
            # independent save check without claiming history-derived values.
            setup+=' root = { '+' '.join(f'add_{s}_skill = -1000 add_{s}_skill = 10' for s in SKILLS)+' add_character_modifier = { modifier = sxat_exhaust_prowess_negation_modifier years = 5 } }'
        if name in ('vanilla-pair-once','tooltip-read-only','no-sex-memory-still-counts'):
            setup+=' scope:sxat_receiver = { set_relation_lover = scope:sxat_donor }'
        if name=='no-sex-memory-still-counts':
            action+=' clear_saved_scope = no_sex_memory'
            condition+=' scope:sxat_receiver = { NOT = { any_memory = { memory_type = had_sex } } }'
        updated.append((name,setup,action,condition))
    cases=updated
    def seed_balance(receiver: int, donor: int) -> str:
        return f'scope:sxat_receiver = {{ set_variable = {{ name = sxad_diplomacy_balance value = {receiver} }} sxad_rebuild_diplomacy_modifier_effect = yes }} scope:sxat_donor = {{ set_variable = {{ name = sxad_diplomacy_balance value = {donor} }} sxad_rebuild_diplomacy_modifier_effect = yes }}'
    transfer='scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }'
    no_modifiers=' '.join(f'scope:{who} = {{ NOT = {{ has_character_modifier = sxad_diplomacy_gain_modifier }} NOT = {{ has_character_modifier = sxad_diplomacy_loss_modifier }} }}' for who in ('sxat_receiver','sxat_donor'))
    cases += [
        ('norman-prowess-penalty-negated', 'scope:sxat_receiver = { remove_character_modifier = sxat_exhaust_prowess_negation_modifier } scope:sxat_donor = { remove_character_modifier = sxat_exhaust_prowess_negation_modifier }', 'scope:sxat_receiver = { sxad_transfer_prowess_effect = { DONOR = scope:sxat_donor } }', 'scope:sxat_receiver = { prowess = sxat_receiver_expected_prowess_value } scope:sxat_donor = { prowess = var:sxat_before_prowess } '+ ' '.join(f'scope:{who} = {{ {s} = var:sxat_before_{s} }}' for who in ('sxat_receiver','sxat_donor') for s in SKILLS if s!='prowess')),
        ('balance-growth',seed_balance(1,-1),transfer,paired_diplomacy),
        ('balance-to-zero',seed_balance(-1,1),transfer,paired_diplomacy+' '+no_modifiers),
        ('balance-sign-flip',seed_balance(-1,1),transfer+' '+transfer,f'scope:sxat_receiver = {{ diplomacy = sxat_receiver_plus_two_diplomacy_value }} scope:sxat_donor = {{ diplomacy = sxat_donor_minus_two_diplomacy_value }} {untouched_diplomacy}'),
        ('receiver-balance-limit',seed_balance(1000000,0),transfer,unchanged),
        ('donor-balance-limit',seed_balance(0,-1000000)+' scope:sxat_donor = { add_character_modifier = { modifier = sxat_balance_limit_buffer_modifier years = 5 } }',transfer,unchanged),
        ('receiver-balance-last-point',seed_balance(999999,0),transfer,untouched_diplomacy),
        ('donor-balance-last-point',seed_balance(0,-999999)+' scope:sxat_donor = { add_character_modifier = { modifier = sxat_balance_limit_buffer_modifier years = 5 } }',transfer,paired_diplomacy),
    ]
    paired_names={'donor-floor-with-positive-modifier','receiver-negative-modifier','receiver-upper-bound-probe','receiver-fractional-modifier','donor-fractional-modifier'}
    ledger_expected={}
    checked=[]
    for name,setup,action,condition in cases:
        receiver_balance=[0]*6;donor_balance=[0]*6
        delta=0;random_direction=1
        if name.startswith('paired-'):
            receiver_balance[SKILLS.index(name.removeprefix('paired-'))]=1
            donor_balance[SKILLS.index(name.removeprefix('paired-'))]=-1
        elif name=='norman-prowess-penalty-negated':receiver_balance[5]=1;donor_balance[5]=-1
        elif name in paired_names:receiver_balance[0]=1;donor_balance[0]=-1
        elif name=='balance-growth':receiver_balance[0]=2;donor_balance[0]=-2
        elif name=='balance-sign-flip':receiver_balance[0]=1;donor_balance[0]=-1
        elif name=='receiver-balance-limit':receiver_balance[0]=1000000
        elif name=='donor-balance-limit':donor_balance[0]=-1000000
        elif name=='receiver-balance-last-point':receiver_balance[0]=1000000;donor_balance[0]=-1
        elif name=='donor-balance-last-point':receiver_balance[0]=1;donor_balance[0]=-1000000
        elif name in ('winner-previous-count','reverse-winner','same-day-two-pairs','player-ai-pair-supported'):
            delta=2 if name=='same-day-two-pairs' else 1
            random_direction=-1 if name=='reverse-winner' else 1
        if delta:
            condition+=f' scope:sxat_receiver = {{ sxat_total_balance_value = {delta*random_direction} }} scope:sxat_donor = {{ sxat_total_balance_value = {-delta*random_direction} }}'
            ledger_expected[name]={'kind':'random-pair','amount':delta,'direction':random_direction}
        else:
            condition+=' '+' '.join(f'scope:{who} = {{ sxat_{s}_balance_value = {balances[i]} }}' for who,balances in (('sxat_receiver',receiver_balance),('sxat_donor',donor_balance)) for i,s in enumerate(SKILLS) if not (name=='dead-partner-rejected' and who=='sxat_donor'))
            ledger_expected[name]={'kind':'exact','receiver':receiver_balance,'donor':donor_balance}
        checked.append((name,setup,action,condition))
    cases=checked
    events=['namespace = sxat\n']
    required=[]
    for index,(name,setup,action,condition) in enumerate(cases):
        create_id=100+index*4
        capture_id,action_id,verify_id=create_id+1,create_id+2,create_id+3
        case_flag=name.replace('-','_')
        minor_age=16 if name=='minor-16-rejected' else 17
        create=character('sxat_receiver')+character('sxat_donor')+character('sxat_minor',age=minor_age)+f'scope:sxat_receiver = {{ add_character_flag = sxat_receiver_{case_flag} }} scope:sxat_donor = {{ add_character_flag = sxat_donor_{case_flag} }}\n'+setup
        create+='\n'+'\n'.join(f'scope:{who} = {{ if = {{ limit = {{ is_alive = yes }} force_character_skill_recalculation = yes }} }}' for who in ('sxat_receiver','sxat_donor','sxat_minor'))
        create+=f'\ntrigger_event = {{ id = sxat.{capture_id} }}'
        capture=''
        for who in ('sxat_receiver','sxat_donor'):
            capture+=f'scope:{who} = {{ if = {{ limit = {{ is_alive = yes }}\n'+ '\n'.join(f'set_variable = {{ name = sxat_before_{s} value = {s} }}\nset_variable = {{ name = sxat_before_balance_{s} value = sxat_{s}_balance_value }}' for s in SKILLS)+'\n} }\n'
        capture+=f'trigger_event = {{ id = sxat.{action_id} }}'
        verify=''
        for who in ('sxat_receiver','sxat_donor'):
            verify+=f'scope:{who} = {{ if = {{ limit = {{ is_alive = yes }}\n'+'\n'.join(f'set_variable = {{ name = sxat_after_{s} value = {s} }}' for s in SKILLS)+'\n} }\n'
        verify+=marker(name,condition)
        required.append(f'SXAT: PASS {name}')
        if index+1<len(cases):
            # Each block contains at most 32 nested events. The same-day pair
            # action itself remains immediate within its single action event.
            delay=' days = 1' if (index+1)%8==0 else ''
            verify+=f'trigger_event = {{ id = sxat.{create_id+4}{delay} }}'
        else:
            verify+='set_variable = { name = sxat_finished value = 1 }\nset_variable = { name = sxad_sex_experience value = 1001 }\nif = { limit = { NOT = { has_trait = sxad_sex_experience } } add_trait = sxad_sex_experience }\ndebug_log = "SXAT: END production-effect-matrix"\n'
        for event_id,body in ((create_id,create),(capture_id,capture),(action_id,action+f'\ntrigger_event = {{ id = sxat.{verify_id} }}'),(verify_id,verify)):
            if event_id==100: body='debug_log = "SXAT: START production-effect-matrix"\n'+body
            events.append(f'sxat.{event_id} = {{\ntype = character_event\nhidden = yes\nimmediate = {{\n{body}\n}}\n}}\n')
    on_action='''on_game_start_after_lobby = { on_actions = { sxat_on_start } }
sxat_on_start = { effect = { debug_log = "SXAT: ON_START" every_player = { limit = { NOT = { has_character_flag = sxat_completed } } set_variable = { name = sxat_scheduled value = 1 } debug_log = "SXAT: SCHEDULED" add_character_flag = sxat_completed trigger_event = { id = sxat.100 days = 1 } } } }
'''
    values=''
    for skill in SKILLS:
        values+=f'sxat_receiver_expected_{skill}_value = {{ value = var:sxat_before_{skill} add = 1 }}\n'
        values+=f'sxat_donor_expected_{skill}_value = {{ value = var:sxat_before_{skill} subtract = 1 }}\n'
    values+='sxat_total_gain_value = { value = 0\n'+'\n'.join(f'add = {s}\nsubtract = var:sxat_before_{s}' for s in SKILLS)+'\n}\n'
    for skill in SKILLS:
        values+=f'sxat_{skill}_balance_value = {{ value = 0 if = {{ limit = {{ has_variable = sxad_{skill}_balance }} add = var:sxad_{skill}_balance }} }}\n'
    values+='sxat_total_balance_value = { value = 0\n'+'\n'.join(f'add = sxat_{s}_balance_value' for s in SKILLS)+'\n}\n'
    values+='sxat_receiver_plus_two_diplomacy_value = { value = var:sxat_before_diplomacy add = 2 }\nsxat_donor_minus_two_diplomacy_value = { value = var:sxat_before_diplomacy subtract = 2 }\n'
    payloads={
        'descriptor.mod':b'name="Superman Qiang External Acceptance Fixture"\nversion="1.0.0"\nsupported_version="1.20.*"\n',
        'common/on_action/sxat_on_actions.txt':on_action.encode('utf-8-sig'),
        'common/script_values/sxat_values.txt':values.encode('utf-8-sig'),
        'common/modifiers/sxat_modifiers.txt':b'\xef\xbb\xbfsxat_positive_diplomacy_modifier = { diplomacy = 5 }\nsxat_negative_diplomacy_modifier = { diplomacy = -50 }\nsxat_fractional_diplomacy_modifier = { diplomacy_mult = -0.5 }\nsxat_zero_all_skills_modifier = { diplomacy = -100 martial = -100 stewardship = -100 intrigue = -100 learning = -100 prowess = -100 }\nsxat_balance_limit_buffer_modifier = { diplomacy = 1000000 }\nsxat_exhaust_prowess_negation_modifier = { prowess = -5 }\n',
        'events/sxat_events.txt':''.join(events).encode('utf-8-sig'),
    }
    output.mkdir(parents=True)
    for relative,data in payloads.items():
        path=output/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    base_contract=[]
    for name,_,_,_ in cases:
        before_receiver=[10]*6;before_donor=[10]*6
        if name=='donor-floor-with-positive-modifier':before_donor[0]=0
        if name=='receiver-upper-bound-probe':before_receiver[0]=100
        if name=='donor-fractional-modifier':before_donor[0]=11
        if name=='all-skills-no-transfer':before_donor=[0]*6
        base_contract.append({'case':name,'receiver_before':before_receiver,'donor_before':before_donor,'expected':'unchanged','ledger_expected':ledger_expected[name],'requires_independent_save_arrays':True,**({'donor_root_reference':'sxat_dead_partner_donor','donor_dead':True} if name=='dead-partner-rejected' else {})})
    report={'schema':'sxad.external-fixture.v3','fixture_root':str(output),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'expected_pass_markers':required,'base_skill_contract':base_contract,'recursion_break_every_cases':8,'baseline_refresh_after_setup':True,'required_start':'SXAT: START production-effect-matrix','required_end':'SXAT: END production-effect-matrix','entry_character_history_id':1128,'entry_bookmark_key':'bookmark_rags_to_riches_duke_robert','covers':'production helper and vanilla-hook matrix; snapshots separated across hidden events','does_not_cover':['production interaction UI','trait hover correctness','save/reload','Workshop clean gameplay media'],'ck3_started':False,'files':[{'path':r,'size':len(d),'sha256':hashlib.sha256(d).hexdigest()} for r,d in sorted(payloads.items())]}
    (output.parent/f'{output.name}.fixture.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True,type=Path); args=parser.parse_args()
    try: print(json.dumps(prepare(args.output),ensure_ascii=False,indent=2))
    except (OSError,ValueError) as error: parser.exit(1,f'SXAD FIXTURE FAILED: {error}\n')
    return 0

if __name__=='__main__': raise SystemExit(main())
