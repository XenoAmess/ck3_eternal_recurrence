package org.xar.ck3.control.wave2.military.actualcontact;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Original-consumer collector/replay adapter. Invoked only by the qualified shared Job. */
public final class CaptureContactConsumerVectors {
    private CaptureContactConsumerVectors() { }

    private static final String SCRIPT = """
        import copy,dataclasses,gzip,hashlib,importlib,inspect,json,os,pathlib,sys,tempfile
        from unittest.mock import Mock
        root=pathlib.Path(sys.argv[1]).resolve(); mode=sys.argv[2]
        vectors_path=pathlib.Path(sys.argv[3]); packet_path=pathlib.Path(sys.argv[4])
        report_path=pathlib.Path(sys.argv[5]); work=pathlib.Path(sys.argv[6])
        pins_path=pathlib.Path(sys.argv[7]); native_path=pathlib.Path(sys.argv[8])
        def strict_json(raw):
            def pairs(rows):
                out={}
                for key,value in rows:
                    if key in out: raise ValueError('duplicate JSON key')
                    out[key]=value
                return out
            return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda token:(_ for _ in ()).throw(ValueError(token)))
        def encoded(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
        def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
        pins=strict_json(pins_path.read_bytes())
        if pins['schema']!='xar.contact-consumer-source-pins/v1': raise RuntimeError('source pins schema')
        def verify_pins():
            for item in pins['files']:
                path=(root/item['path']).resolve()
                if not path.is_relative_to(root) or path.is_symlink() or path.is_junction() or not path.is_file(): raise RuntimeError('source pin path')
                if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']: raise RuntimeError('source pin drift: '+item['path'])
        verify_pins()
        if not native_path.is_file() or native_path.stat().st_size>65536:
            raise RuntimeError('REJECT_MISSING_NATIVE_FIRST: explicit original native FIRST fixture required; no skip or synthetic replacement')
        native_sha=digest(native_path)
        native=strict_json(native_path.read_text(encoding='utf-8-sig'))
        if native.get('schema')!='xar.actual4-route-position-witness-fixture.v1': raise RuntimeError('REJECT_NATIVE_FIRST_SCHEMA')
        work.mkdir(exist_ok=False); (work/'temp').mkdir(); tempfile.tempdir=str(work/'temp')
        os.environ['XAR_NORMAL_THREE_DAY_NATIVE_WIRE']=str(native_path)
        os.environ['XAR_NORMAL_THREE_DAY_ROUTE_WINDOW_OUTPUT']=str(work/'original-first.json')
        os.environ['PYTHONDONTWRITEBYTECODE']='1'; sys.dont_write_bytecode=True
        sys.path.insert(0,str(root/'ck3_autonomous_player/src')); sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
        sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'tools/g2_saved_campaign')); sys.path.insert(0,str(root/'tools'))
        from ck3_live_run_id import current_machine_id
        if current_machine_id()!=pins['machine_id']: raise RuntimeError('source/profile machine differs from actual execution machine')
        modules={name:importlib.import_module(name) for name in (
            'xar_autoplayer.physical_army_inventory_v1',
            'xar_autoplayer.bridge.route_contact_window_projection_v1',
            'xar_autoplayer.bridge.route_contact_window_contract',
            'xar_autoplayer.bridge.actual_contact_contract')}
        inventory=modules['xar_autoplayer.physical_army_inventory_v1']
        definitions=[(inventory,'validate_physical_army_inventory_shape_v1','inventory'),
            (inventory,'validate_native_physical_inventory_mailbox_v1','inventory'),
            (modules['xar_autoplayer.bridge.route_contact_window_projection_v1'],'project_route_contact_window_v1','route_window'),
            (modules['xar_autoplayer.bridge.route_contact_window_contract'],'advance_route_contact_window_step','route_step'),
            (modules['xar_autoplayer.bridge.route_contact_window_contract'],'parse_advance_route_contact_window_step','route_step'),
            (modules['xar_autoplayer.bridge.actual_contact_contract'],'normalize_actual_contact_scope','actual_scope'),
            (modules['xar_autoplayer.bridge.actual_contact_contract'],'query_actual_contact_scope_step','actual_query'),
            (modules['xar_autoplayer.bridge.actual_contact_contract'],'parse_query_actual_contact_scope_step','actual_query')]
        rows={}; calls={}; used=set(); packet=None
        if mode=='probe':
            packet=strict_json(gzip.decompress(packet_path.read_bytes()))
            if packet.get('schema')!='xar.compiled-contact-consumer-packet/v1': raise RuntimeError('packet schema')
            for row in packet['cases']:
                if type(row) is not dict or set(row)!={'operation','input_json','accepted','legacy_error','output_json','java_error'} or type(row['accepted']) is not bool or type(row['operation']) is not str or type(row['input_json']) is not str:
                    raise RuntimeError('actual Java packet case contract')
                key=row['operation']+'|'+row['input_json']
                if key in rows: raise RuntimeError('duplicate actual Java packet request')
                rows[key]=row
        def inventory_frame(value):
            # The existing validator's declared frame projection excludes timestamps,
            # command-history exports and transport diagnostics it never reads. Keep
            # all compared identities and every capability, including future flags.
            if type(value) is not dict: return value
            fields=('snapshot_id','revision','native_revision','date_raw','episode_run_id',
                'played_character','active_wars','player_armies','map_ready','paused',
                'episode_character_id','active_event','pending_character_interaction','route_contact_horizon_supported')
            result={key:value[key] for key in value if key in fields or key.endswith('_supported') or key=='capabilities'}
            if 'diagnostics' in value:
                diagnostics=value['diagnostics']
                result['diagnostics']=({key:diagnostics[key] for key in ('connection_generation',) if key in diagnostics}
                    if type(diagnostics) is dict else diagnostics)
            return result
        def request(name,a):
            if name=='validate_physical_army_inventory_shape_v1':
                return {'mode':'shape','receipt':a['receipt'],'expected':{(key[9:] if key.startswith('expected_') else key):value for key,value in a.items() if key!='receipt'}}
            if name=='validate_native_physical_inventory_mailbox_v1':
                result=dict(mode='mailbox',**a)
                result['starting']=inventory_frame(a['starting']); result['current']=inventory_frame(a['current'])
                return result
            if name=='project_route_contact_window_v1': return {'horizon':a['horizon'],'horizon_days':a['horizon_days']}
            if name=='advance_route_contact_window_step':
                value=dict(a); value['operation']='build'
                if isinstance(value['hostile_army_ids'],(tuple,set)): value['hostile_army_ids']=list(value['hostile_army_ids'])
                return value
            if name=='parse_advance_route_contact_window_step': return {'operation':'parse','step':a['step']}
            if name=='normalize_actual_contact_scope': return {'scope':a['value'],'expected':{key[9:]:value for key,value in a.items() if key!='value'}}
            if name=='query_actual_contact_scope_step': return dict(operation='build_query',**a)
            return {'operation':'parse_query','step':a['step']}
        def wire(name,value):
            if name.startswith('validate_'): return strict_json(encoded(dataclasses.asdict(value)))
            if name.startswith('parse_'): return {'parsed':strict_json(encoded(value))}
            if name in ('advance_route_contact_window_step','query_actual_contact_scope_step'): return {'step':value}
            return value
        def restored(name,value):
            if name.startswith('validate_'):
                return inventory.InventoryShapeCheck(value['valid'],value['reason'],tuple(value['hostile_army_ids']),tuple(value['contact_hostile_army_ids']),value['date_or_action_authorized'])
            if name=='parse_advance_route_contact_window_step':
                x=value['parsed']; return None if x is None else (x[0],x[1],tuple(x[2]),x[3])
            if name=='parse_query_actual_contact_scope_step': return None if value['parsed'] is None else tuple(value['parsed'])
            if name in ('advance_route_contact_window_step','query_actual_contact_scope_step'): return value['step']
            return copy.deepcopy(value)
        def wrapped(original,name,operation):
            signature=inspect.signature(original)
            def invoke(*args,**kwargs):
                bound=signature.bind(*args,**kwargs); bound.apply_defaults()
                raw=encoded(request(name,dict(bound.arguments))); key=operation+'|'+raw
                frame=sys._getframe(1); origin=pathlib.Path(frame.f_code.co_filename).resolve()
                caller=(origin.relative_to(root).as_posix() if origin.is_relative_to(root) else origin.name)+'::'+frame.f_code.co_name
                if origin.is_relative_to(root/'ck3_autonomous_player/src'):
                    calls[caller]=calls.get(caller,0)+1
                if mode=='probe':
                    if key not in rows: raise RuntimeError('actual Java packet lacks exact original-token request: '+name)
                    row=rows[key]; used.add(key)
                    if not row['accepted']: raise ValueError(row['legacy_error'])
                    return restored(name,strict_json(row['output_json']))
                try:
                    result=original(*args,**kwargs)
                except (ValueError,TypeError) as error:
                    row=dict(operation=operation,input_json=raw,accepted=False,expected=None,legacy_error=str(error))
                    if key in rows and rows[key]!=row: raise RuntimeError('same pure input changed rejection')
                    rows[key]=row; raise
                row=dict(operation=operation,input_json=raw,accepted=True,expected=wire(name,result),legacy_error=None)
                if key in rows and rows[key]!=row: raise RuntimeError('same pure input changed result')
                rows[key]=row
                return result
            return invoke
        replacements=[]
        for module,name,operation in definitions:
            original=getattr(module,name); replacement=wrapped(original,name,operation)
            replacements.append((original,replacement)); setattr(module,name,replacement)
        # Already imported production aliases are the real consumer seams; later imports
        # obtain these same replacements. No consumer body or source text is rewritten.
        for module in tuple(sys.modules.values()):
            if module is None or not getattr(module,'__name__','').startswith('xar_autoplayer'): continue
            for name,value in tuple(vars(module).items()):
                for original,replacement in replacements:
                    if value is original: setattr(module,name,replacement)
        import pytest
        test_names=['test_physical_army_inventory_v1','test_actual_contact_scope_contract',
            'test_public_cunit_zero_battle_contracts','test_normal_three_day_route_window',
            'test_campaign_deadline_transport_v1','test_exact_day_same_speed_configuration_v1',
            'test_move_error_bounded_readback','test_observed_move_intent','test_route_window_advance_outcome',
            'test_timeline_control_ack_v1','test_wartime_moving_contact_preview_lease']
        class Results:
            def __init__(self): self.collected=0; self.passed=0; self.failed=0; self.skipped=0
            def pytest_collection_finish(self,session): self.collected=len(session.items)
            def pytest_runtest_logreport(self,report):
                if report.failed: self.failed+=1
                if report.skipped: self.skipped+=1
                if report.when=='call' and report.passed: self.passed+=1
        summary=Results()
        tests=[str(root/'ck3_autonomous_player/tests/unit'/ (name+'.py')) for name in test_names]
        prefix=str(root/'ck3_autonomous_player/tests/unit/test_native_bridge_driver.py')+'::NativeHeadlessGameplayDriverTests::'
        tests += [prefix+name for name in ('test_actual_contact_scope_is_atomic_and_combat_v3_ready',
            'test_actual_contact_scope_step_includes_combat_but_excludes_retreat','test_route_contact_horizon_is_atomic_and_scope_complete')]
        exit_code=pytest.main(['-q','--tb=short','-p','no:cacheprovider','--basetemp='+str(work/'pytest'),*tests],plugins=[summary])
        if exit_code or summary.failed or summary.skipped or summary.passed!=summary.collected:
            raise RuntimeError('complete selected original consumer regression failed or skipped: '+repr(vars(summary)))
        from test_native_bridge_driver import FakeEndpoint,_hello,_snapshot,_army,_war
        import test_actual_contact_scope_contract as actual_fixture
        import test_physical_army_inventory_v1 as inventory_fixture
        import test_normal_three_day_route_window as window_fixture
        import xar_autoplayer.bridge.native_driver as driver_module
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.mcp_server import _ck3_query_actual_contact_scope
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        extra=[]
        # Actual Java scope bytes traverse accepted FakeEndpoint -> unchanged Driver ->
        # unchanged Service -> official MCP facade, preserving the native revision lane.
        for branch in ('new','join','none','observed','zero','drift'):
            endpoint=FakeEndpoint(); driver=driver_module.NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,command_timeout_seconds=0.2)
            endpoint.publish(_hello('game.state.snapshot','game.command.query-actual-contact-scope-v1-N'))
            subject=0 if branch=='zero' else 11
            scope=actual_fixture._scope(snapshot_revision=40,date_raw=53176176,subject_army_id=subject,
                subject_native_carmy_id=201,province_unit_army_ids=[subject,31,41],attacker_army_ids=[subject])
            if branch=='join': scope.update(transition_kind='join_existing',selected_combat_id=71,selected_combat_array_index=1,join_side='defender',defender_seed_character_id=None,initiator_is_defender=False,adjacency_kind_raw=0,opponent_army_ids=[],attacker_army_ids=[31],defender_army_ids=[41,subject])
            if branch=='none': scope.update(transition_kind='none',defender_seed_character_id=None,adjacency_kind_raw=0,opponent_army_ids=[],attacker_army_ids=[],defender_army_ids=[],combat_v3_participant_scope_ready=False)
            if branch=='observed': scope.update(scope_kind='post_contact_observation',transition_kind='in_combat',selected_combat_id=71,selected_combat_array_index=1,defender_seed_character_id=None,adjacency_kind_raw=0,loser_excluded_native_carmy_ids=[],opponent_army_ids=[],attacker_army_ids=[31,subject],defender_army_ids=[41])
            player=_army(subject,province_id=2585,owner_character_id=7,route_province_ids=[])
            endpoint.publish(_snapshot(40,date_raw=53176176,player_armies=[player]))
            def answer(frame):
                if frame.get('type')!='execute_step': return
                endpoint.publish(dict(type='command_result',protocol_version=1,request_id=frame['request_id'],ok=True,result=dict(step=frame['step'],accepted=True,status='available',query_sequence=1,snapshot_revision=40,actual_contact_scope=copy.deepcopy(scope))))
                if branch=='drift': endpoint.publish(_snapshot(41,date_raw=53176176,player_armies=[player]))
            endpoint.send_hook=answer
            try:
                if branch=='drift':
                    try: _ck3_query_actual_contact_scope(GameplayBridgeService(driver),subject,2585)
                    except BridgeUnavailableError: pass
                    else: raise AssertionError('cross-frame result accepted')
                else:
                    result=_ck3_query_actual_contact_scope(GameplayBridgeService(driver),subject,2585)
                    assert result['actual_contact_scope']==scope and result['queried_native_revision']==40
                    assert result['actual_contact_scope']['subject_native_carmy_id']==201
                    assert type(result['queried_revision']) is int and type(result['queried_snapshot_id']) is str
                submitted=[x for x in endpoint.frames if x.get('type')=='execute_step']
                assert len(submitted)==1 and submitted[0]['expected_revision']==40
                extra.append('actual-'+branch)
            finally: driver.close()
        # Native inventory optional field stays absent/null/present at the original
        # Driver branch; present good/malformed mailbox bytes use the Java result.
        for presence in ('good','null','absent','bad'):
            native,_,_=inventory_fixture.mailbox_fixture(); native['query_sequence']=9
            endpoint=FakeEndpoint(); driver=driver_module.NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,command_timeout_seconds=0.2)
            endpoint.publish(_hello('game.state.snapshot','game.state.war-objectives','game.state.army-routes','game.command.query-route-contact-horizon-v1-N'))
            driver._episode_character_id=29829; driver._episode_run_id='native-29829-2bc2d599f7f9'
            player=_army(inventory_fixture.SUBJECT,province_id=2610,owner_character_id=29829,army_state='idle',army_state_code=1,route_province_ids=[],retreating=False,in_combat=False)
            enemy=_army(inventory_fixture.ENEMY,province_id=2629,owner_character_id=30097,controllable=False,army_state='moving',army_state_code=1,route_province_ids=[2610],move_target_province_id=2610,retreating=False,in_combat=False)
            war=_war(allied_armies=[player],enemy_armies=[enemy],war_objective_province_ids=[2610]); war['war_id']=inventory_fixture.WAR
            endpoint.publish(_snapshot(7,date_raw=inventory_fixture.DATE,played_character={'character_id':29829,'alive':True},player_armies=[player],active_wars=[war]))
            horizon=dict(status='available',date_raw=inventory_fixture.DATE,snapshot_revision=7,subject_army_id=inventory_fixture.SUBJECT,target_province_id=2610,hostile_army_ids=[inventory_fixture.ENEMY],
                subject_route=dict(timeline_observable=True,army_id=inventory_fixture.SUBJECT,current_province_id=2610,effective_origin_province_id=2610,route_province_ids=[],arrival_date_raws=[]),
                hostile_routes=[dict(timeline_observable=True,army_id=inventory_fixture.ENEMY,current_province_id=2629,effective_origin_province_id=2629,route_province_ids=[2610],arrival_date_raws=[inventory_fixture.DATE+120])],
                horizon_start_date_raw=inventory_fixture.DATE,horizon_end_date_raw=inventory_fixture.DATE+24,one_day_contact_free=True,conflicts=[])
            if presence=='bad': native['unresolved_slots']=1
            def answer_inventory(frame):
                if frame.get('type')!='execute_step': return
                result=dict(step=frame['step'],accepted=True,status='available',query_sequence=9,snapshot_revision=7,route_contact_horizon=copy.deepcopy(horizon))
                if presence!='absent': result['physical_army_inventory']=None if presence=='null' else copy.deepcopy(native)
                endpoint.publish(dict(type='command_result',protocol_version=1,request_id=frame['request_id'],ok=True,result=result))
            endpoint.send_hook=answer_inventory
            try:
                step='query-route-contact-horizon-v1-'+str(inventory_fixture.SUBJECT)+'-to-2610-h-1-'+str(inventory_fixture.ENEMY)
                result=driver.execute_step(step)
                assert ('physical_army_inventory_check' in result)==(presence!='absent')
                if presence!='absent':
                    check=result['physical_army_inventory_check']; assert check['date_or_action_authorized'] is False
                    assert check['valid']==(presence=='good'),(presence,check)
                    assert check['reason']==('shape_valid_only' if presence=='good' else 'mailbox_receipt_missing_or_extra_fields' if presence=='null' else 'scan_incomplete_or_unresolved')
                extra.append('inventory-'+presence)
            finally: driver.close()
        # Original route proof join, current frame rejection and two-day prefix.
        driver,endpoint,plan,raw,before=window_fixture._driver_case()
        try:
            snapshot=driver.take_internal_semantic_snapshot(); history=copy.deepcopy(driver._command_history)
            proofs=driver_module._fresh_route_contact_window_advance_proofs(snapshot,history)
            assert window_fixture._WINDOW in proofs
            for field in ('snapshot_id','revision','native_revision','date_raw','episode_run_id','connection_generation','current_province_id','route_province_ids'):
                stale=copy.deepcopy(snapshot)
                if field=='connection_generation': stale['diagnostics'][field]+=1
                elif field=='current_province_id': stale['player_armies'][0][field]+=1
                elif field=='route_province_ids': stale['player_armies'][0][field]=[999,2585]
                elif isinstance(stale.get(field),int): stale[field]+=1
                else: stale[field]=str(stale.get(field))+'-stale'
                assert window_fixture._WINDOW not in driver_module._fresh_route_contact_window_advance_proofs(stale,history),field
            for province,allowed in ((199,True),(99,False)):
                sibling=copy.deepcopy(snapshot); own=_army(12,province_id=province,army_state='idle',army_state_code=1,route_province_ids=[],retreating=False,in_combat=False)
                sibling['player_armies'].append(own); sibling['active_wars'][0]['allied_armies'].append(own)
                joined=driver_module._fresh_route_contact_window_advance_proofs(sibling,history)
                assert (window_fixture._WINDOW in joined)==allowed
                if allowed: assert joined[window_fixture._WINDOW]['watch_army_ids']==(11,12,21)
            step=modules['xar_autoplayer.bridge.route_contact_window_contract'].advance_route_contact_window_step(11,2585,(21,),horizon_days=2)
            driver._campaign_clock_deadline_v1={'fixture':'prefix-selection-only'}
            clock=Mock(return_value={'step':step,'fixture_clock_submitted':False}); driver._execute_battle_sentinel_advance=clock
            prefix=driver._execute_route_contact_window_advance(step,expected_revision=snapshot['revision'])
            assert prefix['requested_horizon_days']==2 and prefix['route_contact_window']['horizon_days']==2
            assert clock.call_args.kwargs['route_window_proof']['window_end_date_raw']==window_fixture._START+48
            assert clock.call_count==1 and raw==before
            extra.extend(['route-frame-rejection','route-stationary-conjunction','route-prefix-original-consumer'])
        finally: driver.close()
        # The normal chooser's second builder site is distinct from its sole-army
        # fast path. An observed stationary sibling makes this use the common core.
        from test_gameplay_bridge import _native_war_plan, _army as planner_army
        import xar_autoplayer.strategy as strategy
        contact_horizon=window_fixture._horizon(); contact_horizon['snapshot_revision']=90
        player=planner_army(11,soldiers=900,province_id=20,controllable=True,move_target_province_id=2585,army_state='moving',route_province_ids=[31,2585])
        sibling=planner_army(12,soldiers=400,province_id=199,controllable=True,army_state='regular',route_province_ids=[])
        enemy=planner_army(21,soldiers=800,province_id=99,controllable=False,move_target_province_id=2585,army_state='moving',route_province_ids=[31,2585])
        query=strategy.query_route_contact_horizon_step(11,2585,(21,)); h1=strategy.advance_route_contact_horizon_step(11,2585,(21,))
        selected=strategy.advance_route_contact_window_step(11,2585,(21,),horizon_days=3)
        history=[dict(index=1,command=query,ok=True,result=dict(queried_snapshot_id='session:90',queried_revision=90,queried_native_revision=90,
            queried_connection_generation=1,queried_episode_run_id=None,route_contact_horizon=contact_horizon))]
        core_plan=_native_war_plan(player=player,players=[player,sibling],enemies=[enemy],score=0,date_raw=window_fixture._START,
            objective=2585,history=history,steps=(query,h1,selected),route_contact_horizon_supported=True)
        assert core_plan['selected_step']==selected,core_plan
        extra.append('normal-core-route-window-builder')
        import xar_autoplayer.bridge.campaign_deadline_v1 as deadline
        from types import SimpleNamespace
        from xar_autoplayer.campaign_score_cadence_v1 import date_to_raw
        cap_driver=SimpleNamespace(); start=date_to_raw('1066.9.15')
        deadline.configure_v1(cap_driver,campaign_id='contact-consumer-fixture',start_date='1066.9.15',start_date_raw=start,months=1)
        end=cap_driver._campaign_clock_deadline_v1['endpoint_date_raw']
        step=modules['xar_autoplayer.bridge.route_contact_window_contract'].advance_route_contact_window_step(11,2585,(21,),horizon_days=3)
        capped=deadline.cap_plan_v1(cap_driver,dict(plan={'selected_step':step},planning_source_frame={'date_raw':end-48}))
        assert capped['plan']['selected_step'].endswith('-days-2-h-1-21')
        extra.append('campaign-cap-real-parser-and-builder')
        required=('bridge/native_driver.py::_execute_route_contact_window_advance',
            'bridge/native_driver.py::_fresh_route_contact_window_advance_proofs',
            'bridge/service.py::query_actual_contact_scope','strategy.py::_choose_one_life_turn_core',
            'strategy.py::_sole_committed_moving_contact_first',
            'bridge/war_contract.py::','bridge/tactical_clock_diagnostics_v1.py::','bridge/campaign_deadline_v1.py::cap_plan_v1')
        # Wrappers record actual direct caller frames, never source-string membership.
        for fragment in required:
            if not any(fragment in caller for caller in calls):
                # Service's builder is in this direct frame; its query validation runs
                # after NativeDriver's normalizer and remains independently asserted.
                raise RuntimeError('actual consumer was not reached: '+fragment)
        verify_pins()
        if digest(native_path)!=native_sha: raise RuntimeError('native FIRST input drift')
        if mode=='collect':
            value=dict(schema='xar.original-contact-consumer-vectors/v1',cases=list(rows.values()))
            compressed=gzip.compress(encoded(value).encode('utf-8'),mtime=0)
            if len(compressed)>24576: raise RuntimeError('source consumer vectors exceed admitted gzip cap')
            with vectors_path.open('xb') as stream: stream.write(compressed)
        report=dict(mode=mode,original_tests=vars(summary),extra_checks=extra,unique_requests=len(rows),used_java_requests=len(used),actual_callers=calls,native_fixture_sha256=native_sha,
            actual_java_outputs_consumed=(mode=='probe'),game_rpc_count=0,live_consumer_switched=False)
        report_bytes=encoded(report).encode('utf-8')
        if len(report_bytes)>8192: raise RuntimeError('bounded contact consumer report exceeded')
        with report_path.open('xb') as stream: stream.write(report_bytes)
        print(encoded({'mode':mode,'tests':vars(summary),'extra_checks':len(extra),'unique_requests':len(rows),'actual_java_outputs_consumed':mode=='probe'}))
        """;

