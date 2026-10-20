"""Finite product policy over the original public CaseClient and shared provider."""
from __future__ import annotations
import re

ARTIFACT = 'ck3_query_player_artifact_personal_use_v1'
ACTOR = 'ck3_query_character_skill_effects_v1'
EQUIP = 'ck3_submit_player_artifact_personal_use_v1'
EQUIP_POST = 'ck3_query_player_artifact_personal_use_action_post_v1'
OPEN_INVENTORY = 'ck3_open_player_inventory_window_v1'
INVENTORY_POST = 'ck3_query_player_inventory_window_open_post_v1'
INVENTORY_CLOSE_QUERY = 'ck3_query_player_inventory_window_close_v1'
CLOSE_INVENTORY = 'ck3_close_player_inventory_window_v1'
INVENTORY_CLOSE_POST = 'ck3_query_player_inventory_window_close_post_v1'
ENSHRINE = 'ck3_enshrine_holy_site_relic_v1'
ACTION_CONTEXT = 'ck3_query_player_holy_site_relic_action_context_v1'
RELIC_CONTEXT = 'ck3_query_player_holy_site_relic_context_v1'
READONLY = frozenset({ARTIFACT, ACTOR, 'ck3_query_player_religion_context_v1',
    'ck3_query_player_holy_site_v1', 'ck3_query_player_holy_site_creation_context_v1',
    'ck3_query_player_holy_site_relic_permissions_v1', ACTION_CONTEXT, RELIC_CONTEXT})
PRESENT = frozenset({'ck3_open_holy_site_creation_window_v1', 'ck3_select_holy_site_creation_type_v1',
    'ck3_select_holy_site_creation_barony_v1', 'ck3_set_holy_site_creation_artifact_selection_v1',
    'ck3_open_holy_site_window_v1', 'ck3_select_holy_site_relic_artifact_v1'})
TOOLS = READONLY | PRESENT | {EQUIP, EQUIP_POST, OPEN_INVENTORY, INVENTORY_POST, ENSHRINE,
    INVENTORY_CLOSE_QUERY,CLOSE_INVENTORY,INVENTORY_CLOSE_POST,
    'ck3_get_capabilities', 'ck3_take_snapshot', 'ck3_query_ingame_ui_window_v1'}
TYPES = frozenset({'site_of_wisdom', 'site_of_martyrs', 'site_of_miracles'})

def require(value, message):
    if not value: raise ValueError(message)

def ref(value):
    return type(value) is int and 0 <= value < 2**32 - 1

