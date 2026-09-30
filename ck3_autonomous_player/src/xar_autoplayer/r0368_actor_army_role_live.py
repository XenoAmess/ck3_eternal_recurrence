"""One managed, paused role read using an explicitly frozen native pair.

This entry uses the current Python runtime and the role build's original source
checkout separately. It never changes army roles, starts activities or advances
the date. Source preparation and a live read always use distinct attempts.
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

from . import r0368_actor_army_role_operator as role
from .bridge.actor_army_role_private_transport import query_actor_army_role_private_v1
from .errors import AgentError
from .r0368_actor_army_role_outer_contract import (
    check_source_and_prepared_bytes, inspect_go_evidence,
)


def write_new(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise AgentError(f'expected JSON object: {path}')
    return value


def source_gate(args: argparse.Namespace) -> dict:
    return role.verify_no_launch_source_pair(
        candidate_manifest=args.candidate_manifest,
        release_pair_manifest=args.release_pair_manifest,
        checkout=args.role_source_checkout,
    )


def prepare(args: argparse.Namespace, output: Path) -> dict:
    from .environment import EnvironmentSpec, prepare_profile
    from .ordinary_seed_rebinder import rebind_ordinary_seed_v1

    source = source_gate(args)
    spec = EnvironmentSpec(state_dir=output / 'state', game_dir=args.game_dir,
                           expected_game_version='1.19.0.6')
    prepare_profile(spec, xar_enabled='xar_off', display_mode='windowed')
    targets = {
        'xar_checkpoint.ck3': spec.profile_dir / 'save games' / 'xar_checkpoint.ck3',
        'driver-state.json': spec.state_dir / 'native-session' / 'driver-state.json',
        'player-child-matrilineal-formal-v1.json':
            spec.state_dir / 'player-child-matrilineal-formal-v1.json',
    }
    for name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        shutil.copyfile(Path(source['assets'][name]['path']), target)
        if role._sha256(target) != role._ASSET_SHA256[name]:
            raise AgentError(f'source copy changed: {name}')
    pipe = read_object(targets['driver-state.json'])['pipe_name']
    rebind = rebind_ordinary_seed_v1(spec, expected_pipe_name=pipe)
    rebind_path = spec.state_dir / 'ordinary-seed-rebind-v1.json'
    write_new(rebind_path, rebind)
    manifest = {
        'schema': 'xar.war.r0368.role-only-prepared-source.v1',
        'status': 'READY_NO_LAUNCH', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'live_authorized': False, 'ck3_launch_attempted': False, 'screen_acquired': False,
        'state_dir': str(spec.state_dir), 'profile_dir': str(spec.profile_dir),
        'pipe_name': pipe, 'candidate_manifest_sha256': source['candidate_manifest_sha256'],
        'release_pair_manifest_sha256': source['release_pair_manifest_sha256'],
        'raw_driver_sha256': role._ASSET_SHA256['driver-state.json'],
        'prepared_driver_sha256': role._sha256(targets['driver-state.json']),
        'rebind_receipt_sha256': role._sha256(rebind_path),
        'environment_sha256': role._sha256(spec.manifest_path),
    }
    manifest_path = output / 'prepared-source.json'
    write_new(manifest_path, manifest)
    verified = check_source_and_prepared_bytes(
        candidate_manifest=args.candidate_manifest,
        release_pair_manifest=args.release_pair_manifest,
        checkout=args.role_source_checkout, prepared_manifest=manifest_path,
        state_dir=spec.state_dir, profile_dir=spec.profile_dir,
        environment_manifest=spec.manifest_path, pipe_name=pipe,
    )
    return {'status': 'PREPARED_NO_LAUNCH', 'source': source, 'prepared': verified,
            'prepared_manifest': str(manifest_path), 'ck3_started': False,
            'query_attempts': 0, 'gameplay_actions': 0, 'date_advance_actions': 0}


def run_owned_role_read(*, spec, config, keeper, actor: int, episode: str,
                        war_id: int, army_id: int, output: Path,
                        timeout_seconds: float = 600.0) -> dict:
    """Execute the existing typed collector and always stop the managed session."""
    from .bridge.native_driver import NativeHeadlessGameplayDriver
    from .bridge.driver import BridgeUnavailableError
    from .bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, bind_succession_lifecycle_from_environment_v1,
    )
    from .environment import verify_profile
    from .native_session import native_session
    from .runtime import ck3_process_inventory

    if timeout_seconds <= 0 or timeout_seconds > 1200:
        raise AgentError('role read timeout must be within 1..1200 seconds')
    if ck3_process_inventory()['processes']:
        raise AgentError('role read requires zero current CK3 processes')
    lifecycle_binding = bind_succession_lifecycle_from_environment_v1(
        verify_profile(spec, xar_enabled='xar_off'),
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION, ordinary_campaign_no_pact=True,
    )
    abort = keeper.abort
    done = threading.Event()
    session = {}
    driver = None
    thread = None
    report = {'status': 'RED', 'query_attempts': 0, 'gameplay_actions': 0,
              'date_advance_actions': 0, 'safe_role_release': None,
              'global_commander_or_knight_status': 'unknown',
              'python_runtime_head': role._git(Path(__file__).parents[3], 'rev-parse', 'HEAD')}

    def supervise():
        try:
            session['report'] = native_session(
                spec, timeout_seconds=timeout_seconds + 120,
                native_bridge=config, cold_start_checkpoint=True,
                prepared_xar_enabled='xar_off', stop_event=abort,
                before_process_create=keeper.process_create_gate,
            )
        except BaseException as error:
            session['error'] = f'{type(error).__name__}: {error}'
        finally:
            done.set()

    keeper.start()
    try:
        keeper.refresh()
        driver = NativeHeadlessGameplayDriver(config.pipe_name, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / 'save games',
            succession_lifecycle_binding=lifecycle_binding)
        driver.allow_private_actor_army_role_query = True
        driver.query_actor_army_role_private_v1 = MethodType(query_actor_army_role_private_v1, driver)
        thread = threading.Thread(target=supervise, name='r0368-role-managed-session')
        thread.start()
        deadline = time.monotonic() + timeout_seconds
        last_frame = None
        while time.monotonic() < deadline:
            keeper.require_live()
            if done.is_set():
                raise AgentError(f'managed session exited before role frame: {session}')
            try:
                frame = driver.take_snapshot()
            except BridgeUnavailableError as error:
                report['last_readiness_error'] = str(error)
                time.sleep(0.1)
                continue
            last_frame = frame
            if role._fresh_target(frame, actor=actor, episode=episode,
                                  war_id=war_id, army_id=army_id):
                write_new(output / 'paused-frame-before-query.json', frame)
                keeper.refresh()
                role.ROLE_ONLY_LIVE_AUTHORIZED = True
                report['query_attempts'] = 1
                inner = role.collect_role_only_in_managed_session(
                    driver, actor_character_id=actor, episode_run_id=episode,
                    war_id=war_id, public_army_id=army_id)
                write_new(output / 'role-inner.json', inner)
                report['inner'] = inner
                break
            time.sleep(0.1)
        else:
            report['last_readiness_frame'] = last_frame
            raise AgentError('no fresh paused owned/allied role frame before deadline')
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        role.ROLE_ONLY_LIVE_AUTHORIZED = False
        abort.set()
        if thread is not None:
            thread.join(timeout=180)
        if driver is not None:
            driver.close()
        keeper.stop()
        report['session'] = session
        report['lease'] = keeper.report()
        report['session_thread_exited'] = thread is None or not thread.is_alive()
        report['final_ck3_inventory'] = ck3_process_inventory()
        session_report = session.get('report', {})
        shutdown = session_report.get('shutdown', session_report.get('shutdown_attestation', {}))
        report['managed_cleanup_verified'] = (
            report['session_thread_exited'] and shutdown.get('cleanup_proven') is True
            and report['final_ck3_inventory']['processes'] == [])
        if ('error' not in report and report['managed_cleanup_verified']
                and report['lease'].get('failure') is None):
            report['status'] = 'ROLE_READ_AVAILABLE' if report['inner']['role_observed'] else 'ROLE_READ_PARTIAL_OR_UNAVAILABLE'
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--no-launch', action='store_true')
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--candidate-manifest', type=Path, required=True)
    parser.add_argument('--release-pair-manifest', type=Path, required=True)
    parser.add_argument('--role-source-checkout', type=Path, required=True)
    parser.add_argument('--attempt-dir', type=Path, required=True)
    parser.add_argument('--game-dir', type=Path)
    parser.add_argument('--prepared-manifest', type=Path)
    parser.add_argument('--go', type=Path)
    parser.add_argument('--round-id')
    parser.add_argument('--screen-task-id')
    parser.add_argument('--screen-sequence', type=int)
    parser.add_argument('--task-bus-source', type=Path)
    parser.add_argument('--task-bus-sha256')
    parser.add_argument('--bus-dir', type=Path)
    parser.add_argument('--actor', type=int)
    parser.add_argument('--episode')
    parser.add_argument('--war-id', type=int)
    parser.add_argument('--army-id', type=int)
    args = parser.parse_args(argv)
    args.attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        if args.no_launch:
            report = source_gate(args)
            report['entry_live_branch_implemented'] = True
            report['fresh_go_and_frame_pending'] = True
        elif args.prepare:
            if args.game_dir is None:
                raise AgentError('--prepare requires --game-dir')
            report = prepare(args, args.attempt_dir)
        else:
            required = ('game_dir', 'prepared_manifest', 'go', 'round_id', 'screen_task_id',
                        'screen_sequence', 'task_bus_source', 'task_bus_sha256', 'bus_dir',
                        'actor', 'episode', 'war_id', 'army_id')
            if any(getattr(args, key) is None for key in required):
                raise AgentError('--live requires prepared input, fresh GO, screen lease and exact actor/war/army')
            from .environment import EnvironmentSpec
            from .runtime import NativeBridgeLaunchConfig
            root = Path(__file__).parents[3]
            sys.path.insert(0, str(root / 'promo/ck3_native_war_ai/integration'))
            from screen_bus_lease import ScreenLeaseKeeper
            prepared = read_object(args.prepared_manifest)
            spec = EnvironmentSpec(state_dir=Path(prepared['state_dir']), game_dir=args.game_dir,
                                   expected_game_version='1.19.0.6')
            bound = check_source_and_prepared_bytes(
                candidate_manifest=args.candidate_manifest, release_pair_manifest=args.release_pair_manifest,
                checkout=args.role_source_checkout, prepared_manifest=args.prepared_manifest,
                state_dir=spec.state_dir, profile_dir=spec.profile_dir,
                environment_manifest=spec.manifest_path, pipe_name=prepared['pipe_name'])
            go = inspect_go_evidence(args.go, expected_round=args.round_id,
                                    expected_task_id=args.screen_task_id,
                                    source_pair_sha256=bound['source_pair_manifest_sha256'],
                                    prepared_sha256=bound['prepared_manifest_sha256'])
            source = source_gate(args)
            abort = threading.Event()
            keeper = ScreenLeaseKeeper(
                source=args.task_bus_source, bus_dir=args.bus_dir, expected_sha=args.task_bus_sha256,
                task_id=args.screen_task_id, sequence=args.screen_sequence, repo=root,
                journal=args.attempt_dir / 'lease.jsonl', abort=abort,
                audit_dir=args.attempt_dir / 'lease-audit')
            config = NativeBridgeLaunchConfig(mode='native-headless', pipe_name=prepared['pipe_name'],
                dll_path=Path(source['assets']['xar_ck3_bridge.dll']['path']),
                injector_path=Path(source['assets']['xar_ck3_bridge_injector.exe']['path']))
            report = run_owned_role_read(spec=spec, config=config, keeper=keeper,
                actor=args.actor, episode=args.episode, war_id=args.war_id, army_id=args.army_id,
                output=args.attempt_dir)
            report['source_pair'] = source
            report['go'] = go
        write_new(args.attempt_dir / 'report.json', report)
        print(args.attempt_dir / 'report.json', report['status'])
        return 0 if report['status'] != 'RED' else 2
    except Exception as error:
        write_new(args.attempt_dir / 'report.json', {
            'status': 'RED', 'error': f'{type(error).__name__}: {error}',
            'ck3_started': False, 'query_attempts': 0,
            'gameplay_actions': 0, 'date_advance_actions': 0})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
