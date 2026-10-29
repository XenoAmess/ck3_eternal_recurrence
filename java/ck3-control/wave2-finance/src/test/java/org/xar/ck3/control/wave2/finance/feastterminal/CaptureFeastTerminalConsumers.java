package org.xar.ck3.control.wave2.finance.feastterminal;

/** Fixture definition for the one central resident-host CI process; no executable or process launch. */
public final class CaptureFeastTerminalConsumers {
    private CaptureFeastTerminalConsumers() { }

    /** Central MapAdmissionCi owns bootstrap, process custody, invocation and the bounded final receipt. */
    public static String source() {
        return """
                def run_feast_terminal_consumer_probe(*,config:'JavaProjectionServiceV1',repository:'Path',golden_ref:'ExactRefV1',fixture_root:'Path')->dict[str,object]:
                    import copy,datetime,hashlib,inspect,json,sys
                    from pathlib import Path
                    from unittest.mock import patch
                    from tools.g2_saved_campaign import java_map_admission_client_v1 as client
                    from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,exact_read
                    if not isinstance(config,client.JavaProjectionServiceV1) or config.transport is not None or client.require_current_projection_config_v1() is not config:
                        raise RuntimeError('central actual shared projection bootstrap is required; no injected client or fallback')
                    if not isinstance(repository,Path) or not isinstance(fixture_root,Path) or not isinstance(golden_ref,ExactRefV1):
                        raise ValueError('explicit typed repository/golden/fresh fixture arguments required')
                    repository=repository.resolve()
                    if fixture_root.exists() or fixture_root.is_symlink() or fixture_root.is_junction() or not fixture_root.parent.is_dir():
                        raise RuntimeError('fresh explicitly authorized fixture root required')
                    fixture_root=fixture_root.resolve()
                    def strict_json(raw:bytes)->object:
                        return client.decode_projection_json_v1(raw,maximum_bytes=86016)
                    def canonical(value:object)->bytes:
                        return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+chr(10)).encode('utf-8')
                    def sha(raw:bytes)->str:
                        return hashlib.sha256(raw).hexdigest()
                    golden_bytes=exact_read(config.reader,golden_ref,86016)
                    golden=strict_json(golden_bytes)
                    if type(golden) is not dict or golden.get('schema')!='xar.feast-terminal-producer-golden/v1' or type(golden.get('cases')) is not list or len(golden['cases'])!=48:
                        raise RuntimeError('qualified original terminal golden required')
                    names=set()
                    for row in golden['cases']:
                        if type(row) is not dict or type(row.get('name')) is not str or row['name'] in names or type(row.get('accepted')) is not bool or type(row.get('input_json')) is not str:
                            raise RuntimeError('invalid or duplicate original terminal golden case')
                        names.add(row['name'])
                    identity=client.qualify_projection_service_v1(config)
                    operation=client.ProjectionOperation.FEAST_TERMINAL_NORMALIZE
                    profile=identity.profile(operation)
                    if not identity.actual_http or profile.input_max_bytes!=1048576 or profile.output_max_bytes!=2097152:
                        raise RuntimeError('same actual host must register the exact terminal typed-port profile')
                    for counter_operation in (client.ProjectionOperation.FEAST_COUNTER_NORMALIZE,client.ProjectionOperation.FEAST_COUNTER_PROJECT):
                        counter_profile=identity.profile(counter_operation)
                        if counter_profile.input_max_bytes!=16384 or counter_profile.output_max_bytes!=16384:
                            raise RuntimeError('same host must register both exact counter profiles used by the real consumer')
                    # The central SourceAssembly import observer owns the frozen SDK routes.
                    # Canonical repository paths bind tests and immutable wire fixtures only.
                    import xar_autoplayer.activity_feast_stage5_start_formal_consumer as consumer
                    import xar_autoplayer.bridge.activity_feast_terminal_outcome_v1 as delegate
                    import xar_autoplayer.bridge.activity_feast_stage5_start_private_transport as transport
                    import xar_autoplayer.environment as environment
                    if consumer.normalize_activity_feast_terminal_outcome_v1 is not delegate.normalize_activity_feast_terminal_outcome_v1 or consumer.project_feast_counter_consumer_v1 is not transport.project_feast_counter_consumer_v1:
                        raise RuntimeError('actual SDK consumer delegate/helper binding differs')
                    for module,function in ((consumer,consumer._record_lifecycle_observation),(consumer,consumer.read_feast_start_resolved_private_v1),(delegate,delegate.normalize_activity_feast_terminal_outcome_v1),(transport,transport.project_feast_counter_consumer_v1),(environment,environment.write_json_atomic),(client,client.call_current_projection_v1)):
                        if Path(function.__code__.co_filename).resolve()!=Path(module.__file__).resolve():
                            raise RuntimeError('actual SDK function origin differs from its imported module')
                    source_paths=[Path(module.__file__).resolve() for module in (consumer,delegate,transport,environment,client)]
                    source_paths.extend((Path(config.reader_source_ref.path).resolve(),Path(golden_ref.path).resolve()))
                    source_paths.extend(repository/path for path in (
                        'ck3_autonomous_player/tests/unit/test_ck3_12002_feast_wire.py',
                        'ck3_autonomous_player/tests/unit/test_activity_12004_native_wire.py',
                        'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_feast_hosted_post_wire.json',
                        'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_feast_fullcost_wire.json',
                        'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12003_feast_ordinary_start_wire.json'))
                    def refs()->list[dict[str,object]]:
                        return [dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for path in source_paths]
                    before_refs=refs()
                    fixture_root.mkdir(parents=False,exist_ok=False)
                    modes=('oracle-lifecycle','java-lifecycle','oracle-restore','java-restore')
                    states={mode:fixture_root/mode for mode in modes}
                    for state in states.values():
                        state.mkdir()
                    class FixtureDriver:
                        def __init__(self,state:Path,actor:int,post:dict[str,object])->None:
                            self.state_dir=state
                            self.actor=actor
                            self.post=post
                        def take_snapshot(self)->dict[str,object]:
                            return dict(revision=self.post['snapshot_revision'],paused=True,played_character=dict(character_id=self.actor))
                    def inventory()->list[dict[str,object]]:
                        files=[]
                        for path in fixture_root.rglob('*'):
                            if path.is_symlink() or path.is_junction():
                                raise RuntimeError('unexpected fixture link')
                            if path.is_file():
                                files.append(dict(relative_path=path.relative_to(fixture_root).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes())))
                        if len(files)>64 or sum(row['bytes'] for row in files)>524288:
                            raise RuntimeError('fixture scope exceeds 524288 bytes or 64 files')
                        return files
                    summaries=[]
                    accepted=0
                    rejected=0
                    actual_calls=0
                    actual_terminal_calls=0
                    lifecycle_calls=0
                    guard_cases=0
                    hosted_short_circuit_cases=0
                    request_chain=hashlib.sha256()
                    def retain_actual_call(result)->None:
                        nonlocal actual_calls,actual_terminal_calls
                        if not isinstance(result,client.ProjectionResult):
                            raise RuntimeError('actual common client did not issue a typed result')
                        context=client.require_result_context_v1(result,config=config,operation=result.operation,request_id=result.request_id,payload=result.payload_bytes)
                        if context.process!=identity.process or result.host_identity.process!=identity.process or result.host_identity.identity_sha256!=identity.identity_sha256 or result.http_call.transport_kind!='stdlib-http-loopback/v1' or not result.http_call.actual_http_invoked:
                            raise RuntimeError('projection result moved away from the one actual resident host')
                        actual_calls+=1
                        actual_terminal_calls+=int(result.operation is operation)
                        request_chain.update(canonical(dict(request_id=result.request_id,operation=result.operation.value,request_sha256=result.request_sha256,payload_sha256=result.payload_sha256,response_sha256=result.response_sha256)))
                    for row in golden['cases']:
                        request=client.decode_projection_object_v1(row['input_json'].encode('utf-8'),maximum_bytes=1048576)
                        if not row['accepted']:
                            try:
                                # The public wrapper rejects malformed API IDs locally; the original raw
                                # producer counterexamples must independently reach the actual Java codec.
                                client.call_projection_v1(config=config,operation=operation,payload=row['input_json'].encode('utf-8'),request_id='feast-terminal-rejected-'+row['name'])
                            except client.ProjectionDomainRejected as error:
                                call=error.http_call
                                if call.operation is not operation or call.transport_kind!='stdlib-http-loopback/v1' or not call.actual_http_invoked or call.process_before!=identity.process or call.process_after!=identity.process or error.response_body is None:
                                    raise RuntimeError('domain rejection lacks actual same-host response custody')
                                request_chain.update(canonical(dict(name=row['name'],rejection_code=error.code,request_sha256=call.request_sha256,response_sha256=call.response_sha256)))
                                rejected+=1
                                actual_calls+=1
                                actual_terminal_calls+=1
                            else:
                                raise RuntimeError('actual registered terminal producer accepted an original counterexample')
                            continue
                        post=copy.deepcopy(request['post'])
                        post.setdefault('balances',{key:dict(available=False,raw=None) for key in transport.RESOURCE_KEYS})
                        actor=request['actor_character_id']
                        activity=request['activity_id']
                        # A shared synthetic resolved seed avoids a Start action and UUID-dependent differences.
                        baseline=dict(status='applied',postcondition_verified=True,actor_character_id=actor,activity_id=activity,date_raw=post['date_raw'],post_native_revision=post['snapshot_revision'],next_turn_consumed=False,source_pending=dict(pre_outcome_values=None),post=copy.deepcopy(post))
                        ledger=dict(schema=consumer.LEDGER_SCHEMA,pending=None,resolved=baseline)
                        values={}
                        call_lists={}
                        for mode in modes:
                            state=states[mode]
                            consumer._write(state,copy.deepcopy(ledger))
                            calls=[]
                            terminal_before=actual_terminal_calls
                            def oracle(observed_post,*,activity_id:int,actor_character_id:int)->object:
                                if canonical(observed_post)!=canonical(post) or type(activity_id) is not int or type(actor_character_id) is not int or activity_id!=activity or actor_character_id!=actor:
                                    raise RuntimeError('oracle fixture changed the actual consumer request')
                                calls.append(inspect.currentframe().f_back.f_code.co_name)
                                # Fixed original producer evidence is an oracle, never a production fallback.
                                return copy.deepcopy(row['result'])
                            def query(driver,*,expected_revision:int)->object:
                                if driver.state_dir!=state or expected_revision!=post['snapshot_revision']:
                                    raise RuntimeError('fixture read binding differs')
                                return copy.deepcopy(post)
                            previous_profile=sys.getprofile()
                            def observe(frame,event:str,value)->None:
                                if previous_profile is not None:
                                    previous_profile(frame,event,value)
                                if event=='call' and frame.f_code is delegate.normalize_activity_feast_terminal_outcome_v1.__code__:
                                    calls.append(frame.f_back.f_code.co_name)
                                if event=='return' and frame.f_code is client.call_current_projection_v1.__code__ and isinstance(value,client.ProjectionResult):
                                    retain_actual_call(value)
                                    if value.operation is operation and canonical(client.decode_projection_object_v1(value.result_bytes,maximum_bytes=2097152))!=canonical(row['result']):
                                        raise RuntimeError('actual resident Java terminal result differs from qualified original evidence')
                            def invoke()->object:
                                if mode.endswith('lifecycle'):
                                    return consumer._record_lifecycle_observation(state,copy.deepcopy(ledger),copy.deepcopy(baseline),copy.deepcopy(post))
                                return consumer.read_feast_start_resolved_private_v1(FixtureDriver(state,actor,copy.deepcopy(post)))
                            try:
                                sys.setprofile(observe)
                                with patch.object(consumer,'query_activity_feast_hosted_post_private_v1',query):
                                    if mode.startswith('oracle-'):
                                        with patch.object(consumer,'normalize_activity_feast_terminal_outcome_v1',oracle):
                                            result=invoke()
                                    else:
                                        # Actual production delegate and the unique client remain unpatched.
                                        result=invoke()
                            finally:
                                sys.setprofile(previous_profile)
                            actual_ledger=consumer.read_feast_start_ledger(state)
                            values[mode]=client.decode_projection_json_v1(canonical(dict(result=result,ledger=actual_ledger)),maximum_bytes=524288)
                            call_lists[mode]=calls
                            if mode.startswith('java-') and actual_terminal_calls-terminal_before!=len(calls):
                                raise RuntimeError('a real consumer call did not traverse the one actual Java client')
                            inventory()
                        if canonical(values['oracle-lifecycle'])!=canonical(values['java-lifecycle']) or canonical(values['oracle-restore'])!=canonical(values['java-restore']) or call_lists['oracle-lifecycle']!=call_lists['java-lifecycle'] or call_lists['oracle-restore']!=call_lists['java-restore']:
                            raise RuntimeError('full original-oracle and actual Java consumer results or persisted JSON differ')
                        if call_lists['java-lifecycle']!=['_record_lifecycle_observation']:
                            raise RuntimeError('actual lifecycle consumer normalizer call not reached once')
                        restore_calls=call_lists['java-restore']
                        if any(name not in ('read_feast_start_resolved_private_v1','_record_lifecycle_observation') for name in restore_calls):
                            raise RuntimeError('unexpected actual restore normalizer callsite')
                        guard_cases+=int('read_feast_start_resolved_private_v1' in restore_calls)
                        hosted_short_circuit_cases+=int(restore_calls==['_record_lifecycle_observation'] and values['java-restore']['result'].get('restored_activity_observed') is True)
                        lifecycle_calls+=1+restore_calls.count('_record_lifecycle_observation')
                        accepted+=1
                        summaries.append(dict(name=row['name'],lifecycle_sha256=sha(canonical(values['java-lifecycle'])),restore_sha256=sha(canonical(values['java-restore'])),restore_normalizer_calls=restore_calls))
                    if accepted!=41 or rejected!=7 or guard_cases==0 or hosted_short_circuit_cases==0:
                        raise RuntimeError('finite original vector counts or both real restore branches are missing')
                    final_files=inventory()
                    after_identity=client.qualify_projection_service_v1(config)
                    if refs()!=before_refs or exact_read(config.reader,golden_ref,86016)!=golden_bytes or after_identity.process!=identity.process or after_identity.identity_sha256!=identity.identity_sha256:
                        raise RuntimeError('source/golden/resident process identity drift during consumer suite')
                    summary=dict(schema='xar.feast-terminal-same-host-consumer-probe/v2',machine_id=config.machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='pass',source_refs=before_refs,source_golden=dict(reference=golden_ref.to_wire(),machine_id=golden.get('machine_id')),host=dict(process=identity.process.to_wire(),identity_sha256=identity.identity_sha256,service_evidence_ref=config.service.service_evidence_ref.to_wire(),program_ref=config.service.program_ref.to_wire(),client_source_ref=config.client_source_ref.to_wire(),reader_source_ref=config.reader_source_ref.to_wire()),cases=dict(total=48,accepted=accepted,rejected=rejected,full_result_and_persisted_json_match=True,summaries=summaries),actual_consumer_calls=dict(lifecycle=lifecycle_calls,restore_guard_cases=guard_cases,restore_hosted_identity_short_circuit_cases=hosted_short_circuit_cases),actual_projection_calls=dict(count=actual_calls,terminal=actual_terminal_calls,request_response_chain_sha256=request_chain.hexdigest(),transport='stdlib-http-loopback/v1',same_resident_process=True),fixture_write_scope=dict(root=str(fixture_root),maximum_bytes=524288,maximum_files=64,retained_bytes=sum(row['bytes'] for row in final_files),files=final_files),scope='source-bound shared host and actual terminal delegate to both full legacy consumers and isolated original writer; no Game/SDK/canonical ledger or production action qualification')
                    if len(canonical(summary))>86016:
                        raise RuntimeError('consumer summary exceeds unchanged 86016-byte profile')
                    return summary
                """;
    }
}
