"""Default-off future actual4 data-watch adapter. Never queries SDK or writes game memory."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys

import importlib.util as _owner_import
_owner_spec = _owner_import.spec_from_file_location('_writer_owner_binding_v2', Path(__file__).with_name('owner_binding.py'))
owner = _owner_import.module_from_spec(_owner_spec)
_owner_spec.loader.exec_module(owner)

def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def require_int(value,name):
    require(type(value) is int and value>=0,name+' must be exact nonnegative integer')
    return value
def require_ordinary_compiled_source(receipt):
    expected=sha(Path(__file__).with_name('cold_observer.cpp'))
    rows=[row for row in receipt['input_pins'] if Path(row['path']).name=='cold_observer.cpp']
    require(len(rows)==1 and rows[0]['sha256']==expected,
            'Ordinary-null requires a new observer build/SYSTEM source pin; a07 cannot gain this capability')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-ck3-12004-data-watch',action='store_true')
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--machine-execution-gate',type=Path,required=True)
    parser.add_argument('--cash-response',type=Path,required=True)
    parser.add_argument('--before-response',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    for name in ['pid','created','generation','window','epoch','character-id','revision','native-revision','date']:
        parser.add_argument('--expected-'+name,type=int,required=True)
    parser.add_argument('--expected-episode')
    parser.add_argument('--owner-binding-mode',choices=(owner.EPISODE_BOUND,owner.ORDINARY),default=owner.EPISODE_BOUND)
    parser.add_argument('--expected-game-state',type=int)
    parser.add_argument('--expected-local-player-id',type=int)
    parser.add_argument('--expected-machine',required=True)
    parser.add_argument('--timeout-ms',type=int,default=10000)
    parser.add_argument('--max-slot-hits',type=int,default=64)
    args=parser.parse_args()
    require(args.enable_ck3_12004_data_watch,'Default OFF: explicit enable and independent Root expectations are required')
    require(500<=args.timeout_ms<=30000 and 1<=args.max_slot_hits<=128,'Finite native watch budget out of range')
    repo=args.repo.resolve();build=args.build_dir.resolve();out=args.output_root.resolve()
    require(not out.exists(),'Append-only output already exists')
    sys.dont_write_bytecode=True;sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src')]
    from tools.ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge import war_payment_observations_v1 as payment
    from xar_autoplayer.bridge.nonwar_private_build import private_native_build_identity
    from xar_autoplayer.bridge.version_identity import CK3_12004
    from xar_autoplayer.bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1
    require(current_machine_id()==args.expected_machine,'Root expected current machine differs')
    packets={}
    for name,path in [('cash',args.cash_response),('before',args.before_response)]:
        raw=path.read_bytes();require(len(raw)<=3*1024**2,'Bounded fresh packet cap exceeded')
        packet=json.loads(raw.decode('utf-8-sig'))
        require(packet['machine_id']==args.expected_machine and packet['is_error'] is False,'Original packet machine/error mismatch')
        require(type(packet['body']) is dict,'Original packet body missing')
        structured=packet.get('sdk_result',{}).get('structured_content')
        if structured is not None:require(structured==packet['body'],'SDK receipt/body differ')
        packets[name]=packet
    snapshot=packets['before']['body'];cash=packets['cash']['body']
    require(packets['before']['request']['tool']=='ck3_take_snapshot' and packets['cash']['request']['tool']=='ck3_query_war_cash_current_resources_private_v1','Only existing paired readonly query is eligible')
    require(packets['cash']['request']['arguments']['payment_sampling']=='query','Current same-frame journal query required')
    require(private_native_build_identity(snapshot)==CK3_12004,'Exact actual4 hello qualification absent')
    from xar_autoplayer.bridge.war_cash_current_raw_context_v1 import validate_current_raw_context_v1
    validate_current_raw_context_v1(cash,snapshot=snapshot)
    normalize_war_cash_current_resources_v1(cash,snapshot=snapshot)
    extras=payment.normalize_payment_extras(cash,snapshot=snapshot,payment_sampling='query')
    journal=extras[payment.JOURNAL_KEY];session=journal['current_session'];sampling=journal['sampling']
    expected=dict(pid=args.expected_pid,process_create_time_100ns=args.expected_created,connection_generation=args.expected_generation,controlled_window_id=args.expected_window,player_character_full_id=args.expected_character_id)
    for key,value in expected.items():
        require(require_int(session[key],key)==value and value>0,'Independent Root identity mismatch '+key)
    require(session['same_owned_process_no_load_window'] is True and journal['controlled_window_admitted'] is True,'Current owned no-load window absent')
    require(require_int(sampling['epoch'],'payment epoch')==args.expected_epoch and args.expected_epoch>0,'Independent Root payment epoch differs')
    require(journal['installed'] is True and journal['install_failure_flags']==0 and journal['read_complete'] is True,'Current journal install/read incomplete')
    require(sampling['available'] is True and sampling['capture_enabled'] is True and sampling['busy'] is False and sampling['active_captures']==0,'Current query observer journal unavailable/busy')
    require(journal['steam_build_id']==25734779,'Exact Steam build absent')
    require(snapshot['revision']==args.expected_revision and snapshot['native_revision']==args.expected_native_revision and snapshot['date_raw']==args.expected_date and snapshot.get('episode_run_id')==args.expected_episode,'Independent Root frame/episode differs')
    require(snapshot['diagnostics']['bridge_pid']==args.expected_pid and snapshot['diagnostics']['connection_generation']==args.expected_generation,'Independent snapshot PID/generation differs')
    require(snapshot['played_character']['character_id']==args.expected_character_id and snapshot['played_character']['alive'] is True and snapshot['paused'] is True and snapshot['map_ready'] is True,'Paused living current-player frame absent')
    leaf=cash.get('current_raw_context_v1')
    require(type(leaf) is dict,'Fresh optional current raw leaf missing; never substitute historical callback addresses')
    fields={'schema_version','observation_kind','attribution_scope','maintenance_attribution','character','character_full_id','snapshot_revision','date_raw','actor_identity_stable','same_frame_ready','values','admission_ready','unavailable_reason'}
    require(set(leaf)==fields and leaf['schema_version']==1 and leaf['observation_kind']=='paused_current_raw_context' and leaf['attribution_scope']=='current_raw_context_only' and leaf['maintenance_attribution']=='unclosed','Current raw leaf source/version/scope mismatch')
    require(leaf['actor_identity_stable'] is True and leaf['same_frame_ready'] is True and leaf['admission_ready'] is True and leaf['unavailable_reason'] is None,'Fresh raw leaf not admission-ready')
    require(leaf['character_full_id']==args.expected_character_id and leaf['snapshot_revision']==args.expected_native_revision and leaf['date_raw']==args.expected_date,'Raw leaf frame/actor differs')
    values=leaf['values'];context=values['context_identity_before'];character=leaf['character']
    require(type(character) is int and 0<character<=0x7ffffffff000 and type(context) is int and 0<context<=0x7ffffffff000 and context%8==0,'Fresh raw Character/context invalid, unaligned or overflow')
    require(values['context_identity_after']==context and values['capture_complete'] is True and values['context_stable'] is True and values['failed_reads']==0,'Fresh raw context double-pointer snapshot incomplete')
    for key in ['value_2c0','value_2c8','value_28','value_30']:require(type(values[key]) is int and -(1<<63)<=values[key]<(1<<63),'Fresh signed64 term unavailable')
    owner_binding=owner.qualify(args.owner_binding_mode,args.expected_episode,snapshot,journal,leaf,expected_game_state=args.expected_game_state,expected_local_player_id=args.expected_local_player_id)
    # Exact SYSTEM registration is checked before any project observer execution.
    result=json.loads((build/'native-msvc-result.json').read_bytes());exclusion=result['defender_exclusions'];receipt_path=Path(exclusion['receipt']);manifest_path=Path(exclusion['manifest']);receipt=json.loads(receipt_path.read_bytes());manifest=json.loads(manifest_path.read_bytes())
    require(result['built'] is True and exclusion['status']=='verified' and sha(receipt_path)==exclusion['receipt_sha256'],'Standard producer not verified')
    require(receipt['status']=='verified' and receipt['admin_token'] is True and receipt['system_token_sid']=='S-1-5-18' and receipt['missing_requested_paths']==[],'Actual SYSTEM project EXE gate incomplete')
    require(receipt['manifest_sha256']==hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'Canonical manifest differs')
    machine_gate=json.loads(args.machine_execution_gate.read_bytes())
    require(machine_gate['machine_id']==args.expected_machine==current_machine_id(),'Machine-labelled execution gate belongs to another host')
    require(machine_gate['status']=='verified-before-first-project-EXE-execution' and machine_gate['system_token_sid']=='S-1-5-18' and machine_gate['admin_token'] is True,'Host execution gate not SYSTEM-qualified')
    require(Path(machine_gate['receipt']).resolve()==receipt_path.resolve() and machine_gate['receipt_sha256']==sha(receipt_path) and machine_gate['manifest_file_sha256']==sha(manifest_path) and machine_gate['manifest_canonical_sha256']==receipt['manifest_sha256'],'Machine gate does not bind exact unmodified SYSTEM evidence')
    require(machine_gate['files']==manifest['files'],'Machine gate/executable manifest differs')

    require({Path(x['path']).name for x in manifest['files']}=={'maintenance_writer_cold_observer.exe','maintenance_writer_cold_target.exe'},'Declared project target names differ')
    for item in manifest['files']:
        p=Path(item['path']);require(p.parent==build and p.stat().st_size==item['size'] and sha(p)==item['sha256'] and str(p) in receipt['verified_requested_paths'],'Exact project EXE path/bytes/readback differ')
        require(any(x['path']==str(p) and x['sha256']==item['sha256'] for x in receipt['files']),'SYSTEM receipt source file pin missing')
    for pin in receipt['input_pins']:require(sha(Path(pin['path']))==pin['sha256'],'Producer input provenance pin differs')
    if owner_binding is not None:require_ordinary_compiled_source(receipt)
    out.mkdir(parents=True)
    meta=dict(pid=args.expected_pid,tid=0,created=args.expected_created,character=character,context=context,full_id=args.expected_character_id,module_base=0,module_size=0,qualified_exe_sha256='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518',game_version='1.20.0.4',steam_build_id=25734779,controlled_window_id=args.expected_window,payment_epoch=args.expected_epoch,connection_generation=args.expected_generation,source_observation_kind='paused_current_raw_context',native_revision=args.expected_native_revision,date_raw=args.expected_date,episode_id=args.expected_episode,source_cash_sha256=sha(args.cash_response))
    if owner_binding is not None:meta.update(owner.metadata(owner_binding))
    meta_path=out/'CURRENT-RAW-ADMISSION.meta.txt';write_new(meta_path,''.join(k+'='+str(v)+'\n' for k,v in meta.items()))
    argv=[str(build/'maintenance_writer_cold_observer.exe'),'--enable-ck3-12004-data-watch','--fixture-meta',str(meta_path),'--timeout-ms',str(args.timeout_ms),'--raw',str(out/'writer.raw.ndjson'),'--ready',str(out/'writer.ready.json'),'--expected-hits',str(args.max_slot_hits),'--machine-id',args.expected_machine]
    argv+=owner.native_argv_tail(owner_binding)
    admission=dict(schema='xar.maintenance.writer_pc.future-admission.v2' if owner_binding is not None else 'xar.maintenance.writer_pc.future-admission.v1',machine_id=args.expected_machine,prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),prepare_only=args.prepare_only,scope='Current raw query plus original same-frame journal/Root identity only; not a wallet callback or military attribution',expected_root_identity=expected,expected_payment_epoch=args.expected_epoch,expected_episode=args.expected_episode,raw_leaf=leaf,source_packet_pins=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in [args.cash_response,args.before_response]],SYSTEM_receipt_pin=dict(path=str(receipt_path),sha256=sha(receipt_path)),machine_execution_gate_pin=dict(path=str(args.machine_execution_gate),sha256=sha(args.machine_execution_gate)),argv=argv,native_revalidation_required=['Exact actual4 Root-qualified SHA/build plus process create/name, mapped image size and known16B parent anchor','Character ID/magic and context pointer stable twice before watch and after each read','All observed threads watch before continuing, reserved slots never stolen'],old_packet_freshness_not_inferred_from_mtime=True,Root_responsibility='These independently supplied current-window expectations must come from the fresh paused owned frame; this adapter never manufactures a new query, advances time, or grants observation permission from archived packet timestamps.',maintenance_attribution='unclosed',known_producer=False)
    if owner_binding is not None:
        admission['owner_binding']=owner_binding
        admission['native_required_contract']='xar.maintenance.writer_pc.owner-binding.v2; a07 is incompatible'
    write_new(out/'ADMISSION.actual.json',admission)
    if args.prepare_only:
        print(json.dumps(dict(status='PREPARED_ONLY_NATIVE_NOT_RUN',output=str(out),maintenance_attribution='unclosed')));return 0
    with (out/'observer.stdout').open('xb') as stdout,(out/'observer.stderr').open('xb') as stderr:
        run=subprocess.run(argv,stdout=stdout,stderr=stderr,creationflags=0x08000000,timeout=args.timeout_ms/1000+15,check=False)
    write_new(out/'EXECUTION.actual.json',dict(argv=argv,returncode=run.returncode,closed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),maintenance_attribution='unclosed',note='Read raw trap RIP_after as postinstruction PC. No instruction_start or business producer qualification is synthesized.'))
    return run.returncode

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:print(type(error).__name__+': '+str(error),file=sys.stderr);raise SystemExit(2)
