"""Validate only packaged small reports; default PLAN never opens source media."""
import argparse
import hashlib
import json
from pathlib import Path

START = 53148432
END = 53150592
EPISODE = 'native-33388-1be6dd7a468f'
SAVE_SHA = 'd052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a'
SOURCE = '7f1db1a773e647b9f31378d4a9ccf57a60cf9e73'


def check(condition, message):
    if not condition:
        raise ValueError(message)


def body(root, relative):
    path = (root / relative).resolve()
    check(path.is_relative_to(root.resolve()), 'relative input escaped package')
    return json.loads(path.read_bytes())


def relative_pin(root, relative):
    raw = (root / relative).read_bytes()
    return {'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def pin_matches(root, relative, source_pin):
    pin = relative_pin(root, relative)
    return all(pin[key] == source_pin[key] for key in ('bytes', 'sha256'))


def derive(root):
    protocol = body(root, 'inputs/Root-ABC-protocol.json')
    prepared = body(root, 'inputs/C-prepared.json')
    cold = body(root, 'inputs/cold-compare-report.json')
    accepted = body(root, 'inputs/Root-cold-acceptance.json')
    move = body(root, 'inputs/phase1-result.json')
    intent = body(root, 'inputs/phase1-intent.json')
    ack = body(root, 'inputs/phase1-move-ack.json')
    reports = [body(root, 'inputs/day%d-source-analysis.json' % day) for day in (2, 3, 4)]
    reviews = [body(root, 'inputs/Root-day%d-review.json' % day) for day in (2, 3)]
    timeline = protocol['timeline']
    check(protocol['source_commit'] == SOURCE and protocol['actor_id'] == 33388, 'frozen source/actor mismatch')
    check(timeline['t0_date_raw'] == START and timeline['absolute_end_date_raw'] == END and timeline['maximum_actual_game_days'] == 90 and timeline['raw_units_per_day'] == 24, '90-day clock mismatch')
    check(protocol['sampling_policy']['maximum_batches_per_arm'] == protocol['ABC']['sampling_policy']['maximum_batches_per_arm'] == 120, 'shared arm batch ceiling mismatch')
    checkpoint = prepared['checkpoint']
    original = checkpoint['source']
    check(original['actor_id'] == 33388 and original['date_raw'] == START, 'checkpoint identity mismatch')
    check(original['save']['sha256'] == checkpoint['profile_copy']['sha256'] == SAVE_SHA and original['save']['bytes'] == checkpoint['profile_copy']['bytes'] == 73795635, 'checkpoint recorded pin mismatch')
    check(cold['status'] == accepted['cold_compare_status'] == 'PASS_COLD_BASELINE_EQUAL' and cold['semantic_differences'] == [] and cold['semantic_difference_count'] == accepted['semantic_difference_count'] == 0, 'cold semantic report failed')
    check(cold['row_counts']['target'] == cold['row_counts']['normative'] == {'regiments': 27, 'DATA': 37}, 'cold counts mismatch')
    check(cold['entire_rows_sha256']['target'] == cold['entire_rows_sha256']['normative'] and accepted['full27reg37DATA_entire_rows_equal'] is True, 'cold entire-row digests mismatch')
    check(accepted['episode'] == ack['submitted_episode_run_id'] == EPISODE, 'new C episode mismatch')
    check(pin_matches(root, 'inputs/cold-compare-report.json', accepted['compare']), 'Root cold compare pin mismatch')
    check(move['actual_route'] == intent['phase1_expected_fresh_whole_route'] == [2175, 2179, 2176], 'phase1 route mismatch')
    check(move['start_raw'] == intent['start_raw'] == START and move['absolute_end_raw'] == intent['absolute_end_raw'] == END, 'two-stage common clock mismatch')
    check(move['no_budget_reset'] is True and move['ack_not_arrival_or_completion'] is True and move['comparison_completion_credit'] == 0, 'command/arrival boundary changed')
    check(intent['phase2_London_actual_route'] is None, 'future phase2 route filled')
    check(ack['accepted'] is True and ack['target_province_id'] == 2176 and ack['war_action']['postcondition_verified'] is True, 'typed move not accepted')
    own = ack['player_armies']
    check(len(own) == 1 and own[0]['army_id'] == 0 and own[0]['owner_character_id'] == 33388 and own[0]['route_province_ids'] == [2175, 2179, 2176], 'actual submitted cohort route mismatch')
    for report, day in zip(reports, (2, 3, 4)):
        check(report['after_date_raw'] == START + 24 * day and report['before_date_raw'] == START + 24 * (day - 1), 'reported date mismatch')
        check(report['counts_before'] == report['counts_after'] == {'regiments': 27, 'DATA': 37}, 'completed report row counts mismatch')
        check(report['full_regiment_row_delta'] == report['full_DATA_container_row_delta'] == [], 'own entire-row change in reported window')
        check(report['required_identity_max_commander_runtime_war_gate_pass'] is True, 'reported identity gate failed')
        for field in ('scalars_before', 'scalars_after'):
            scalars = report[field]
            check(scalars['current_soldiers'] == 6679 and scalars['maximum_soldiers'] == 6747 and scalars['current_supply_capacity_raw'] == 30000000, 'own count/capacity report changed')
        check(report['gold_before'] == report['gold_after'] == {'raw': 63754562, 'scale': 100000}, 'observed own cash changed')
    for report, review, day in zip(reports, reviews, (2, 3)):
        check(review['status'] == 'ROOT_ACTUAL_C_CURRENT_BASIS_ACCEPTED_BEFORE_NEXT_RESUME' and review['episode_run_id'] == EPISODE, 'Root current-basis review missing')
        check(review['actual_date_raw'] == report['after_date_raw'] and review['start_raw'] == START and review['absolute_end_raw'] == END and review['no_budget_reset'] is True, 'Root review clock mismatch')
        check(pin_matches(root, 'inputs/day%d-source-analysis.json' % day, review['source_analysis']), 'Root analysis pin mismatch')
        check(review['basis_observation'] == report['source_after'], 'Root actual basis pin mismatch')
        check(review['full27reg37DATA_commander27357_and_actual_clocks_reviewed'] is True, 'Root cohort/commander review missing')
    day2, day3, day4 = reports
    before = day2['scalars_before']['current_supply_raw']
    after = day2['scalars_after']['current_supply_raw']
    check((before, after) == (11037716, 10613988), 'day2 stock endpoints mismatch')
    check(after - before == day2['scalars_before']['current_supply_change_monthly_raw'] == -423728, 'day2 supply delta mismatch')
    check(day2['clock_before']['last_supply_update_date_raw'] == 53147760 and day2['clock_after']['last_supply_update_date_raw'] == 53148480 and day2['clock_before']['last_supply_update_date_storage_raw64'] != day2['clock_after']['last_supply_update_date_storage_raw64'], 'day2 stored supply write missing')
    for report in (day3, day4):
        check(report['material_delta'] == [] and report['scalars_before'] == report['scalars_after'], 'later own material report changed')
    strength = [item for item in day3['outside_world_delta'] if item['path'].endswith('/besieging_strength')]
    check(len(strength) == 1 and strength[0]['before'] == 5257 and strength[0]['after'] == 5235, 'offsite strength endpoints mismatch')
    check('NPC1609' in reviews[1]['Root_actual_review_notes'] and 'UNKNOWN' in reviews[1]['Root_actual_review_notes'], 'Root NPC scope/cause boundary missing')
    check(len(day4['outside_world_delta']) == 4 and all('/active_siege/' in item['path'] for item in day4['outside_world_delta']), 'day4 world-only field classification mismatch')
    return {
        'schema': 'ck3.e04.C.intermediate-small-reports.v1',
        'status': 'IN_PROGRESS',
        'validation_scope': 'completed small report pins and their source metadata joins; not independent replay of full native rows',
        'run': 'R0176-a01', 'episode_run_id': EPISODE,
        'actual_actor_id': 33388, 'actual_cold_pid_from_receipt': accepted['actual_pid'],
        'checkpoint_recorded_pin': {'bytes': 73795635, 'sha256': SAVE_SHA},
        'save_bytes_read_by_consumer': False,
        'source_commit': SOURCE, 'start_raw': START, 'absolute_end_raw': END,
        'maximum_actual_days': 90, 'maximum_batches_per_arm': 120,
        'shared_across_both_phases': True, 'budget_reset': False,
        'completed_report_cutoff_raw': day4['after_date_raw'],
        'completed_report_days_used': 4, 'remaining_game_days_at_report_cutoff': 86,
        'cold_report_difference_count': 0, 'cold_report_counts': {'regiments': 27, 'DATA': 37},
        'cold_entire_row_digests': cold['entire_rows_sha256']['target'],
        'baseline': {'current_soldiers': 6679, 'maximum_soldiers': 6747, 'stock_raw': 11037716, 'capacity_raw': 30000000, 'supply_scale': 100000, 'commander_id': 27357, 'gold_raw': 63754562, 'gold_scale': 100000},
        'phase1': {'target': 2176, 'actual_submitted_route': [2175, 2179, 2176], 'typed_move_accepted': True, 'waypoint_stationary_arrival': None},
        'day2_supply': {'before_raw': before, 'after_raw': after, 'delta_raw': after - before, 'monthly_raw': -423728, 'stored_update_before_raw': 53147760, 'stored_update_after_raw': 53148480, 'original27_and37_reported_entire_rows_unchanged': True, 'own_soldier_delta': 0, 'net_gold_delta_raw': 0},
        'day3_offsite': {'Root_identity_label': 'NPC1609 siege3 Army7', 'identity_label_source': 'inputs/Root-day3-review.json', 'strength_before': 5257, 'strength_after': 5235, 'net_delta': -22, 'cause': None, 'own_loss_or_applied_attrition_credit': False},
        'day4': {'own_material_delta': [], 'ordinary_offsite_siege_progress_field_count': 4, 'offsite_strength_change': False},
        'phase2_actual_London_route': None,
        'London_arrival': None, 'terminal': None, 'endpoint_raw': None,
        'endpoint_date': None, 'endpoint_whole': None, 'endpoint_stock': None,
        'endpoint_gold': None, 'net_endpoint_deltas': None,
        'winner': None, 'deadline_censored': None, 'runtime_closure': None,
        'media_audit': None, 'human_signoff': False,
        'Root_cold_receipt_original_pending_fields_preserved': True,
        'day4_Root_current_basis_review': None,
        'SDK_Game_UI_raw_media_or_external_source_calls': False,
    }


def verify(root):
    manifest = body(root, 'manifest.json')
    check(manifest['schema'] == 'ck3.e04.C.intermediate-package.v1', 'unsupported manifest')
    for pin in manifest['files']:
        relative = Path(pin['path'])
        check(not relative.is_absolute() and '..' not in relative.parts and ':' not in pin['path'], 'unsafe relative leaf')
        path = (root / relative).resolve()
        check(path.is_relative_to(root.resolve()) and path.suffix in ('.json', '.py', '.md'), 'external/media leaf rejected')
        raw = path.read_bytes()
        check(len(raw) <= 262144 and len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'relative byte mismatch: ' + pin['path'])
    actual = derive(root)
    check(actual == body(root, 'C-intermediate-values.json'), 'derived intermediate summary mismatch')
    comparison = body(root, 'A-C-comparison-template.json')
    check(comparison['comparison_status'] == 'PENDING_ACTUAL_C_ENDPOINT' and comparison['comparison'] is None and comparison['winner'] is None, 'comparison prematurely filled')
    check(comparison['C']['status'] == 'IN_PROGRESS' and comparison['C']['endpoint'] is None and comparison['C']['arrival_interval_raw'] is None and comparison['C']['net_treasury_change_raw'] is None, 'C terminal prematurely filled')
    return {'status': 'PASS_COMPLETED_SMALL_REPORT_BINDINGS_C_IN_PROGRESS', 'C_status': actual['status'], 'last_completed_report_raw': actual['completed_report_cutoff_raw'], 'C_endpoint': None, 'comparison': None, 'winner': None, 'relative_pin_count': len(manifest['files']), 'native_entire_row_replay': False, 'save_RAW_PNG_or_live_sources_opened': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY', 'source_or_live_reads': False}))
        return 0
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status': 'FAIL_COMPLETED_SMALL_REPORT_BINDINGS', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)
