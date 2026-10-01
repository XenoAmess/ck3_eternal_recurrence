"""Real clergy worker -> owner mailbox -> provider -> wire; files/fixtures only."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
import subprocess

from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE=Path(__file__).resolve().parent.parent
SOURCES=('ck3_12002.cpp','religion_rite_governance12002_clergy.cpp',
         'main_thread_query_mailbox_v1.cpp','ck3_12002_query_mailbox.cpp','protocol.cpp',
         'religion_rite_governance12002_clergy_mailbox.cpp')
TEST='religion_rite_governance12002_clergy_mailbox_test.cpp'
WIRE=('vacant-valid.json','incumbent-reassign-denied.json','candidate-native-denied.json',
      'foreign-context.json','position-absent.json','candidate-unavailable.json','context-unavailable.json')
EXE_SHA='AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition,message):
    if not condition:
        raise RuntimeError(message)

def validate_wire(directory):
    pins={}
    for name in WIRE:
        path=directory/name
        packet=json.loads(path.read_text(encoding='utf-8'))
        require(packet['protocol_version']==1 and packet['type']=='command_result' and packet['ok'] is True and
                packet['request_id']=='clergy"worker-fixture','actual protocol and escaped request')
        result=packet['result']; out=result['player_clergy_appointment']
        require(result['step']=='query-player-clergy-appointment-v1' and result['domain_key']=='player_clergy_appointment_v1' and
                result['backend_id']=='ck3-1.20.0.2-native-player-clergy-appointment-v1' and result['accepted'] is True and
                result['private_build'] is True and result['read_only'] is True and result['advertised'] is False and
                result['game_version']=='1.20.0.2' and result['executable_sha256']==EXE_SHA and
                result['snapshot_revision']==701 and result['date_raw']==53175816,'actual result metadata')
        require(out['schema']=='xar.ck3.religion-clergy-appointment/v1' and out['owner_character_id']==0x03000004 and
                out['candidate_character_id']==0x06000005 and out['capture_epoch']!=701 and
                out['action_eligibility_complete'] is False,'specific actual candidate and independent final observation')
        unavailable=name in ('candidate-unavailable.json','context-unavailable.json')
        require(result['status']==('unavailable' if unavailable else 'observed') and
                out['status']==('unavailable' if unavailable else 'available'),'typed unavailable and native false differ')
        if name=='vacant-valid.json':
            require(out['owner_rite_id']==0 and out['candidate_rite_id']==0 and out['native_valid_character'] is True and
                    out['native_can_reassign'] is True and out['incumbent_character_id'] is None,'actual vacant native predicates')
        elif name=='incumbent-reassign-denied.json':
            require(out['candidate_is_incumbent'] is True and out['native_valid_character'] is True and
                    out['native_can_reassign'] is False,'native final false remains observed')
        elif name=='candidate-native-denied.json':
            require(out['native_valid_character'] is False and out['candidate_rite_id']==0x83000003,'actual candidate final false and full Rite ID')
        elif name=='foreign-context.json':
            require(out['candidate_matches_owner_context'] is False and out['native_valid_character'] is True,'opaque foreign candidate context is separate')
        elif name=='position-absent.json':
            require(out['position_present'] is False and out['native_can_reassign'] is None and
                    out['native_valid_character'] is None,'legal seat absence stays nullable')
        elif unavailable:
            require(out['native_valid_character'] is None and out['native_can_reassign'] is None,'failed source has no invented final bool')
        pins[name]=sha(path)
    require(not (directory/'frame-changed.json').exists(),'changed full frame must not produce success wire')
    reject=json.loads((directory/'frame-changed-rejection.json').read_text(encoding='utf-8'))
    require(reject['success_wire_emitted'] is False and reject['mailbox_reclaimed'] is True and
            bool(reject['failure']),'actual owner post-read change rejection and ticket reclamation')
    return pins

def run_mode(shell,root,mode):
    out=root/mode; out.mkdir(parents=True,exist_ok=True)
    compiler=['cl.exe','/nologo','/std:c++20','/EHsc','/W4','/WX','/utf-8','/DNOMINMAX',f'/{mode}',
              '/DXAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1',
              '/DXAR_CLERGY_MAILBOX_STANDALONE_ADAPTER=1',f'/I{NATIVE / "include"}']
    run_batch(command=compiler+['/c','/MP32']+[str(NATIVE/'src'/name) for name in SOURCES],
              shell=shell,output=out,tag='compile')
    executable=out/'clergy_mailbox.exe'
    run_batch(command=compiler+[str(NATIVE/'src'/TEST)]+[str(out/Path(name).with_suffix('.obj')) for name in SOURCES]+
              ['User32.lib',f'/Fe:{executable}'],shell=shell,output=out,tag='link')
    wire=out/'wire'; wire.mkdir(exist_ok=True)
    run=subprocess.run([str(executable),str(wire)],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15)
    (out/'run.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    require(run.returncode==0,f'{mode} actual mailbox fixture failed: {out / "run.log"}')
    return dict(mode=mode,compile='GREEN_W4_WX',stdout=run.stdout.strip(),executable_sha256=sha(executable),
                actual_wire_sha256=validate_wire(wire))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,required=True)
    args=parser.parse_args(); out=args.artifacts.resolve(); out.mkdir(parents=True,exist_ok=True)
    temp=out/'temp'; temp.mkdir(exist_ok=True); os.environ['TEMP']=os.environ['TMP']=str(temp)
    shell=visual_studio_developer_shell()
    source_pins={name:sha(NATIVE/'src'/name) for name in SOURCES+(TEST,)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda mode:run_mode(shell,out,mode),('Od','O2')))
    require(source_pins=={name:sha(NATIVE/'src'/name) for name in SOURCES+(TEST,)},'compiled source changed during fixture')
    receipt=dict(schema='xar.ck3.religion-clergy-appointment-mailbox-fixture/v1',status='GREEN',
                 time_utc=datetime.now(timezone.utc).isoformat(),results=results,source_sha256=source_pins,
                 first_component_matrix_repeated=False,native_api='real explicit candidate full CharacterID; current owner only',
                 actual_pipeline='worker TrySubmit -> owning ObservePumpDrain -> actual Core/Clergy reader -> Wait/Reclaim -> native command_result serializer -> Python json decoder',
                 mailbox_permit='existing primary offline permitted_executor; central permitted_executor_clergy12002 pending',
                 dedicated_production_registration_tested=False,ck3_accessed=False,live_verified=False,readiness='static-ready')
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='GREEN',result=str(out/'result.json'),result_sha256=sha(out/'result.json'),fixtures=[r['stdout'] for r in results])))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
