"""Verify the paused-pair entry without MCP, desktop, Steam or game access.

The profile written here is explicitly a hypothetical schema fixture. No
sdk-generation.json or live-argv-adoption.json is produced, so it is not a
launch preparation. Each verification directory must be new.
"""
import argparse
import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

import paused_join_pair as consumer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--release-readback', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'xar.jd11.paused-pair.offline-verification/v1', 'created_at': consumer.utc(),
              'status': 'OFFLINE_ENTRY_CHECKS_ONLY', 'checks': [], 'commands': [],
              'scope': {'mcp_initialized': False, 'game_started': False, 'screen_accessed': False,
                        'date_advanced': False, 'live_profile_created': False,
                        'new_ui_evidence_obtained': False, 'historical_truth_recomputed': False}}
    for name in ('paused_join_pair.py', 'run_paused_join_sdk.py', 'verify_offline_entry.py', 'hwnd_wgc_frame.py', 'native_locale_probe.py'):
        source = Path(__file__).with_name(name)
        copy = args.output_dir / name
        shutil.copyfile(source, copy)
        report.setdefault('sources', {})[name] = {'source': consumer.identity(source), 'preserved': consumer.identity(copy)}
        ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
    report['checks'].append('all five code files parse; actual bytes preserved')
    plan, lock, config = consumer.pinned_inputs()
    report['source_binding'] = {'head': consumer.HEAD, 'lock': consumer.identity(consumer.SEAL / 'admission-lock.json'),
                                'config': consumer.identity(consumer.CONFIG), 'sealed_plan': consumer.identity(consumer.SEAL / 'live-argv-plan.json')}
    report['checks'].append('fixed 475b source, sealed native pair/checkpoint, all selected source and a15 helper bytes match')
    for command in ([str(consumer.PYTHON), '-X', 'utf8=0', '-B', str(Path(consumer.__file__)), '--help'],
                    [str(consumer.PYTHON), '-X', 'utf8=0', '-B', str(Path(consumer.__file__)), 'prepare', '--help'],
                    [str(consumer.PYTHON), '-X', 'utf8=0', '-B', str(Path(consumer.__file__).with_name('run_paused_join_sdk.py')), '--help'],
                    [str(consumer.PYTHON), '-X', 'utf8=0', '-B', str(Path(consumer.__file__)), 'environment-probe']):
        response = subprocess.run(command, env=consumer.locale_environment(), capture_output=True, text=True, encoding='utf-8', timeout=30)
        report['commands'].append({'argv': command, 'returncode': response.returncode,
                                   'stdout': response.stdout, 'stderr': response.stderr})
        consumer.require(response.returncode == 0, 'actual offline CLI failed')
    environment = json.loads(report['commands'][-1]['stdout'])
    release = consumer.formal_release(consumer.load(args.release_readback))
    consumer.require(environment['packages']['xar-promo-toolchain'] == release['tag_name'].removeprefix('v'), 'current version mismatch')
    wheel = environment['installed_direct_url']['archive_info']['hashes']['sha256'].upper()
    consumer.require(wheel == release['wheel_sha256'].upper(), 'current wheel SHA mismatch')
    consumer.require(all(value is None for value in environment['promo_source_environment'].values()), 'unexpected source override')
    report['environment'] = environment
    consumer.require(environment['locale']['utf8_mode'] == 0
                     and environment['locale']['process_environment_overrides'] == consumer.LOCALE_OVERRIDES,
                     'actual child locale probe did not read back the required settings')
    report['process_environment_overrides'] = consumer.LOCALE_OVERRIDES
    report['latest_release_readback'] = consumer.identity(args.release_readback)
    report['checks'].append('actual verified interpreter CLI/help/dependencies, latest formal release/version/wheel SHA and null source overrides')
    hypothetical_root = args.output_dir / 'NEVER_LAUNCH-hypothetical-live-root'
    argv = consumer.substituted_argv(plan, hypothetical_root, args.release_readback,
                                     'OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH', 1, r'\\.\pipe\OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH')
    sys.path.insert(0, str(consumer.REPO / 'promo/ck3_native_war_ai/integration'))
    from d11_admission import strip_live_variants
    consumer.require(strip_live_variants(argv) == strip_live_variants(plan['argv']), 'sealed immutable argv mismatch')
    changed = list(argv)
    changed[changed.index('--frontend-timeout') + 1] = '901'
    consumer.require(strip_live_variants(changed) != strip_live_variants(plan['argv']), 'non-variant mutation escaped')
    preview = deepcopy(consumer.load(consumer.BASE))
    preview.update(offline_validation_only=True, state_directory=str(args.output_dir / 'NEVER_LAUNCH-operator-state'),
                   endpoint={'transport': 'stdio'})
    preview['jobs'] = {consumer.JOB: {'command': consumer.execution_command(argv), 'working_directory': str(consumer.REPO),
                                   'exclusive_process_names': ['ck3.exe', 'ffmpeg.exe'],
                                   'required_paths': [{'path': item['path'], 'kind': 'file', 'size': item['bytes'], 'sha256': item['sha256']}
                                                      for item in lock['files'].values()],
                                   'absent_paths': [str(hypothetical_root)], 'controls': {}}}
    preview_path = args.output_dir / 'offline-profile-shape-only.json'
    consumer.write_new(preview_path, preview)
    sys.path.insert(0, str(consumer.REPO / 'ck3_autonomous_player/src'))
    from xar_autoplayer.operator_mcp import load_operator_profile
    actual_profile = load_operator_profile(preview_path)
    consumer.require(consumer.JOB in actual_profile.jobs, 'real operator loader rejected hypothetical job')
    consumer.require(list(actual_profile.jobs[consumer.JOB].command) == consumer.execution_command(argv)
                     and consumer.execution_command(argv)[1:4] == ['-X', 'utf8=0', '-B'],
                     'operator job lost locale startup options')
    report['hypothetical_profile'] = consumer.identity(preview_path)
    report['checks'].append('actual operator profile loader accepts schema; only approved live argv variants change; non-variant mutation rejected')

    allowed_root = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-06-d11-offline-binding-fixture-20261001')
    allowed_argv = consumer.substituted_argv(plan, allowed_root, args.release_readback,
        'OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH', 1, r'\\.\pipe\OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH')
    binding = consumer.validate_frozen_ui_binding(allowed_argv)
    consumer.require(binding['status'] == 'ACTUAL_FROZEN_UI_BINDING_PASSED_NO_LAUNCH' and not allowed_root.exists(),
                     'actual frozen A04 UI binding failed or created a live path')
    report['actual_frozen_ui_binding'] = binding
    binding_rejections = []
    rejected_argv = [('old recommended external evidence root', argv),
                     ('wrong attempt prefix', consumer.substituted_argv(plan,
                        allowed_root.with_name('wrong-prefix-offline-binding-fixture'), args.release_readback,
                        'OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH', 1, r'\\.\pipe\OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH'))]
    different_output = list(allowed_argv)
    different_output[different_output.index('--output-dir') + 1] = str(allowed_root.with_name('other-output-parent') / 'ck3-output')
    rejected_argv.append(('state/output parent mismatch', different_output))
    for label, invalid_argv in rejected_argv:
        try:
            consumer.validate_frozen_ui_binding(invalid_argv)
        except (ValueError, RuntimeError) as failure:
            binding_rejections.append({'case': label, 'rejected': True, 'reason': str(failure)})
        else:
            raise AssertionError('actual UI gate accepted invalid target: ' + label)
    report['actual_ui_binding_rejections'] = binding_rejections
    report['checks'].append('actual frozen validate_a04_ui_gui_source_binding/bind_a04_ui_target pass correct AppData d11 root and reject old external root, wrong prefix and mismatched state/output; no launch paths created')

    locale_command = [str(consumer.PYTHON), '-X', 'utf8=0', '-B', str(Path(consumer.__file__).with_name('native_locale_probe.py'))]
    locale_reply = subprocess.run(locale_command, env=consumer.locale_environment(), capture_output=True,
                                  text=True, encoding='utf-8', timeout=30)
    report['commands'].append({'argv': locale_command, 'environment_overrides': consumer.LOCALE_OVERRIDES,
                               'returncode': locale_reply.returncode, 'stdout': locale_reply.stdout, 'stderr': locale_reply.stderr})
    consumer.require(locale_reply.returncode == 0, 'actual Chinese Windows native tasklist inventory probe failed')
    locale_body = json.loads(locale_reply.stdout)
    consumer.require(locale_body['utf8_mode'] == 0 and locale_body['environment_overrides'] == consumer.LOCALE_OVERRIDES
                     and isinstance(locale_body['inventory'].get('processes'), list), 'native locale inventory readback mismatch')
    report['actual_native_inventory_locale_probe'] = locale_body
    report['inventory_is_launch_approval'] = False
    report['checks'].append('actual frozen native process inventory decodes successfully under -X utf8=0 and the explicit stdio UTF-8 environment; existing CK3 is not a launch authorization')

    import hwnd_wgc_frame as window_capture
    report['wgc_library'] = window_capture.library_identity()
    sys.path.insert(0, str(window_capture.LIB / 'wgc-lib'))
    from windows_capture import WindowsCapture
    import inspect
    consumer.require('window_hwnd' in inspect.signature(WindowsCapture).parameters, 'actual WGC library lacks HWND capture option')
    state = {'expected_ck3_pid': 99, 'expected_process': {'pid': 99, 'create_time': 1, 'exe': 'synthetic/ck3.exe'},
             'desktop_size': [2560, 1440], 'focus': {'foreground_hwnd': 7, 'foreground_pid': 99},
             'mouse_buttons': {'left': False, 'right': False},
             'windows': [{'hwnd': 7, 'pid': 99, 'visible': True, 'minimized': False,
                          'window_rect': [0, 0, 1024, 768]}]}
    image_contract = {'image_kind': 'original-hwnd-wgc', 'desktop_full_frame': False,
                      'mouse_coordinate_source_allowed': False, 'before': state, 'after': deepcopy(state),
                      'target_hwnd': 7, 'events': [{'width': 1024, 'height': 768}], 'image_size': [1024, 768],
                      'foreground_required_for_input': True}
    window_capture.validate_frame(image_contract)
    rejects = [('window presented as desktop', lambda row: row.update(desktop_full_frame=True)),
               ('window presented as pointer source', lambda row: row.update(mouse_coordinate_source_allowed=True)),
               ('wrong HWND', lambda row: row.update(target_hwnd=8)),
               ('wrong process generation', lambda row: row['after']['expected_process'].update(create_time=2)),
               ('window rect changed', lambda row: row['after']['windows'][0].update(window_rect=[1, 0, 1025, 768]))]
    window_rejections = []
    for label, mutate in rejects:
        invalid = deepcopy(image_contract)
        mutate(invalid)
        try:
            window_capture.validate_frame(invalid)
        except ValueError as error:
            window_rejections.append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('WGC contract accepted invalid scope: ' + label)
    report['wgc_scope_rejections'] = window_rejections
    report['checks'].append('actual frozen WGC library exposes window_hwnd; 1024x768 window stays distinct from 2560x1440 desktop, cannot become a pointer source; HWND/process/rect drift rejected; no WGC capture instantiated')

    # Use an existing reply solely to validate the actual native response schema.
    # There is no new run, no mechanistic recalculation and no new footage claim.
    reference = Path('D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01/ck3-output/interactive-requests-responses/e2-06-d11-trace-finish.json')
    body = consumer.load(reference)['body']
    token = body['managed_daily_sequence_token']
    consumer.trace_contract(body, token)
    reject_cases = []
    mutations = [('missing exact day', lambda row: row['managed_trace']['managed_checkpoint'].update(exact_one_day_observed=False)),
                 ('wrong width army', lambda row: row['managed_trace']['trace']['runtime_join_width']['boundaries'][0].update(army_id=999)),
                 ('wrong width date', lambda row: row['managed_trace']['trace']['runtime_join_width']['boundaries'][0].update(native_date_raw=consumer.DATE)),
                 ('missing full entries', lambda row: row['managed_trace']['trace']['runtime_join_full_entries'].update(status='unavailable')),
                 ('detours not removed', lambda row: row['managed_trace']['managed_checkpoint'].update(detours_uninstalled=False))]
    for label, mutate in mutations:
        altered = deepcopy(body)
        mutate(altered)
        try:
            consumer.trace_contract(altered, token)
        except ValueError as error:
            reject_cases.append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('invalid native contract accepted: ' + label)
    report['schema_reference_only'] = consumer.identity(reference)
    report['rejection_cases'] = reject_cases
    report['checks'].append('actual native trace reply shape recognized; exact-day/battle/army/date/missing-trace/cleanup failures rejected')

    branch_cases = []
    for case in ('failed phase reply 1040', 'finish timeout with no reply', 'finish timeout with failed reply preserved'):
        order = []
        failed_body = deepcopy(body)
        failed_body['accepted'] = False
        failed_body['managed_trace']['trace'].update(status='failed', failure_flags=1040)

        def probe_after():
            order.append('native-paused-plus24-actor-control-verified')
            return {'values': {'revision': 2, 'date_raw': consumer.DATE + 24}, 'synthetic_flow_fixture_only': True}

        def finish_trace(revision):
            order.append('finish-single-attempt')
            if case == 'failed phase reply 1040':
                return failed_body, {'synthetic_receipt': True}
            raise TimeoutError('synthetic missing finish reply; no date resubmit')

        def recover_finish():
            order.append('read-preserved-finish-reply-only')
            return (failed_body if case.endswith('preserved') else None), {'synthetic_preserved_reply': True}

        def after_pixels():
            order.append('after-snapshot-control-original-ui-collected')
            return {'synthetic_flow_fixture_only': True, 'no_real_ui_claim': True}

        collected = consumer.collect_after_independent_of_trace(probe_after, finish_trace, after_pixels, recover_finish, token)
        consumer.require(order.count('after-snapshot-control-original-ui-collected') == 1
                         and order.count('finish-single-attempt') == 1
                         and collected['trace_status']['all_phase_and_join_boundaries_closed'] is False,
                         'finish failure suppressed the next-day image or promoted an incomplete trace')
        branch_cases.append({'case': case, 'callback_order': order, 'after_collection_count': 1,
                             'strict_trace_complete': False, 'date_requests_in_test': 0,
                             'actual_ui_obtained_by_test': False})
    report['after_collection_on_trace_failure_cases'] = branch_cases
    report['checks'].append('failed1040/missing finish reply/preserved failed reply each retain the after collection once; trace failure stays explicit and no date action is retried')
    values = {'revision': 1, 'native_revision': 2, 'snapshot_id': 'synthetic-identity', 'date_raw': consumer.DATE,
              'paused': True, 'actor': consumer.ACTOR, 'army_id': consumer.ARMY, 'army_state': 'combat'}
    consumer.require(consumer.same_paused_frame(values, dict(values)), 'same pause rejected')
    for key, value in (('revision', 2), ('native_revision', 3), ('snapshot_id', 'other'), ('date_raw', consumer.DATE + 24), ('paused', False)):
        consumer.require(not consumer.same_paused_frame(values, {**values, key: value}), 'pause drift accepted: ' + key)
    report['checks'].append('pause frame revision/native revision/snapshot/date/pause drift rejected')
    source_tree = ast.parse(Path(consumer.__file__).read_text(encoding='utf-8'))
    day_calls = [node for node in ast.walk(source_tree) if isinstance(node, ast.Call)
                 and any(isinstance(argument, ast.Constant) and argument.value == 'ck3_execute_step' for argument in node.args)]
    consumer.require(len(day_calls) == 1, 'consumer has more than one date action call site')
    consumer.require('from recording_continuation import' not in Path(consumer.__file__).read_text(encoding='utf-8'), 'old continuation imported')
    report['checks'].append('one date action call site; no old recording continuation import')
    # Intentionally use a real non-offline receipt: preparation must refuse
    # before writing any profile or pretending that screen authorization exists.
    refusal_output = args.output_dir / 'refused-profile-must-not-exist'
    invalid = argparse.Namespace(offline_receipt=args.release_readback, latest_release_readback=args.release_readback,
                                  screen_task_id='OFFLINE_SCHEMA_ONLY_DO_NOT_LAUNCH', screen_expected_sequence=1,
                                  live_root=hypothetical_root, output_dir=refusal_output, frame_backend='hwnd-wgc')
    try:
        consumer.prepare(invalid)
    except ValueError as error:
        report['actual_missing_offline_review_refusal'] = str(error)
    else:
        raise AssertionError('profile created without an actual offline visual review')
    consumer.require(not refusal_output.exists() and not hypothetical_root.exists(), 'refused preparation wrote live paths')
    report['checks'].append('missing actual Steam offline visual review refuses preparation and leaves launch paths absent')
    report['open_kaishek'] = consumer.open_kaishek_assessment(lock)
    report['result'] = 'OFFLINE_ENTRY_VERIFIED_LIVE_NOT_RUN'
    consumer.write_new(args.output_dir / 'offline-verification.json', report)
    print(json.dumps({'result': report['result'], 'report': consumer.identity(args.output_dir / 'offline-verification.json'),
                      'checks': len(report['checks']), 'scope': report['scope']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
