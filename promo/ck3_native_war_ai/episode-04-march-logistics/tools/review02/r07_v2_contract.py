"""Offline R07-v2 design and one-window payment reader; no runtime entry points.

This reader validates a source-qualified journal slice, not the full two-arm film
experiment. Its output always leaves full_v2_qualified false. Root must seal and
review the independent common-S0, route and exact-day evidence described by the
versioned design before crediting R07-v2. V1 evidence is never relabelled.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

SCHEMA = 'xar.e04.r07-boarding-two-arm-design.v2'
READER_SCHEMA = 'xar.e04.r07-v2-window-slice.v1'
JOURNAL = 'war_payment_observations_v1'


def need(value, message):
    if not value:
        raise ValueError(message)


def integer(value, low=0):
    return type(value) is int and value >= low


def sha(value, length=64):
    return (isinstance(value, str) and len(value) == length
            and all(c in '0123456789abcdef' for c in value))


def read_json(path, limit=16 * 1024 * 1024):
    path = Path(path)
    need(path.suffix.lower() == '.json', 'only an explicit JSON file is accepted')
    need(0 < path.stat().st_size <= limit, 'explicit JSON exceeds bounded read')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def validate_design(value):
    need(value.get('schema') == SCHEMA, 'not an R07-v2 design')
    need(value.get('original_R07_v1_qualified') is False,
         'v1 closure must not be inferred from the revised design')
    need(value.get('future_actual_status') == 'pending', 'design is not observation')
    timing = value['timing']
    need(timing == {'nominal_embark_days': 30, 'margin_days': 2,
                    'max_natural_days_per_arm': 32, 'exact_day_hours': 24},
         'v2 bounded timing differs; issue another explicit revision instead')
    source = value['source_contract']
    need(source['game_version'] == '1.20.0.4' and source['steam_build'] == 25734779,
         'unsupported exact game')
    need(sha(source['executable_sha256']), 'exact executable source pin required')
    # A planned future build is not forced to have an invented actual DLL/PID.
    need(source['native_build_binding'] == 'same_actual_source_and_dll_for_both_arms',
         'both arms must use the same actual native build')
    for key in ('source_head', 'bridge_dll_sha256'):
        need(source[key] is None or sha(source[key], 40 if key == 'source_head' else 64),
             'invalid future/source pin')
    seed = value['common_stationary_S0']
    need(sha(seed['save_sha256']) and integer(seed['save_bytes'], 1)
         and integer(seed['date_raw'], 1) and seed['save_origin'] == 'normal_checkpoint',
         'common S0 must refer to a real normal checkpoint receipt')
    need(seed['independent_loaded_stationary_readback'] == 'required_in_each_arm',
         'saving or copying S0 is not an independent loaded baseline')
    need(value['arms'] == {'control': 'fresh_normal_load_stationary_no_Move',
                           'treatment': 'fresh_normal_load_one_new_normal_Move'},
         'both independent normal-load arms are required')
    screen = value['army_screening']
    need(screen['candidate_public_army_ids'] == [93, 94, 95]
         and screen['selection_status'] == 'pending_actual_whole_DATA_and_native_legal'
         and screen['event_troop_strength_is_not_assumed'] is True,
         'event-army source applicability must be independently established')
    journal = value['journals']
    need(journal['natural_hard_stop'] == 56 and journal['payment_hard_stop'] == 384
         and journal['renewal_review_at_natural'] == 48
         and journal['renewal_review_at_payment'] == 320
         and journal['renewal_is_explicit_paused_archive_disable_clear_enable'] is True
         and journal['cross_segment_sequence_join'] is False,
         'journal loss/segment policy differs')
    need(value['claims']['boarding_basis'] == 'source_qualified_positive_SUB_callbacks'
         and value['claims']['net_gold_difference_is_boarding_cost'] is False
         and value['claims']['maintenance_attribution'] == 'unclosed',
         'net wallet changes or generic context cannot become maintenance costs')
    return {'schema': SCHEMA, 'design_valid_for_observation_preparation': True,
            'future_actual_status': 'pending', 'actual_runtime_admission': False,
            'full_v2_qualified': False, 'original_R07_v1_qualified': False}


def load_normalizer(repo_root):
    repo = Path(repo_root).resolve()
    need((repo / 'ck3_autonomous_player/src').is_dir(), 'explicit repository root required')
    sys.path[:0] = [str(repo), str(repo / 'ck3_autonomous_player/src')]
    from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_journal
    return normalize_journal


def snapshot_body(packet, binding, date):
    need(packet.get('machine_id') == binding['machine_id']
         and packet.get('is_error') is False
         and packet.get('request', {}).get('tool') == 'ck3_take_snapshot',
         'snapshot source machine/tool/error differs')
    s = packet['body']; d = s.get('diagnostics') or {}
    need(s.get('paused') is True and s.get('map_ready') is True
         and s.get('date_raw') == date and s.get('episode_run_id') == binding['episode']
         and d.get('bridge_pid') == binding['pid']
         and d.get('connection_generation') == binding['generation']
         and s.get('played_character', {}).get('character_id') == binding['actor_id'],
         'independent paused process/actor/episode/date differs')
    return s


def consume_window(packet, snapshot_packet, binding, normalize_journal):
    """One exact response only; explicit segment, no glob/latest or auto-clear.

    The caller retains the full response. Returned amounts are callback requests,
    not net treasury changes. No absence-of-fee or full-experiment claim is made.
    """
    for key in ('pid', 'create_filetime', 'generation', 'actor_id', 'unit_id',
                'payment_epoch', 'window_id', 'date_raw'):
        need(integer(binding.get(key), 1), 'missing actual segment binding: ' + key)
    need(isinstance(binding.get('segment_id'), str) and binding['segment_id'],
         'an explicit local segment identity is required')
    need(isinstance(binding.get('machine_id'), str) and binding['machine_id']
         and isinstance(binding.get('episode'), str) and binding['episode'],
         'explicit producer machine and actual episode required')
    s = snapshot_body(snapshot_packet, binding, binding['date_raw'])
    need(packet.get('machine_id') == binding['machine_id']
         and packet.get('is_error') is False
         and packet.get('request', {}).get('tool') ==
         'ck3_query_war_cash_current_resources_private_v1', 'cash source differs')
    args = packet['request']['arguments']; body = packet['body']
    need(args.get('payment_sampling') == 'query'
         and args.get('expected_revision') == s['revision'],
         'cash request is not bound to the explicit fresh snapshot')
    need(body.get('date_raw') == binding['date_raw']
         and body.get('snapshot_revision') == s['native_revision'],
         'cash is not from this native frame')
    control = body.get('war_payment_control_v1') or {}
    need(control.get('requested') == 'query' and control.get('accepted') is True,
         'read-only payment query not accepted')
    j = normalize_journal(body[JOURNAL], snapshot=s, machine_id=binding['machine_id'])
    c = j['current_session']; p = j['sampling']; n = j['natural_journal_status']
    need((c['pid'], c['process_create_time_100ns'], c['connection_generation'],
          c['player_character_full_id'], c['controlled_window_id'], p['epoch']) ==
         (binding['pid'], binding['create_filetime'], binding['generation'],
          binding['actor_id'], binding['window_id'], binding['payment_epoch']),
         'actual own-process/window/epoch identity differs')
    need(j['installed'] and not j['install_failure_flags'] and j['controlled_window_admitted']
         and p['available'] and p['capture_enabled'] and not p['busy'] and not p['active_captures']
         and j['read_complete'] and not j['overwritten'] and not j['publication_failures']
         and n['read_complete'] and not n['overwritten_records'] and not n['failed_appends'],
         'lost, disabled or incomplete journal is not an observed zero')
    need(n['retained_records'] <= 56 and p['retained_records'] <= 384,
         'retain evidence and stop at the declared ring stopline')
    previous = binding.get('previous_latest_sequence', 0)
    need(integer(previous) and previous <= j['latest_sequence'], 'within-segment sequence rollback')
    need(j['latest_sequence'] - previous <= 512, 'previous sequence is not this retained segment baseline')
    new_records = [r for r in j['records'] if r['journal_sequence'] > previous]
    need([r['journal_sequence'] for r in new_records] ==
         list(range(previous + 1, j['latest_sequence'] + 1)), 'within-segment record gap')
    by_sequence = {r['journal_sequence']: r for r in j['records']}
    boarding = []
    other_army = []
    for q in j['qualified_boarding_debits']:
        if q['writer_sequence'] <= previous:
            continue
        t = by_sequence[q['transition_sequence']]
        match = all(t[k]['requested_unit_id'] == binding['unit_id'] for k in ('before', 'after'))
        item = {'segment_id': binding['segment_id'], 'payment_epoch': p['epoch'],
                'controlled_window_id': c['controlled_window_id'], **q,
                'transition_army_full_id': t['before']['army_id'],
                'requested_public_unit_id': t['before']['requested_unit_id'],
                'transition_province_id': t['before']['province_id']}
        (boarding if match else other_army).append(item)
    generic = [{'segment_id': binding['segment_id'], 'journal_sequence': r['journal_sequence'],
                'amount_raw': r['amount_raw'], 'resource_kind_raw': r['resource_kind_raw'],
                'component_raw': r['component_raw'], 'caller_return_rva': r['caller_return_rva'],
                'generic_wallet_context_v1': r.get('generic_wallet_context_v1'),
                'maintenance_attribution': 'unclosed'} for r in new_records if r['kind'] == 2]
    return {'schema': READER_SCHEMA, 'producer_machine_id': binding['machine_id'],
            'segment_identity': {k: binding[k] for k in ('segment_id', 'pid', 'create_filetime',
                'generation', 'episode', 'payment_epoch', 'window_id')},
            'date_raw': binding['date_raw'],
            'native_date_storage_u64_raw': c['native_date_raw'],
            'native_date_i32_low32': ((c['native_date_raw'] & 0xffffffff) -
                                    ((1 << 32) if c['native_date_raw'] & (1 << 31) else 0)),
            'native_date_high32_is_not_a_date': True,
            'latest_sequence': j['latest_sequence'], 'natural_retained_records': n['retained_records'],
            'payment_retained_records': p['retained_records'],
            'renewal_review_required': n['retained_records'] >= 48 or p['retained_records'] >= 320,
            'selected_army_boarding_callbacks': boarding,
            'other_army_boarding_callbacks': other_army,
            'generic_wallet_callbacks_unattributed': generic,
            'current_treasury_observation': body.get('current_treasury'),
            'net_treasury_difference_used': False, 'observed_empty_is_free_boarding': False,
            'maintenance_attribution': 'unclosed', 'full_v2_qualified': False,
            'original_R07_v1_qualified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', type=Path)
    p.add_argument('--for-observation', action='store_true')
    p.add_argument('--response', type=Path)
    p.add_argument('--snapshot', type=Path)
    p.add_argument('--binding', type=Path)
    p.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[5])
    a = p.parse_args()
    if a.for_observation:
        need(a.design is not None and not any((a.response, a.snapshot, a.binding)),
             'design preparation is separate from actual journal consumption')
        result = validate_design(read_json(a.design, 64 * 1024))
    else:
        need(all((a.response, a.snapshot, a.binding)) and a.design is None,
             'one explicit response, fresh snapshot and actual segment binding required')
        result = consume_window(read_json(a.response), read_json(a.snapshot),
                                read_json(a.binding, 64 * 1024), load_normalizer(a.repo_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
