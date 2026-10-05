"""Small portable closed B terminal, metadata receipts only; no raw stat/open."""
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
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py', '.md', '.bin'}, 'small relative receipt only')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'raw/save/media leaf forbidden')
    if expected:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'exact receipt bytes/SHA differs')
    return json.loads(raw) if path.suffix in {'.json', '.bin'} else raw


def verify():
    if (HERE / 'manifest.json').is_file():
        for row in read('manifest.json')['files']:
            read(row['path'], row)
    terminal = read('terminal-stage/inputs/terminal.json', {'bytes': 3963, 'sha256': '6f8eaa3cdef8942effe5b2809a13cb5417d54504c0147f195f3a56396978f163'})
    prior = read('terminal-stage/B-terminal-append-values.json')
    need(prior['B_disposition'] == terminal['status'] == 'STOPPED_GATE_INCOMPLETE'
         and terminal['observed_stop_raw'] == 53149344 and terminal['actual_days_used'] == 38
         and terminal['remaining_actual_days'] == 52 and terminal['deadline_reached'] is False, 'same gate terminal, not deadline censor')
    need(terminal['raw_closure_pending'] is True, 'original pending field retained')
    closure = read('inputs/B-actual-closure.json', {'bytes': 1606, 'sha256': '76282f501f7b7c52a7c585180db1695040e251ad40de7e3dd60d7c03db5a66ef'})
    need(closure['arm'] == 'B' and closure['B_status'] == terminal['status'] and closure['B_actual_days'] == 38
         and closure['B_deadline_censor'] is False, 'closure does not change experiment outcome')
    need(closure['Root_frozen_gate_terminal']['bytes'] == 3963
         and closure['Root_frozen_gate_terminal']['sha256'] == '6f8eaa3cdef8942effe5b2809a13cb5417d54504c0147f195f3a56396978f163', 'closure pin joins actual terminal')
    for key in ('SDK_thread_exited', 'keeper_thread_exited', 'GameJob0', 'native_CK3_inventory_empty', 'watchdog_absent',
                'first_recorder_closed', 'continuation_job0', 'all_owned_process_trees_zero'):
        need(closure[key] is True, 'actual Root closure pending/failed: ' + key)
    release = read('inputs/B-release-stdout.bin', {'bytes': 1332, 'sha256': 'b34dd0d9b173f24832b353c6254e1e6c064a127258928486bdc060106292d0e8'})
    result = read('inputs/B-release-result.json', {'bytes': 22, 'sha256': '1e3f6691f455051e8adb15d961e4bf3c7a17e83dd88b2afdd13315cc288250bb'})
    need(result['returncode'] == 0 and release['ok'] is True
         and release['task']['state'] == 'done' and release['task']['resources'] == []
         and release['task']['last_sequence'] == release['event']['sequence'] == 5115
         and release['event']['task_id'] == release['task']['task_id'] == 'war-e04-capture-abc-B-a08-20261006-a24', 'actual B CAS release DONE5115/resources0')
    sealed = read('inputs/B-S02-sealed-result.json', {'bytes': 1057, 'sha256': '3db7f2f83352a157174b91aa25828e0cf21fe2b428daf8b2fa9afc8e42458d9e'})
    need(closure['continuation_recorder']['bytes'] == 1057 and closure['continuation_recorder']['sha256'] == '3db7f2f83352a157174b91aa25828e0cf21fe2b428daf8b2fa9afc8e42458d9e', 'same sealed continuation source')
    need(sealed['state'] == sealed['job']['state'] == 'NORMAL_TREE_EMPTY'
         and sealed['job']['returncode'] == 0 and sealed['job']['job_active_processes'] == 0
         and sealed['job']['error'] is None and sealed['same_B'] is True
         and sealed['episode_run_id'] == terminal['episode_run_id']
         and sealed['checkpoint_reload'] is False and sealed['budget_reset'] is False
         and sealed['absolute_end_raw'] == terminal['absolute_end_raw'] == 53150592, 'same experiment, actual sealed job0')
    need(sealed['raw']['bytes'] == 3363279647 and sealed['raw']['sha256'] == 'de8f9c72f64e62bc14461ee6611a301d1dc765599f138b015cacaf54dcd7f468'
         and sealed['raw_hash_performed_once_after_job_empty'] is True, 'terminal-owned raw pin, no rehash')
    need(terminal['winner'] is None and terminal['London_endpoint_metrics'] is None
         and closure['B_comparable_London_metrics'] is None and closure['C_and_winner'] is None
         and sealed['clean_spans_certified'] is False and sealed['human_approval'] is False, 'no outcome/media shortcut')
    return {'schema': 'ck3.e04.B.closed-gate-terminal.v1', 'status': 'PASS_SMALL_CLOSED_GATE_TERMINAL_METADATA_ONLY',
            'B_disposition': 'STOPPED_GATE_INCOMPLETE', 'actual_raw': 53149344, 'days_used': 38, 'remaining_days': 52,
            'deadline_reached': False, 'is_90_day_censored_arrival_result': False, 'budget_reset': False,
            'actual_B_owned_runtime_closed': True, 'actual_screen_release_sequence': 5115, 'actual_screen_resources': [],
            'Root_supervisor_exit0_actual_unified_session': closure['supervisor_exit0_actual_unified_session'],
            'Game_process_exitcode_not_inferred': None,
            'S02_normal_sealed_job0': True, 'S02_terminal_owned_raw_pin_only': sealed['raw'],
            'raw_bytes_opened_or_rehashed': False, 'old73_native_body_rescan': False,
            'Root_terminal_original': 'terminal-stage/inputs/terminal.json', 'original_raw_closure_pending_retained': True,
            'actual_closure_original': 'inputs/B-actual-closure.json', 'actual_release_original': 'inputs/B-release-stdout.bin',
            'actual_sealed_original': 'inputs/B-S02-sealed-result.json',
            'merge_cohort_gate_or_commander_preserved_PASS': False,
            'new_unit_type_or_producer_cause': None, 'London_endpoint_metrics': None, 'winner': None,
            'media_audit_encoded_review_clean_spans_full_film_human_signoff_or_ABC_complete_credit': None,
            'historical_closure_media_audit_pending_preserved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY_CLOSED_B_RECEIPTS_NO_SOURCE_READS', 'entry': '--verify', 'actual_projection': None}, indent=2))
        return 0
    try:
        print(json.dumps(verify(), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'STOP_B_CLOSED_METADATA_SOURCE_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
