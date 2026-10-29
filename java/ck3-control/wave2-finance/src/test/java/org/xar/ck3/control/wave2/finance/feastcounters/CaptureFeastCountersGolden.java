package org.xar.ck3.control.wave2.finance.feastcounters;

/** Source provider for the single central same-host fixture process; former executable is retired. */
public final class CaptureFeastCountersGolden {
    private CaptureFeastCountersGolden() { }

    /** MapAdmissionCi owns the one Session, bootstrap, process custody, invocation and final receipt. */
    public static String source() {
        return """
                def run_feast_counter_consumer_probe(*,config:'JavaProjectionServiceV1',repository:'Path',golden_ref:'ExactRefV1',fixture_root:'Path')->dict[str,object]:
                    import copy,datetime,hashlib,json,sys
                    from pathlib import Path
                    from tools.g2_saved_campaign import java_map_admission_client_v1 as client
                    from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,exact_read
                    if not isinstance(config,client.JavaProjectionServiceV1) or config.transport is not None or client.require_current_projection_config_v1() is not config:
                        raise RuntimeError('central actual shared projection bootstrap required; no injected client/fallback')
                    if not isinstance(repository,Path) or not isinstance(fixture_root,Path) or not isinstance(golden_ref,ExactRefV1):
                        raise ValueError('explicit typed repository/golden/fresh fixture arguments required')
                    repository=repository.resolve()
                    if fixture_root.exists() or fixture_root.is_symlink() or fixture_root.is_junction() or not fixture_root.parent.is_dir():
                        raise RuntimeError('fresh separately authorized fixture root required')
                    fixture_root=fixture_root.resolve()
                    def canonical(value:object)->bytes:
                        return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+chr(10)).encode('utf-8')
                    def sha(raw:bytes)->str:
                        return hashlib.sha256(raw).hexdigest()
                    golden_bytes=exact_read(config.reader,golden_ref,65536)
                    if sha(golden_bytes)!='97130a69ec77296caed08a46e220cdce81d0b15cdb90d5819eec4e3f8d36cd4e':
                        raise RuntimeError('original immutable counter oracle differs')
                    golden=client.decode_projection_object_v1(golden_bytes,maximum_bytes=65536)
                    if golden.get('schema')!='xar.feast-counter-producer-consumer-golden/v1' or type(golden.get('producer_cases')) is not list or len(golden['producer_cases'])!=25 or type(golden.get('projection_cases')) is not list or len(golden['projection_cases'])!=9:
                        raise RuntimeError('original counter producer/consumer fixture contract differs')
                    identity=client.qualify_projection_service_v1(config)
                    native_operation=client.ProjectionOperation.FEAST_COUNTER_NORMALIZE
                    projection_operation=client.ProjectionOperation.FEAST_COUNTER_PROJECT
                    terminal_operation=client.ProjectionOperation.FEAST_TERMINAL_NORMALIZE
                    for operation,input_cap,output_cap in ((native_operation,16384,16384),(projection_operation,16384,16384),(terminal_operation,1048576,2097152)):
                        profile=identity.profile(operation)
                        if profile.input_max_bytes!=input_cap or profile.output_max_bytes!=output_cap:
                            raise RuntimeError('shared host has missing or widened Feast profile')
                    sys.dont_write_bytecode=True
                    # Root measured the frozen SDK graph; repository contains canonical tests/fixtures only.
                    import xar_autoplayer.bridge.activity_feast_stage5_start_private_transport as transport
                    import xar_autoplayer.activity_feast_stage5_start_formal_consumer as consumer
                    import xar_autoplayer.bridge.activity_feast_terminal_outcome_v1 as terminal
                    import xar_autoplayer.environment as environment
                    import test_activity_feast_stage5_start_formal_consumer as fixtures
                    from xar_autoplayer.bridge.driver import BridgeUnavailableError
                    if Path(fixtures.__file__).resolve()!=(repository/'ck3_autonomous_player/tests/unit/test_activity_feast_stage5_start_formal_consumer.py').resolve():
                        raise RuntimeError('canonical original consumer test route differs')
                    production={module:Path(module.__file__).resolve() for module in (transport,consumer,terminal,environment)}
                    origins=((transport,transport._outcome_values),(transport,transport.project_feast_counter_consumer_v1),(consumer,consumer.consume_feast_start_private_v1),(consumer,consumer._record_lifecycle_observation),(terminal,terminal.normalize_activity_feast_terminal_outcome_v1))
                    for module,function in origins:
                        if Path(function.__code__.co_filename).resolve()!=production[module] or function.__module__!=module.__name__:
                            raise RuntimeError('actual frozen SDK function origin differs')
                    if consumer.project_feast_counter_consumer_v1 is not transport.project_feast_counter_consumer_v1 or consumer.normalize_activity_feast_terminal_outcome_v1 is not terminal.normalize_activity_feast_terminal_outcome_v1:
                        raise RuntimeError('consumer no longer calls actual shared SDK delegates')
                    native=repository/'ck3_autonomous_player/native_bridge/research/fixtures'
                    paths=[*production.values(),Path(fixtures.__file__).resolve(),native/'ck3_12002_feast_outcome_values_wire.json',native/'ck3_12002_feast_outcome_values_wire_baseline.json',native/'ck3_12002_feast_hosted_post_wire.json',Path(client.__file__).resolve(),Path(config.reader_source_ref.path).resolve()]
                    def refs()->list[dict[str,object]]:
                        return [dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for path in paths]
                    before_refs=refs()
                    calls={operation.value:0 for operation in (native_operation,projection_operation,terminal_operation)}
                    chain=hashlib.sha256()
                    def retain(result)->None:
                        if not isinstance(result,client.ProjectionResult):
                            raise RuntimeError('actual shared client did not issue a typed result')
                        context=client.require_result_context_v1(result,config=config,operation=result.operation,request_id=result.request_id,payload=result.payload_bytes)
                        if context.process!=identity.process or result.host_identity.process!=identity.process or result.host_identity.identity_sha256!=identity.identity_sha256 or result.http_call.transport_kind!='stdlib-http-loopback/v1' or not result.http_call.actual_http_invoked:
                            raise RuntimeError('producer/consumer moved away from the one actual resident host')
                        if result.operation.value in calls:
                            calls[result.operation.value]+=1
                        chain.update(canonical(dict(request_id=result.request_id,operation=result.operation.value,request_sha256=result.request_sha256,payload_sha256=result.payload_sha256,response_sha256=result.response_sha256)))
                    previous_profile=sys.getprofile()
                    def observe(frame,event:str,value)->None:
                        if previous_profile is not None:
                            previous_profile(frame,event,value)
                        if event=='return' and frame.f_code is client.call_current_projection_v1.__code__ and isinstance(value,client.ProjectionResult):
                            retain(value)
                    accepted=0
                    rejected=0
                    summaries=[]
                    fixture_root.mkdir(parents=False,exist_ok=False)
                    state=fixture_root/'counter-consumers'
                    state.mkdir()
                    def inventory()->list[dict[str,object]]:
                        files=[]
                        for path in fixture_root.rglob('*'):
                            if path.is_symlink() or path.is_junction():
                                raise RuntimeError('link in isolated fixture root')
                            if path.is_file():
                                files.append(dict(relative_path=path.relative_to(fixture_root).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes())))
                        if len(files)>64 or sum(row['bytes'] for row in files)>524288:
                            raise RuntimeError('isolated counter fixture exceeds original 524288-byte/64-file scope')
                        return files
                    try:
                        sys.setprofile(observe)
                        names=set()
                        for row in golden['producer_cases']:
                            if type(row) is not dict or type(row.get('name')) is not str or row['name'] in names or type(row.get('accepted')) is not bool or type(row.get('input_json')) is not str:
                                raise RuntimeError('invalid or duplicate original producer case')
                            names.add(row['name'])
                            raw=row['input_json'].encode('utf-8')
                            original=client.decode_projection_object_v1(raw,maximum_bytes=16384)
                            try:
                                value=transport._outcome_values(original)
                            except BridgeUnavailableError as failure:
                                error=failure.__cause__
                                if row['accepted'] or not isinstance(error,client.ProjectionDomainRejected):
                                    raise RuntimeError('native producer failed without the expected real Java domain rejection') from failure
                                call=error.http_call
                                if call.operation is not native_operation or call.transport_kind!='stdlib-http-loopback/v1' or not call.actual_http_invoked or call.process_before!=identity.process or call.process_after!=identity.process or error.response_body is None:
                                    raise RuntimeError('counter rejection lacks actual same-host response evidence')
                                calls[native_operation.value]+=1
                                chain.update(canonical(dict(name=row['name'],rejection=error.code,request_sha256=call.request_sha256,response_sha256=call.response_sha256)))
                                rejected+=1
                            else:
                                if not row['accepted'] or canonical(value)!=canonical(row['result']):
                                    raise RuntimeError('actual native four-field producer differs from the original oracle')
                                accepted+=1
                        trace=client.decode_projection_json_v1((native/'ck3_12002_feast_outcome_values_wire.json').read_bytes(),maximum_bytes=65536)
                        if type(trace) is not list or len(trace)<2:
                            raise RuntimeError('archived counter producer trace unavailable')
                        helper=fixtures.FeastLifecycleConsumerTest()
                        helper.setUp()
                        names=set()
                        value_keys={'pre_start_outcome_values','outcome_values','counter_changes','reveler_presence_transition','counter_values_observed','counter_changes_attributed_to_feast'}
                        for row in golden['projection_cases']:
                            if type(row) is not dict or type(row.get('name')) is not str or row['name'] in names or type(row.get('input_json')) is not str or type(row.get('expected')) is not dict or set(row['expected'])!=value_keys or type(row.get('actual_counter_read_pending_after_start')) is not bool:
                                raise RuntimeError('invalid original consumer projection case')
                            names.add(row['name'])
                            pair=client.decode_projection_object_v1(row['input_json'].encode('utf-8'),maximum_bytes=16384)
                            if set(pair)!={'before','after'}:
                                raise RuntimeError('counter before/after contract differs')
                            before=pair['before']
                            after=pair['after']
                            normalized_before=None if before is None else transport._outcome_values(before)
                            normalized_after=None if after is None else transport._outcome_values(after)
                            consumer._write(state,dict(schema=consumer.LEDGER_SCHEMA,pending=None,resolved=None))
                            start_post=copy.deepcopy(trace[0])
                            observed_post=copy.deepcopy(trace[1])
                            project_before=calls[projection_operation.value]
                            if normalized_before is not None:
                                start_post['outcome_values']=normalized_before
                                driver=helper.start_with_counter_baseline(state,start_post)
                            else:
                                start_post.pop('outcome_values',None)
                                driver=fixtures.Driver(state)
                                driver.post=start_post
                                driver.native_build_12002=True
                                driver.date_raw=start_post['date_raw']
                                driver.actor_character_id=start_post['actor_character_id']
                                driver.native_revision=start_post['snapshot_revision']-1
                                qualified=client.decode_projection_object_v1((native/'ck3_12002_feast_outcome_values_wire_baseline.json').read_bytes(),maximum_bytes=65536)
                                qualified.pop('outcome_values',None)
                                qualified.update(native_guest_route_qualified=True,actor_character_id=driver.actor_character_id,date_raw=driver.date_raw,snapshot_revision=driver.native_revision,queried_snapshot_id='native:'+str(driver.native_revision),queried_revision=5,balances=copy.deepcopy(start_post['balances']))
                                qualified['balances']['gold']['raw']+=1000000
                                guest=dict(fixtures.guest(),actor_character_id=driver.actor_character_id,date_raw=driver.date_raw,snapshot_revision=driver.native_revision)
                                result=consumer.consume_feast_start_private_v1(driver,inputs=qualified,guest=guest,budget=dict(fixtures.budget(),gold_floor_raw=0))
                                if result['status']!='applied':
                                    raise RuntimeError('actual missing-group Start consumer did not settle')
                            ledger=consumer.read_feast_start_ledger(state)
                            resolved=ledger['resolved']
                            seed=resolved['source_pending']['pre_outcome_values']
                            if canonical(seed)!=canonical(row['actual_start_seed']) or consumer._terminal_counter_read_pending(resolved) is not row['actual_counter_read_pending_after_start'] or calls[projection_operation.value]<=project_before:
                                raise RuntimeError('actual Java seed changed persisted group presence, contents, reader timing or Start did not traverse shared Java')
                            if normalized_after is None:
                                observed_post.pop('outcome_values',None)
                            else:
                                observed_post['outcome_values']=normalized_after
                            project_before=calls[projection_operation.value]
                            updated=consumer._record_lifecycle_observation(state,ledger,resolved,observed_post)
                            view={key:updated['lifecycle']['value_observation'][key] for key in value_keys}
                            persisted=consumer.read_feast_start_ledger(state)['resolved']
                            stored_view={key:persisted['lifecycle']['value_observation'][key] for key in value_keys}
                            if canonical(view)!=canonical(row['expected']) or canonical(stored_view)!=canonical(view) or calls[projection_operation.value]<=project_before:
                                raise RuntimeError('actual lifecycle consumer/JSON roundtrip differs from the six-field oracle or missed the common host')
                            files=inventory()
                            summaries.append(dict(name=row['name'],actual_start_seed_sha256=sha(canonical(seed)),actual_value_projection_sha256=sha(canonical(view)),counter_read_pending_after_start=consumer._terminal_counter_read_pending(resolved),retained_fixture_bytes=sum(item['bytes'] for item in files)))
                    finally:
                        sys.setprofile(previous_profile)
                    after_identity=client.qualify_projection_service_v1(config)
                    if accepted+rejected!=25 or len(summaries)!=9 or any(count==0 for count in calls.values()) or refs()!=before_refs or exact_read(config.reader,golden_ref,65536)!=golden_bytes or after_identity.process!=identity.process or after_identity.identity_sha256!=identity.identity_sha256:
                        raise RuntimeError('counter vectors, source/golden or single resident-host proof incomplete')
                    final_files=inventory()
                    summary=dict(schema='xar.feast-counter-same-host-consumer-probe/v2',machine_id=config.machine_id,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='pass',source_refs=before_refs,source_golden=dict(reference=golden_ref.to_wire(),machine_id=golden.get('machine_id')),host=dict(process=identity.process.to_wire(),identity_sha256=identity.identity_sha256,service_evidence_ref=config.service.service_evidence_ref.to_wire(),program_ref=config.service.program_ref.to_wire(),client_source_ref=config.client_source_ref.to_wire(),reader_source_ref=config.reader_source_ref.to_wire()),producer_cases=dict(total=25,accepted=accepted,rejected=rejected),consumer_cases=dict(total=9,actual_Start_seed_matches=True,actual_lifecycle_subtree_and_JSON_roundtrip_match=True,summaries=summaries),actual_projection_calls=dict(by_operation=calls,request_response_chain_sha256=chain.hexdigest(),transport='stdlib-http-loopback/v1',same_resident_process=True),fixture_write_scope=dict(root=str(fixture_root),maximum_bytes=524288,maximum_files=64,retained_bytes=sum(row['bytes'] for row in final_files),files=final_files),scope='actual native counter producer and actual Start/lifecycle consumers via the one source-qualified client and one resident host; isolated original fixture writer only; no Game/SDK/canonical ledger or action qualification')
                    if len(canonical(summary))>65536:
                        raise RuntimeError('counter summary exceeds unchanged 65536-byte capture profile')
                    return summary
                """;
    }
}