def validate(plan):
    require(type(plan) is dict and set(plan) == {'steps'} and type(plan['steps']) is list
        and 1 <= len(plan['steps']) <= 4, 'Finite original public plan required')
    ids = []
    mutations = 0
    for position,step in enumerate(plan['steps']):
        require(type(step) is dict and set(step) <= {'id','tool','args','fresh_revision','continue_on_error','timeout'},
            'No raw, lifecycle or day operations')
        require(type(step.get('id')) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',step['id']), 'Portable unique step ID required')
        ids.append(step['id']); tool = step.get('tool'); args = step.get('args', {})
        require(tool in TOOLS and type(args) is dict and step.get('fresh_revision') is True
            and step.get('continue_on_error') is True, 'Unlisted tool or stale command')
        require(type(step.get('timeout',30)) in (int,float) and 0 < step.get('timeout',30) <= 30, 'Bounded 30 second call required')
        needed, optional = set(), {'expected_revision'}
        if tool == 'ck3_get_capabilities': optional = set()
        elif tool == 'ck3_take_snapshot': optional = {'include_native_command_history'}
        elif tool == ARTIFACT: needed = {'artifact_id'}
        elif tool == ACTOR:
            needed = {'character_id','skill'}
            require(args.get('skill') == 'diplomacy', 'This case reads only the chosen original diplomacy breakdown')
        elif tool == EQUIP:
            needed = {'artifact_id','desired_equipped','expected_slot_index','expected_replacing_artifact_id','policy_positive'}
            require(type(args.get('desired_equipped')) is bool and args.get('policy_positive') is True, 'One positive native equipment intent required')
            require(type(args.get('expected_slot_index')) is int and 0 <= args['expected_slot_index'] <= 63, 'Actual personal slot required')
            require(args.get('expected_replacing_artifact_id') is None, 'This minimal case never displaces another equipped item')
        elif tool == EQUIP_POST: needed = {'artifact_id','expected_intent_sequence'}
        elif tool in {INVENTORY_POST,INVENTORY_CLOSE_POST}: needed = {'expected_intent_sequence'}
        elif tool in {OPEN_INVENTORY,INVENTORY_CLOSE_QUERY,CLOSE_INVENTORY}: pass
        elif tool == ENSHRINE:
            needed = {'holy_site_id','artifact_id','expected_effective_slot_index','expected_replacing_empty','expected_preview_sha256'}
            require(type(args.get('expected_effective_slot_index')) is int and 0 <= args['expected_effective_slot_index'] < 4096,
                'Actual source-bound shrine slot required')
            require(args.get('expected_replacing_empty') is True and type(args.get('expected_preview_sha256')) is str
                and re.fullmatch('[0-9a-f]{64}',args['expected_preview_sha256']), 'Only a freshly quoted empty shrine slot')
        elif tool == 'ck3_query_player_holy_site_v1': optional.add('holy_site_id')
        elif tool in {'ck3_open_holy_site_window_v1', RELIC_CONTEXT, 'ck3_query_player_holy_site_relic_permissions_v1'}:
            needed = {'holy_site_id'}
            if tool.endswith('permissions_v1'): optional.add('artifact_id')
        elif tool in {ACTION_CONTEXT,'ck3_select_holy_site_relic_artifact_v1'}: needed = {'holy_site_id','artifact_id'}
        elif tool == 'ck3_query_ingame_ui_window_v1':
            needed = {'window_kind'}
            require(args.get('window_kind') in {'holy_site','holy_site_creation','inventory'}, 'Only actual selected original windows')
        elif tool == 'ck3_select_holy_site_creation_type_v1':
            needed = {'type_key'}; require(args.get('type_key') in TYPES, 'Only original current type rows')
        elif tool == 'ck3_select_holy_site_creation_barony_v1': needed = {'barony_title_id'}
        elif tool == 'ck3_set_holy_site_creation_artifact_selection_v1':
            needed = {'artifact_id','selected'};require(type(args.get('selected')) is bool, 'Exact UI selected state required')
        require(needed <= set(args) <= needed | optional, 'Tool argument shape differs: '+str(tool))
        for name in ('artifact_id','holy_site_id','character_id','barony_title_id'):
            require(name not in args or ref(args[name]), 'Actual complete reference required: '+name)
        if 'expected_revision' in args: require(type(args['expected_revision']) is int and args['expected_revision'] > 0, 'Fresh public revision required')
        if 'expected_intent_sequence' in args: require(type(args['expected_intent_sequence']) is int and args['expected_intent_sequence'] > 0, 'Actual original native sequence required')
        require(args.get('include_native_command_history',False) is False, 'No command history export')
        if tool in {EQUIP,ENSHRINE,OPEN_INVENTORY,CLOSE_INVENTORY}: mutations += 1
        if tool in PRESENT:
            require(position+1 < len(plan['steps']), 'Original presentation requires immediate independent readback')
            following = plan['steps'][position+1]
            expected = ('ck3_query_ingame_ui_window_v1' if tool == 'ck3_open_holy_site_window_v1' else
                ACTION_CONTEXT if tool == 'ck3_select_holy_site_relic_artifact_v1' else
                'ck3_query_player_holy_site_creation_context_v1')
            require(following.get('tool') == expected, 'Original presentation readback differs')
            if tool == 'ck3_open_holy_site_window_v1':
                require(following.get('args',{}).get('window_kind') == 'holy_site', 'Wrong original site window readback')
            if tool == 'ck3_select_holy_site_relic_artifact_v1':
                require(all(following.get('args',{}).get(key) == args[key] for key in ('holy_site_id','artifact_id')),
                    'Selected relic readback crossed original full IDs')
    require(len(ids) == len(set(ids)), 'Duplicate command IDs are never replayed')
    require(mutations <= 1, 'One reviewed world/UI-opening intent per original public batch')
    return {'validated':True,'submitted':False,'automatic_retry':False}
