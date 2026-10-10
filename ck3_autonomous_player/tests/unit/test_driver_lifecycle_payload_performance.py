"""One new synthetic joined regression; no runtime Driver or CK3 access."""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
PIPE = r'\\.\pipe\perf-small-synthetic'
CHECKS = 0
CASES = []


def check(condition, message):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(message)


def binding(digest):
    return {'schema': 'xar.ck3.succession-lifecycle-binding/v1',
            'lifecycle': 'ordinary_campaign_succession', 'xar_enabled': 'xar_off',
            'pact_contract': 'absent_by_fresh_campaign_xar_off_contract',
            'source': 'prepared-environment-manifest', 'environment_sha256': digest}


def compact(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def install(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def result_of(call):
    try:
        return ('returned', call())
    except Exception as error:
        return ('raised', type(error).__name__, str(error))


def state_fixture(spec):
    save = b'SAV0101e741a8ef0000864d\nU1\x01\x00\x03\x00\x8f\x05\x01\x00' + b'opaque-save\x00\xff' * 4
    save_path = spec.profile_dir / 'save games/xar_checkpoint.ck3'
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(save)
    checkpoint = {'name': 'xar_checkpoint.ck3', 'size': len(save),
                  'sha256': hashlib.sha256(save).hexdigest(), 'date_raw': 53144328,
                  'history_index': 2, 'episode_character_id': 31853,
                  'episode_run_id': 'native-31853-perf-synthetic',
                  'succession_lifecycle': binding('a' * 64)}
    opaque = {'label': '完整 opaque\n : , 雪', 'bytes': 'z' * 16384,
              'ordered': [{'z': 1, 'a': False}, None, 2**63 - 1]}
    wars = {'date_raw': 53144328, 'wars': [
        {'war_id': 7, 'objective_province_states': [
            {'province_id': 4, 'active_siege': None, 'opaque': opaque},
            {'province_id': 5, 'active_siege': {'work': 2}, 'opaque': opaque}],
         'player_armies': [], 'enemy_armies': []}]}
    payload = {'format_version': 2, 'pipe_name': PIPE, 'bridge_pid': 42424,
               'episode_character_id': 31853, 'episode_run_id': 'native-31853-perf-synthetic',
               'last_checkpoint': copy.deepcopy(checkpoint), 'command_history': [
                   {'index': 1, 'command': 'observe-synthetic', 'ok': True,
                    'result': {'war_progress_before': copy.deepcopy(wars),
                               'war_progress_after': copy.deepcopy(wars), 'opaque': opaque}},
                   {'index': 2, 'command': 'save-checkpoint', 'ok': True,
                    'result': {'checkpoint': copy.deepcopy(checkpoint), 'opaque': opaque}},
                   {'index': 3, 'command': 'unconsumed-synthetic', 'ok': False,
                    'result': {'opaque': opaque, 'raw_unknown': [0, -7, 255, None]}}],
               'rollback_war_failure': None, 'rollback_war_failures': [],
               'managed_restore_transaction': None, 'succession_expectation': None,
               'succession_lifecycle': binding('a' * 64), 'unconsumed_root': opaque}
    driver = spec.state_dir / 'native-session/driver-state.json'
    driver.parent.mkdir(parents=True, exist_ok=True)
    return payload, driver, save_path, save


@contextlib.contextmanager
def count_driver_io(driver):
    counts = {'parse': 0, 'file_hash': 0, 'bytes_hash': 0, 'read_text': 0, 'read_bytes': 0}
    original_loads, original_sha = json.loads, hashlib.sha256
    original_text, original_bytes = Path.read_text, Path.read_bytes

    def loads(data, *args, **kwargs):
        if isinstance(data, (str, bytes, bytearray)) and 'perf-small-synthetic' in (
                data.decode('utf-8-sig') if not isinstance(data, str) else data):
            counts['parse'] += 1
        return original_loads(data, *args, **kwargs)

    def sha(data=b'', *args, **kwargs):
        if isinstance(data, (bytes, bytearray)) and b'perf-small-synthetic' in data:
            counts['bytes_hash'] += 1
        return original_sha(data, *args, **kwargs)

    def text(path, *args, **kwargs):
        if path.resolve() == driver.resolve():
            counts['read_text'] += 1
        return original_text(path, *args, **kwargs)

    def read_bytes(path):
        if path.resolve() == driver.resolve():
            counts['read_bytes'] += 1
        return original_bytes(path)

    import xar_autoplayer.environment as environment
    original_file_hash = environment.sha256_file

    def file_hash(path):
        if Path(path).resolve() == driver.resolve():
            counts['file_hash'] += 1
        return original_file_hash(path)

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(json, 'loads', side_effect=loads))
        stack.enter_context(mock.patch.object(hashlib, 'sha256', side_effect=sha))
        stack.enter_context(mock.patch.object(Path, 'read_text', text))
        stack.enter_context(mock.patch.object(Path, 'read_bytes', read_bytes))
        for module in (OLD_REBIND, OLD_PREFLIGHT):
            stack.enter_context(mock.patch.object(module, 'sha256_file', file_hash))
        yield counts


@contextlib.contextmanager
def no_launch(module, manifest):
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(module, 'ck3_process_inventory', return_value={'processes': []}))
        stack.enter_context(mock.patch.object(module, 'verify_profile', return_value=manifest))
        stack.enter_context(mock.patch.object(module, 'exclusive_state_lock', return_value=contextlib.nullcontext()))
        yield


