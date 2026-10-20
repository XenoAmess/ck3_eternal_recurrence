"""Finite saved-checkpoint recovery after the exact C22 storage-schema abort.

Pure bounded metadata validation. No Driver/SAVE body read, projection credit,
process operation or fallback from an arbitrary crash to a normal close.
"""
from pathlib import Path
import hashlib
import json
import re

MACHINE='xenoamess-full-tower-eb9d2c1186'
KIND='EXACT_C22_STORAGE_SCHEMA_ABORT_SAVE10480_FOR_C23'
OLD_GAME={'pid':30852,'creation_filetime':134368995759027619}
OLD_PAIR={('sdk_queue',9808,134369190683587530),('sdk_application',30936,134369190706095204)}
ABORT_BYTES=9089
ABORT_SHA='312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce'
STATE_SHA='c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8'
GOV_SHA='41851c235d40748cc598cf20a86bfba2bae53a19664e09e0dbf444ce3b121f14'
SDK_SHA='1f2ea42a30671772fa05483a382b5987e4a23f13dcc67af0958ff928ba9da664'
PAIR_SHA='e957d96f860a2171986f60edb9b026b85bfad9f1c3147ce8520f58f55eb0e65a'
SAVE_SHA='f0edd690a08320c52fb61cafc21d8991aca8e7775e1f1c2692e7e09c865b0061'
SAVE_RESPONSE_SHA='5b0844c484d3ca23ab73e7b6af9db528398fe40eef62648128d3bd4e1578853b'
DRIVER_SHA='b9f271f9b36885f008b6e05ab788ecbc47214178c64509646d44ea5e34872c29'


def require(ok,why):
    if not ok:raise ValueError('C23 exact source-schema-abort recovery denied: '+why)


