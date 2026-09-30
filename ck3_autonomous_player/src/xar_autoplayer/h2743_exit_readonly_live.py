"""Prepare H2743 source bytes or run one explicitly admitted paused read.

The managed session and query driver share this process. One lease keeper is
the sole renewal owner and gates native process creation. There are no peace,
surrender, movement or date-advance actions in this entry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import threading
import time
from types import MethodType

from .h2743_exit_source_pair import read_object, require, sha256, verify_pair
from .bridge.h2743_exit_readonly_transport import (
    OPTIONS_STEP, frame_key, query_h2743_exit_baseline, target_frame,
)

GAME_EXE_SHA256 = '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
WAR_VALUES_SHA256 = 'ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B'
EPISODE = 'native-29829-2bc2d599f7f9'
PIPE = r'\\.\pipe\xar-g2-robert-1066-seed-66f926d'


def write_new(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def runtime_fingerprint() -> dict:
    root = Path(__file__).resolve().parents[3]
    files = ['ck3_autonomous_player/src/xar_autoplayer/runtime.py',
             'ck3_autonomous_player/src/xar_autoplayer/native_session.py',
             'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
             'ck3_autonomous_player/src/xar_autoplayer/h2743_exit_readonly_live.py',
             'ck3_autonomous_player/src/xar_autoplayer/h2743_exit_source_pair.py',
             'ck3_autonomous_player/src/xar_autoplayer/bridge/h2743_exit_readonly_transport.py',
             'ck3_autonomous_player/src/xar_autoplayer/bridge/defender_dejure_exit_terms_v1.py',
             'promo/ck3_native_war_ai/integration/screen_bus_lease.py']
    return {'root': str(root), 'files': {name: sha256(root / name) for name in files}}


def check_game(game_dir: Path) -> None:
    require(sha256(game_dir / 'binaries/ck3.exe') == GAME_EXE_SHA256, 'H2743 exact CK3 EXE changed')
    require(sha256(game_dir / 'game/common/script_values/00_war_values.txt') == WAR_VALUES_SHA256,
            'H2743 stock war values changed')


def prepare(source: dict, game_dir: Path, output: Path) -> dict:
    from .environment import EnvironmentSpec, prepare_profile
    from .ordinary_seed_rebinder import rebind_ordinary_seed_v1
    from .one_generation_preflight import native_one_generation_preflight

    check_game(game_dir)
    spec = EnvironmentSpec(state_dir=output / 'state', game_dir=game_dir, expected_game_version='1.19.0.6')
    profile = prepare_profile(spec, xar_enabled='xar_off', display_mode='windowed')
    write_new(output / 'profile-preparation.json', profile)
    targets = {'xar_checkpoint.ck3': spec.profile_dir / 'save games/xar_checkpoint.ck3',
               'driver-state.json': spec.state_dir / 'native-session/driver-state.json',
               'first-heir-marriage-formal-v1.json': spec.state_dir / 'first-heir-marriage-formal-v1.json'}
    for name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), f'H2743 preparation target already exists: {target}')
        shutil.copyfile(Path(source['source_quartet'][name]['path']), target)
        require(sha256(target) == source['source_quartet'][name]['sha256'], f'H2743 copied input differs: {name}')
    rebind = rebind_ordinary_seed_v1(spec, expected_pipe_name=PIPE)
    write_new(output / 'rebind.json', rebind)
    derived_sha = sha256(targets['driver-state.json'])
    preflight = native_one_generation_preflight(
        spec, pipe_name=PIPE, expected_character_id=29829, expected_episode_run_id=EPISODE,
        expected_checkpoint_sha256=source['source_quartet']['xar_checkpoint.ck3']['sha256'],
        expected_driver_state_sha256=derived_sha, xar_enabled='xar_off',
        succession_lifecycle='ordinary_campaign_succession', ordinary_campaign_no_pact=True)
    write_new(output / 'native-one-generation-preflight.json', preflight)
    require(preflight.get('ok') is True, 'H2743 native no-launch preflight did not return ok')
    result = {'schema': 'xar.ck3.h2743.managed-prepared-source.v1',
              'status': 'READY_NO_LAUNCH', 'state_dir': str(spec.state_dir.resolve()),
              'pair_sha256': source['pair_sha256'], 'runtime_fingerprint': runtime_fingerprint(),
              'pipe_name': PIPE, 'derived_driver_sha256': derived_sha,
              'environment_sha256': sha256(spec.manifest_path),
              'prepared_input_paths': {name: str(target) for name, target in targets.items()},
              'prepared_input_sha256': {name: sha256(target) for name, target in targets.items()},
              'preflight_sha256': sha256(output / 'native-one-generation-preflight.json'),
              'ck3_started': False, 'gameplay_actions': 0, 'date_advance_actions': 0}
    write_new(output / 'prepared-source.json', result)
    return result


def check_prepared(path: Path, source: dict) -> dict:
    body = read_object(path)
    require(body.get('schema') == 'xar.ck3.h2743.managed-prepared-source.v1'
            and body.get('status') == 'READY_NO_LAUNCH' and body.get('ck3_started') is False,
            'H2743 prepared input receipt is unavailable')
    require(body.get('pair_sha256') == source['pair_sha256']
            and body.get('runtime_fingerprint') == runtime_fingerprint(),
            'H2743 prepared source or Python runtime changed')
    require(body.get('pipe_name') == PIPE, 'H2743 prepared pipe differs')
    for name, value in body['prepared_input_paths'].items():
        require(sha256(Path(value)) == body['prepared_input_sha256'][name],
                f'H2743 prepared input changed: {name}')
    state = Path(body['state_dir'])
    from .environment import PROFILE_MANIFEST_NAME
    require(sha256(state / 'profile' / PROFILE_MANIFEST_NAME) == body['environment_sha256'],
            'H2743 prepared environment changed')
    preflight_path = path.parent / 'native-one-generation-preflight.json'
    require(sha256(preflight_path) == body['preflight_sha256']
            and read_object(preflight_path).get('ok') is True,
            'H2743 prepared no-launch preflight changed')
    return body


def check_steam_gate(path: Path, *, task_id: str) -> dict:
    gate = read_object(path)
    require(gate.get('task_id') == task_id and gate.get('steam_offline_visible') is True
            and bool(gate.get('reviewer')), 'H2743 fresh Steam offline review absent')
    reviewed = datetime.fromisoformat(gate['reviewed_at_utc'].replace('Z', '+00:00'))
    require(reviewed.tzinfo is not None and 0 <= (datetime.now(timezone.utc) - reviewed).total_seconds() <= 600,
            'H2743 Steam review is stale')
    image, frame_path = Path(gate['screenshot_path']), Path(gate['fresh_frame_receipt_path'])
    require(sha256(image) == gate['screenshot_sha256'], 'H2743 Steam screenshot changed')
    frame = read_object(frame_path)
    captured = datetime.fromisoformat(frame['captured_at_utc'].replace('Z', '+00:00'))
    require(frame.get('schema') == 'ck3.steam_fresh_desktop_frame.v1'
            and frame.get('moving_edge_changed') is True and Path(frame['moved_path']) == image
            and frame['moved_sha256'].upper() == sha256(image)
            and captured.tzinfo is not None and 0 <= (reviewed - captured).total_seconds() <= 600,
            'H2743 Steam screenshot lacks a fresh frame binding')
    return {'path': str(path.resolve()), 'sha256': sha256(path),
            'screenshot_sha256': sha256(image), 'fresh_frame_receipt_sha256': sha256(frame_path)}


def run_owned_read(*, spec, config, keeper, output: Path, timeout_seconds: float = 1800) -> dict:
    from .bridge.native_driver import NativeHeadlessGameplayDriver
    from .bridge.driver import BridgeUnavailableError
    from .native_session import native_session
    from .runtime import ck3_process_inventory
    from .environment import verify_profile
    from .bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, bind_succession_lifecycle_from_environment_v1,
    )

    require(0 < timeout_seconds <= 1800, 'H2743 readiness deadline must be within 1..1800 seconds')
    require(not ck3_process_inventory()['processes'], 'H2743 read requires zero CK3 processes')
    abort, done = keeper.abort, threading.Event()
    session, driver, thread = {}, None, None
    report = {'status': 'RED', 'query_attempts': 0, 'gameplay_actions': 0,
              'date_advance_actions': 0, 'material_complete': False, 'action_literal': None}

    def supervise():
        try:
            session['report'] = native_session(
                spec, timeout_seconds=timeout_seconds + 1200, native_bridge=config,
                cold_start_checkpoint=True, prepared_xar_enabled='xar_off', stop_event=abort,
                before_process_create=keeper.process_create_gate)
        except BaseException as error:
            session['error'] = f'{type(error).__name__}: {error}'
        finally:
            done.set()

    keeper.start()
    try:
        keeper.refresh()
        lifecycle = bind_succession_lifecycle_from_environment_v1(
            verify_profile(spec, xar_enabled='xar_off'),
            lifecycle=ORDINARY_CAMPAIGN_SUCCESSION, ordinary_campaign_no_pact=True)
        driver = NativeHeadlessGameplayDriver(config.pipe_name, state_dir=spec.state_dir,
                                              save_dir=spec.profile_dir / 'save games',
                                              succession_lifecycle_binding=lifecycle)
        driver.query_h2743_exit_baseline = MethodType(query_h2743_exit_baseline, driver)
        thread = threading.Thread(target=supervise, name='h2743-managed-session')
        thread.start()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            keeper.require_live()
            require(not done.is_set(), f'H2743 native session exited before paused frame: {session}')
            try:
                before = driver.take_snapshot()
            except BridgeUnavailableError as error:
                report['last_readiness_error'] = str(error)
                time.sleep(0.1)
                continue
            if target_frame(before) is not None:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('H2743 paused frame was not ready within the original 1800-second bound')
        write_new(output / 'before-frame.json', before)
        values = []
        for number in (1, 2):
            keeper.require_live()
            report['query_attempts'] += 1
            value = driver.query_h2743_exit_baseline(expected_frame=before)
            write_new(output / f'baseline-{number}.json', value)
            values.append(value['defender_de_jure_exit_terms_v1'])
            if number == 1:
                keeper.require_live()
                report['query_attempts'] += 1
                options = driver.execute_step(OPTIONS_STEP, expected_revision=before['revision'])
                write_new(output / 'termination-options.json', options)
                require(options.get('accepted') is True and options.get('status') == 'available'
                        and options.get('war_termination_options', {}).get('war_id') == 16777231,
                        'H2743 read-only termination options unavailable')
        after = driver.take_snapshot()
        write_new(output / 'after-frame.json', after)
        require(target_frame(after) == target_frame(before) and frame_key(after) == frame_key(before),
                'H2743 same paused frame changed after the three queries')
        require(values[0] == values[1], 'H2743 double baseline read disagrees')
        report['baseline'] = values[0]
        report['same_frame_double_read'] = True
        report['stock_border_raid_pair_observed'] = False
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        abort.set()
        if thread is not None:
            thread.join(timeout=180)
        try:
            if driver is not None:
                driver.close()
        except BaseException as error:
            report['error'] = f'H2743 driver close failed: {type(error).__name__}: {error}'
        finally:
            try:
                keeper.stop()
            except BaseException as error:
                report['error'] = f'H2743 keeper stop failed: {type(error).__name__}: {error}'
        report['session'] = session
        report['lease'] = keeper.report()
        report['session_thread_exited'] = thread is None or not thread.is_alive()
        report['final_ck3_inventory'] = ck3_process_inventory()
        shutdown = session.get('report', {}).get('shutdown', {})
        report['managed_cleanup_verified'] = (
            report['session_thread_exited'] and shutdown.get('cleanup_proven') is True
            and report['final_ck3_inventory']['processes'] == [])
        if 'error' not in report and report['managed_cleanup_verified'] and report['lease'].get('failure') is None:
            report['status'] = 'READONLY_BASELINE_AVAILABLE_MATERIAL_PENDING'
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--no-launch', action='store_true')
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--pair-manifest', type=Path, required=True)
    parser.add_argument('--native-source-checkout', type=Path, required=True)
    parser.add_argument('--attempt-dir', type=Path, required=True)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--prepared-manifest', type=Path)
    parser.add_argument('--go', type=Path)
    parser.add_argument('--steam-gate', type=Path)
    parser.add_argument('--round-id')
    parser.add_argument('--screen-task-id')
    parser.add_argument('--screen-sequence', type=int)
    parser.add_argument('--task-bus-source', type=Path)
    parser.add_argument('--task-bus-sha256')
    parser.add_argument('--bus-dir', type=Path)
    args = parser.parse_args(argv)
    args.attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        source = verify_pair(args.pair_manifest, native_source_checkout=args.native_source_checkout)
        check_game(args.game_dir)
        if args.no_launch:
            report = {**source, 'runtime_fingerprint': runtime_fingerprint(),
                      'entry_live_branch_implemented': True, 'fresh_go_and_frame_pending': True}
        elif args.prepare:
            report = prepare(source, args.game_dir, args.attempt_dir)
        else:
            required = ('prepared_manifest', 'go', 'steam_gate', 'round_id', 'screen_task_id',
                        'screen_sequence', 'task_bus_source', 'task_bus_sha256', 'bus_dir')
            require(all(getattr(args, key) is not None for key in required),
                    'H2743 live requires fresh prepared source, GO, Steam frame and exact screen claim')
            prepared = check_prepared(args.prepared_manifest, source)
            go = read_object(args.go)
            require(go.get('schema') == 'xar.ck3.h2743.managed-readonly-go.v1'
                    and go.get('round_id') == args.round_id and go.get('task_id') == args.screen_task_id
                    and go.get('pair_sha256') == source['pair_sha256']
                    and go.get('prepared_manifest_sha256') == sha256(args.prepared_manifest)
                    and go.get('steam_gate_sha256') == sha256(args.steam_gate)
                    and go.get('allowed_query_steps') ==
                    ['query-defender-de-jure-exit-terms-v1-16777231', OPTIONS_STEP]
                    and go.get('allowed_gameplay_steps') == [], 'H2743 current read-only GO differs')
            steam = check_steam_gate(args.steam_gate, task_id=args.screen_task_id)
            from .environment import EnvironmentSpec
            from .runtime import NativeBridgeLaunchConfig
            root = Path(__file__).resolve().parents[3]
            sys.path.insert(0, str(root / 'promo/ck3_native_war_ai/integration'))
            from screen_bus_lease import ScreenLeaseKeeper
            keeper = ScreenLeaseKeeper(
                source=args.task_bus_source, bus_dir=args.bus_dir, expected_sha=args.task_bus_sha256,
                task_id=args.screen_task_id, sequence=args.screen_sequence, repo=root,
                journal=args.attempt_dir / 'lease.jsonl', abort=threading.Event(),
                audit_dir=args.attempt_dir / 'lease-audit')
            spec = EnvironmentSpec(state_dir=Path(prepared['state_dir']), game_dir=args.game_dir,
                                   expected_game_version='1.19.0.6')
            config = NativeBridgeLaunchConfig(mode='native-headless', pipe_name=PIPE,
                dll_path=Path(source['dll']['path']), injector_path=Path(source['injector']['path']))
            report = run_owned_read(spec=spec, config=config, keeper=keeper, output=args.attempt_dir)
            report['source_pair'] = source
            report['go_sha256'] = sha256(args.go)
            report['steam_gate'] = steam
        write_new(args.attempt_dir / 'report.json', report)
        print(args.attempt_dir / 'report.json', report['status'])
        return 2 if report['status'] == 'RED' else 0
    except BaseException as error:
        write_new(args.attempt_dir / 'report.json', {'status': 'RED', 'error': f'{type(error).__name__}: {error}',
                  'gameplay_actions': 0, 'date_advance_actions': 0, 'material_complete': False, 'action_literal': None})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