def restore_three(value):
    value = copy.deepcopy(value)
    value['succession_lifecycle'] = binding('a' * 64)
    value['last_checkpoint']['succession_lifecycle'] = binding('a' * 64)
    index = value['last_checkpoint']['history_index'] - 1
    value['command_history'][index]['result']['checkpoint']['succession_lifecycle'] = binding('a' * 64)
    return value


def check_consumers(payload, driver):
    driver.write_bytes(compact(payload))
    old = OLD_DRIVER.load_native_driver_state_for_resume(driver, PIPE)
    raw = copy.deepcopy(payload)
    before = compact(raw)
    new = NEW_DRIVER.load_native_driver_state_for_resume_payload(raw, PIPE)
    check(compact(new) == compact(old), 'Complete legacy normalized output or key order changed')
    check(compact(raw) == before, 'Full normalized consumer mutated the supplied raw payload')
    thin = NEW_DRIVER.load_native_driver_state_for_resume_payload(raw, PIPE, include_command_history=False)
    expected = {key: value for key, value in old.items() if key != 'command_history'}
    check(compact(thin) == compact(expected), 'Validation-only result differs outside omitted history')
    check(compact(raw) == before, 'Validation-only call mutated the raw history')
    check(len(new['command_history'][0]['result']['war_progress_before']['wars'][0]['objective_province_states']) == 1,
          'Existing active-siege compaction was not preserved')
    new['command_history'][0]['result']['opaque']['label'] = 'caller edit'
    check(compact(raw) == before, 'Returned history aliases raw input')
    with mock.patch.object(NEW_DRIVER, '_resume_command_history_projection', side_effect=AssertionError('history copied')):
        check(NEW_DRIVER.load_native_driver_state_for_resume_payload(raw, PIPE, include_command_history=False) == thin,
              'Thin call materialized history')
    mutations = [lambda p: p.update(format_version=99), lambda p: p.update(pipe_name='other'),
                 lambda p: p.update(bridge_pid=True), lambda p: p.update(episode_run_id=None),
                 lambda p: p['command_history'][2].update(index=88), lambda p: p.update(last_checkpoint=[]),
                 lambda p: p.update(rollback_war_failures={}), lambda p: p.update(succession_lifecycle={})]
    for mutate in mutations:
        bad = copy.deepcopy(payload)
        mutate(bad)
        driver.write_bytes(compact(bad))
        old_error = result_of(lambda: OLD_DRIVER.load_native_driver_state_for_resume(driver, PIPE))
        new_error = result_of(lambda: NEW_DRIVER.load_native_driver_state_for_resume_payload(bad, PIPE))
        check(old_error == new_error, 'Consumer validation result/error changed')
    CASES.append('legacy-full-and-thin-consumer-equivalence-immutability-rejections')


