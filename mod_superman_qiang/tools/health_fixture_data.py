"""Twenty targeted v1.1.0 health cases; external fixtures, never production."""
from decimal import Decimal
SKILLS=('diplomacy','martial','stewardship','intrigue','learning','prowess')
DELTA=Decimal('0.00075')
MAX=Decimal('1000000')

def dec(v):return format(Decimal(v),'f')
def seed(role,balance):
 return f'scope:sxat_{role} = {{ set_variable = {{ name = sxad_health_balance value = {dec(balance)} }} sxad_rebuild_health_modifier_effect = yes }}\n'
def excluded():
 return 'scope:sxat_receiver = { '+ ' '.join(f'set_variable = {{ name = sxad_{s}_balance value = 1000000 }} sxad_rebuild_{s}_modifier_effect = yes' for s in SKILLS)+' }\n'
TRANSFER='scope:sxat_receiver = { sxad_transfer_health_effect = { DONOR = scope:sxat_donor } }\n'
PAIR='scope:sxat_receiver = { sxad_record_pair_effect = { PARTNER = scope:sxat_donor } }\n'

cases=[]
def add(name,setup='',action=TRANSFER,receiver_delta=DELTA,donor_delta=-DELTA,receiver_balance=0,donor_balance=0,receiver_target='5',donor_target='5',counts=None,health_exact=True,skill_delta=None):
 cases.append({'name':name,'setup':setup,'action':action,'receiver_delta':dec(receiver_delta),'donor_delta':dec(donor_delta),'receiver_initial_balance':dec(receiver_balance),'donor_initial_balance':dec(donor_balance),'receiver_target':receiver_target,'donor_target':donor_target,'counts':counts,'health_exact':health_exact,'skill_delta':skill_delta})

add('player-native-health-75',setup='scope:sxat_receiver = { remove_character_flag = sxat_receiver_player_native_health_75 } root = { save_scope_as = sxat_receiver add_character_flag = sxat_receiver_player_native_health_75 }',receiver_target=None)
add('health-flat-75')
add('health-floor-below-3_00074',donor_target='3.00074',receiver_delta=0,donor_delta=0)
add('health-floor-at-3_00075',donor_target='3.00075')
add('health-floor-same-day-repeat',donor_target='3.00075',action=TRANSFER+TRANSFER)
add('health-penalty-mitigation',setup='scope:sxat_donor = { add_character_modifier = { modifier = sxat_health_penalty_mitigation_modifier years = 5 } }',donor_delta=0,health_exact=True)
add('health-rebuild-idempotent',action=TRANSFER+'scope:sxat_receiver = { sxad_rebuild_health_modifier_effect = yes sxad_rebuild_health_modifier_effect = yes } scope:sxat_donor = { sxad_rebuild_health_modifier_effect = yes sxad_rebuild_health_modifier_effect = yes }')
add('health-ledger-growth',setup=seed('receiver',DELTA)+seed('donor',-DELTA),receiver_balance=DELTA,donor_balance=-DELTA)
add('health-ledger-to-zero',setup=seed('receiver',-DELTA)+seed('donor',DELTA),receiver_balance=-DELTA,donor_balance=DELTA)
add('health-upper-balance-block',setup=seed('receiver',MAX),receiver_delta=0,donor_delta=0,receiver_balance=MAX)
add('health-upper-balance-last',setup=seed('receiver',MAX-DELTA),receiver_balance=MAX-DELTA)
buffer='scope:sxat_donor = { add_character_modifier = { modifier = sxat_health_capacity_buffer_modifier years = 5 } }\n'
add('health-lower-balance-block',setup=seed('donor',-MAX)+buffer,receiver_delta=0,donor_delta=0,donor_balance=-MAX)
add('health-lower-balance-last',setup=seed('donor',-MAX+DELTA)+buffer,donor_balance=-MAX+DELTA)
add('six-skill-diplomacy-regression',action='scope:sxat_receiver = { sxad_transfer_diplomacy_effect = { DONOR = scope:sxat_donor } }',receiver_delta=0,donor_delta=0,skill_delta='diplomacy')
add('six-skill-prowess-regression',setup='scope:sxat_receiver = { add_character_modifier = { modifier = sxat_exhaust_prowess_negation_modifier years = 5 } } scope:sxat_donor = { add_character_modifier = { modifier = sxat_exhaust_prowess_negation_modifier years = 5 } }',action='scope:sxat_receiver = { sxad_transfer_prowess_effect = { DONOR = scope:sxat_donor } }',receiver_delta=0,donor_delta=0,skill_delta='prowess')
xp='scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 5 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 1 } }\n'
add('equal-experience-health-no-transfer',setup=excluded()+'scope:sxat_receiver = { set_variable = { name = sxad_sex_experience value = 5 } } scope:sxat_donor = { set_variable = { name = sxad_sex_experience value = 5 } }',action=PAIR,receiver_delta=0,donor_delta=0,counts=[6,6])
add('only-health-eligible-dispatch',setup=excluded()+xp,action=PAIR,counts=[6,2])
add('health-zero-receiver',receiver_target='0')
add('health-negative-receiver',receiver_target='-1')
add('health-reverse-capacity-boundaries',setup=seed('receiver',-MAX)+seed('donor',MAX)+excluded()+xp,action=PAIR,receiver_balance=-MAX,donor_balance=MAX,counts=[6,2])
assert len(cases)==20
