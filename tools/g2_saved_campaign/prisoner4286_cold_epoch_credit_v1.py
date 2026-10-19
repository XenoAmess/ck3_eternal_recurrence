"""One sealed prisoner receipt across the actually verified C11 cold epoch.

Never edit the receipt/ACK/state input. All existing typed guards still execute;
only its one revision comparison uses the separately verified cold provenance.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
ROOT = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
PACK = ROOT.parent.parent/'p51-fresh1066-v20261019-prepare01/c11-prisoner4286-failure85'
PACK_SHA = '3b8b99f588845ea9cf95637b9861ea34f0240cf2480e515186eb74e45ecdfaac'
QUEUE_SHA = '71d5863c986ebea245c7f633fd3b6e9170fe92a8ee881f0ca652ac6771c8eb19'
ROW_SHA = '3d5ca2de50e1a20718dd51f3962ce77236820f842a09f5eb6b13ccfa909af27f'
BOUND_SHA = '0ef49a55a04c23417f554fdd5bf4e3d472dce34d234e488db13db6f5f416d8b4'
_CACHE = {}


def require(ok, reason):
    if not ok:
        raise ValueError('sealed4286 cold epoch denied: ' + reason)


def checked(ref, limit=262144):
    path = Path(ref['path']); raw = path.read_bytes()
    require(len(raw) <= limit and len(raw) == ref['bytes']
        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'exact named input differs: '+str(path))
    return json.loads(raw)


def fixed(path, digest, limit=262144):
    raw = Path(path).read_bytes()
    require(len(raw) <= limit and hashlib.sha256(raw).hexdigest() == digest, 'sealed source differs')
    return json.loads(raw)


def verify_cold_epoch(body, state, initial_frame, game_pid):
    packet = fixed(PACK/'FROZEN.json', PACK_SHA)
    require(packet['machine_id'] == MACHINE and packet['next_sequence'] == 4287, 'packet identity differs')
    refs = {r['original_source']: r for r in packet['source_refs'] if 'path' in r}
    def frozen(relative):
        original = str(ROOT/relative)
        return checked(refs[original])
    row = frozen('p37-responses/4286-1-result.json')
    require(refs[str(ROOT/'p37-responses/4286-1-result.json')]['sha256'] == ROW_SHA
        and row['result']['is_error'] is False and row.get('client_error') is None
        and row['request']['tool'] == 'ck3_auto_turn'
        and body == row['result']['structured_content'], 'only original successful4286 body is eligible')
    gov = frozen('p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')
    require(state == gov['state'], 'current original governance state differs')
    known = state['prisoner_release_pending']; inner = body['result']
    require(body['selected_step'] == 'query-player-prisoner-release-receipt-v1'
        and body['status'] == 'executed' and inner['status'] == 'applied'
        and known == body['plan']['prisoner_release_pending'] == inner['source_pending'], 'original pending/plan/source tuple differs')
    admission = frozen('ROOT-P37C11-COLD-RESUME-ADMISSION.json')
    require(admission['machine_id'] == MACHINE and admission['schema'] == 'xar.c11.normal-checkpoint-cold-queue/v1'
        and admission['new_Game'] == {'pid':15512,'creation_filetime':134368811928524228,'creation_date':'20261019105952.852422+000'},
        'actual new Game identity differs')
    pre = checked(admission['cold_prelaunch']); close = checked(pre['final_driver_close'])
    require(pre['machine_id'] == close['machine_id'] == MACHINE
        and pre['status'] == 'EXACT_CLOSED_CHECKPOINT_COLD_INPUT_VALIDATED'
        and pre['validator_api'] == 'xar_autoplayer.native_session.validate_cold_start_checkpoint_for_pipe'
        and close['old_Game'] == {'pid':153556,'creation_filetime':134368602545256920}, 'old Game/canonical cold identity differs')
    oldgov = checked(admission['governance']); oldstate = checked(admission['original_state'])
    require(oldgov['state']['prisoner_release_pending'] == known
        and oldstate['completed_cycles'] == oldgov['completed_cycles'] == 2010,
        'old source epoch known ACK differs')
    oldframe = oldstate['before']; checkpoint = pre['checkpoint']
    saved = checked(admission['save_response'])['result']['structured_content']['checkpoint']
    bound = fixed(ROOT/'p37-queue/ROOT-C11-NORMAL-COLD-BOUND.json', BOUND_SHA)
    ready = fixed(PACK.parent/'c11-native29-cold84/ACTUAL-COLD-READY.json',
        '53d39c582e7dfddf4e591cc583973c929e873478bafba873962e9746e5661f2a')
    launch = checked(ready['actual_Game'])
    require(ready['machine_id'] == MACHINE and ready['status'] == 'ACTUAL_COLD_SEM_CAP_AND_ROOT_MAP_GREEN'
        and {k:launch[k] for k in ('pid','creation_filetime','creation_date')} == admission['new_Game']
        and ready['semantic']['path'] == bound['semantic_response'], 'actual new Game/SEM source differs')
    opening_row = checked(ready['semantic'])
    caps = checked(ready['capabilities'])['result']['structured_content']['native_session_control']
    require(caps['driver_state_restored'] is True and caps['driver_state_restore_kind'] == 'cold_checkpoint'
        and caps['episode_binding_state'] == 'active_resumed' and caps['driver_state_error'] is None,
        'actual cold restore differs')
    opening_body = opening_row['result']['structured_content']
    opening_diag = opening_body['diagnostics']; opening_hello = opening_diag['hello']
    opening = bound['opening_frame']
    require(bound['machine_id'] == MACHINE and bound['completed_cycles'] == 2010
        and bound['T0_date_raw'] == 53144328 and bound['new_ordinary_cycle_credit'] == 0
        and bound['AUTO_or_MET_replayed'] is False
        and opening_row['request']['sequence'] == admission['next_sequence'] == 4235
        and opening_row['request']['tool'] == 'ck3_take_semantic_snapshot_private_v1'
        and opening_row['result']['is_error'] is False and opening_row.get('client_error') is None
        and opening_diag['bridge_pid'] == opening_hello['pid'] == game_pid == admission['new_Game']['pid']
        and initial_frame == opening, 'actual cold opening binding differs')
    require(checkpoint == saved == bound['checkpoint'] and pre['save_response'] == admission['save_response']
        and checkpoint['sha256'] == '7de16f6f16a3b3ff686ae35d103675384e3432b154534b9ef95da8c021695c51'
        and checkpoint['history_index'] == 332 and checkpoint['date_raw'] == opening['date_raw'] == 53189040,
        'actual SAVE4234/checkpoint/opening differs')
    current = body['planning_source_frame']; readback = inner['independent_readback']
    require(current['bridge_pid'] == game_pid and current['native_revision'] == inner['post_native_revision'] == 27
        and current['revision'] == readback['queried_revision'] == 28
        and readback['queried_native_revision'] == current['native_revision']
        and current['date_raw'] == inner['post_date_raw'] == 53189232
        and current['snapshot_id'] == readback['queried_snapshot_id'] == 'native:27'
        and current['connection_generation'] == opening_diag['connection_generation'] == 1
        and opening['native_revision'] == 1 <= current['native_revision'], 'new epoch query frame differs')
    require(all(f['actor_character_id'] == 40526 and f['episode_run_id'] == 'native-40526-1bec95182886'
        for f in (oldframe, opening, current))
        and checkpoint['episode_character_id'] == known['player_character_id'] == 40526
        and checkpoint['episode_run_id'] == current['episode_run_id']
        and known['prisoner_character_id'] == inner['prisoner_character_id'] == 45172
        and known['action_ack']['request_id'] == 'prisoner-release-6180f156f98a4e15a76f563884f4053f'
        and known['pre_native_revision'] == known['action_ack']['pre_native_revision'] == 3138 <= oldframe['native_revision']
        and known['pre_date_raw'] == known['action_ack']['pre_date_raw'] == 53188032 <= oldframe['date_raw']
        and oldframe['date_raw'] == checkpoint['date_raw'] <= current['date_raw'], 'old ACK/player/date provenance differs')
    sidecar = frozen('state/player-prisoner-release-formal-v1.json')
    require(sidecar['pending'] is None and sidecar['resolved'] == inner,
        'existing SDK independent receipt is not resolved exactly')
    return {'old_Game':close['old_Game'],'new_Game':admission['new_Game'],
        'old_pre_native_revision':known['pre_native_revision'],'new_post_native_revision':inner['post_native_revision'],
        'original_response_sha256':ROW_SHA,'causation_or_cost_credit':False}


def functions(namespace):
    key = id(namespace)
    if key in _CACHE:
        return _CACHE[key]
    raw = (ROOT/'root_p37c11_sdk_queue.py').read_bytes()
    require(len(raw) == 267955 and hashlib.sha256(raw).hexdigest() == QUEUE_SHA, 'original Queue source differs')
    original = next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='classify_existing_typed_v1')
    original_ns = dict(namespace)
    exec(compile(ast.Module(body=[original],type_ignores=[]),str(ROOT/'root_p37c11_sdk_queue.py'),'exec'),original_ns)
    altered = ast.parse(ast.get_source_segment(raw.decode('utf-8'),original)).body[0]
    needle = ast.dump(ast.parse('inner["post_native_revision"] >= known["pre_native_revision"]',mode='eval').body,include_attributes=False)
    matched = []
    class CrossEpoch(ast.NodeTransformer):
        def visit_Compare(self,node):
            if ast.dump(node,include_attributes=False) == needle:
                matched.append(node)
                return ast.copy_location(ast.Constant(True),node)
            return self.generic_visit(node)
    altered = ast.fix_missing_locations(CrossEpoch().visit(altered))
    require(len(matched) == 1, 'one exact revision comparison required')
    alternate_ns = dict(namespace)
    exec(compile(ast.Module(body=[altered],type_ignores=[]),'sealed4286-one-comparison','exec'),alternate_ns)
    result = original_ns['classify_existing_typed_v1'],alternate_ns['classify_existing_typed_v1']
    _CACHE[key] = result
    return result


def classify(body, *, state, initial_frame, game_pid, namespace):
    original, across = functions(namespace)
    known = (state or {}).get('prisoner_release_pending')
    inner = body.get('result') if isinstance(body,dict) else None
    is_cross = (body.get('selected_step') == 'query-player-prisoner-release-receipt-v1'
        and isinstance(known,dict) and isinstance(inner,dict)
        and type(inner.get('post_native_revision')) is int and type(known.get('pre_native_revision')) is int
        and inner['post_native_revision'] < known['pre_native_revision'])
    if not is_cross:
        return original(body,state=state,initial_frame=initial_frame,game_pid=game_pid)
    provenance = verify_cold_epoch(body,state,initial_frame,game_pid)
    record, changed = across(body,state=state,initial_frame=initial_frame,game_pid=game_pid)
    record['source_bound_cold_epoch'] = provenance
    return record, changed
