"""Read local, pinned recording metadata; never open media or operate a game.

This checks consistency of a supplied experiment/segment metadata projection.
It does not prove capture coverage, native application, arrival, or approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


class MetadataError(ValueError):
    pass


def need(value, message):
    if value is not True:
        raise MetadataError(message)


def integer(value, message):
    need(type(value) is int, message)
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise MetadataError('nonfinite JSON constant: ' + value)


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


def pointer(value, path):
    need(type(path) is str and path.startswith('/'), 'explicit JSON pointer required')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            need(part.isdigit() and str(int(part)) == part, 'canonical array index required')
            value = value[int(part)]
        else:
            value = value[part]
    return value


def local_sources(table, base):
    objects = {}
    for pin in table['source_pins']:
        name, relative = pin['id'], pin['path']
        need(type(name) is str and name not in objects, 'unique source id required')
        need(type(relative) is str, 'relative JSON source path required')
        path = PurePosixPath(relative)
        need(not path.is_absolute() and '..' not in path.parts and ':' not in relative and '\\' not in relative,
             'unsafe relative source path')
        need(path.suffix == '.json', 'only small JSON sources may be read')
        source = base.joinpath(*path.parts)
        need(source.resolve().is_relative_to(base.resolve()), 'source escapes package')
        expected = integer(pin['bytes'], 'source bytes must be integer')
        need(0 <= expected <= 1024 * 1024, 'bounded small JSON source required')
        raw = source.read_bytes()
        need(len(raw) == expected and hashlib.sha256(raw).hexdigest() == pin['sha256'],
             'source bytes differ: ' + name)
        objects[name] = decode(raw)
    return objects


def validate(table, base):
    need(table['schema'] == 'xar.ck3.recording-segments.metadata.v1', 'metadata schema')
    sources = local_sources(table, base)
    refs = table['source_refs']
    protocol = sources[refs['protocol']]
    reshoot = sources[refs['prospective_reshoot']]
    scope = sources[refs['scope_addendum']]
    addendum = sources[refs['segment_addendum']]
    experiment = table['experiment']
    need(experiment['state'] in {'active', 'closed'}, 'known experiment metadata state')
    t0 = integer(experiment['start_raw'], 'T0 integer')
    end = integer(experiment['absolute_end_raw'], 'END integer')
    current = integer(experiment['observed_boundary_raw'], 'boundary integer')
    units = integer(experiment['raw_units_per_day'], 'day scale integer')
    days = integer(experiment['maximum_actual_days'], 'maximum days integer')
    need(units > 0 and days > 0 and end - t0 == units * days, 'shared actual-day budget')
    need(t0 <= current <= end and (current - t0) % units == 0, 'bounded actual boundary')
    boundary_ref = experiment['observed_boundary_source']
    need(pointer(sources[boundary_ref['source_ref']], boundary_ref['json_pointer']) == current,
         'declared boundary must come from an actual supplied source field')
    for source in (protocol, reshoot, scope, addendum):
        need(source['start_raw'] == t0 and source['absolute_end_raw'] == end,
             'source T0/END differs; segments cannot reset budget')
    need(protocol['common_checkpoint']['sha256'] == experiment['checkpoint_sha256'], 'same checkpoint identity')
    need(reshoot['independent_common_checkpoint_sha256'] == experiment['checkpoint_sha256'], 'reshoot common save')
    need(protocol['source_commit'] == experiment['source_commit'], 'source head identity')
    need(reshoot['primary_arms']['A'] == experiment['primary_run_description'], 'primary A selection')
    need(addendum['same_A2_experiment'] is True and addendum['new_independent_replay_or_A3'] is False
         and addendum['checkpoint_reloaded'] is False and addendum['date_reset'] is False,
         'continuation cannot become a new experiment or reload')
    need(experiment['game_pid'] == addendum['same_game_pid'], 'same declared game PID')
    need(experiment['episode_run_id'] == scope['episode_run_id'] == addendum['same_episode_run_id'], 'same declared episode')
    need(scope['budget_and_strategy_and_arrival_predicate_unchanged'] is True, 'scope change cannot alter strategy')
    need(scope['required_native_carmy_ids'] == experiment['required_native_carmy_ids'], 'required subject native identity')
    need(scope['required_full_regiments'] == experiment['required_regiments']
         and scope['required_full_DATA'] == experiment['required_DATA'], 'complete required cohort size')
    need(scope['global_scope_status_retained'] == 'partial'
         and scope['unassessed_CUnit_native_carmy_id'] is None
         and scope['unassessed_CUnit_health'] is None
         and scope['unassessed_CUnit_classification'] is None, 'unassessed roster rows remain unknown')
    need(scope['required_Main_rows_available'] is True
         and scope['no_unknown_value_coerced_to_zero_or_transport'] is True, 'strict required Main availability')
    terminal = experiment['terminal_observation_ref']
    if experiment['state'] == 'active':
        need(terminal is None, 'active experiment cannot have terminal observation')
    else:
        need(terminal in sources, 'closed experiment needs independent source reference')
        closure = sources[refs['experiment_closure']]
        acceptance = sources[refs['endpoint_acceptance']]
        need(all(closure[key] is True for key in ['SDK_thread_exited', 'keeper_thread_exited', 'GameJob0',
             'native_CK3_inventory_empty', 'watchdog_absent', 'first_recorder_closed', 'continuation_job0']),
             'closed experiment source must retain all independent closure facts')
        need(closure['A2_actual_days'] == (current - t0) // units
             and closure['primary_numeric_ABC_completed'] == 1 and closure['B_C_and_winner'] is None,
             'Root declared A-only completion and budget')
        need(acceptance['actual_raw'] == current and acceptance['endpoint_numeric_accepted'] is True
             and acceptance['exact_arrival_tick'] is None and acceptance['B_and_C_results'] is None,
             'Root acceptance original bounded endpoint')
        pin_by_id = {pin['id']: pin for pin in table['source_pins']}
        need(closure['Root_endpoint_accepted']['sha256'] == pin_by_id[refs['endpoint_acceptance']]['sha256'],
             'later closure must bind the original acceptance receipt')
    need(table['credits'] == {'completed_primary_arms': 0, 'valid_primary_arrivals': 0,
                             'continuous_video': 0, 'clean_span': 0, 'human_signoff': 0,
                             'native_application_or_exact_threshold': 0},
         'metadata consistency must not award execution or media credits')
    need(all(type(v) is int for v in table['credits'].values()), 'credit counters are explicit integers')
    need(table['arrival_result'] is None and table['strategy_ranking'] is None, 'no arrival or ranking from segments')
    segments = table['recording_segments']
    need(type(segments) is list and len(segments) >= 2, 'multi-segment metadata required')
    ids = [s['id'] for s in segments]
    need(all(type(value) is str and value for value in ids), 'explicit segment names required')
    need(len(set(ids)) == len(ids), 'unique segment identities')
    need([s['ordinal'] for s in segments] == list(range(1, len(segments) + 1)), 'ordered finite segments')
    need(all(type(s['ordinal']) is int for s in segments), 'segment ordinals are integers')
    closed, prospective = [], []
    for segment in segments:
        need(segment['experiment_id'] == experiment['id'], 'segment belongs to same experiment')
        need(segment['attempt'] == experiment['attempt'], 'segment is not A3 or an independent replay')
        need(segment['start_raw'] == t0 and segment['absolute_end_raw'] == end, 'segment cannot reset clock')
        need(segment['recorded_game_interval'] is None and segment['encoded_binding'] is None,
             'metadata cannot fabricate video game dates or encoded timecodes')
        need(segment['planned_maximum_wall_seconds'] == addendum['segment2_max_wall_seconds'], 'declared recorder wall limit')
        if segment['state'] == 'prospective':
            need(segment['finish_source_ref'] is None and segment['raw_provenance'] is None,
                 'unobserved segment cannot fabricate a raw or closure')
            need(segment['continuation_addendum_ref'] == refs['segment_addendum'], 'prospective continuation reference')
            prospective.append(segment['id'])
            continue
        need(segment['state'] == 'closed', 'only closed or prospective source metadata supported')
        source = sources[segment['finish_source_ref']]
        fields = segment['closure_fields']
        need(integer(pointer(source, fields['returncode']), 'recorder returncode integer') == 0,
             'recorder source did not exit successfully')
        need(integer(pointer(source, fields['job_active_processes']), 'job count integer') == 0,
             'recorder source still has active processes')
        if fields.get('is_error') is not None:
            need(pointer(source, fields['is_error']) is False, 'recorder tool source error')
        raw = pointer(source, fields['raw'])
        need(type(raw) is dict and raw == segment['raw_provenance'], 'raw identity must come from supplied closure source')
        need(type(raw['path']) is str and integer(raw['bytes'], 'raw bytes integer') > 0
             and type(raw['sha256']) is str and len(raw['sha256']) == 64
             and all(c in '0123456789abcdef' for c in raw['sha256']), 'source raw identity shape')
        # raw['path'] is provenance only and is never passed to filesystem access.
        closed.append({'id': segment['id'], 'source_ref': segment['finish_source_ref'], 'raw_provenance': raw})
        attempts = segment.get('recording_attempts', [])
        if attempts:
            need(len({item['id'] for item in attempts}) == len(attempts), 'unique nested recording attempts')
            successes = 0
            for attempt in attempts:
                if attempt['state'] == 'failed_before_start':
                    failed = sources[attempt['result_ref']]
                    need(failed['state'] == 'RED_START_FAILED' and failed['job'] is None and failed['raw'] is None
                         and failed['started_at_utc'] is None and failed['start_monotonic_ns'] is None,
                         'failed recorder admission must retain no job/raw/start')
                    need(attempt['failure_ref'] in sources, 'failed admission diagnostic source')
                else:
                    need(attempt['state'] == 'closed' and attempt['finish_source_ref'] == segment['finish_source_ref'],
                         'nested recording retry is not another experiment')
                    started = sources[attempt['start_source_ref']]
                    need(started['state'] == 'RECORDING' and started['same_A2'] is True
                         and started['pid'] == source['job']['pid']
                         and started['started_at_utc'] == source['started_at_utc']
                         and started['start_monotonic_ns'] == source['start_monotonic_ns'],
                         'successful retry actual start and closure identity')
                    need(source['same_A2'] is True and source['checkpoint_reload'] is False
                         and source['budget_reset'] is False and source['absolute_end_raw'] == end,
                         'recorder retry cannot reset game experiment')
                    successes += 1
            need(successes == 1, 'one actual successful recorder attempt per supplied segment')
    intervals = table['inter_segment_intervals']
    need(len(intervals) == len(segments) - 1, 'one separately declared interval per adjacent pair')
    for i, interval in enumerate(intervals):
        need(interval['from_segment'] == ids[i] and interval['to_segment'] == ids[i + 1], 'adjacent segment interval')
        need(interval['source_ref'] in sources, 'interval source required')
        authority = sources[interval['source_ref']]
        need(authority['same_game_pid'] == experiment['game_pid']
             and authority['same_episode_run_id'] == experiment['episode_run_id'], 'interval declared identity')
        need(authority['no_game_advance_between_segments'] is True
             and interval['Root_declared_no_game_advance'] is True, 'Root continuation no-advance declaration')
        need(interval['boundary_raw'] == authority['actual_raw_before_segment2'], 'actual declared gap boundary')
        need(interval['wall_gap_seconds'] is None and interval['continuous_video_credit'] is False,
             'unknown wall gap is not continuous recording proof')
        lifecycle = interval.get('lifecycle_interval')
        if lifecycle is not None:
            first = integer(pointer(sources[lifecycle['from_source_ref']], lifecycle['from_json_pointer']),
                            'first controller event timestamp integer')
            second = integer(pointer(sources[lifecycle['to_source_ref']], lifecycle['to_json_pointer']),
                             'next controller event timestamp integer')
            need(second >= first and lifecycle['delta_nanoseconds'] == second - first,
                 'controller event interval from actual supplied timestamps')
            need(lifecycle['kind'] == 'reported_finish_event_to_next_process_start_event'
                 and lifecycle['is_encoded_last_to_first_frame'] is False,
                 'controller events must not become encoded-frame continuity')
    return {
        'status': 'PASS_PINNED_SEGMENT_METADATA_ONLY',
        'scope': 'SmallJSON exact pins and supplied metadata consistency; not native/session/recording coverage validation',
        'experiment_id': experiment['id'], 'experiment_state': experiment['state'],
        'actual_declared_boundary_raw': current, 'declared_days_used': (current - t0) // units,
        'declared_days_remaining': (end - current) // units,
        'source_count': len(sources), 'closed_segment_sources': closed,
        'prospective_segment_ids': prospective,
        'raw_source_identities_reused_without_read_or_rehash': True,
        'source_public_native_frame_cohort_replay': 'Separate validator and original packets required',
        'credits': table['credits'],
        'no_IO_to_referenced_media_paths': True,
        'side_effects': {'files_written': 0, 'Game_SDK_UI_Steam_bus_Git_network_media_calls': 0},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, help='Local package metadata JSON; referenced sources must be relative smallJSON')
    args = parser.parse_args()
    try:
        path = args.manifest.resolve()
        result = validate(decode(path.read_bytes()), path.parent)
    except (MetadataError, OSError, KeyError, TypeError, IndexError, json.JSONDecodeError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