def check_cold(payload, spec, driver, save_path, save):
    driver.write_bytes(compact(payload))
    before = compact(payload)
    check(OLD_SESSION.validate_cold_start_checkpoint_for_pipe(spec, PIPE) ==
          PURE_COLD.validate_cold_start_checkpoint_payload_for_pipe(spec, PIPE, payload), 'Cold validator result changed')
    check(compact(payload) == before, 'Cold validator mutated supplied payload')
    faults = [lambda p: p.update(format_version=1), lambda p: p.update(pipe_name='other'),
              lambda p: p['last_checkpoint'].update(history_index=99),
              lambda p: p['command_history'][1]['result']['checkpoint'].update(sha256='c' * 64),
              lambda p: p['last_checkpoint'].update(succession_lifecycle=binding('c' * 64))]
    for mutate in faults:
        bad = copy.deepcopy(payload)
        mutate(bad)
        driver.write_bytes(compact(bad))
        check(result_of(lambda: OLD_SESSION.validate_cold_start_checkpoint_for_pipe(spec, PIPE)) ==
              result_of(lambda: PURE_COLD.validate_cold_start_checkpoint_payload_for_pipe(spec, PIPE, bad)),
              'Cold validator rejected differently')
    driver.write_bytes(compact(payload))
    save_path.write_bytes(save + b'changed')
    check(result_of(lambda: OLD_SESSION.validate_cold_start_checkpoint_for_pipe(spec, PIPE)) ==
          result_of(lambda: PURE_COLD.validate_cold_start_checkpoint_payload_for_pipe(spec, PIPE, payload)),
          'Cold save-integrity error changed')
    save_path.write_bytes(save)
    CASES.append('pure-cold-validator-anchor-save-errors-and-input-immutability')


