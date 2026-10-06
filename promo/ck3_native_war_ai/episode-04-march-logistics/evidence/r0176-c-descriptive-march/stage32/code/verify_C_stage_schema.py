"""Validate relative completed small reports while C's terminal fields remain null."""
import argparse
import hashlib
import json
from pathlib import Path

START, END = 53148432, 53150592
EPISODE = 'native-33388-1be6dd7a468f'


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def load(root, name):
    return json.loads((root / name).read_bytes())


def exact_pin(root, relative, expected):
    raw = (root / relative).read_bytes()
    need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'source pin mismatch: ' + relative)


def derive(root):
    early = load(root, 'early-stage/C-intermediate-values.json')
    protocol = load(root, 'early-stage/inputs/Root-ABC-protocol.json')
    manifest = load(root, 'inputs/London-runtime-inputs.json')
    growth = load(root, 'inputs/day27-source-analysis.json')
    growth_review = load(root, 'inputs/Root-day27-review.json')
    arrival = load(root, 'inputs/day28-source-analysis.json')
    arrival_result = load(root, 'inputs/waypoint-arrival-result.json')
    transition = load(root, 'inputs/Root-day28-phase-transition-review.json')
    move = load(root, 'inputs/phase2-result.json')
    ack = load(root, 'inputs/phase2-move-ack.json')
    day32 = load(root, 'inputs/day32-source-analysis.json')
    review = load(root, 'inputs/Root-day32-review.json')
    audit = load(root, 'inputs/S01-media-audit.json')
    frames = load(root, 'inputs/Root-S01-encoded-review.json')
    need(early['start_raw'] == manifest['start_raw'] == START and early['absolute_end_raw'] == manifest['absolute_end_raw'] == END, 'shared clock mismatch')
    need(protocol['sampling_policy']['maximum_batches_per_arm'] == 120 and protocol['timeline']['maximum_actual_game_days'] == 90 and manifest['budget_reset_on_phase2'] is False, 'two-phase budget mismatch')
    need(manifest['expected_runtime']['episode_run_id'] == review['episode_run_id'] == ack['submitted_episode_run_id'] == EPISODE, 'same episode mismatch')
    for source, root_review, relative in ((growth, growth_review, 'inputs/day27-source-analysis.json'), (day32, review, 'inputs/day32-source-analysis.json')):
        exact_pin(root, relative, root_review['source_analysis'])
        need(source['source_after'] == root_review['basis_observation'] and source['required_identity_max_commander_runtime_war_gate_pass'] is True, 'Root actual source/gate mismatch')
        need(source['counts_before'] == source['counts_after'] == {'regiments': 27, 'DATA': 37} and root_review['full27reg37DATA_commander27357_and_actual_clocks_reviewed'] is True, 'reported cohort gate failed')
    changes = growth['full_regiment_row_delta']
    need(len(changes) == 6 and all(item['path'].endswith('/current_soldiers') for item in changes), 'six integer regiment changes expected')
    current = [item for item in growth['full_DATA_container_row_delta'] if item['path'].endswith('/current_soldiers')]
    prepared = [item for item in growth['full_DATA_container_row_delta'] if 'prepared_replenishment_fraction' in item['path']]
    permissions = [item for item in growth['full_DATA_container_row_delta'] if item['path'].endswith(('/native_can_replenish', '/native_chunk_can_replenish'))]
    need(len(current) == 6 and sum(item['after'] - item['before'] for item in current) == sum(item['after'] - item['before'] for item in changes) == 10, 'integer growth sum mismatch')
    need(growth['scalars_before']['current_soldiers'] == 6679 and growth['scalars_after']['current_soldiers'] == 6689 and growth['before_date_raw'] == START + 26 * 24 and growth['after_date_raw'] == START + 27 * 24, 'growth endpoint mismatch')
    exact_pin(root, 'inputs/day28-source-analysis.json', transition['source_analysis'])
    exact_pin(root, 'inputs/waypoint-arrival-result.json', transition['arrival_fresh_full4'])
    exact_pin(root, 'inputs/phase2-result.json', transition['London_move_route_readback'])
    own = arrival['player_after'][0]
    need(arrival['before_date_raw'] == START + 27 * 24 and arrival['after_date_raw'] == START + 28 * 24 and own['current_province_id'] == 2176 and own['route_province_ids'] == [] and own['route_read_status'] == 'complete_empty' and own['army_state'] == 'regular' and own['in_combat'] is False and own['retreating'] is False, 'waypoint predicate not reported')
    need(arrival_result['actual_paused'] is True and arrival_result['actual_target'] == 2176 and arrival_result['status'] == 'STOP_ACTUAL_C_PHASE_STATIONARY_ARRIVAL', 'fresh waypoint result mismatch')
    need(move['actual_date_raw'] == arrival_result['actual_date_raw'] == START + 28 * 24 and move['no_budget_reset'] is True and move['actual_route'] == manifest['actual_C_stage_preview_route'] == [729, 965, 686, 628, 629, 1527] and ack['accepted'] is True, 'same-day London typed route mismatch')
    need(day32['before_date_raw'] == START + 31 * 24 and day32['after_date_raw'] == START + 32 * 24 and day32['full_regiment_row_delta'] == day32['full_DATA_container_row_delta'] == [], 'day32 report mismatch')
    before, after = day32['scalars_before']['current_supply_raw'], day32['scalars_after']['current_supply_raw']
    need((before, after) == (10613988, 10190260) and after - before == -423728 and day32['clock_before']['last_supply_update_date_raw'] == 53148480 and day32['clock_after']['last_supply_update_date_raw'] == 53149200, 'day32 stock/write mismatch')
    deviations = review['sampling_protocol_deviations']
    need(len(deviations) == 3 and review['descriptive_continuation_only'] is True and review['controlled_comparison_eligibility_granted'] is False, 'deviation/eligibility boundary lost')
    for day, deviation in zip((14, 22, 31), deviations):
        stop = load(root, 'inputs/overshoot-day%d-original-STOP.json' % day)
        need(stop['status'] == 'STOP_ONE_DAY_BATCH_TARGET' and stop['actual_paused'] is True and stop['actual_overshoot_raw'] == deviation['overshoot_raw'] == 24 and stop['actual_date_raw'] == START + day * 24, 'old overshoot STOP changed')
        need(deviation['planned_max_target_days'] == 1 and deviation['actual_days'] == 2 and deviation['window_one_day_sampling_eligible'] is False and deviation['arm_controlled_comparison_eligibility_not_granted'] is True and deviation['actual_global_budget_breach'] is False, 'sampling deviation was repaired or relabeled')
    exact_pin(root, 'inputs/S01-media-audit.json', frames['actual_media_audit'])
    need(audit['state'] == 'PASS' and audit['decoded_frames'] == audit['video_packets'] == 107167 and audit['source_identity'] == frames['actual_closed_raw_identity_reused'], 'S01 reported audit mismatch')
    need(len(frames['rows']) == 6 and frames['one_x_full_movie_review_completed'] is False and frames['human_signoff'] is False, 'S01 single-frame boundary lost')
    return {
        'schema': 'ck3.e04.C.stage-before-terminal.v1', 'status': 'IN_PROGRESS',
        'experiment': {'run': 'R0176-a01', 'episode': EPISODE, 'actor': 33388, 'commander': 27357, 'source_commit': early['source_commit'], 'checkpoint': early['checkpoint_recorded_pin'], 'start_raw': START, 'absolute_end_raw': END, 'maximum_actual_days': 90, 'maximum_batches_shared_across_phases': 120, 'budget_reset': False},
        'last_completed_report': {'raw': day32['after_date_raw'], 'day': 32, 'current_soldiers': 6689, 'maximum_soldiers': 6747, 'stock_raw': after, 'capacity_raw': 30000000, 'monthly_raw': -423728, 'gold': day32['gold_after']},
        'route': {'phase1_actual': [2175, 2179, 2176], 'waypoint_arrival_interval_raw': [arrival['before_date_raw'], arrival['after_date_raw']], 'waypoint_interval_open_left_closed_right': True, 'waypoint_exact_tick': None, 'same_day_phase2_move_raw': move['actual_date_raw'], 'phase2_actual': move['actual_route']},
        'day27_integer_change': {'net_current_soldiers': 10, 'six_Regiment_changes': changes, 'six_DATA_current_changes': current, 'prepared_fraction_changes': prepared, 'permission_changes': permissions, 'application_ledger_or_cause': None},
        'day32_supply_change': {'before': before, 'after': after, 'delta': after - before, 'scale': 100000, 'stored_write_before_raw': 53148480, 'stored_write_after_raw': 53149200, 'own_rows_unchanged_in_this_window': True},
        'sampling_deviations': deviations, 'descriptive_continuation_only': True, 'controlled_comparison_eligibility': 'NOT_GRANTED',
        'S01_media': {'reported_machine_state': 'PASS', 'duration_seconds': audit['actual_duration_seconds'], 'frames': 107167, 'packets': 107167, 'six_Root_still_reviews': [{'ordinal': item['actual_frame_ordinal'], 'PTS': item['actual_pts'], 'pixels': item['Root_actual_pixels']} for item in frames['rows']], 'native_exact_event_PTS': None, 'continuous_clean': False, 'human_1x': False},
        'terminal_status': None, 'terminal_exact_date': None, 'London_arrival': None, 'London_arrival_interval_raw': None,
        'endpoint_whole': None, 'endpoint_stock': None, 'endpoint_cash': None, 'net_treasury_change_raw': None,
        'runtime_closure': None, 'S02_media': None, 'final_raw_pin': None, 'winner': None, 'human_signoff': False,
        'validation_scope': 'packaged completed small reports; no full native endpoint, media, live SDK or game revalidation',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY', 'reads_or_writes': False}))
        return 0
    root = Path(__file__).resolve().parents[1]
    manifest = load(root, 'manifest.json')
    for pin in manifest['files']:
        relative = Path(pin['path'])
        need(not relative.is_absolute() and '..' not in relative.parts and ':' not in pin['path'], 'unsafe relative pin')
        path = (root / relative).resolve()
        need(path.is_relative_to(root.resolve()) and path.suffix in ('.json', '.md', '.py'), 'external/media file excluded')
        exact_pin(root, pin['path'], pin)
    actual = derive(root)
    need(actual == load(root, 'C-stage-before-terminal.json'), 'derived stage differs')
    for name in load(root, 'C-final-schema.json')['must_remain_null_before_terminal_sources']:
        need(actual[name] is None, 'future terminal field filled: ' + name)
    comparison = load(root, 'ABC-status-skeleton.json')
    need(comparison['C']['status'] == 'IN_PROGRESS_DESCRIPTIVE_ONLY' and comparison['C']['controlled_comparison_eligibility'] == 'NOT_GRANTED' and comparison['C']['terminal'] is None and comparison['winner'] is None and comparison['controlled_ABC_comparison_complete'] is False, 'comparison prematurely completed')
    print(json.dumps({'status': 'PASS_SMALL_STAGE_SCHEMA_C_STILL_IN_PROGRESS', 'relative_files': len(manifest['files']), 'cutoff_raw': actual['last_completed_report']['raw'], 'deviations': 3, 'controlled_eligibility': 'NOT_GRANTED', 'terminal': None, 'winner': None, 'Game_SDK_UI_process_bus_Git_RAW_calls': False}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({'status': 'FAIL_SMALL_STAGE_SCHEMA', 'error': str(error)}))
        raise SystemExit(1)
