"""Portable completed B child branch: relative small JSON only, no SDK/game/raw access."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ANCHOR_RAW, LOCAL_END, GLOBAL_END = 53148576, 53149320, 53150592


def need(value, reason):
    if not value:
        raise ValueError(reason)


def read(relative, expected=None):
    path = (HERE / relative).resolve(strict=True)
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py'}, 'bounded package leaf required')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'small JSON/code leaf only')
    if expected is not None:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'raw source pin mismatch: ' + relative)
    return json.loads(raw) if path.suffix == '.json' else raw


def module(relative, name):
    path = HERE / relative
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def observed(relative, reader, frozen):
    packet = read(relative + '/observation.json')
    commanders = {aid: read(relative + '/commander-' + str(aid) + '.json') for aid in (0, 204)}
    projection = reader.project(packet, commanders)
    need(projection['unassessed_ancillary'] == [], 'actual two required subjects only')
    need({key: row['maximum_soldiers'] for key, row in projection['regiments'].items()} == frozen['regiment_maximum_by_FullID'], 'original27 FullIDs/max')
    need({key: row['maximum_soldiers'] for key, row in projection['records'].items()} == frozen['DATA_maximum_by_identity'], 'original37 DATA identities/max')
    for frame in (packet['before'], packet['after']):
        need(frame['diagnostics']['pipe_name'] == r'\\.\pipe\ck3-e04-r0175-20261006-a02'
             and frame['diagnostics']['bridge_pid'] == 19560 and frame['diagnostics']['connected'] is True, 'actual B runtime source')
    need(packet['before']['revision'] == packet['after']['revision']
         and packet['before']['native_revision'] == packet['after']['native_revision'], 'same paused observation source brackets')
    rows = {row['army_id']: row for row in packet['health']['army_strengths']}
    roster = {row['army_id']: row for row in packet['after']['player_armies']}
    need(set(rows) == set(roster) == {0, 204}, 'actual two subject roster/health')
    regs, data = {}, {}
    for row in packet['health']['army_strengths']:
        for regiment in row['regiment_strengths']:
            regs[regiment['army_regiment_id']] = regiment
        for group in row['regiment_replenishment_records_v1']:
            for record in group['records']:
                key = (group['army_regiment_id'], record['record_index'], record['persistent_regiment_id'], record['chunk_index'])
                data[key] = record
    return {'snapshot': packet['after'], 'health': packet['health'], 'main': rows[0], 'child': rows[204],
            'main_roster': roster[0], 'child_roster': roster[204], 'regiments': regs, 'DATA': data}, projection


def verify():
    manifest = read('manifest.json')
    for pin in manifest['files']:
        read(pin['path'], pin)
    reader = module('code/paired_snapshot_reader.py', 'B_child_portable_reader')
    pure = module('code/paired_window_pure.py', 'B_child_portable_pure_window')
    frozen = read('code/frozen-cohort.json')
    phase0 = read('inputs/phase0/result.json')
    need(phase0['status'] == 'PHASE0_ACTUAL_SPLIT_AND_CHILD_ROUTE_SUBMITTED_PAUSED'
         and phase0['date_raw'] == 53148432 and phase0['actual_game_days_advanced'] == 0
         and [phase0[key] for key in ('main_public_id', 'main_native_id', 'child_public_id', 'child_native_id')] == [0, 0, 204, 199], 'actual dynamic split binding')
    anchor = read('inputs/rest-anchor.json')
    need(anchor['date_raw'] == ANCHOR_RAW and anchor['local_max_days'] == 31
         and anchor['fixed_global_END'] == GLOBAL_END, 'original accepted anchor without reset')
    read('inputs/anchor/observation.json', anchor['observation'])
    read('inputs/phase0/result.json', anchor['phase0_result'])
    _, anchor_view = observed('inputs/anchor', reader, frozen)
    window = read('inputs/child-window.json')
    read('inputs/before/observation.json', window['before_observation'])
    read('inputs/after/observation.json', window['after_observation'])
    left, left_view = observed('inputs/before', reader, frozen)
    right, right_view = observed('inputs/after', reader, frozen)
    for view in (left_view, right_view):
        need(ANCHOR_RAW <= view['date_raw'] <= LOCAL_END <= GLOBAL_END, 'window inside immutable original31/globalEND')
        need(view['regiment_arm'] == anchor_view['regiment_arm'] and view['record_arm'] == anchor_view['record_arm'], 'split full cohort membership stable')
        need(all(row['stationary_at_required_site'] and row['monthly'] > 0 for row in view['arms'].values()), 'both stationary positive source endpoints')
    computed = pure.window(left, right)
    need(computed == window['actual_window'], 'complete actual_window must recompute exactly')
    need(computed['child_window_success'] is True and computed['main_window_success'] is False, 'child-only actual branch / Main still pending')
    need(left_view['regiments'] == right_view['regiments'] and left_view['records'] == right_view['records'], 'entire27/37 unchanged in actual source pair')
    return {'status': 'PASS_B_CHILD_FULL_BRANCH_PARTIAL_ONLY',
            'run': 'R0175-a02', 'episode_run_id': reader.EPISODE,
            'start_raw': reader.START, 'absolute_end_raw': GLOBAL_END,
            'rest_anchor_raw': ANCHOR_RAW, 'local31_absolute_END_raw': LOCAL_END,
            'actual_pair': computed, 'full27_regiment_entire_rows_unchanged': True,
            'full37_DATA_entire_rows_unchanged': True,
            'Root_world_review_source': 'inputs/root-review.json',
            'world_paths': reader.changes(left_view['active_wars'], right_view['active_wars'], '/active_wars'),
            'offsite_garrison_loss_cause_or_refill_death_payment_ledger': None,
            'Main_recovery_return_merge_London_B_terminal_final_raw_result': None,
            'complete_B_qualification_or_ABC_comparison_or_clean_human_credit': 0}


def main():
    try:
        print(json.dumps(verify(), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({'status': 'STOP_B_CHILD_PORTABLE_SOURCE_OR_NUMERIC_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
