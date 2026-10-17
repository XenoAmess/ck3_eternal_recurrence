from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
MACHINE='desktop-3fevhd2-1c74096080'
HEAD='dc031358981450ae3f8e40c6234b7f27fd4662ef'
RUN=MACHINE+'--vanilla--R0198'

def need(ok,why):
    if not ok: raise ValueError(why)

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    index=json.loads((HERE/'source-index.json').read_text(encoding='utf-8'))
    need(index['schema']=='xar.e04.r198-military-toggle-portable-index.v1','index schema')
    need(index['machine_id']==MACHINE and index['source_head']==HEAD and index['run_id']==RUN,'index identity')
    zp=HERE/index['archive']['path']; zb=zp.read_bytes()
    need(len(zb)==index['archive']['bytes'] and sha(zb)==index['archive']['sha256'],'archive pin')
    rows=index['members']; names=[x['member'] for x in rows]
    need(len(names)==len(set(names)) and len(names)>=12,'members')
    with ZipFile(zp) as z:
        need(set(z.namelist())==set(names),'zip membership')
        for row in rows:
            b=z.read(row['member'])
            need(len(b)==row['bytes'] and sha(b)==row['sha256'],row['member'])
        get=lambda name: json.loads(z.read(name))
        take=get('military-take.json'); ident=get('runtime-actor-identity.json')
        action=get('05-toggle-once.json'); opener=get('02-open-once.json')
        before=get('04-fresh-before-toggle.json'); after=get('06-toggle-fence.json')
        finish=get('film-finish.json'); normal=get('normal-save.json'); release=get('screen-release.json')
        need(take['machine_id']==ident['machine_id']==normal['machine_id']==release['machine_id']==MACHINE,'machine')
        need(take['source_head']==ident['source_head']==normal['source_head']==HEAD,'source')
        need(take['run_id']==ident['run_id']==normal['run_id']==release['run_id']==RUN,'run')
        need(ident['pid']==normal['pid']==24728 and ident['connection_generation']==1,'pid/generation')
        need(ident['process_creation_filetime_100ns']==normal['process_creation_filetime_100ns']==134367039851411170,'creation time')
        need(ident['episode_run_id']==normal['episode_run_id']=='native-31254-a9475f27e7e8','episode')
        need(take['primary_error'] is None and not take['secondary_errors'],'take errors')
        need(take['one_opener_and_one_reverse_toggle'] is True and take['no_replay_after_unknown'] is True,'action sequence')
        tr=take['take']['verified_transition']
        need(tr['status']=='verified_desired' and tr['postcondition_verified'] is True,'transition')
        need(tr['before_switch']['raw_byte_4a9']==1 and tr['later_switch']['raw_byte_4a9']==0,'raw4a9')
        need(tr['before_switch']['owner_full_id']==tr['later_switch']['owner_full_id']==31254,'owner')
        need(tr['before_frame']['ticket_sequence']==7 and tr['later_frame']['ticket_sequence']==9,'tickets')
        need(tr['before_frame']['pump_epoch']==90051 and tr['later_frame']['pump_epoch']==90065,'pump')
        need(tr['before_frame']['thread_id']==tr['later_frame']['thread_id']==29140,'thread')
        need(tr['before_frame']['date_raw']==tr['later_frame']['date_raw']==normal['date_raw']==53148192,'date')
        need(take['take']['desired_enabled'] is False and take['take']['clock_advanced'] is False,'scope')
        need(take['take']['instruction_ADD_qualified'] is False and take['take']['PTS_or_clean_span_qualified'] is False,'credit')
        need(opener['request']['arguments']['step']=='activate-ingame-military-v1' and opener['body']['status']=='verified_visible','opener')
        need(action['request']['arguments']['step']=='disable-military-reinforcement-v1','toggle endpoint')
        need(action['body']['accepted'] is True and action['body']['status']=='verified_desired' and action['body']['postcondition_verified'] is True,'toggle result')
        need(action['body']['before_switch']['raw_byte_4a9']==1 and action['body']['native_after_switch']['raw_byte_4a9']==1,'immediate readback retained 1')
        need(action['body']['later_observation']['switch']['raw_byte_4a9']==0,'later readback 0')
        need(action['body']['current_variable_table_observed'] is False and action['body']['native_receiver_selected'] is False and action['body']['provider_invoked'] is False,'no provider/receiver')
        need(before['body']['date_raw']==after['body']['date_raw']==53148192,'frame snapshots')
        need(finish['finish']['state']=='NORMAL_TREE_EMPTY' and finish['finish']['capture_guard_error'] is None and finish['finish']['partial_video'] is False,'film finish')
        need(normal['checkpoint']['sha256']=='09c5bf2f2aa3dad559a602c292ede45868d90c185bf491fb2e958f849f5bf9a0','checkpoint pin')
        need(release['normal_save']['sha256']==sha(z.read('normal-save.json')),'normal save binding')
        need(release['exit_code']==release['game_exit_code']==0 and release['normal_exit_zero'] is True and release['task_done_resources_empty'] is True,'normal close')
        need(normal['video_human_signoff'] is False,'human signoff')
    print('PASS: exact packets/frames, 4A9 1->0, identity, no ADD/media credit, normal close')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('FAIL:',e,file=sys.stderr); sys.exit(1)
