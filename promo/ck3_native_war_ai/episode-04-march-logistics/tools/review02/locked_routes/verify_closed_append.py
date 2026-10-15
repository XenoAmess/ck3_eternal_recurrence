"""Verify a later R0176 close append without altering the original R13 packet."""
from __future__ import annotations
import argparse, datetime, hashlib, io, json, zipfile
from pathlib import Path, PurePosixPath


def require(ok,message):
    if not ok:raise ValueError(message)


def check(index, archive, prior):
    raw=archive.read_bytes()
    require(len(raw)==index['archive']['bytes'] and hashlib.sha256(raw).hexdigest()==index['archive']['sha256'],'close archive pin differs')
    require(len(raw)<=1024*1024,'finite close archive bound')
    values={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(set(z.namelist())=={r['path'] for r in index['files']},'close archive membership differs')
        for row in index['files']:
            path=PurePosixPath(row['path'])
            require(not path.is_absolute() and '..' not in path.parts,'unsafe close member')
            body=z.read(row['path'])
            require(len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256'],'close member changed')
            values[row['path']]=json.loads(body)
    closed=values['CLOSED.actual-a01.json'];machine=index['machine_id'];run=closed['run_id']
    require(closed.get('machine_id')==prior.get('machine_id')==machine and prior.get('run_id')==run,'R13/close source binding differs')
    require(closed.get('normal_exit_code')==0 and closed.get('game_recorder_SDK_keeper_closed') is True
            and closed.get('source_freeze_released') is True,'actual normal close missing')
    def proof(key):
        ref=closed['evidence'][key]
        rows=[r for r in index['files'] if r['sha256']==ref['sha256'] and r['bytes']==ref['bytes']]
        require(len(rows)==1,'close proof not archived exactly: '+key)
        return values[rows[0]['path']]
    bootstrap=proof('bootstrap');session=bootstrap['session']
    require(session.get('process_exit_code')==0 and session.get('exit_reason')=='process_exit'
            and session.get('shutdown',{}).get('ck3_exit_code')==0,'final main process did not exit0')
    require(bootstrap.get('sdk_thread_exited') is True and bootstrap.get('screen_lease',{}).get('thread_exited') is True,'SDK/lease keeper not exited')
    release=proof('screen_release');result=json.loads(release['stdout'])
    require(release.get('machine_id')==machine and release.get('exit_code')==0 and result.get('ok') is True
            and result.get('task',{}).get('state')=='done' and result['task'].get('resources')==[],'screen release not actual')
    argv=release['argv'];sequence=int(argv[argv.index('--expected-sequence')+1])
    require(sequence==bootstrap['screen_lease']['last_sequence']==5483 and result['event']['sequence']==5484,'screen release CAS sequence differs')
    display=proof('display_restore')
    require(display.get('machine_id')==machine and display.get('apply_result')==0
            and display.get('after')==display.get('original') and display.get('desktop_size')==[1024,768]
            and display.get('game_and_recorder_absent') is True,'actual display restore missing')
    saved=proof('terminal_normal_save')
    require(saved.get('machine_id')==machine and saved.get('is_error') is False,'normal save response rejected')
    checkpoint=saved['body']['checkpoint']
    require(checkpoint.get('status')=='saved' and checkpoint.get('size')==71305933
            and checkpoint.get('sha256')=='31c57bc0032f0af4dcb90b4f00567cd68638e71856bbd570ee847aa644c26378'
            and checkpoint.get('date_raw')==53146632 and checkpoint.get('episode_run_id')==prior['binding']['episode'],'terminal save receipt differs')
    require(prior.get('runtime_close_qualified') is False,'original pre-close qualification should remain unmodified')
    return {'schema':'episode04.r0176.closed-append-replay.v1','status':'PASS','machine_id':machine,
            'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':run,
            'original_R13_preclose_status_preserved':True,'later_actual_closed_at_utc':closed['at_utc'],
            'normal_exit_code':0,'SDK_and_keeper_exited':True,'screen_release_expected_sequence':sequence,
            'screen_release_completed_sequence':5484,'display_restored':[1024,768],
            'terminal_save_receipt':{'sha256':checkpoint['sha256'],'bytes':checkpoint['size'],'date_raw':checkpoint['date_raw']},
            'save_body_read_or_rehashed':False,'continuous_clean_review':False,'human_approval':False,
            'R09_full_card_closed':False,'new_live_evidence_by_replay':False,'game_actions_sent':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,required=True);parser.add_argument('--archive',type=Path)
    parser.add_argument('--prior-r13',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'append-only output already exists')
    index=json.loads(args.index.read_bytes());prior_raw=args.prior_r13.read_bytes()
    require(hashlib.sha256(prior_raw).hexdigest()==index['prior_R13_qualification']['sha256'],'original R13 qualification bytes changed')
    result=check(index,args.archive or args.index.parent/index['archive']['path'],json.loads(prior_raw))
    with args.output.open('xb') as f:f.write((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({'status':result['status'],'normal_exit_code':0,'later_closed_at_utc':result['later_actual_closed_at_utc']}))


if __name__=='__main__':main()
