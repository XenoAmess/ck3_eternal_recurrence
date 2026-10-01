"""Pure additive validation of actual-current death commit ancestry.

The frozen READY source/PID/receipt and monitor projectors are prerequisites.
This validates raw new fields, and never joins cases by saved endpoints.
"""
from __future__ import annotations

CONTEXT_KIND = 'currently_executing_original_264BCB0_same_thread'


def pointer_token(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.startswith('process-local-0x'):
        return int(value[len('process-local-0x'):], 16)
    raise ValueError('unknown raw process-local token encoding')


def correlate_signature_commits(monitor: dict, journal: dict, *, victim: int, related: int) -> dict:
    for obj in (monitor, journal):
        if obj.get('failure_flags') != 0 or obj.get('truncated') is not False:
            raise ValueError('original collector failed/truncated')
        if obj['character_ids'] != [victim, related]:
            raise ValueError('same full character scope required')
        if any(r['failure_flags'] != 0 for r in obj['records']):
            raise ValueError('individual original journal record failed')
    if monitor['whole_game_mutable_bundle_complete'] is not False or journal['global_mutable_bundle_complete'] is not False:
        raise ValueError('whole-game complete flag was raised')
    bindings = {p['definition_key']: p for p in monitor['prearmed_event_definitions']}
    pairs = {}
    for r in journal['records']:
        if r['boundary'] in ('death_commit_enter', 'death_commit_return'):
            kind = r['boundary'].rsplit('_', 1)[1]
            pair = pairs.setdefault(r['invocation'], {})
            if kind in pair:
                raise ValueError('duplicate original commit invocation edge')
            pair[kind] = r
    if any(set(pair) != {'enter', 'return'} for pair in pairs.values()):
        raise ValueError('incomplete actual native commit')
    case_commits = {inv: pair for inv, pair in pairs.items() if pair['enter']['death_victim_id'] == victim}
    write_pairs = {}
    for r in monitor['records']:
        if r['boundary'] in ('variable_write_enter', 'variable_write_return'):
            kind = r['boundary'].rsplit('_', 1)[1]
            pair = write_pairs.setdefault(r['invocation'], {})
            if kind in pair:
                raise ValueError('duplicate original write invocation edge')
            pair[kind] = r
    results = []
    for invocation, pair in write_pairs.items():
        if set(pair) != {'enter', 'return'}:
            raise ValueError('incomplete original write')
        entered, returned = pair['enter'], pair['return']
        p = entered.get('event_producer', {})
        result = {'write_invocation': invocation, 'character_id': entered['character_id'],
                  'notification_key': p.get('definition_key') if p.get('identity_read') else None,
                  'specific_victim_correlation': 'pending', 'time_resolution': 'actual-original-call-lifecycle'}
        contexts = [p.get('activation_death_commit_context'), entered.get('current_death_commit_context'),
                    returned.get('event_producer', {}).get('activation_death_commit_context'),
                    returned.get('current_death_commit_context')]
        if p.get('identity_read') is not True:
            result['gap'] = 'write has no actual matched notification immediate producer'
            results.append(result)
            continue
        if not all(isinstance(c, dict) and c.get('read') is True for c in contexts):
            result['gap'] = 'actual notification activation or write is outside a current scoped original death commit'
            results.append(result)
            continue
        first = contexts[0]
        if any(c != first for c in contexts[1:]):
            raise ValueError('notification activation/current write commit tuple differs')
        if not (first['context_kind'] == CONTEXT_KIND and first['managed_daily_sequence_token'] == journal['managed_daily_sequence_token'] and
                first['thread_id'] == entered['thread_id'] == returned['thread_id'] and
                first['native_date_raw'] == entered['date_raw'] == returned['date_raw'] and
                first['combat_id'] == journal['combat_id'] and first['victim_full_identity_matches'] is True and
                first['killer_full_identity_matches'] is True and first['manager_token'] > 0 and
                first['victim_token'] > 0 and first['killer_token'] > 0 and first['date_argument_token'] > 0 and
                first['reason_token'] > 0 and first['reason_key_read'] is True):
            raise ValueError('active original commit identity/token/thread/date/typed tuple invalid')
        if first['victim_id'] != victim or first['killer_id'] != related:
            result['gap'] = 'actual current commit belongs to a different scoped victim/killer tuple'
            result['observed_current_commit'] = first
            results.append(result)
            continue
        if first['invocation'] not in case_commits:
            result['gap'] = 'no same-run victim commit invocation matches current original call'
            results.append(result)
            continue
        commit = case_commits[first['invocation']]
        left, right = commit['enter'], commit['return']
        fields = {'victim_id': 'death_victim_id', 'killer_id': 'death_killer_id',
                  'requested_death_date_raw': 'requested_death_date_raw', 'artifact_id': 'requested_death_artifact_id'}
        if not all(first[ctx_key] == edge[record_key] for ctx_key, record_key in fields.items() for edge in (left, right)):
            raise ValueError('active original commit tuple differs from its actual native invocation')
        tokens = {'reason_token': 'requested_death_reason_token', 'artifact_token': 'requested_death_artifact_token'}
        if not all(pointer_token(first[ck]) == pointer_token(edge[rk]) for ck, rk in tokens.items() for edge in (left, right)):
            raise ValueError('active original commit pointer tuple differs from actual journal')
        if not (left['thread_id'] == right['thread_id'] == first['thread_id'] and
                left['native_date_raw'] == right['native_date_raw'] == first['native_date_raw'] and
                left['parent_invocation'] == right['parent_invocation'] == first['parent_invocation'] and
                left['sequence'] < right['sequence'] and first['reason_key'] == 'death_battle'):
            raise ValueError('active original commit journal date/order/reason differs')
        if first['artifact_actual_null'] is True:
            if first['artifact_token'] != 0 or first['artifact_id'] != -1:
                raise ValueError('actual null artifact contradicts original tuple')
        elif not (first['artifact_actual_null'] is False and first['artifact_token'] > 0 and first['artifact_id_read'] is True and first['artifact_id'] > 0 and
                  left['requested_artifact_id_read'] is True and right['requested_artifact_id_read'] is True):
            raise ValueError('nonnull artifact lacks independent original full-ID reads')
        bound = bindings.get(p['definition_key'])
        metadata = ('definition_token', 'definition_index', 'definition_id', 'runtime_stats_ordinal',
                    'compiled_immediate_root_token', 'definition_vtable_rva', 'root_vtable_rva', 'root_hash',
                    'original_execute_rva', 'children_data_token', 'children_capacity', 'children_count')
        if bound is None or any(p[k] != bound[k] for k in metadata):
            raise ValueError('actual root/children identity differs from initialized original definition')
        if entered['character_id'] != related:
            result['gap'] = 'actual write target is not this case killer'
        else:
            result['specific_victim_correlation'] = 'closed'
            result['same_current_original_commit'] = first
            result['commit_sequence_enter'] = left['sequence']
            result['commit_sequence_return'] = right['sequence']
            result['allowed_statement'] = 'During this original victim/killer death commit, this actual notification immediate produced the killer signature variable write.'
        results.append(result)
    return {'schema_version': 2, 'kind': 'SAME_RUN_CURRENT_ORIGINAL_COMMIT_CORRELATION',
            'specific_victim_trigger_closed': bool(results) and all(r['specific_victim_correlation'] == 'closed' for r in results),
            'writes': results, 'same_run_victim_commit_count': len(case_commits),
            'unique_case_victim_commit_observed': len(case_commits) == 1,
            'sole_cause_proven': False, 'dead_character_named_scope_decoded': False,
            'whole_game_mutable_bundle_complete': False,
            'limits': 'Checks synchronous original-call ancestry per write. The complete case death request/queue/commit chain and named scopes are separate.'}
