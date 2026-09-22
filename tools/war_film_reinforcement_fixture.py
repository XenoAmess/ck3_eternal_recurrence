"""Offline qualification of a three-unit reinforcement capture bundle.

This never starts CK3 or constructs a save. It rejects the historical singleton
requester fixture before a separately authorized daily observation window.
Accepted input is still only a declared, hash-bound capture bundle, not a native
assignment, ETA, rejoin, or semantic proof. Do not invent missing IDs or frames.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXE_SHA256 = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'
SCHEMA = 'xar.war-film-reinforcement-capture-bundle.v1'
STAMP = ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')


def integer(value, minimum=0):
    return type(value) is int and minimum <= value < 0xffffffff


def required(ok, label):
    if not ok:
        raise ValueError(label)


def template():
    return {
        'schema': SCHEMA, 'evidence_kind': 'unfilled-template',
        'exe_sha256': EXE_SHA256,
        'roles': {'withdrawn_helper': None, 'requester_anchor': None, 'requester_partner': None},
        'combat_id': None, 'province_id': None, 'side': None,
        'snapshot_before': None, 'snapshot_after': None,
        'baseline_battle_transition': None, 'battle_transition': None,
        'units': [],
        'instructions': 'Fill from exact existing native query responses and semantic army rows. Each units entry is {public_cunit_id, semantic_army, first, second}; first/second are unmodified query response objects. No manual replacement of unavailable memberships. Baseline roster must precede withdrawal; current bundle follows production AI membership reopening.',
    }


def qualify(bundle):
    required(isinstance(bundle, dict) and bundle.get('schema') == SCHEMA, 'unsupported bundle schema')
    required(bundle.get('evidence_kind') in {'recorded-native-responses', 'synthetic-offline-test'}, 'unfilled or unsupported evidence kind')
    required(bundle.get('exe_sha256', '').lower() == EXE_SHA256, 'wrong executable identity')
    roles = bundle.get('roles', {})
    ids = [roles.get(name) for name in ('withdrawn_helper', 'requester_anchor', 'requester_partner')]
    required(all(integer(v, 1) for v in ids) and len(set(ids)) == 3, 'three distinct generation-bearing CUnit IDs required')
    helper_id, anchor_id, partner_id = ids
    combat, province, side = (bundle.get(k) for k in ('combat_id', 'province_id', 'side'))
    required(integer(combat, 1) and integer(province, 1) and side in {'attacker', 'defender'}, 'typed combat/province/side required')
    before, after = bundle.get('snapshot_before'), bundle.get('snapshot_after')
    required(isinstance(before, dict) and isinstance(after, dict), 'snapshot bracket required')
    required(before.get('paused') is True and after.get('paused') is True, 'capture must be paused at both ends')
    required(all(before.get(k) is not None and before[k] == after.get(k) for k in STAMP), 'snapshot bracket changed or lacks identity')
    for key in ('revision', 'native_revision', 'date_raw'):
        required(integer(before.get(key)), 'typed snapshot ' + key + ' required')
    required(isinstance(before.get('episode_run_id'), str) and bool(before['episode_run_id']), 'episode identity required')

    rosters = []
    for name in ('baseline_battle_transition', 'battle_transition'):
        battle = bundle.get(name)
        required(isinstance(battle, dict) and battle.get('status') == 'available' and battle.get('battle_transition_ready') is True, name + ' unavailable')
        required(battle.get('combat_id') == combat and battle.get('province_id') == province, name + ' combat identity differs')
        own = battle.get(side + '_public_cunit_ids_in_stored_order')
        other = battle.get(('defender' if side == 'attacker' else 'attacker') + '_public_cunit_ids_in_stored_order')
        required(isinstance(own, list) and isinstance(other, list), name + ' side rosters required')
        required(all(integer(v, 1) for v in own + other) and len(set(own + other)) == len(own + other), name + ' malformed or duplicate roster')
        rosters.append((own, other))
    required(all(v in rosters[0][0] for v in ids), 'all three must have belonged to the same old CombatID side before withdrawal')
    required(anchor_id in rosters[1][0] and partner_id in rosters[1][0] and helper_id not in rosters[1][0] + rosters[1][1], 'after withdrawal both anchors must remain; helper must have left old combat')

    unit_rows = bundle.get('units')
    required(isinstance(unit_rows, list), 'units array required')
    selected = {}
    for row in unit_rows:
        required(isinstance(row, dict) and integer(row.get('public_cunit_id'), 1), 'invalid unit record')
        ident = row['public_cunit_id']
        required(ident not in selected, 'duplicate unit record')
        selected[ident] = row
    required(all(v in selected for v in ids), 'all three native unit capture pairs required')
    frames = {}
    for ident in ids:
        row = selected[ident]
        army = row.get('semantic_army', {})
        required(army.get('unit_id') == ident and army.get('controllable') is False, 'selected unit must be under production AI control')
        first, second = row.get('first'), row.get('second')
        required(isinstance(first, dict) and isinstance(second, dict), 'two native responses required')
        required(integer(first.get('query_sequence')) and integer(second.get('query_sequence')) and second['query_sequence'] > first['query_sequence'], 'query sequences must increase')
        for response in (first, second):
            for target, source in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'), ('queried_native_revision', 'native_revision'), ('snapshot_revision', 'revision')):
                required(response.get(target) == before[source], 'query bound to a different snapshot')
        frame = first.get('battle_reinforcement_assignment')
        required(isinstance(frame, dict) and frame == second.get('battle_reinforcement_assignment'), 'native pair differs')
        required(frame.get('status') == 'available' and frame.get('battle_reinforcement_assignment_ready') is True and frame.get('unavailable_reason') is None, 'native membership unavailable; do not promote a handoff acknowledgement')
        required(frame.get('selected_public_cunit_id') == ident and integer(frame.get('selected_native_carmy_id'), 1) and integer(frame.get('coordinator_id'), 1), 'native selected identity invalid')
        required(frame.get('observed_date_raw') == before['date_raw'], 'native frame date differs')
        stack, sub = frame.get('unit_stack_stored_index'), frame.get('subunit_stored_index')
        required(integer(stack) and integer(sub), 'parent/subunit ordinal missing')
        order = frame.get('native_order', {})
        parent = order.get('parent_subunits_in_stored_order')
        required(isinstance(parent, list) and sub < len(parent), 'invalid parent subunit vector')
        flattened = []
        for member in parent:
            members = member.get('public_cunit_ids_in_stored_order') if isinstance(member, dict) else None
            required(isinstance(members, list) and bool(members) and all(integer(v, 1) for v in members), 'empty or untyped native subunit')
            flattened.extend(members)
        required(len(set(flattened)) == len(flattened) and ident in parent[sub]['public_cunit_ids_in_stored_order'], 'duplicate membership or selected backlink differs')
        search = order.get('support_search_province_ids_in_stored_order')
        required(isinstance(search, list) and all(integer(v, 1) for v in search), 'untyped native support search vector')
        frames[ident] = frame

    helper, anchor, partner = (frames[v] for v in ids)
    required(len({frame['selected_native_carmy_id'] for frame in frames.values()}) == 3, 'distinct CUnits must have distinct selected CArmy bindings')
    # A CArmy identity belongs to the selected unit. It is not a parent-stack key.
    key = lambda frame: (frame['coordinator_id'], frame['unit_stack_stored_index'])
    required(key(anchor) == key(partner), 'requester pair must share coordinator plus parent stack ordinal')
    required(anchor['subunit_stored_index'] != partner['subunit_stored_index'], 'two CUnits merged into one subunit do not repair singleton asking')
    required(anchor['native_order']['parent_subunits_in_stored_order'] == partner['native_order']['parent_subunits_in_stored_order'], 'same parent claims differ between query frames')
    required(len(anchor['native_order']['parent_subunits_in_stored_order']) >= 2, 'singleton requester parent cannot ask')
    required(helper['coordinator_id'] == anchor['coordinator_id'] and key(helper) != key(anchor), 'this minimal experiment requires an independent helper stack under the same coordinator')
    required(province in helper['native_order']['support_search_province_ids_in_stored_order'], 'requester province absent from helper support-search vector')
    for ident in (anchor_id, partner_id):
        army, frame = selected[ident]['semantic_army'], frames[ident]
        assignment = frame.get('assignment', {})
        required(army.get('in_combat') is True and army.get('current_province_id') == province, 'remaining requester unit not in old combat province')
        required(assignment.get('active_combat_id') == combat and assignment.get('combat_binding_status') == 'already_in_active_combat', 'remaining requester unit not bound to old CombatID')
    army = selected[helper_id]['semantic_army']
    required(army.get('in_combat') is False and army.get('retreating') is False, 'helper must finish withdrawal before candidate window')
    required(helper.get('signal', {}).get('asking_for_help') is False, 'asking helper is ineligible for the intended matching branch')
    required(helper.get('signal', {}).get('assigned_to_help') is False and helper.get('assignment', {}).get('assignment_target_province_id') is None, 'initial helper must be unassigned so the window can observe a transition')
    return {
        'schema': 'xar.war-film-reinforcement-fixture-check.v1',
        'result': 'structural-preconditions-met', 'live_execution_performed': False,
        'native_assignment_proven': False, 'eta_proven': False, 'same_combat_join_proven': False,
        'evidence_kind': bundle['evidence_kind'],
        'requester_parent_key': list(key(anchor)),
        'requester_subunit_count': len(anchor['native_order']['parent_subunits_in_stored_order']),
        'helper_parent_key': list(key(helper)),
        'minimum_missing_observation': [
            'new daily-tick asking bit and valid demand, not only AI handoff or parent membership',
            'helper assignment bit transition plus target Province, same revision and AI control',
            'aligned native route/direct target and typed assignment ETA',
            'later same CombatID/side roster and helper CArmy binding; stop if combat ends first',
        ],
        'limitation': 'This checks supplied capture records, not their authenticity or a causal native match. At least three CUnits is necessary for this fixture, not sufficient for success. Busy/reserve/power and candidate competition remain native conditions.',
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--template', action='store_true')
    mode.add_argument('--bundle', type=Path)
    p.add_argument('--output', type=Path, help='exclusive create; omit for JSON stdout')
    args = p.parse_args(argv)
    code = 0
    try:
        if args.template:
            result = template()
        else:
            raw = args.bundle.read_bytes()
            result = qualify(json.loads(raw.decode('utf-8-sig')))
            result['bundle_sha256'] = hashlib.sha256(raw).hexdigest()
            result['bundle_path'] = str(args.bundle.resolve())
    except (ValueError, OSError, TypeError, KeyError) as exc:
        result = {'result': 'structural-preconditions-not-met', 'reason': str(exc), 'live_execution_performed': False}
        code = 2
    body = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as out:
            out.write(body)
    else:
        print(body, end='')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