def validate_business_anchor(anchor):
    """Source24 is a then-actual Root input, not the old Source23 placeholder."""
    rows=anchor.get('complete_rows_JSON') or {}
    require(anchor.get('schema')=='xar.source24.canonical-git-anchor/v1'
        and anchor.get('machine_id')==MACHINE and anchor.get('status')=='CANONICAL_REF_CREATED_NOT_DEPLOYED'
        and anchor.get('execution_owner')=='Root' and anchor.get('root_direct_execution_release') is True
        and anchor.get('parent')=='330d6e67c99eb22a60919b2bf7666c1ed0ca1b71'
        and isinstance(anchor.get('commit'),str) and re.fullmatch('[0-9a-f]{40}',anchor['commit'])
        and anchor['commit']!=anchor['parent']
        and isinstance(anchor.get('tree'),str) and re.fullmatch('[0-9a-f]{40}',anchor['tree'])
        and type(anchor.get('source_file_count')) is int and 1456<=anchor['source_file_count']<=1500
        and type(anchor.get('source_bytes')) is int and 59198354<=anchor['source_bytes']<=67108864
        and type(rows.get('bytes')) is int and 0<rows['bytes']<=1048576
        and isinstance(rows.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',rows['sha256'])
        and anchor.get('actual_loaded_provider') is False and anchor.get('Native30_bound') is False,
        'actual complete Source24 Root anchor with Source23 parent required')
    return anchor


def validate_frozen_business(admission,freeze,checked):
    anchor=validate_business_anchor(checked(admission['business_anchor'],65536))
    raw=json.dumps(freeze['files'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    require(freeze.get('machine_id')==MACHINE
        and freeze.get('business_source_commit')==admission.get('business_source_commit')==anchor['commit']
        and freeze.get('source_file_count')==len(freeze['files'])==anchor['source_file_count']
        and freeze.get('source_bytes')==sum(r['bytes'] for r in freeze['files'])==anchor['source_bytes']
        and {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==anchor['complete_rows_JSON'],
        'actual Source24 full canonical rows and runtime freeze must be identical')
    return anchor


def content_ref(ref,other):
    return isinstance(ref,dict) and all(ref.get(k)==other.get(k) for k in ('bytes','sha256'))


def validate_source_abort_closure(close,checked):
    require(close.get('machine_id')==MACHINE and close.get('old_sdk_closure_kind')==KIND
        and close.get('old_Game')==OLD_GAME,'exact F99 checkpoint recovery branch required')
    ref=close['source_abort_index']
    require(content_ref(ref,{'bytes':ABORT_BYTES,'sha256':ABORT_SHA}),'exact immutable F99 index pin required')
    abort=checked(ref,16384)
    require(abort.get('schema')=='xar.C22-warm-prepare-storage-schema-abort/v1'
        and abort.get('machine_id')==MACHINE
        and abort.get('status')=='GAME_AND_RECORDING_CLOSED_SDK_PREFLIGHT_FAILED_NO_RPC'
        and abort.get('actual_supervisor_failure')=={'type':'KeyError','message':"'retained_other_reservations'"}
        and abort.get('cleanup_classification')=='FORCED_OWNED_GAME_CLEANUP'
        and abort.get('new_SDK_pair_published') is False
        and abort.get('request10481_exists') is False and abort.get('response10481_exists') is False
        and abort.get('Game_RPC_calls_in_C22')==0 and abort.get('new_business_or_day_credit')==0
        and abort.get('next_sequence')==10481 and abort.get('completed_cycles')==4753
        and abort.get('date_raw')==53274624 and abort.get('checkpoint_saved_count')==74,
        'only the source-schema abort with zero subsequent MCP activity is eligible')
    sources=abort['sources']
    sdkref=close['sdk_closed'];pairref=close['old_sdk_pair']
    require(content_ref(sdkref,{'bytes':862,'sha256':SDK_SHA})
        and content_ref(pairref,{'bytes':462,'sha256':PAIR_SHA}),'last actual SDK is C20, not a fabricated C22 pair')
    sdk=checked(sdkref);pair=checked(pairref)
    require(sdk.get('machine_id')==MACHINE and sdk.get('status')=='ACTUAL_BOTH_SDK_EXITS_OBSERVED'
        and sdk.get('normal') is True and sdk.get('launcher_exit_code')==0
        and len(sdk.get('processes',[]))==len(pair.get('processes',[]))==2
        and all({(x.get('role'),x.get('pid'),x.get('creation_filetime')) for x in doc['processes']}==OLD_PAIR
            for doc in (sdk,pair))
        and all(x.get('kernel_exit_observed') is True and x.get('wait_result')==0
            and x.get('exit_code')==0 and x.get('observation_error') is None for x in sdk['processes']),
        'actual C20 kernel0/0 pair closure differs')
    require(content_ref(close['Game_exit'],sources['Game_exit']),'F99 exact old Game exit source required')
    game=checked(close['Game_exit']);supervisor=checked(sources['supervisor_closed'])
    require(game.get('machine_id')==MACHINE and all(game.get(k)==v for k,v in OLD_GAME.items())
        and game.get('kernel_signaled') is True and type(game.get('exit_code')) is int and game['exit_code']==1
        and game.get('forced_owned_job_cleanup') is True and game.get('normal_wm_close_qualified') is False
        and supervisor.get('machine_id')==MACHINE and supervisor.get('failure')==abort['actual_supervisor_failure']
        and supervisor.get('cleanup_classification')=='FORCED_OWNED_GAME_CLEANUP'
        and (supervisor.get('owned_cleanup') or {}).get('ck3_pid')==OLD_GAME['pid']
        and supervisor['owned_cleanup'].get('ck3_exit_code')==1
        and supervisor['owned_cleanup'].get('job_active_processes_final')==0,
        'forced old Game1 is retained as abnormal, never converted to normal0')
    # The supervisor's embedded C16 SDK view is historical. It is intentionally
    # not consumed as the last SDK pair; sdkref above binds the actual C20 pair.
    task=checked(sources['SDK_Task_CLOSED']);cleanup=checked(sources['record_cleanup'])
    require(task.get('machine_id')==MACHINE and task.get('child_exit_code')==1
        and task.get('bootstrap_exit_code')==1 and task.get('job_active_after_stage')==0
        and task.get('forced_remaining_cleanup') is False
        and (sources.get('record_capture_closed') or {}).get('exists') is False
        and cleanup.get('inputs_unbound') is True
        and (cleanup.get('engine_close') or {}).get('actual_exit_code')==0
        and cleanup['engine_close'].get('normal_exit_proven') is True
        and cleanup['engine_close'].get('forced_process_calls')==0,
        'C22 preflight Task1/1/no App and failed-record cleanup must remain separate')
    publisher=checked(sources['publisher_owner_closed']);child=checked(sources['publisher_closed'])
    require(publisher.get('machine_id')==child.get('machine_id')==MACHINE
        and publisher.get('status')=='PUBLISHER_NORMAL_KERNEL_EXIT_ZERO'
        and publisher.get('kernel_exit_observed') is True and publisher.get('exit_code')==0
        and publisher.get('forced_process_calls')==0 and child.get('normal_STOP_observed') is True
        and child.get('first_error') is None and publisher.get('publisher')==child.get('publisher'),
        'actual old publisher closure differs')
    hashed=checked(sources['Driver_hash_only'])
    require(hashed.get('machine_id')==MACHINE
        and content_ref(close['driver_state'],{'bytes':38356800,'sha256':DRIVER_SHA})
        and content_ref(close['driver_state'],hashed['closed_Driver'])
        and close.get('original_command_history_preserved') is True
        and type(close.get('history_rows')) is int and close['history_rows']>=5268,
        'original closed Driver is only serialized input; exact SAVE validator remains required')
    checkpoint=close['checkpoint']
    require(checkpoint==abort['actual_saved_checkpoint']
        and checkpoint.get('status')=='saved' and checkpoint.get('sha256')==SAVE_SHA
        and checkpoint.get('size')==116203629 and checkpoint.get('history_index')==5268
        and checkpoint.get('date_raw')==53274624 and checkpoint.get('episode_character_id')==40526
        and checkpoint.get('episode_run_id')=='native-40526-1bec95182886',
        'this branch accepts only the already saved10480 checkpoint')
    return abort


def validate_saved_seed(admission,seed,original,save,semantic,governance,*,projector=None,checked):
    require(admission.get('old_sdk_closure_kind')==KIND and admission.get('old_Game')==OLD_GAME
        and admission.get('next_sequence')==10481,'exact saved frontier/admission required')
    require(content_ref(admission['original_state'],{'bytes':9054,'sha256':STATE_SHA})
        and content_ref(admission['governance'],{'bytes':511,'sha256':GOV_SHA})
        and content_ref(admission['save_response'],{'bytes':10236,'sha256':SAVE_RESPONSE_SHA}),
        'immutable original state/governance/SAVE row sources required')
    require(seed==original and seed.get('completed_cycles')==4753
        and seed.get('counts',{}).get('checkpoint_saved')==74
        and seed.get('checkpoint_dirty_since_save') is False
        and all(seed.get(k) is None for k in ('pending_cycle','pending_checkpoint','terminal',
            'pending_natural_succession','pending_unsafe_route_halt'))
        and governance.get('pending_cycle') is None and governance.get('completed_cycles')==4753,
        'saved frontier is already accounted; no projection credit or count increment is permitted')
    require(save.get('client_error') is None and save.get('result',{}).get('is_error') is False
        and save['result'].get('result_type')=='complete'
        and save.get('request',{}).get('tool')=='ck3_save_checkpoint'
        and semantic.get('client_error') is None and semantic.get('result',{}).get('is_error') is False
        and semantic['result'].get('result_type')=='complete'
        and semantic.get('request',{}).get('tool')=='ck3_take_semantic_snapshot_private_v1',
        'actual SAVE10480 and preceding successful semantic sources required')
    body=semantic['result']['structured_content'];cp=save['result']['structured_content']['checkpoint']
    before=seed['before']
    require(cp==seed['actual_saved_checkpoint'] and body.get('paused') is True and body.get('map_ready') is True
        and body.get('one_life_terminal') is False and body.get('played_character',{}).get('alive') is True
        and body['played_character'].get('character_id')==before.get('actor_character_id')==40526
        and body.get('date_raw')==before.get('date_raw')==cp.get('date_raw')==53274624
        and body.get('episode_run_id')==before.get('episode_run_id')==cp.get('episode_run_id')
        and body.get('campaign_goal')==seed.get('campaign_goal_anchor')
        and body.get('diagnostics',{}).get('bridge_pid')==OLD_GAME['pid']
        and save['request'].get('arguments')=={'expected_revision':body['revision']}
        and seed.get('start_date_raw')==53144328,
        'saved paused actor/episode/goal/T0 source tuple differs')
    close=checked(checked(admission['cold_prelaunch'])['final_driver_close'])
    validate_source_abort_closure(close,checked)
    require(close['checkpoint']==cp and content_ref(close['source_abort_index'],admission['source_abort_index']),
        'bootstrap and Queue must consume the same finite abort authority')
    return True


def current_recording_inputs_v1(admission,checked):
    """Then-actual cold identity; original verify_segment performs live validation."""
    from uuid import UUID
    binding=checked(admission['recording_binding'],65536);game=admission['new_Game']
    require(binding.get('schema')=='xar.C23-actual-cold-recording-binding/v1'
        and binding.get('machine_id')==MACHINE and binding.get('status')=='ACTUAL_NEW_RECORDING_READY'
        and (game['pid'],game['creation_filetime'])!=(OLD_GAME['pid'],OLD_GAME['creation_filetime'])
        and type(game['pid']) is int and game['pid']>0
        and type(game['creation_filetime']) is int and game['creation_filetime']>0
        and binding.get('Game_pid')==game['pid'] and binding.get('Game_creation_filetime')==game['creation_filetime'],
        'actual new cold Game and recording binding required')
    request=checked(binding['request'],16384);job=checked(binding['job'],65536)
    started=checked(binding['started'],32768);first=checked(binding['first_frame_admission'],32768)
    checked(binding['publisher_started'],65536)
    sid=str(UUID(binding['session_id']));root=Path(request['receipt_root']).resolve()
    n=Path(admission['queue_source']['path']).resolve().parent;first_path=Path(binding['first_frame_admission']['path']).resolve()
    require(sid==binding['session_id'] and sid not in ('2b8912a6-757d-46a4-a8ae-b7702a730a90','79872e3d-e384-4be0-b160-c3608d419525')
        and root.is_relative_to(n/'recordings') and root.name==sid
        and request.get('session_id')==job.get('session_id')==first.get('recorder_session_id')==sid
        and Path(job['receipt_root']).resolve()==root
        and Path(binding['job']['path']).resolve()==root/'job.json'
        and Path(binding['started']['path']).resolve()==root/'started.json'
        and type(request.get('worker_pid')) is int and request['worker_pid']>0
        and type(request.get('worker_creation_filetime')) is int and request['worker_creation_filetime']>0
        and job.get('pid')==started.get('game_pid')==first.get('game_pid')==game['pid']
        and job.get('game_creation_filetime')==started.get('game_creation_filetime')==first.get('game_creation_filetime')==game['creation_filetime']
        and started.get('state')=='recording' and first.get('status')=='GREEN' and first.get('machine_id')==MACHINE
        and first_path.is_relative_to(n)
        and first_path.name not in ('ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json','ROOT-SAVED-MAP-RECORDING-ADMITTED-C22.json')
        and Path(first['recording_job_root']).resolve()==root
        and first.get('publisher_started')==job.get('decision_text_publisher_receipt')==binding['publisher_started'],
        'actual new publisher/recording/Root firstgate tuple differs')
    return {'binding':binding,'requested':request,'root':root,'first_path':first_path}
