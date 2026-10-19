"""P51 C11 cold checkpoint primitive; never rewrites a Driver or SAVE.

Copy this source as root_checkpoint_bootstrap_c11.py beside the actual receipts.
Only the sole runtime operator calls prepare_prelaunch/launch_prepared.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
N = Path(__file__).resolve().parent
FREEZE = 'ROOT-FINAL-SDK-FREEZE-P37C11.json'
PRELAUNCH = 'ROOT-C11-COLD-PRELAUNCH.json'


def require(ok, why):
    if not ok:
        raise ValueError('C11 canonical cold denied: ' + why)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            result.update(block)
    return result.hexdigest()


def read(path, limit=262144):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'oversized metadata: ' + str(path))
    value = json.loads(raw)
    require(isinstance(value, dict), 'object metadata required')
    return value


def checked(ref, limit=262144):
    path = Path(ref['path']).resolve(strict=True)
    require(path.stat().st_size == ref['bytes'] and ref['bytes'] <= limit
        and sha(path) == ref['sha256'], 'exact bounded receipt differs: ' + str(path))
    return read(path, limit)


def pin(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def api():
    """Use the admitted Host and business roots as two separate source domains."""
    frozen = read(N / FREEZE, 2*1024**2)
    repo = Path(frozen['runtime_source_repo']).resolve(strict=True)
    source = Path(frozen['source_root']).resolve(strict=True)
    sys.path.insert(0, str(repo / 'tools'))
    sys.path.insert(0, str(repo / 'ck3_autonomous_player/src'))
    sys.path.insert(0, str(source))
    import xar_autoplayer
    xar_autoplayer.__path__[:] = [str(source / 'xar_autoplayer')]
    from xar_autoplayer import environment, native_session, runtime
    for module, name in ((environment, 'environment.py'), (native_session, 'native_session.py'), (runtime, 'runtime.py')):
        actual = Path(module.__file__).resolve()
        require(actual in {source / 'xar_autoplayer' / name, repo / 'ck3_autonomous_player/src/xar_autoplayer' / name}
            and sha(actual) == sha(source / 'xar_autoplayer' / name), 'cached foreign canonical API source')
    environment.REPO_ROOT = repo
    environment.TOOLS_DIR = repo / 'tools'
    return environment, native_session, runtime


def validate_actual_checkpoint(validation, checkpoint):
    require(all(validation.get(key) == checkpoint.get(other) for key, other in (
        ('size', 'size'), ('sha256', 'sha256'), ('saved_date_raw', 'date_raw'),
        ('history_index', 'history_index'), ('succession_lifecycle', 'succession_lifecycle')))
        and validation.get('name') == checkpoint.get('name')
        and validation.get('load_save_name') == 'xar_checkpoint'
        and Path(validation.get('path', '')).resolve() == Path(checkpoint['path']).resolve(),
        'canonical validator did not accept the actual new SAVE')


def prepare_prelaunch(spec, *, save_response, final_driver_close, pipe_name, output_path):
    """Read the real post-close Driver/SAVE once through the existing validator.

    final_driver_close is a small source-bound receipt, not the Driver body. Its
    driver_state pin names the canonical state file; any protected frozen copy
    is listed separately by the operator. All closure receipts remain original.
    """
    _, native_session, _ = api()
    save = checked(save_response)
    result = save.get('result') or {}
    checkpoint = (result.get('structured_content') or {}).get('checkpoint')
    require(save.get('client_error') is None and result.get('is_error') is False
        and result.get('result_type') == 'complete'
        and save.get('request', {}).get('tool') == 'ck3_save_checkpoint'
        and isinstance(checkpoint, dict), 'actual completed normal SAVE required')
    close = checked(final_driver_close)
    require(close.get('machine_id') == MACHINE and close.get('checkpoint') == checkpoint
        and close.get('original_command_history_preserved') is True
        and type(close.get('history_rows')) is int and close['history_rows'] >= checkpoint['history_index'],
        'actual post-close Driver/checkpoint/history provenance required')
    sdk = checked(close['sdk_closed'])
    require(sdk.get('normal') is True and sdk.get('machine_id') == MACHINE
        and sdk.get('launcher_exit_code') == 0 and len(sdk.get('processes', [])) == 2
        and all(p.get('exit_code') == 0 and p.get('kernel_exit_observed') is True
            and p.get('observation_error') is None for p in sdk['processes']), 'normal actual SDK kernel closure required')
    game = checked(close['Game_exit'])
    require(game.get('machine_id') == MACHINE and game.get('kernel_signaled') is True
        and type(game.get('exit_code')) is int and game.get('pid') == close['old_Game']['pid']
        and game.get('creation_filetime') == close['old_Game']['creation_filetime'],
        'actual old Game kernel closure required; nonzero exit remains recorded')
    recording = checked(close['recording_shutdown'])
    require(recording.get('status') == 'CLEANUP_OBSERVED' and recording.get('inputs_unbound') is True
        and recording.get('decision_text_publisher', {}).get('status') == 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO',
        'old recording inputs and publisher must actually be closed')
    state_path = (spec.state_dir / native_session.NATIVE_SESSION_QUEUE_DIRNAME
        / native_session.NATIVE_DRIVER_STATE_FILENAME).resolve()
    require(Path(close['driver_state']['path']).resolve() == state_path
        and pin(state_path) == close['driver_state'], 'actual canonical post-close Driver changed')
    for ref in close['sidecars']:
        require(pin(ref['path']) == {k: ref[k] for k in ('path', 'bytes', 'sha256')},
            'post-close sidecar changed')
    validation = native_session.validate_cold_start_checkpoint_for_pipe(spec, pipe_name)
    validate_actual_checkpoint(validation, checkpoint)
    manifest = read(spec.manifest_path)
    pre = {'schema': 'xar.c11.canonical-cold-prelaunch/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'EXACT_CLOSED_CHECKPOINT_COLD_INPUT_VALIDATED',
        'validator_api': 'xar_autoplayer.native_session.validate_cold_start_checkpoint_for_pipe',
        'final_driver_close': final_driver_close, 'save_response': save_response,
        'driver_state': close['driver_state'], 'sidecars': close['sidecars'],
        'checkpoint': checkpoint, 'pipe_name': pipe_name, 'validation': validation,
        'environment_sha256': manifest['environment_sha256'], 'Game_created': False,
        'Driver_or_SAVE_modified': False}
    output = Path(output_path).resolve()
    require(output == (N / PRELAUNCH).resolve(), 'exact create-only prelaunch target required')
    with output.open('xb') as stream:
        stream.write((json.dumps(pre, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pre


def verify_cold_profile(spec):
    environment, native_session, _ = api()
    manifest = read(spec.manifest_path)
    pre = read(N / PRELAUNCH)
    require(pre.get('machine_id') == MACHINE
        and pre.get('status') == 'EXACT_CLOSED_CHECKPOINT_COLD_INPUT_VALIDATED'
        and Path(manifest['state_dir']).resolve() == spec.state_dir.resolve()
        and Path(manifest['profile_dir']).resolve() == spec.profile_dir.resolve()
        and manifest['load_profile']['enabled_mods'] == []
        and manifest['mod'] == {'enabled': False, 'mounted_mods': []}
        and read(spec.profile_dir / 'dlc_load.json') == {'enabled_mods': [], 'disabled_dlcs': []}
        and sha(spec.profile_dir / 'dlc_load.json') == manifest['load_profile']['dlc_load_sha256']
        and not any(row['rule'].startswith('xar_') for row in manifest['rules']['profile'])
        and not ((spec.profile_dir / 'mod').exists() and any((spec.profile_dir / 'mod').iterdir()))
        and environment._contract_digest(manifest) == manifest['environment_sha256'] == pre['environment_sha256'],
        'actual same-profile vanilla ordinary environment differs')
    close = checked(pre['final_driver_close'])
    require(close['driver_state'] == pre['driver_state'] and close['sidecars'] == pre['sidecars']
        and close['checkpoint'] == pre['checkpoint'], 'post-close provenance differs')
    require(pin(pre['driver_state']['path']) == pre['driver_state'], 'post-close Driver changed before launch')
    for ref in pre['sidecars']:
        require(pin(ref['path']) == {k: ref[k] for k in ('path', 'bytes', 'sha256')}, 'post-close sidecar changed')
    expected = native_session.validate_cold_start_checkpoint_for_pipe(spec, pre['pipe_name'])
    validate_actual_checkpoint(expected, pre['checkpoint'])
    require(expected == pre['validation'], 'canonical cold validation changed after prelaunch')
    return manifest


def launch_prepared(spec, dll, injector, *, before_process_create=None, pre_native_resume=None):
    _, native_session, runtime = api()
    verify_cold_profile(spec)
    pre = read(N / PRELAUNCH)
    native_session.validate_cold_start_checkpoint_for_pipe(spec, pre['pipe_name'])
    bridge = runtime.NativeBridgeLaunchConfig('native-headless', pre['pipe_name'], Path(dll), Path(injector))
    return runtime.launch(spec, native_bridge=bridge, continue_last_save=False,
        load_save_name='xar_checkpoint', verify_prepared_profile=False,
        start_minimized=True, before_process_create=before_process_create,
        **({"pre_native_resume": pre_native_resume} if pre_native_resume is not None else {}))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--save-response', type=Path, required=True)
    parser.add_argument('--final-driver-close', type=Path, required=True)
    parser.add_argument('--pipe-name', required=True)
    args = parser.parse_args()
    environment, _, _ = api()
    spec = environment.make_spec(state_dir=N/'state', game_dir=args.game_dir.resolve())
    result = prepare_prelaunch(spec, save_response=pin(args.save_response),
        final_driver_close=pin(args.final_driver_close), pipe_name=args.pipe_name,
        output_path=N/PRELAUNCH)
    print(json.dumps({'status': result['status'], 'prelaunch': pin(N/PRELAUNCH),
        'Game_created': False, 'Driver_or_SAVE_modified': False}))


if __name__ == '__main__':
    main()
