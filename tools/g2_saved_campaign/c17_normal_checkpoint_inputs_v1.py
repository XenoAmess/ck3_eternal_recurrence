"""Finite normal C16->C17 cold inputs. No rollback, restore, file writes or RPC."""
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
KIND = 'EXACT_C16_NORMAL_CHECKPOINT_FOR_C17'
OLD_GAME = {'pid': 30852, 'creation_filetime': 134368995759027619}
OLD_PAIR = {('sdk_queue', 238856, 134369001730588409),
            ('sdk_application', 158356, 134369001760813642)}


def require(ok, why):
    if not ok:
        raise ValueError('C17 normal checkpoint input denied: ' + why)


def validate_normal_closure(close, checked):
    require(close.get('machine_id') == MACHINE and close.get('old_sdk_closure_kind') == KIND
        and close.get('old_Game') == OLD_GAME, 'only the current exact C16 normal cold boundary is supported')
    sdk = checked(close['sdk_closed']); pair = checked(close['old_sdk_pair'])
    require(sdk.get('machine_id') == MACHINE and sdk.get('normal') is True
        and sdk.get('launcher_exit_code') == 0 and len(sdk.get('processes', [])) == 2
        and {(r.get('role'), r.get('pid'), r.get('creation_filetime')) for r in sdk['processes']} == OLD_PAIR
        and {(r.get('role'), r.get('pid'), r.get('creation_filetime')) for r in pair['processes']} == OLD_PAIR
        and all(r.get('exit_code') == 0 and r.get('kernel_exit_observed') is True
            and r.get('observation_error') is None for r in sdk['processes']), 'original actual SDK normal0/0 closure required')
    game = checked(close['Game_exit'])
    require(game.get('machine_id') == MACHINE and game.get('pid') == OLD_GAME['pid']
        and game.get('creation_filetime') == OLD_GAME['creation_filetime']
        and game.get('kernel_signaled') is True and game.get('exit_code') == 0
        and game.get('forced_owned_job_cleanup') is False,
        'normal exact C16 Game closure is unproved; abnormal closure needs its own finite authority')
    record = checked(close['recording_shutdown'])
    require(record.get('status') == 'CLEANUP_OBSERVED' and record.get('capture_closed_verified') is True
        and record.get('inputs_unbound') is True and record.get('engine_exit_code') == 0
        and record.get('normal_engine_exit_proven') is True and record.get('stop_rpc_calls') == 0,
        'original recording normal cleanup receipt required')
    capture = checked(record['capture_closed'])
    require(capture.get('game_pid') == OLD_GAME['pid']
        and capture.get('game_creation_filetime') == OLD_GAME['creation_filetime']
        and capture.get('inputs_unbound') is True
        and capture.get('engine_close', {}).get('actual_exit_code') == 0
        and capture['engine_close'].get('normal_exit_proven') is True
        and capture['engine_close'].get('forced_process_calls') == 0,
        'capture belongs to a different or unresolved Game/OBS generation')
    publisher = record.get('decision_text_publisher') or {}
    require(publisher.get('status') == 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO'
        and publisher.get('machine_id') == MACHINE and publisher.get('normal_exit_claimed') is True
        and publisher.get('exit_proof_consumed_from_original_owner') is True
        and publisher.get('forced_process_calls') == 0, 'original publisher owner did not prove normal closure')
    owner = checked(publisher['owner_closed']); child = checked(owner['child_closed'])
    started = checked(publisher['publisher_started'])
    require(started.get('game') == {**started.get('game', {}), **OLD_GAME}
        and owner.get('machine_id') == child.get('machine_id') == MACHINE
        and owner.get('status') == 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO'
        and owner.get('publisher') == child.get('publisher') == started.get('publisher')
        and owner.get('kernel_exit_observed') is True and owner.get('exit_code') == 0
        and owner.get('forced_process_calls') == 0 and owner.get('Popen_original_kernel_handle_retained') is True
        and child.get('normal_STOP_observed') is True and child.get('first_error') is None,
        'publisher child/original-owner/source Game closure differs')
    return True


def validate_saved_seed(admission, seed, original, save, semantic, governance, *, projector, checked):
    require(admission.get('old_sdk_closure_kind') == KIND and admission.get('old_Game') == OLD_GAME
        and semantic.get('client_error') is None and semantic.get('result', {}).get('is_error') is False,
        'normal exact maintenance semantic source required')
    body = semantic['result']['structured_content']; checkpoint = save['result']['structured_content']['checkpoint']
    require(body.get('paused') is True and body.get('map_ready') is True
        and body.get('one_life_terminal') is False
        and body['played_character'].get('alive') is True
        and body['diagnostics'].get('bridge_pid') == body['diagnostics'].get('hello', {}).get('pid') == OLD_GAME['pid']
        and all(body.get(k) is None for k in ('active_event', 'pending_character_interaction'))
        and body['date_raw'] == checkpoint['date_raw'] == original['before']['date_raw']
        and body['played_character']['character_id'] == checkpoint['episode_character_id'] == original['before']['actor_character_id']
        and body['episode_run_id'] == checkpoint['episode_run_id'] == original['before']['episode_run_id']
        and body.get('campaign_goal') == original.get('campaign_goal_anchor')
        and save['request']['arguments'] == {'expected_revision': body['revision']},
        'real maintenance SAVE does not bind the current clean paused player/frame/goal')
    expected = projector(original, save, save_response=admission['save_response']['path'],
        semantic_response=admission['saved_semantic_response']['path'])
    require(seed == expected and seed['completed_cycles'] == original['completed_cycles']
        and governance.get('completed_cycles') == seed['completed_cycles']
        and governance.get('pending_cycle') is None, 'only the original direct-SAVE cadence projection may create this cold seed')
    close = checked(checked(admission['cold_prelaunch'])['final_driver_close'])
    validate_normal_closure(close, checked)
    require(close['checkpoint'] == checkpoint, 'post-close Driver provenance targets another SAVE')
    return True