def check_rebind(payload, spec, driver, save_path, save, manifest):
    results = []
    for module in (OLD_REBIND, NEW_REBIND):
        driver.write_bytes(compact(payload))
        with no_launch(module, manifest), count_driver_io(driver) as counts:
            receipt = module.rebind_ordinary_seed_v1(spec, expected_pipe_name=PIPE,
                                                   lock_factory=module.exclusive_state_lock)
        results.append((receipt, driver.read_bytes(), dict(counts)))
        check(save_path.read_bytes() == save, 'Rebind changed opaque save')
    check(results[0][0] == results[1][0], 'Rebind receipt differs')
    check(results[0][1] == results[1][1], 'Complete persisted Driver bytes/order changed')
    target = json.loads(results[1][1].decode('utf-8-sig'))
    check(compact(restore_three(target)) == compact(payload), 'Fields outside the three lifecycle anchors changed')
    check(results[0][2]['parse'] == 5 and results[1][2]['parse'] == 2, 'Rebind parse count did not fall from5 to2')
    check(results[0][2]['file_hash'] == 2 and results[1][2]['file_hash'] == 0
          and results[1][2]['bytes_hash'] == 2, 'Rebind file hash passes were not replaced by source/readback byte hashes')
    check(results[1][2]['read_bytes'] == 2 and results[1][2]['read_text'] == 0, 'Rebind rereads unchanged Driver')
    check(results[1][0]['driver_state']['target_sha256'] == hashlib.sha256(results[1][1]).hexdigest(),
          'Target digest is not the actual persisted readback digest')
    # Sharing unchanged history is safe because all changed ancestors and all
    # three mutable binding objects are independently copied.
    raw = copy.deepcopy(payload)
    rebound = NEW_REBIND._replace_lifecycle_anchors(raw, binding('b' * 64))
    check(compact(raw) == compact(payload), 'Path-copy replacement mutated source')
    check(rebound['command_history'][0] is raw['command_history'][0], 'Unchanged opaque history row was copied')
    anchors = [rebound['succession_lifecycle'], rebound['last_checkpoint']['succession_lifecycle'],
               rebound['command_history'][1]['result']['checkpoint']['succession_lifecycle']]
    check(len({id(value) for value in anchors}) == 3, 'The three bindings alias one another')
    anchors[0]['environment_sha256'] = 'c' * 64
    check(anchors[1]['environment_sha256'] == anchors[2]['environment_sha256'] == 'b' * 64,
          'Binding mutation leaked between anchors')
    # Inject the same postwrite failure after one successful validation. Raw
    # bytes (including pretty/BOM representation) must be restored exactly.
    original = ('\ufeff' + json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    for module, name in ((OLD_REBIND, 'validate_cold_start_checkpoint_for_pipe'),
                         (NEW_REBIND, 'validate_cold_start_checkpoint_payload_for_pipe')):
        driver.write_bytes(original)
        real = getattr(module, name)
        calls = [0]
        def fail_second(*args):
            calls[0] += 1
            if calls[0] == 2:
                raise RuntimeError('injected synthetic postwrite RED')
            return real(*args)
        with no_launch(module, manifest), mock.patch.object(module, name, side_effect=fail_second):
            error = result_of(lambda: module.rebind_ordinary_seed_v1(spec, expected_pipe_name=PIPE,
                                                                  lock_factory=module.exclusive_state_lock))
        check(error == ('raised', 'RuntimeError', 'injected synthetic postwrite RED'), 'Postwrite error changed')
        check(driver.read_bytes() == original, 'Rollback did not restore exact raw BOM/pretty bytes')
    CASES.append('joined-rebind-complete-bytes-three-anchors-rollback-and-operation-counts')
    return {'old': results[0][2], 'new': results[1][2]}


def normalize_report(report):
    report = copy.deepcopy(report)
    for key in ('run_id', 'started_at', 'finished_at', 'run_dir', 'report_path'):
        report.pop(key, None)
    return report


def check_preflight(payload, spec, driver, manifest):
    results = []
    checkpoint_digest = payload['last_checkpoint']['sha256']
    for module in (OLD_PREFLIGHT, NEW_PREFLIGHT):
        driver.write_bytes(compact(payload))
        digest = hashlib.sha256(driver.read_bytes()).hexdigest()
        with no_launch(module, manifest), count_driver_io(driver) as counts:
            report = module.native_one_generation_preflight(spec, pipe_name=PIPE,
                expected_character_id=31853, expected_episode_run_id='native-31853-perf-synthetic',
                expected_checkpoint_sha256=checkpoint_digest, expected_driver_state_sha256=digest,
                xar_enabled='xar_off', succession_lifecycle='ordinary_campaign_succession',
                ordinary_campaign_no_pact=True)
        results.append((normalize_report(report), dict(counts)))
        check(report['ok'] is True, 'Synthetic preflight unexpectedly blocked')
    check(results[0][0] == results[1][0], 'Preflight identity/lifecycle/artifact report differs')
    check(results[0][1]['parse'] == 2 and results[1][1]['parse'] == 1, 'Preflight parses did not fall from2 to1')
    check(results[0][1]['file_hash'] == 1 and results[1][1]['file_hash'] == 0
          and results[1][1]['bytes_hash'] == 1, 'Preflight reused-byte digest failed')
    check(results[1][1]['read_bytes'] == 1 and results[1][1]['read_text'] == 0, 'Preflight driver reread remained')
    # Expected digest mismatches retain their old blocked report/error.
    errors = []
    for module in (OLD_PREFLIGHT, NEW_PREFLIGHT):
        with no_launch(module, manifest):
            report = module.native_one_generation_preflight(spec, pipe_name=PIPE,
                expected_character_id=31853, expected_episode_run_id='native-31853-perf-synthetic',
                expected_checkpoint_sha256=checkpoint_digest, expected_driver_state_sha256='0' * 64,
                xar_enabled='xar_off', succession_lifecycle='ordinary_campaign_succession',
                ordinary_campaign_no_pact=True)
        errors.append(normalize_report(report))
        check(report['ok'] is False, 'Expected digest mismatch did not block')
    check(errors[0] == errors[1], 'Preflight failure report/error changed')
    CASES.append('joined-preflight-exact-report-errors-and-operation-counts')
    return {'old': results[0][1], 'new': results[1][1]}


def main(argv=None):
    """Run the four existing groups against an explicit legacy source tree.

    The recipe contains repository-relative candidate paths and their pins.
    Synthetic files use a temporary directory unless --output-root is supplied.
    This entry never obtains legacy source from Git or accesses a live Driver.
    """
    global OLD_DRIVER, OLD_SESSION, OLD_REBIND, OLD_PREFLIGHT
    global NEW_DRIVER, PURE_COLD, NEW_SESSION, NEW_REBIND, NEW_PREFLIGHT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-source-root', required=True, type=Path,
                        help='Legacy checkout src directory containing xar_autoplayer')
    parser.add_argument('--recipe', required=True, type=Path,
                        help='JSON containing candidate_maps with repository_path and sha256')
    parser.add_argument('--output-root', type=Path,
                        help='Optional synthetic output directory; otherwise temporary')
    args = parser.parse_args(argv)
    recipe = json.loads(args.recipe.read_text(encoding='utf-8'))
    require_paths = [REPO / row['repository_path'] for row in recipe['candidate_maps']]
    check(all(path.resolve().is_relative_to(REPO.resolve()) for path in require_paths),
          'Candidate sources must all be inside the repository')
    for row, path in zip(recipe['candidate_maps'], require_paths):
        check(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'],
              'Frozen candidate pin changed')
    sys.path.insert(0, str(args.baseline_source_root.resolve()))
    # Capture the legacy modules before installing the same candidate modules.
    OLD_DRIVER = importlib.import_module('xar_autoplayer.bridge.native_driver')
    OLD_SESSION = importlib.import_module('xar_autoplayer.native_session')
    OLD_REBIND = importlib.import_module('xar_autoplayer.ordinary_seed_rebinder')
    OLD_PREFLIGHT = importlib.import_module('xar_autoplayer.one_generation_preflight')
    maps = {row['repository_path'].rsplit('/', 1)[-1]: REPO / row['repository_path']
            for row in recipe['candidate_maps']}
    NEW_DRIVER = install('xar_autoplayer.bridge.native_driver', maps['native_driver.py'])
    PURE_COLD = install('xar_autoplayer.cold_checkpoint_validator', maps['cold_checkpoint_validator.py'])
    NEW_SESSION = install('xar_autoplayer._performance_native_session', maps['native_session.py'])
    NEW_REBIND = install('xar_autoplayer._performance_rebinder', maps['ordinary_seed_rebinder.py'])
    NEW_PREFLIGHT = install('xar_autoplayer._performance_preflight', maps['one_generation_preflight.py'])
    from xar_autoplayer.environment import EnvironmentSpec
    output_context = (contextlib.nullcontext(args.output_root) if args.output_root is not None
                      else tempfile.TemporaryDirectory(prefix='xar-driver-payload-performance-'))
    with output_context as output_root:
        OUT = Path(output_root)
        OUT.mkdir(parents=True, exist_ok=True)
        spec = EnvironmentSpec(OUT / 'synthetic-state', OUT / 'synthetic-game')
        payload, driver, save_path, save = state_fixture(spec)
        manifest = {'environment_sha256': 'b' * 64,
                    'rules': {'profile': [{'rule': 'xar_enabled', 'setting': 'xar_off'}]}}
        try:
            check_consumers(payload, driver)
            check_cold(payload, spec, driver, save_path, save)
            rebind_counts = check_rebind(payload, spec, driver, save_path, save, manifest)
            rebound = json.loads(driver.read_text(encoding='utf-8-sig'))
            # check_rebind ends on rollback source; preflight requires the prepared
            # target environment, so use the exact path-copy binding projection.
            rebound = NEW_REBIND._replace_lifecycle_anchors(payload, binding('b' * 64))
            preflight_counts = check_preflight(rebound, spec, driver, manifest)
            result = {'status': 'GREEN', 'new_groups': CASES, 'checks': CHECKS,
                      'rebind_driver_operations': rebind_counts, 'preflight_driver_operations': preflight_counts,
                      'real_Driver_body_reads': 0, 'Game_SDK_Git_calls': 0,
                      'old_test_matrix_replays': 0, 'real_3GB_speed': 'UNKNOWN_NEXT_COLD_MEASUREMENT_REQUIRED'}
        except Exception as error:
            result = {'status': 'RED', 'completed_groups': CASES, 'checks': CHECKS,
                      'error': f'{type(error).__name__}: {error}', 'real_Driver_body_reads': 0,
                      'Game_SDK_Git_calls': 0, 'old_test_matrix_replays': 0}
            (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            raise
        (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    main()
