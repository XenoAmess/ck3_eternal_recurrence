package org.xar.ck3.control.wave3.governance.governmentquery;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit Java fixture capture of unchanged original query and real fixture driver. */
public final class CaptureGovernmentQueryGolden {
    private CaptureGovernmentQueryGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository-root existing-python output-json"); }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("never overwrite a captured original"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var reader = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = reader.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(75, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original query capture timeout");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) {
            throw new IllegalStateException("original query capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Original government query capture: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,copy,importlib.util,unittest,subprocess,datetime
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            refs=['ck3_autonomous_player/src/xar_autoplayer/bridge/government_runtime_adapter_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/tests/unit/test_g2_government_python_wire.py','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_government_adapter_available.json','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_government_adapter_unavailable.json','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_government_adapter_actual_caller_unavailable.json','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_government_adapter_python_provenance.json']
            def sources():return [{'path':rel,'bytes':len((root/rel).read_bytes()),'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()} for rel in refs]
            before=sources()
            spec=importlib.util.spec_from_file_location('original_government_query_tests',root/refs[3]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            tests=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(module))
            if not tests.wasSuccessful() or tests.testsRun!=7 or tests.skipped:sys.exit(2)
            from xar_autoplayer.bridge.government_runtime_adapter_private_transport import query_government_runtime_adapter_private_v1 as query
            class Driver(module.NativeWireDriver):
                def __init__(self,value):
                    super().__init__(value);self.after=copy.deepcopy(self.snapshot);self.reads=0;self.packet_mutation=None;self.packet=None
                def take_snapshot(self):
                    self.reads+=1;return copy.deepcopy(self.snapshot if self.reads==1 else self.after)
                def wait_for_command_result(self,request_id,timeout):
                    result=super().wait_for_command_result(request_id,timeout)
                    if self.packet_mutation:self.packet_mutation(result)
                    self.packet=copy.deepcopy(result);return result
            def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
            def patch(before,after,path=''):
                if isinstance(before,dict) and isinstance(after,dict):
                    result=[]
                    for key in before.keys()-after.keys():result.append({'op':'remove','path':path+'/'+key})
                    for key in after:
                        at=path+'/'+key
                        if key not in before:result.append({'op':'set','path':at,'value':after[key]})
                        elif before[key]!=after[key]:result.extend(patch(before[key],after[key],at))
                    return result
                return [] if before==after else [{'op':'set','path':path,'value':after}]
            raw_cases=[]
            def add(name,mutation=None,wire='available',expected_revision=702):
                driver=Driver(module.wire(wire))
                if mutation:mutation(driver)
                expected=None;failure=None
                try:expected=query(driver,expected_revision=expected_revision)
                except Exception as error:failure={'python_type':type(error).__name__,'message':str(error)}
                request_id=driver.requests[0]['request_id'] if driver.requests else 'fixture-not-submitted'
                prepare={'schema':'xar.java-government-query-prepare/v1','query_enabled':driver.allow_private_government_runtime_adapter_query,'expected_revision':expected_revision,'request_id':request_id,'before_snapshot':copy.deepcopy(driver.snapshot)}
                consume=None if driver.packet is None else {'schema':'xar.java-government-query-consume/v1','expected_revision':expected_revision,'request_id':request_id,'before_snapshot':copy.deepcopy(driver.snapshot),'after_snapshot':copy.deepcopy(driver.after),'command_result':driver.packet}
                raw_cases.append({'name':name,'prepare':prepare,'consume':consume,'expected_request':None if not driver.requests else driver.requests[0],'expected_output_sha256':None if expected is None else digest(expected),'expected_status':None if expected is None else expected['status'],'failure':failure,'native_read_request_count':len(driver.requests)})
            add('actual_available_query_producer')
            add('actual_native_unavailable',wire='unavailable')
            add('disabled_no_send',lambda d:setattr(d,'allow_private_government_runtime_adapter_query',False))
            add('stale_public_revision_no_send',expected_revision=703)
            add('unpaused_no_send',lambda d:d.snapshot.update(paused=False))
            add('map_not_ready_no_send',lambda d:d.snapshot.update(map_ready=False))
            add('dead_actor_no_send',lambda d:d.snapshot['played_character'].update(alive=False))
            add('zero_native_revision_no_send',lambda d:d.snapshot.update(native_revision=0))
            add('correlation_differs',lambda d:setattr(d,'packet_mutation',lambda p:p.update(request_id='wrong-original-correlation')))
            add('command_red',lambda d:setattr(d,'packet_mutation',lambda p:p.update(ok=False)))
            add('accepted_flag_false',lambda d:setattr(d,'packet_mutation',lambda p:p['result'].update(accepted=False)))
            add('source_revision_stale',lambda d:d.value.update(snapshot_revision=702))
            add('post_date_changed',lambda d:d.after.update(date_raw=d.after['date_raw']+1))
            add('post_actor_changed',lambda d:d.after['played_character'].update(alive=False))
            add('post_full_actor_extension_changed',lambda d:d.after['played_character'].update(name='changed-observed-name'))
            add('post_native_progress_allowed',lambda d:d.after.update(native_revision=702,snapshot_id='native:702'))
            add('post_map_flag_is_not_an_added_veto',lambda d:d.after.update(map_ready=False))
            base_prepare=raw_cases[0]['prepare'];base_consume=raw_cases[0]['consume'];cases=[]
            for row in raw_cases:
                cases.append({key:value for key,value in row.items() if key not in {'prepare','consume'}}|{'prepare_patch':patch(base_prepare,row['prepare']),'consume_patch':None if row['consume'] is None else patch(base_consume,row['consume'])})
            after=sources()
            if before!=after:raise RuntimeError('original query source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.java-government-query-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'historical_fixture_machine_id':'unknown','scope':'Original unchanged query transport + existing NativeWireDriver over checked-in actual native CPP serializer fixtures. Synthetic outer frame/correlation/mutation seams are explicit; no Game, Steam or live native pipe.','source_refs':before,'source_refs_unchanged':True,'original_unittest':{'tests':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'skipped':len(tests.skipped)},'base_prepare':base_prepare,'base_consume':base_consume,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
