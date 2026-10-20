"""Finite public CaseClient policy for the two independent artifact arms."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from faith_e02_artifact_pair_contract import Object, array, boolean, encode, field, integer, mapping, read, require, sha, text

KNIGHT = 'ck3_query_character_knight_effectiveness_v1'
ITEM = 'ck3_query_player_artifact_personal_use_v1'
EQUIP = 'ck3_submit_player_artifact_personal_use_v1'
EQUIP_POST = 'ck3_query_player_artifact_personal_use_action_post_v1'
CREATION = 'ck3_query_player_holy_site_creation_context_v1'
ACTION = 'ck3_query_player_holy_site_relic_action_context_v1'
RELIC = 'ck3_query_player_holy_site_relic_context_v1'
PERMISSION = 'ck3_query_player_holy_site_relic_permissions_v1'
DONATE = 'ck3_enshrine_holy_site_relic_v1'
OPEN = 'ck3_open_player_inventory_window_v1'
OPEN_POST = 'ck3_query_player_inventory_window_open_post_v1'
CLOSE = 'ck3_close_player_inventory_window_v1'
CLOSE_QUERY = 'ck3_query_player_inventory_window_close_v1'
CLOSE_POST = 'ck3_query_player_inventory_window_close_post_v1'
WINDOW = 'ck3_query_ingame_ui_window_v1'
SITE_OPEN = 'ck3_open_holy_site_window_v1'
SELECT_ITEM = 'ck3_select_holy_site_relic_artifact_v1'
DRAFT = frozenset({'ck3_open_holy_site_creation_window_v1', 'ck3_select_holy_site_creation_type_v1',
                   'ck3_select_holy_site_creation_barony_v1', 'ck3_set_holy_site_creation_artifact_selection_v1'})
READONLY = frozenset({KNIGHT, ITEM, EQUIP_POST, CREATION, ACTION, RELIC, PERMISSION, OPEN_POST,
                      CLOSE_QUERY, CLOSE_POST})
OPTIN_READONLY = frozenset({KNIGHT, ITEM, CREATION, ACTION, RELIC, PERMISSION})
TOOLS = READONLY | DRAFT | {EQUIP, DONATE, OPEN, CLOSE, WINDOW, SITE_OPEN, SELECT_ITEM, 'ck3_take_snapshot'}
LIFECYCLE = frozenset({'ck3_query_campaign_root_context_v1', 'ck3_query_current_event_window_context_v1',
    'ck3_query_pending_character_interaction_context_v1', 'ck3_reply_pending_character_interaction',
    'ck3_select_event_option', 'ck3_query_normal_exit_context_v1', 'ck3_request_normal_exit_v1',
    'ck3_observe_normal_exit_v1', 'ck3_execute_step'})
# The existing public relic flag is an indivisible four-tool registration bundle.
# Its remove/slot-selector tools are declared for registration and remain forbidden by validate().
REQUIRED = TOOLS | LIFECYCLE | {'ck3_remove_holy_site_relic_v1', 'ck3_set_holy_site_relic_slot_selection_v1'}


def step(name: str, tool: str, args: Object | None = None) -> Object:
    return {'id': name, 'tool': tool, 'args': {} if args is None else args,
            'fresh_revision': True, 'continue_on_error': True, 'timeout': 20}


def validate(plan: object) -> Object:
    outer = mapping(plan, 'finite pair queue')
    require(set(outer) == {'steps'}, 'No lifecycle/raw/day injection')
    rows = array(outer['steps'], 'public steps')
    require(1 <= len(rows) <= 3, 'At most three bounded original calls per batch')
    ids: set[str] = set()
    changes = 0
    for index, value in enumerate(rows):
        row = mapping(value, 'public step')
        require(set(row) == {'id', 'tool', 'args', 'fresh_revision', 'continue_on_error', 'timeout'}, 'Exact public step fields')
        name = text(row['id'], 'control ID')
        require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}', name) is not None and name not in ids, 'Unique portable control ID')
        ids.add(name)
        tool = text(row['tool'], 'tool')
        if tool in DRAFT | {EQUIP, DONATE, OPEN, CLOSE, SITE_OPEN, SELECT_ITEM}: changes += 1
        require(changes <= 1, 'One mutation/presentation per batch; an unknown first action cannot fall through to another')
        require(tool in TOOLS and row['fresh_revision'] is True and row['continue_on_error'] is True, 'Finite fresh public calls only')
        require(integer(row['timeout'], 'call timeout', 1, 20) == 20, 'Fixed bounded timeout')
        args = mapping(row['args'], 'tool arguments')
        needed: set[str] = set()
        optional = {'expected_revision'}
        if tool == 'ck3_take_snapshot': optional = {'include_native_command_history'}
        elif tool == KNIGHT: needed = {'character_id'}
        elif tool == ITEM: needed = {'artifact_id'}
        elif tool == EQUIP:
            needed = {'artifact_id', 'desired_equipped', 'expected_slot_index', 'expected_replacing_artifact_id', 'policy_positive'}
            require(args.get('desired_equipped') is True and args.get('policy_positive') is True, 'Personal arm equips once, never toggles or unequips')
        elif tool == EQUIP_POST: needed = {'artifact_id', 'expected_intent_sequence'}
        elif tool in {OPEN_POST, CLOSE_POST}: needed = {'expected_intent_sequence'}
        elif tool in {SITE_OPEN, RELIC}: needed = {'holy_site_id'}
        elif tool == PERMISSION:
            needed = {'holy_site_id'}
            optional.add('artifact_id')
        elif tool in {ACTION, SELECT_ITEM}: needed = {'holy_site_id', 'artifact_id'}
        elif tool == DONATE:
            needed = {'holy_site_id', 'artifact_id', 'expected_effective_slot_index', 'expected_replacing_empty',
                      'expected_preview_sha256', 'expected_replacing_artifact_id'}
            require(args.get('expected_replacing_empty') is True and args.get('expected_replacing_artifact_id') is None,
                    'This controlled experiment never replaces an existing site relic')
            sha(args.get('expected_preview_sha256'))
        elif tool == WINDOW:
            needed = {'window_kind'}
            require(args.get('window_kind') in ('inventory', 'holy_site', 'holy_site_creation'), 'Finite original window kinds')
        elif tool == 'ck3_select_holy_site_creation_type_v1':
            needed = {'type_key'}
            require(args.get('type_key') in ('site_of_wisdom', 'site_of_martyrs', 'site_of_miracles'), 'Finite original type keys')
        elif tool == 'ck3_select_holy_site_creation_barony_v1': needed = {'barony_title_id'}
        elif tool == 'ck3_set_holy_site_creation_artifact_selection_v1':
            needed = {'artifact_id', 'selected'}
            require(boolean(args.get('selected'), 'selected') is True, 'Only positive explicit draft selection')
        require(needed <= set(args) <= needed | optional, 'Exact allowed arguments for ' + tool)
        if 'expected_revision' in args: integer(args['expected_revision'], 'revision', 1)
        for key in ('character_id', 'artifact_id', 'holy_site_id', 'barony_title_id'):
            if key in args: integer(args[key], key, 0, 2**32-2)
        for key in ('expected_slot_index', 'expected_effective_slot_index'):
            if key in args: integer(args[key], key, 0, 63 if tool == EQUIP else 4095)
        if 'expected_replacing_artifact_id' in args and args['expected_replacing_artifact_id'] is not None:
            integer(args['expected_replacing_artifact_id'], 'replacement', 0, 2**32-2)
        if 'expected_intent_sequence' in args: integer(args['expected_intent_sequence'], 'original observed sequence', 1)
        if tool == 'ck3_take_snapshot': require(args.get('include_native_command_history', False) is False, 'No history export')
        if tool in DRAFT | {SITE_OPEN, SELECT_ITEM}:
            require(index + 1 < len(rows), 'Original presentation requires immediate independent query')
            next_step = mapping(rows[index + 1], 'presentation readback')
            expected = CREATION if tool in DRAFT else WINDOW if tool == SITE_OPEN else ACTION
            require(next_step.get('tool') == expected, 'Independent presentation readback missing')
            next_args = mapping(field(next_step, 'args'), 'independent readback arguments')
            if tool == SITE_OPEN: require(next_args.get('window_kind') == 'holy_site', 'Read back the same holy-site window')
            if tool == SELECT_ITEM:
                require(next_args.get('holy_site_id') == args['holy_site_id'] and next_args.get('artifact_id') == args['artifact_id'],
                        'Read back the exact selected artifact/site')
    return {'schema': 'faith-e02-artifact-pair-queue-v1', 'validated': True, 'submitted': False,
            'automatic_retry': False, 'create_or_adopt_allowed': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
    print(encode(validate(read(args.plan))).decode('utf-8'), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
