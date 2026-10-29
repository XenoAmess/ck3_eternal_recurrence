package org.xar.ck3.control.wave3.governance.crownfinalterms;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit existing Python query and actual C++ serializer fixture capture. */
public final class CaptureCrownFinalTermsGolden {
    private CaptureCrownFinalTermsGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository-root existing-python output-json"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("never overwrite an original capture"); }
        Path scratch = Path.of(arguments[3]).toAbsolutePath().normalize();
        Path owned = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/governance-resume02/government-lifestyle").toRealPath();
        if (!scratch.startsWith(owned) || !output.startsWith(owned) || Files.exists(scratch)) throw new IllegalArgumentException("fresh owned D scratch/output required");
        Files.createDirectory(scratch);
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-X", "utf8", "-", root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("TEMP", scratch.toString()); builder.environment().put("TMP", scratch.toString());
        Process child = builder.start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
        catch (Exception failure) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); child.waitFor(); throw failure; }
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(262_145));
            if (!child.waitFor(60, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original full-cost law capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } child.waitFor(); }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 262_144) {
            throw new IllegalStateException("original full-cost law capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT).onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                .decode(java.nio.ByteBuffer.wrap(raw));
        java.io.ByteArrayOutputStream aggregate = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(aggregate)) { gzip.write(raw); }
        byte[] stored = aggregate.toByteArray();
        if (stored.length > 32768) throw new IllegalStateException("aggregate compressed golden exceeds 32KiB");
        Files.createDirectories(output.getParent()); Files.write(output, stored, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original full-cost law query: " + raw.length + " raw bytes, " + stored.length + " gzip bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,copy,subprocess,datetime,importlib.util,unittest
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/realm_law_paused_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/crown_authority_cooldown_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/tests/unit/test_realm_law_paused_private_transport.py','ck3_autonomous_player/tests/unit/test_ck3_12002_sway_law_transport_wire.py','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_final_terms_wire.json','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_final_terms_wire.provenance.json']
            def refs():return [{'path':p,'bytes':len((root/p).read_bytes()),'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths]
            before_refs=refs()
            def module(name,path):
                spec=importlib.util.spec_from_file_location(name,root/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
            original=module('original_law_transport_tests',paths[4]);wire=module('original_law_cpp_wire_tests',paths[5])
            suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(original),wire.SwayLaw12002WireTest('test_native_law_costs_and_copied_reasons_survive_python_read')])
            tested=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
            if not tested.wasSuccessful() or tested.testsRun!=4 or tested.skipped:sys.exit(2)
            from xar_autoplayer.bridge.realm_law_paused_private_transport import query_realm_law_final_terms_private_v1 as query,_valid_payload,STEP,COOLDOWN_FIELD,COOLDOWN_TURN_TICK_FIELD,COOLDOWN_EXPIRY_TYPE,COOLDOWN_REMAINING_UNIT,COOLDOWN_PROJECTED_REMAINING_UNIT,COOLDOWN_TURN_TICK_SOURCE
            from xar_autoplayer.bridge.version_identity import CK3_12003,CK3_12004
            native=wire.envelope('ck3_12002_realm_law_final_terms_wire.json');base_before=wire.paused_frame(native)
            base_envelope={'step':STEP,'accepted':True,'status':'available','private_build':True,'read_only':True,'advertised':False,'realm_law_final_terms':native,'backend_id':'native-headless'}
            def patch(before,after,path=''):
                if isinstance(before,dict) and isinstance(after,dict):
                    changes=[]
                    for key in sorted(before.keys()-after.keys()):changes.append({'op':'remove','path':path+'/'+key})
                    for key in after:
                        at=path+'/'+key
                        if key not in before:changes.append({'op':'set','path':at,'value':after[key]})
                        elif before[key]!=after[key]:changes.extend(patch(before[key],after[key],at))
                    return changes
                return [] if before==after else [{'op':'set','path':path,'value':after}]
            class Driver(wire.FixtureDriver):
                def __init__(self):
                    super().__init__(copy.deepcopy(base_envelope),copy.deepcopy(base_before));self.after=copy.deepcopy(base_before);self.transform=None;self.last_command=None
                def take_snapshot(self):return copy.deepcopy(self.after if self.sent else self.snapshot)
                def wait_for_command_result(self,request_id,timeout):
                    value=super().wait_for_command_result(request_id,timeout)
                    if self.transform:self.transform(value)
                    self.last_command=copy.deepcopy(value);return value
            cases=[];base_prepare=None;base_consume=None;base_result=None
            def add(name,mutation=None):
                global base_prepare,base_consume,base_result
                driver=Driver()
                if mutation:mutation(driver)
                expected_revision=base_before['revision'];result=None;error=None
                try:result=query(driver,expected_revision=expected_revision)
                except (ValueError,RuntimeError) as failure:error={'type':type(failure).__name__,'message':str(failure)}
                request_id=driver.sent[0]['request_id'] if driver.sent else 'fixture-no-send-'+name
                prepare={'schema':'xar.java-crown-final-terms-prepare/v1','query_enabled':driver.allow_private_realm_law_paused_query,'expected_revision':expected_revision,'request_id':request_id,'before_snapshot':driver.snapshot}
                consume={'schema':'xar.java-crown-final-terms-consume/v1','expected_revision':expected_revision,'request_id':request_id,'before_snapshot':driver.snapshot,'after_snapshot':driver.after,'command_result':driver.last_command}
                if base_prepare is None:base_prepare=copy.deepcopy(prepare);base_consume=copy.deepcopy(consume);base_result=copy.deepcopy(result)
                if error is None and result is None:raise RuntimeError('original query produced neither result nor rejection')
                cases.append({'name':name,'prepare_patch':patch(base_prepare,prepare),'consume_patch':patch(base_consume,consume),'sent_count':len(driver.sent),'actual_request':driver.sent[0] if driver.sent else None,'expected_readback_patch':patch(base_result,result) if error is None else None,'legacy_error':error})
            def modern(driver,build=CK3_12004):
                driver.snapshot['diagnostics']['hello'].update(expected_ck3_version=build.game_version,expected_ck3_sha256=build.executable_sha256)
                driver.after=copy.deepcopy(driver.snapshot)
                for row in driver.reply['realm_law_final_terms']['groups'][1]['candidates']:row.update(succession_profile_status='absent',succession_profile=None)
            def available(driver):
                modern(driver,CK3_12003)
                driver.reply['realm_law_final_terms']['groups'][1]['candidates'][1].update(succession_profile_status='available',succession_profile={'order':'inheritance','traversal':'children','rank':'oldest','division':'partition','primary_heir_minimum_share_raw':50000,'primary_heir_minimum_share_scale':100000,'create_primary_tier_titles':True})
            def raw_clock(driver):
                modern(driver);driver.reply['realm_law_final_terms'][COOLDOWN_FIELD]={'read_available':True,'present':True,'timed':True,'expiry_raw':110,'current_clock_raw':100,'remaining_raw':10,'retry_date_raw':None,'expiry_type':COOLDOWN_EXPIRY_TYPE,'remaining_unit':COOLDOWN_REMAINING_UNIT}
            def projected(driver):
                raw_clock(driver);value=driver.reply['realm_law_final_terms'];value[COOLDOWN_FIELD].update(remaining_unit=COOLDOWN_PROJECTED_REMAINING_UNIT,retry_date_raw=base_before['date_raw']+5*24)
                value[COOLDOWN_TURN_TICK_FIELD]={'source':COOLDOWN_TURN_TICK_SOURCE,'read_available':True,'manager_match_count':2,'manager_contains_context':True,'scalar_tail_allows_tick':True,'context_tick_eligible':True,'unavailable_reason':None}
            def both(first,second):return lambda d:(first(d),second(d))
            add('actual_cpp_serializer_fixture_query')
            add('archived_119_contract_without_hello',lambda d:(d.snapshot.pop('diagnostics'),d.after.pop('diagnostics')))
            add('explicit_12003_available_succession_profile',available)
            add('explicit_12004_absent_profile_and_raw_timed_counter',raw_clock)
            add('explicit_12004_same_query_projected_clock',projected)
            add('signed64_cost_extremes_retained',lambda d:d.reply['realm_law_final_terms']['groups'][0]['candidates'][1].update(cost_raw=[-(1<<63),(1<<63)-1]+[0]*8))
            add('nullable_native_succession_selectors',both(available,lambda d:d.reply['realm_law_final_terms']['groups'][1]['candidates'][1]['succession_profile'].update(order=None,traversal=None,rank=None,division=None)))
            add('query_disabled_no_send',lambda d:setattr(d,'allow_private_realm_law_paused_query',False))
            add('stale_public_revision_no_send',lambda d:d.snapshot.update(revision=base_before['revision']+1))
            add('unpaused_before_no_send',lambda d:d.snapshot.update(paused=False))
            add('dead_actor_before_no_send',lambda d:d.snapshot['played_character'].update(alive=False))
            add('zero_native_revision_no_send',lambda d:d.snapshot.update(native_revision=0))
            add('unknown_exact_build_no_send',lambda d:d.snapshot['diagnostics']['hello'].update(expected_ck3_sha256='0'*64))
            add('truncated_ten_slot_cost',lambda d:d.reply['realm_law_final_terms']['groups'][0]['candidates'][1].update(cost_raw=[0]*6))
            add('reordered_cost_slots',lambda d:d.reply['realm_law_final_terms']['cost_slots'].reverse())
            add('duplicate_law_key',lambda d:d.reply['realm_law_final_terms']['groups'][0]['candidates'][1].update(law_key='crown_authority_0'))
            add('active_law_key_mismatch',lambda d:d.reply['realm_law_final_terms']['groups'][0].update(active_law_key=None))
            add('native_verdict_status_disagrees',lambda d:d.reply['realm_law_final_terms']['groups'][0]['candidates'][1].update(final_can_enact=False))
            add('modern_succession_fields_missing',both(lambda d:modern(d),lambda d:d.reply['realm_law_final_terms']['groups'][1]['candidates'][0].pop('succession_profile_status')))
            add('unknown_succession_selector',both(available,lambda d:d.reply['realm_law_final_terms']['groups'][1]['candidates'][1]['succession_profile'].update(order='fixture_unknown')))
            add('projected_clock_without_same_query_tick',both(projected,lambda d:d.reply['realm_law_final_terms'].pop(COOLDOWN_TURN_TICK_FIELD)))
            add('projected_clock_wrong_same_query_count',both(projected,lambda d:d.reply['realm_law_final_terms'][COOLDOWN_TURN_TICK_FIELD].update(manager_match_count=3)))
            add('command_correlation_mismatch',lambda d:setattr(d,'transform',lambda c:c.update(request_id='foreign-command')))
            add('missing_command_protocol_version',lambda d:setattr(d,'transform',lambda c:c.pop('protocol_version')))
            add('native_red_retains_original_reason',lambda d:setattr(d,'transform',lambda c:c.update(ok=False,error='fixture-native-red')))
            add('envelope_extra_field',lambda d:d.reply.update(unmigrated_extra=True))
            add('outer_revision_mismatch',lambda d:d.reply.update(snapshot_revision=base_before['native_revision']+1))
            add('payload_revision_mismatch',lambda d:d.reply['realm_law_final_terms'].update(snapshot_revision=base_before['native_revision']+1))
            add('after_date_changed',lambda d:d.after.update(date_raw=base_before['date_raw']+24))
            add('after_full_actor_changed',lambda d:d.after['played_character'].update(unmigrated_actor_metadata='different'))
            add('after_map_not_ready',lambda d:d.after.update(map_ready=False))
            add('later_native_revision_same_actor_date_allowed',lambda d:d.after.update(native_revision=base_before['native_revision']+1,snapshot_id='native:later'))
            negatives=[]
            for name,mutation in [('float_payload_revision',lambda p:p.update(snapshot_revision=float(native['snapshot_revision']))),('bool_actor_identity',lambda p:p.update(actor_character_id=True)),('float_cost_scale',lambda p:p.update(cost_scale=100000.0)),('bool_native_cost',lambda p:p['groups'][0]['candidates'][0]['cost_raw'].__setitem__(0,False))]:
                payload=copy.deepcopy(native);mutation(payload)
                request={'schema':'xar.java-crown-final-terms-payload/v1','expected_revision':native['snapshot_revision'],'date_raw':native['date_raw'],'actor_character_id':native['actor_character_id'],'exact_ck3_build':'1.20.0.2','payload':payload}
                negatives.append({'name':name,'raw_request_json':json.dumps(request,separators=(',',':'),ensure_ascii=False,allow_nan=False),'legacy_payload_valid':_valid_payload(payload,revision=native['snapshot_revision'],date_raw=native['date_raw'],actor_id=native['actor_character_id'],exact_ck3_build='1.20.0.2'),'expected_java_wire_rejection':True})
            after_refs=refs()
            if before_refs!=after_refs:raise RuntimeError('original query/helper/input source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.java-crown-final-terms-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'historical_fixture_machine_id':'unknown','scope':'Unchanged original full-cost law query and payload predicate, all three original isolated transport unittests and the actual existing C++ serializer wire consumer test. Eight explicit file pins, not complete transitive SDK qualification. Existing FixtureDriver supplies archived native-produced wire; modern profiles/clocks/before-after changes are explicit offline fixture seams. No native pipe, Game, action or SDK runtime qualification.','source_refs':before_refs,'source_refs_unchanged':True,'original_unittest':{'tests':tested.testsRun,'failures':len(tested.failures),'errors':len(tested.errors),'skipped':len(tested.skipped)},'base_prepare':base_prepare,'base_consume':base_consume,'base_readback':base_result,'cases':cases,'wire_rejections':negatives}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
