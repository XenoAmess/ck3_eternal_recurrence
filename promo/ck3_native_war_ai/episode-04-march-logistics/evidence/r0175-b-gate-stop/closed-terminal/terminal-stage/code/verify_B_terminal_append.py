"""Portable small terminal append; old catalog pin joins only, no old body rescan."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def need(value, reason):
    if not value:
        raise ValueError(reason)


def read(relative, expected=None):
    path = (HERE / relative).resolve(strict=True)
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py', '.md'}, 'bounded relative append leaf')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'small append source only')
    if expected:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'original append pin differs')
    return json.loads(raw) if path.suffix == '.json' else raw


def verify():
    if (HERE / 'manifest.json').is_file():
        for pin in read('manifest.json')['files']:
            read(pin['path'], pin)
    catalog = read('inputs/base-73-pin-catalog.json', {'bytes': 35350, 'sha256': '4b1666df2a17a075e7d5f6ac79e9493f7b4492cd592fcf5088aca1d0b484dc64'})
    need(len(catalog['files']) == 73, 'original73 catalog unchanged')
    old_pins = {row['path']: row for row in catalog['files']}
    terminal = read('inputs/terminal.json', {'bytes': 3963, 'sha256': '6f8eaa3cdef8942effe5b2809a13cb5417d54504c0147f195f3a56396978f163'})
    ui = read('inputs/Root-Main-UI-receipt.json', {'bytes': 2036, 'sha256': 'b2457fa89ae8921008918592e309203b10f45a635799aadba986264cc8d0f46e'})
    need(terminal['status'] == 'STOPPED_GATE_INCOMPLETE' and terminal['arm'] == 'B'
         and terminal['episode_run_id'] == 'native-33388-23726fbd8a80' and terminal['actual_game_pid'] == 19560,
         'actual B Root terminal binding')
    start, stop, end = terminal['start_raw'], terminal['observed_stop_raw'], terminal['absolute_end_raw']
    need((start, stop, end) == (53148432, 53149344, 53150592)
         and terminal['actual_days_used'] == (stop - start) / 24 == 38
         and terminal['remaining_actual_days'] == (end - stop) / 24 == 52,
         'actual38/rem52 immutable budget')
    need(terminal['deadline_reached'] is False and terminal['checkpoint_reload_or_date_reset'] is False
         and terminal['no_more_resume_or_strategy_mutations'] is True, 'gate failure; no deadline censor or reset')
    for key, old in [('Root_protocol', 'qualified-rest/intermediate/child-cap/inputs/protocol.json'),
                     ('rest_qualification', 'qualified-rest/inputs/Root-qualification.json'),
                     ('merge_command', 'inputs/merge-response.json'), ('original_merge_STOP', 'inputs/stage-STOP.json'),
                     ('actual_postmerge_source', 'inputs/post/observation.json')]:
        ref, pin = terminal[key], old_pins[old]
        need(ref['bytes'] == pin['bytes'] and ref['sha256'] == pin['sha256'], 'terminal exact source joins preserved old catalog/' + key)
    need(terminal['postmerge_original_UI']['bytes'] == 2036
         and terminal['postmerge_original_UI']['sha256'] == 'b2457fa89ae8921008918592e309203b10f45a635799aadba986264cc8d0f46e', 'same completed UI source receipt')
    need(ui['actual_pid'] == 19560 and ui['episode'] == terminal['episode_run_id'] and ui['date_raw'] == stop
         and ui['subject_army'] == 0 and ui['expected_player_army_count'] == 1
         and ui['actual_available_UI_subject_verified'] is True and ui['strategy_time_advanced'] is False,
         'actual UI subject/date and zero strategy advance')
    need(ui['image'] == terminal['Root_direct_original_review']['image'], 'Root direct review binds same original image metadata')
    need(terminal['new_Regiment_identity_or_mechanism'] is None and terminal['winner'] is None
         and terminal['London_endpoint_metrics'] is None and terminal['actual_London_arrival'] is False
         and terminal['arrival_comparable'] is False and terminal['ABC_complete'] is False,
         'no type/cause/London/winner/overall completion shortcut')
    need(terminal['raw_closure_pending'] is True, 'historical closure-pending receipt retained')
    return {'schema': 'ck3.e04.B.terminal-append-projection.v1', 'status': 'PASS_TERMINAL_APPEND_SOURCE_PINS_ONLY',
            'B_disposition': 'STOPPED_GATE_INCOMPLETE', 'actual_raw': stop, 'actual_days_used': 38, 'remaining_actual_days': 52,
            'deadline_reached': False, 'is_90_day_censored_arrival_result': False, 'budget_reset': False,
            'Root_terminal_original': 'inputs/terminal.json', 'Root_postmerge_UI_original': 'inputs/Root-Main-UI-receipt.json',
            'preserved_base_catalog': {'path': 'inputs/base-73-pin-catalog.json', 'bytes': 35350,
                                       'sha256': '4b1666df2a17a075e7d5f6ac79e9493f7b4492cd592fcf5088aca1d0b484dc64', 'old_pinned_files': 73},
            'base_dataset_must_be_retained_for_full_native_cohort_recompute': True,
            'old_73_body_rescan_or_original_cohort_revalidation': False,
            'Root_declared_return_arrival_reference_unopened': terminal['actual_return_arrival'],
            'London_arrival': False, 'London_endpoint_metrics': None, 'arrival_comparable': False, 'winner': None,
            'frozen_cohort_PASS_or_commander_preserved': False,
            'new_unit_type_or_cause': None,
            'actual_S02_sealed_raw_or_final_SDK_Game_closure': None,
            'original_terminal_raw_closure_pending_preserved': True,
            'Root_original_pixels_review_source': terminal['Root_direct_original_review'],
            'full_film_clean_human_signoff_ABC_complete_comparison_credit': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY_TERMINAL_APPEND_NO_SOURCE_READS',
                          'actual_terminal_projection': None, 'entry': '--verify', 'raw_Game_SDK_or_old73_body_reads': False}, indent=2))
        return 0
    try:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'STOP_TERMINAL_APPEND_SOURCE_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
