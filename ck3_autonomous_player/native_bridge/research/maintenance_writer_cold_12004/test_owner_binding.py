"""One production-contract compound; synthetic cash/OS/raw, no observer execution."""
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from types import SimpleNamespace

def need(ok, why):
    if not ok:
        raise ValueError(why)

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def rejected(call, text=None):
    try:call()
    except (ValueError,RuntimeError) as error:
        need(text is None or text in str(error),'Wrong rejection: '+str(error));return str(error)
    raise ValueError('Malformed ownership was accepted')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--actual-frame',type=Path)
    p.add_argument('--common-adapter',type=Path)
    p.add_argument('--external-driver',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    need(not a.output.exists(),'Create-only test result already exists')
    repo=a.repo.resolve();here=Path(__file__).resolve().parent
    sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src')]
    reader=load(here/'consume_writer_actual.py','_owner_actual_reader')
    prepare=load(here/'prepare_writer_admission.py','_owner_actual_prepare')
    card=load(here/'build_card.py','_owner_actual_card')
    contract=reader.owner
    reader.configure(repo)
    compiled=json.loads((repo/'ck3_autonomous_player/tests/unit/fixtures/war_payment_compiled_12004_a06.json').read_bytes())
    selected=next(r['value'] for r in compiled if r['case']=='controlled_window_personal')
    journal=copy.deepcopy(selected.get('war_payment_observations_v1',selected))
    s=journal['current_session']
    if a.actual_frame:
        original=json.loads(a.actual_frame.read_bytes());frame=copy.deepcopy(original['body'])
        need(frame.get('episode_projection')=='native_campaign' and 'episode_run_id' not in frame,'Actual source no longer has the observed missing episode')
        source=dict(path=str(a.actual_frame),sha256=hashlib.sha256(a.actual_frame.read_bytes()).hexdigest(),body_kind='R214 derived original; not original wire bytes')
    else:
        frame=dict(episode_projection='native_campaign',local_player_id=1,paused=True,map_ready=True,
                   revision=8,native_revision=7,date_raw=53149056,
                   played_character=dict(character_id=s['player_character_full_id'],alive=True),
                   diagnostics=dict(bridge_pid=s['pid'],connection_generation=s['connection_generation'],
                     hello=dict(expected_ck3_version=journal['game_version'],expected_ck3_sha256=journal['executable_sha256']),
                     last_heartbeat=dict(main_thread_query_mailbox_v1=dict(game_state=0x500000))))
        source=None
    frame['paused']=True;frame['map_ready']=True
    state=frame['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['game_state']
    s.update(pid=frame['diagnostics']['bridge_pid'],connection_generation=frame['diagnostics']['connection_generation'],
             player_character_full_id=frame['played_character']['character_id'],snapshot_revision=frame['native_revision'],
             native_date_raw=frame['date_raw'],process_create_time_100ns=123456789,
             game_state_identity_witness=state,loaded_game_epoch=None,same_owned_process_no_load_window=True,
             absolute_day_raw=389000)
    journal.update(records=[],natural_parent_returns=[],qualified_boarding_debits=[],latest_sequence=0,oldest_sequence=0,
                   overwritten=0,publication_failures=0,controlled_window_admitted=True)
    journal['sampling'].update(retained_records=0,qualified_records=0,capture_enabled=True,busy=False,active_captures=0,clear_completed=False)
    journal['natural_journal_status'].update(read_complete=True,retained_records=0,overwritten_records=0,failed_appends=0)
    if 'raw_resource4_getter_v1' in journal:
        journal['raw_resource4_getter_v1'].update(records=[],latest_sequence=0,oldest_sequence=0,overwritten=0,publication_failures=0,read_complete=True)
    values=dict(context_identity_before=0x300000,context_identity_after=0x300000,value_2c0=0,value_2c8=0,value_28=0,value_30=0,capture_complete=True,context_stable=True,failed_reads=0)
    leaf=dict(schema_version=1,observation_kind='paused_current_raw_context',attribution_scope='current_raw_context_only',maintenance_attribution='unclosed',character=0x100000,character_full_id=s['player_character_full_id'],snapshot_revision=frame['native_revision'],date_raw=frame['date_raw'],actor_identity_stable=True,same_frame_ready=True,values=values,admission_ready=True,unavailable_reason=None)
    cash=dict(game_version=journal['game_version'],executable_sha256=journal['executable_sha256'],played_character_id=s['player_character_full_id'],snapshot_revision=frame['native_revision'],date_raw=frame['date_raw'],readiness={'same_frame_ready':True},current_raw_context_v1=leaf,war_payment_observations_v1=journal)
    owner=prepare.owner.qualify(contract.ORDINARY,None,frame,journal,leaf,expected_game_state=state,expected_local_player_id=frame['local_player_id'])
    need(owner['episode_run_id'] is None and owner['original_episode_key_present'] is False,'Original absent episode was fabricated')
    meta=prepare.owner.metadata(owner)
    need(meta['episode_id']=='' and meta['episode_is_null']==1 and 'None' not in meta.values(),'Null was stringified')
    need(prepare.owner.native_argv_tail(owner)==['--ordinary-null-owner-binding'],'New native opt-in absent')
    checks=['actual_missing_EP_owner_to_metadata_v2']
    expected={k:s[k] for k in ['pid','process_create_time_100ns','connection_generation','controlled_window_id','player_character_full_id']}
    def envelope(tool,body,args):return dict(machine_id=journal['machine_id'],is_error=False,body=body,request=dict(tool=tool,arguments=args))
    def blobs(f,c):
        return (json.dumps(envelope('ck3_query_war_cash_current_resources_private_v1',c,dict(payment_sampling='query',expected_revision=f['revision']))).encode(),json.dumps(envelope('ck3_take_snapshot',f,dict(include_native_command_history=False))).encode())
    cashraw,beforeraw=blobs(frame,cash)
    admission=dict(schema='xar.maintenance.writer_pc.future-admission.v2',machine_id=journal['machine_id'],expected_root_identity=expected,expected_payment_epoch=journal['sampling']['epoch'],expected_episode=None,raw_leaf=leaf,source_packet_pins=[dict(sha256=reader.digest(r)) for r in [cashraw,beforeraw]],known_producer=False,maintenance_attribution='unclosed',owner_binding=owner)
    binding=reader.bind_inputs(admission,cashraw,beforeraw)
    start={k:v for k,v in binding.items() if k not in ('current_raw_cache','admission_owner_binding')}
    start.update(kind='start',schema='xar.maintenance.writer_pc.cold.v2',synthetic=False,CK3_observed=True,maintenance_attribution='unclosed',module_base=0x140000000,module_size=102518784,actual_writer_game_date=None,DR7_write_len8_mask=0x99990055,field_offsets=list(reader.OFFSETS),initial_values=[0]*4,owner_binding=copy.deepcopy(owner),native_owner_memory_verified=True)
    arm=dict(kind='arm',thread_id=901,success=True,saved_debug=[0]*6,armed_debug=[0x300000+x for x in reader.OFFSETS]+[0,0x99990055])
    restore=dict(kind='restore',thread_id=901,readback=True,debug=[0]*6)
    terminal=dict(kind='terminal',reason='timeout',restored=True,detached=True,pending_event=False,cleanup_complete=True,hit_count=0,data_event_count=0,writer_thread_count=0,created_thread_events=0,restore_readback_rows=1,process_exited=False,observation_thread_admission_complete=True,full_window_all_writes_covered=False,CK3_observed=True,known_producer=False,military_attribution='unclosed')
    result=reader.project([start,arm,restore,terminal],binding)
    need(result['cleanup_proved'] and result['qualified_slot_count']==0 and result['Root_binding']['admission_owner_binding']==owner and result['maintenance_attribution']=='unclosed','v2 raw bind/project failed')
    checks.append('prepare_owner_to_actual_bind_to_v2_raw_projection')
    bad=copy.deepcopy(start);bad['native_owner_memory_verified']=False
    rejected(lambda:reader.project([bad,arm,restore,terminal],binding),'Native ordinary owner')
    bad=copy.deepcopy(start);bad['owner_binding']['game_state_identity_witness']+=8
    rejected(lambda:reader.project([bad,arm,restore,terminal],binding),'Native ordinary owner')
    checks.append('native_memory_readback_missing_or_foreign_owner_rejected')
    for key,path in [('projection',('episode_projection',)),('PID',('diagnostics','bridge_pid')),('generation',('diagnostics','connection_generation')),('actor',('played_character','character_id')),('local_player',('local_player_id',)),('GameState',('diagnostics','last_heartbeat','main_thread_query_mailbox_v1','game_state'))]:
        f=copy.deepcopy(frame);item=f
        for part in path[:-1]:item=item[part]
        item[path[-1]]='one_life' if key=='projection' else item[path[-1]]+1
        rejected(lambda f=f:prepare.owner.qualify(contract.ORDINARY,None,f,journal,leaf,expected_game_state=state,expected_local_player_id=frame['local_player_id']))
    checks.append('projection_PID_generation_actor_localplayer_GameState_drift_rejected')
    rejected(lambda:prepare.owner.qualify(contract.EPISODE_BOUND,None,frame,journal,leaf),'legacy episode')
    rejected(lambda:prepare.owner.episode_arguments(contract.ORDINARY,'None'),'cannot relabel')
    legacy_frame=copy.deepcopy(frame);legacy_frame['episode_run_id']='real-source-bound-episode'
    need(prepare.owner.qualify(contract.EPISODE_BOUND,legacy_frame['episode_run_id'],legacy_frame,journal,leaf) is None,'Legacy nonempty branch changed')
    legacy_cash,legacy_before=blobs(legacy_frame,cash)
    legacy=copy.deepcopy(admission);legacy.pop('owner_binding');legacy.update(schema='xar.maintenance.writer_pc.future-admission.v1',expected_episode=legacy_frame['episode_run_id'],source_packet_pins=[dict(sha256=reader.digest(r)) for r in [legacy_cash,legacy_before]])
    legacy_binding=reader.bind_inputs(legacy,legacy_cash,legacy_before)
    need('admission_owner_binding' not in legacy_binding,'Legacy gained ordinary fields')
    checks.append('legacy_nonempty_accepted_null_and_fake_None_rejected')
    cpp=here/'cold_observer.cpp';cppsha=hashlib.sha256(cpp.read_bytes()).hexdigest()
    prepare.require_ordinary_compiled_source({'input_pins':[dict(path=str(cpp),sha256=cppsha)]})
    rejected(lambda:prepare.require_ordinary_compiled_source({'input_pins':[dict(path='source-a08/cold_observer.cpp',sha256='24b9d584ee451ef822c6386484efcda2578072cb5569ce1740b910e3bbadd0ee')]}),'a07 cannot gain')
    checks.append('a07_source_manifest_rejected_new_exact_source_pin_accepted')
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    cfg=dict(repo=str(repo),python=sys.executable,source_head=head,watch_output_root=str(a.output.with_suffix('.UNCREATED-WATCH')),owner_binding_mode=contract.ORDINARY,expected={k:1 for k in card.EXPECTED},timeout_ms=30000,max_slot_hits=128,build_dir=str(here),machine_execution_gate=str(__file__),cash_response=str(__file__),before_response=str(__file__))
    cfg['expected'].update(episode=None,machine=journal['machine_id'],game_state_identity_witness=state,local_player_id=frame['local_player_id'])
    rendered=card.make_card(cfg)
    need('--expected-episode' not in rendered['prepare_argv'] and '--owner-binding-mode' in rendered['prepare_argv'] and 'None' not in rendered['prepare_argv'],'Card fabricated or lost null ownership')
    checks.append('real_build_card_explicit_mode_no_string_episode')
    adapter=load(a.common_adapter or repo/'tools/ck3_mod_acceptance_cases/r08_writer_common_adapter.py','_owner_actual_common')
    with tempfile.TemporaryDirectory(dir=a.output.parent,prefix='owner-seam-') as scratch:
        out=Path(scratch);calls=[]
        def execute_plan(steps,name,timeout=None):
            need(len(steps)==1,'Not the original single common step')
            step=steps[0];calls.append(step)
            row=dict(id=step['id'],ok=True,error=None,result=frame if step['tool']=='ck3_take_snapshot' else cash)
            (out/(name+'.actual-results.json')).write_text(json.dumps({'rows':[row]}),encoding='utf-8')
            return [row]
        client=SimpleNamespace(output=out,guard=lambda:None,retain_process=lambda:None,
            _process={'pid':s['pid']},execute_plan=execute_plan,validate_frame=lambda *x,**kw:None)
        common=adapter.collect_current_context({'output':str(out)},client,machine=journal['machine_id'],
            prefix='synthetic-owner',packet_root=out/'views',_created_reader=lambda _:123456789,
            owner_binding_mode=contract.ORDINARY)
        need(common['owner_binding_mode']==contract.ORDINARY and common['expected']['episode'] is None
             and common['expected']['game_state_identity_witness']==state
             and common['expected']['local_player_id']==frame['local_player_id']
             and [x['tool'] for x in calls]==['ck3_take_snapshot',adapter.CASH_TOOL]
             and calls[1]['args']=={'expected_revision':frame['revision'],'payment_sampling':'query'}
             and common['sampling_actions']==0 and common['observer_started'] is False,
             'Same common client changed null provenance or enabled observation')
    checks.append('actual_common_collect_explicit_null_mode_readonly_same_client')
    if a.external_driver:
        tree=ast.parse(a.external_driver.read_text(encoding='utf-8'))
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='native_argv_matches']
        need(len(nodes)==1,'Actual Root driver v2 argv seam missing')
        ns={'Path':Path,'need':need};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(a.external_driver),'exec'),ns)
        cfg={'watch':{'owner_binding_mode':contract.ORDINARY,'build_dir':str(here),'expected':{'episode':None,'machine':journal['machine_id']}}}
        watch=here/'NOT-CREATED'
        prepared={'schema':admission['schema'],'expected_episode':None,'owner_binding':owner,
            'argv':[str(here/'maintenance_writer_cold_observer.exe'),'--enable-ck3-12004-data-watch',
                '--fixture-meta',str(watch/'CURRENT-RAW-ADMISSION.meta.txt'),'--timeout-ms','30000',
                '--raw',str(watch/'writer.raw.ndjson'),'--ready',str(watch/'writer.ready.json'),
                '--expected-hits','128','--machine-id',journal['machine_id'],'--ordinary-null-owner-binding']}
        need(ns['native_argv_matches'](cfg,watch,prepared),'New exact native argv rejected')
        bad=copy.deepcopy(prepared);bad['argv'].pop()
        need(not ns['native_argv_matches'](cfg,watch,bad),'Old 14-item a07 argv accepted for v2')
        bad=copy.deepcopy(prepared);bad['schema']='xar.maintenance.writer_pc.future-admission.v1'
        rejected(lambda:ns['native_argv_matches'](cfg,watch,bad),'Explicit v2')
        checks.append('actual_external_driver_exact_v2_argv_and_a07_rejection')
    # Native code is deliberately not compiled/executed in this contract check.
    report=dict(status='PASS_ONE_PRODUCTION_OWNER_BINDING_COMPOUND',checks=checks,actual_frame_source=source,synthetic_cash_and_OS_FILETIME=True,synthetic_raw_not_native_wire=True,native_build_or_execution=False,SDK_DR_game_desktop_calls=0,old_matrix_runs=0,live_or_paid_credit=False,python=sys.version,optimization=sys.flags.optimize)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report));return 0

if __name__=='__main__':
    raise SystemExit(main())