    public static void run(Path root, String python, String mode, Path vectors, Path packet,
                           Path report, Path fixtures, Path pins, Path nativeFixture) throws IOException, InterruptedException {
        if (!mode.equals("collect") && !mode.equals("probe")) { throw new IllegalArgumentException("collect/probe only"); }
        Process process = new ProcessBuilder(python, "-B", "-X", "utf8", "-c",
                "import sys; exec(compile(sys.stdin.buffer.read(), '<contact-consumer-adapter>', 'exec'))",
                root.toString(), mode, vectors.toString(), packet.toString(), report.toString(),
                fixtures.toString(), pins.toString(), nativeFixture.toString()).directory(root.toFile()).redirectErrorStream(true).start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var reader = executor.submit(() -> tail(process.getInputStream()));
            try {
                try (var stdin = process.getOutputStream()) { stdin.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
                if (!process.waitFor(75, TimeUnit.SECONDS)) { throw new IOException("contact original consumer timeout"); }
                byte[] diagnostics = reader.get(10, TimeUnit.SECONDS); System.err.write(diagnostics);
                if (process.exitValue() != 0) { throw new IOException("contact original consumer exit " + process.exitValue()); }
            } catch (java.util.concurrent.ExecutionException | java.util.concurrent.TimeoutException error) {
                throw new IOException("contact original consumer output incomplete", error);
            } finally { if (process.isAlive()) { process.destroyForcibly().waitFor(); } }
        }
    }

    private static byte[] tail(InputStream input) throws IOException {
        try (input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[1024]; int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > 2048) {
                    byte[] previous = output.toByteArray(); output.reset();
                    int keep = Math.min(previous.length, 1024);
                    output.write(previous, previous.length - keep, keep);
                }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
